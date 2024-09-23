#!/usr/bin/env python3
"""
API Toolkit - Lightweight alternative to MCP servers
Token usage: ~500-1000 per service vs 90,000 for MCP

Usage:
    python toolkit.py [service] [command] [args...]
    
Examples:
    python toolkit.py supabase query users
    python toolkit.py supabase test
    python toolkit.py list
"""

import sys
import os
import json
import importlib.util
from pathlib import Path
from typing import Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.documentation import Documentation

class APIToolkit:
    """
    Master toolkit for managing API services.
    Lazy loads services only when needed.
    """
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.services_path = self.base_path / "services"
        self._loaded_services = {}
    
    def list_services(self) -> list:
        """List all available services"""
        services = []
        for service_dir in self.services_path.iterdir():
            if service_dir.is_dir() and not service_dir.name.startswith('_'):
                api_file = service_dir / "api.py"
                if api_file.exists():
                    services.append(service_dir.name)
        return services
    
    def get_service(self, service_name: str, project: Optional[str] = None):
        """
        Load and return a service API client.
        Services are cached after first load.
        """
        cache_key = f"{service_name}:{project or 'default'}"
        
        if cache_key in self._loaded_services:
            return self._loaded_services[cache_key]
        
        # Check if service exists
        service_path = self.services_path / service_name
        if not service_path.exists():
            raise ValueError(f"Service '{service_name}' not found")
        
        api_file = service_path / "api.py"
        if not api_file.exists():
            raise ValueError(f"Service '{service_name}' has no api.py file")
        
        # Dynamically import the service module
        spec = importlib.util.spec_from_file_location(
            f"services.{service_name}.api", 
            api_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find the API class (assumes it ends with 'API')
        api_class = None
        for name in dir(module):
            if name.endswith('API') and not name.startswith('Base'):
                api_class = getattr(module, name)
                break
        
        if not api_class:
            raise ValueError(f"No API class found in {service_name}")
        
        # Instantiate with project if applicable
        if service_name == 'supabase' and project:
            instance = api_class(project)
        else:
            instance = api_class()
        
        self._loaded_services[cache_key] = instance
        return instance
    
    def get_documentation(self, service_name: str, level: str = 'quick') -> str:
        """Get documentation for a service"""
        doc = Documentation(service_name)
        return doc.get_context(level)
    
    def check_environment(self, service_name: str) -> dict:
        """Check if service environment is configured"""
        return Config.check_environment(service_name)
    
    def get_token_cost(self, service_name: str) -> int:
        """Get estimated token cost for a service"""
        return Config.get_token_cost(service_name)
    
    def run_command(self, service_name: str, command: str, *args):
        """Run a command for a specific service"""
        try:
            # Special handling for multi-project services
            project = None
            if service_name == 'supabase' and args and args[0] in ['main', 'project2', 'project3', 'project1', 'project2', 'project3']:
                project = args[0]
                args = args[1:]
            
            api = self.get_service(service_name, project)
            
            # Map common commands to methods
            if command == 'test':
                return api.test_connection()
            
            elif hasattr(api, command):
                method = getattr(api, command)
                return method(*args)
            
            else:
                return f"Unknown command: {command}"
        
        except Exception as e:
            return f"Error: {e}"


def main():
    """CLI interface for the toolkit"""
    toolkit = APIToolkit()
    
    if len(sys.argv) < 2:
        print("API Toolkit - Lightweight alternative to MCP servers")
        print("Token usage: ~500-1000 per service vs 90,000 for MCP\n")
        print("Usage: python toolkit.py [service] [command] [args...]\n")
        print("Commands:")
        print("  list                          - List available services")
        print("  [service] test                - Test service connection")
        print("  [service] docs [level]        - Get service documentation")
        print("  [service] check               - Check environment setup")
        print("  [service] [command] [args...] - Run service command\n")
        print("Examples:")
        print("  python toolkit.py list")
        print("  python toolkit.py supabase test")
        print("  python toolkit.py supabase query smoothed users")
        print("  python toolkit.py context7 quick_start")
        print("  python toolkit.py context7 search 'react hooks'")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == 'list':
        print("Available services:")
        for service in toolkit.list_services():
            cost = toolkit.get_token_cost(service)
            print(f"  - {service} (~{cost} tokens)")
    
    elif command in toolkit.list_services():
        service = command
        
        if len(sys.argv) < 3:
            print(f"Usage: python toolkit.py {service} [command] [args...]")
            print(f"Try: python toolkit.py {service} test")
            sys.exit(1)
        
        subcommand = sys.argv[2]
        args = sys.argv[3:]
        
        if subcommand == 'docs':
            level = args[0] if args else 'quick'
            print(toolkit.get_documentation(service, level))
        
        elif subcommand == 'check':
            status = toolkit.check_environment(service)
            print(f"Environment check for {service}:")
            for var, is_set in status.items():
                symbol = "✓" if is_set else "✗"
                print(f"  {symbol} {var}")
        
        else:
            result = toolkit.run_command(service, subcommand, *args)
            if result is not None:
                if isinstance(result, (dict, list)):
                    print(json.dumps(result, indent=2))
                else:
                    print(result)
    
    else:
        print(f"Unknown command or service: {command}")
        print("Run 'python toolkit.py' for help")
        sys.exit(1)


if __name__ == "__main__":
    main()