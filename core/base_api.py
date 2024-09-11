#!/usr/bin/env python3
"""
Base API client with common patterns for all services.
Provides retry logic, error handling, and rate limiting.
"""

import os
import time
import json
import requests
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

class RateLimiter:
    """Simple rate limiter to prevent API throttling"""
    def __init__(self, requests_per_second: float = 10):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()

class BaseAPI(ABC):
    """
    Base API client that all service APIs inherit from.
    Provides common functionality like retry, auth, and error handling.
    """
    
    def __init__(self, api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 requests_per_second: float = 10,
                 max_retries: int = 3,
                 validate_responses: bool = False,
                 service_name: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limiter = RateLimiter(requests_per_second)
        self.max_retries = max_retries
        self.session = requests.Session()
        self.usage_patterns = []
        self.validate_responses = validate_responses
        self.service_name = service_name or self.__class__.__name__.replace('API', '').lower()
        self.doc_manager = None

        # Initialize documentation manager if validation is enabled
        if self.validate_responses:
            self._init_doc_manager()

        self._setup_auth()
    
    @abstractmethod
    def _setup_auth(self):
        """Setup authentication headers - implemented by each service"""
        pass
    
    def _init_doc_manager(self):
        """Initialize documentation manager for validation"""
        try:
            from documentation import DocumentationManager
            self.doc_manager = DocumentationManager(self.service_name)
        except ImportError:
            print(f"Warning: DocumentationManager not available for {self.service_name}")
            self.validate_responses = False

    def _make_request(self, method: str, endpoint: str,
                     data: Optional[Dict] = None,
                     params: Optional[Dict] = None,
                     headers: Optional[Dict] = None,
                     validate: Optional[bool] = None) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling.
        Records successful patterns for documentation.
        Optionally validates against OpenAPI schema.
        """
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith('http') else endpoint

        # Validate request if enabled
        if (validate or self.validate_responses) and self.doc_manager and data:
            try:
                self.doc_manager.validate_request(endpoint, method, data)
            except Exception as e:
                print(f"Request validation warning: {e}")

        retry_count = 0
        last_error = None

        while retry_count < self.max_retries:
            try:
                self.rate_limiter.wait_if_needed()

                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                )

                if response.status_code >= 500:
                    # Server error - retry
                    retry_count += 1
                    last_error = APIError(
                        f"Server error: {response.status_code}",
                        response.status_code,
                        response.text
                    )
                    time.sleep(2 ** retry_count)  # Exponential backoff
                    continue

                if response.status_code >= 400:
                    # Client error - don't retry
                    raise APIError(
                        f"Client error: {response.status_code} - {response.text}",
                        response.status_code,
                        response.text
                    )
                
                # Success - record pattern and return
                self._record_usage(method, endpoint, data, params, response.status_code)
                
                if response.status_code == 204:
                    return {}
                
                return response.json() if response.text else {}
                
            except requests.exceptions.RequestException as e:
                retry_count += 1
                last_error = e
                if retry_count < self.max_retries:
                    time.sleep(2 ** retry_count)
        
        raise APIError(f"Max retries exceeded. Last error: {last_error}")
    
    def _record_usage(self, method: str, endpoint: str, 
                     data: Optional[Dict], params: Optional[Dict], 
                     status_code: int):
        """Record successful API patterns for documentation"""
        pattern = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'endpoint': endpoint,
            'has_data': data is not None,
            'has_params': params is not None,
            'status_code': status_code
        }
        self.usage_patterns.append(pattern)
        
        # Save patterns to file for learning
        patterns_file = f"services/{self.__class__.__name__.lower()}/patterns.json"
        if os.path.exists(os.path.dirname(patterns_file)):
            try:
                with open(patterns_file, 'w') as f:
                    json.dump(self.usage_patterns[-100:], f, indent=2)  # Keep last 100
            except:
                pass  # Silently fail pattern recording
    
    def get_usage_patterns(self) -> List[Dict]:
        """Get recorded usage patterns for documentation"""
        return self.usage_patterns
    
    def test_connection(self) -> bool:
        """Test if API connection is working - override in subclass"""
        return True