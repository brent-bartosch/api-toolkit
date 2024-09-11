#!/usr/bin/env python3
"""
Configuration management for API toolkit.
Handles environment variables and service registry.
"""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables with smart fallback strategy
# Priority order:
# 1. Project root (where user is working) - HIGHEST PRIORITY
# 2. Toolkit directory (for standalone toolkit usage)
# 3. User home directory (global fallback)

def _load_env_with_priority():
    """Load .env with intelligent priority-based search"""
    locations = [
        # 1. PROJECT ROOT - Check current working directory first
        Path.cwd() / '.env',

        # 2. TOOLKIT ROOT - For standalone usage
        Path(__file__).parent.parent / '.env',

        # 3. HOME FALLBACK - Global config
        Path.home() / '.api-toolkit.env'
    ]

    loaded_from = None
    for env_path in locations:
        if env_path.exists():
            load_dotenv(env_path, override=False)  # Don't override already-set vars
            if not loaded_from:  # Track first successful load
                loaded_from = env_path

    return loaded_from

# Execute env loading
_env_loaded_from = _load_env_with_priority()

class Config:
    """Centralized configuration management"""
    
    # Service configurations with project references
    SERVICES = {
        'supabase': {
            'projects': {
                'project1': 'your-project-1-ref',
                'project2': 'your-project-2-ref',
                'project3': 'your-project-3-ref'
            },
            'env_vars': ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY'],
            'token_cost': 600
        },
        'klaviyo': {
            'env_vars': ['KLAVIYO_API_KEY'],
            'lists': {
                'example_list': 'your-list-id'
            },
            'flows': {
                'example_flow': 'your-flow-id'
            },
            'token_cost': 500
        },
        'render': {
            'env_vars': ['RENDER_API_KEY'],
            'token_cost': 400
        },
        'brightdata': {
            'env_vars': ['BRIGHTDATA_API_KEY'],
            'token_cost': 500
        },
        'shopify': {
            'env_vars': ['SHOPIFY_SHOP_DOMAIN', 'SHOPIFY_ACCESS_TOKEN'],
            'token_cost': 600
        }
    }
    
    @classmethod
    def get_api_key(cls, service: str, key_name: Optional[str] = None) -> Optional[str]:
        """Get API key for a service from environment"""
        if key_name:
            return os.getenv(key_name)
        
        if service not in cls.SERVICES:
            return None
        
        env_vars = cls.SERVICES[service].get('env_vars', [])
        if env_vars:
            # Return first API key found
            for var in env_vars:
                if 'KEY' in var or 'TOKEN' in var:
                    value = os.getenv(var)
                    if value:
                        return value
        return None
    
    @classmethod
    def get_service_config(cls, service: str) -> Dict[str, Any]:
        """Get configuration for a specific service"""
        return cls.SERVICES.get(service, {})
    
    @classmethod
    def get_token_cost(cls, service: str) -> int:
        """Get estimated token cost for loading a service"""
        return cls.SERVICES.get(service, {}).get('token_cost', 1000)
    
    @classmethod
    def list_services(cls) -> list:
        """List all available services"""
        return list(cls.SERVICES.keys())

    @classmethod
    def get_env_source(cls) -> Optional[str]:
        """Get the path where environment variables were loaded from"""
        return str(_env_loaded_from) if _env_loaded_from else None
    
    @classmethod
    def check_environment(cls, service: str) -> Dict[str, bool]:
        """Check if required environment variables are set"""
        if service not in cls.SERVICES:
            return {'error': f'Unknown service: {service}'}
        
        env_vars = cls.SERVICES[service].get('env_vars', [])
        status = {}
        for var in env_vars:
            status[var] = os.getenv(var) is not None
        
        return status
    
    @classmethod
    def save_pattern(cls, service: str, pattern_type: str, pattern: Dict):
        """Save a usage pattern for future reference"""
        patterns_dir = Path(f"services/{service}/patterns")
        patterns_dir.mkdir(parents=True, exist_ok=True)
        
        patterns_file = patterns_dir / f"{pattern_type}.json"
        
        existing = []
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                existing = json.load(f)
        
        existing.append(pattern)
        
        # Keep only last 50 patterns per type
        with open(patterns_file, 'w') as f:
            json.dump(existing[-50:], f, indent=2)
    
    @classmethod
    def load_patterns(cls, service: str, pattern_type: str) -> list:
        """Load saved usage patterns"""
        patterns_file = Path(f"services/{service}/patterns/{pattern_type}.json")
        
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                return json.load(f)
        
        return []