#!/usr/bin/env python3
"""
OpenAPI Specification Generator for Supabase API
Generates interactive API documentation using spec-kit patterns
"""

import json
import yaml
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

from services.supabase.api import SupabaseAPI
from services.supabase.table_docs import SMOOTHED_TABLES, BLINGSTING_TABLES, SCRAPING_TABLES


class SupabaseOpenAPIGenerator:
    """
    Generates OpenAPI 3.0 specifications for Supabase projects.
    This enables:
    - Auto-generated API documentation
    - Client SDK generation
    - Interactive API testing (Swagger UI)
    - Type-safe contracts
    """
    
    def __init__(self, project: str = 'project1'):
        self.project = project
        self.api = SupabaseAPI(project)
        self.spec = {
            "openapi": "3.0.0",
            "info": {
                "title": f"Supabase {project.title()} API",
                "version": "1.0.0",
                "description": self._get_project_description(),
                "contact": {
                    "name": "API Toolkit Support",
                    "email": "support@example.com"
                }
            },
            "servers": self._get_servers(),
            "paths": {},
            "components": {
                "schemas": {},
                "parameters": {},
                "securitySchemes": {
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "apikey"
                    }
                }
            },
            "security": [{"ApiKeyAuth": []}]
        }
    
    def _get_project_description(self) -> str:
        """Get project-specific description"""
        descriptions = {
            'project1': "Lead Generation Database - Brands, leads, and scraping results",
            'project2': "CRM System - Customers, orders, and products",
            'project3': "Web Project 3 - Project 3 guides, results, and queue"
        }
        return descriptions.get(self.project, "Supabase Database API")
    
    def _get_servers(self) -> List[Dict]:
        """Get project-specific servers"""
        servers = {
            'project1': [{"url": "https://your-project-1.supabase.co/rest/v1"}],
            'project2': [{"url": "https://your-project-2.supabase.co/rest/v1"}],
            'project3': [{"url": "https://your-project-3.supabase.co/rest/v1"}]
        }
        return servers.get(self.project, [])
    
    def generate_table_spec(self, table_name: str, table_info: Dict) -> None:
        """Generate OpenAPI paths for a specific table"""
        
        # GET endpoint - Query records
        self.spec["paths"][f"/{table_name}"] = {
            "get": {
                "summary": f"Query {table_name}",
                "description": table_info.get('description', f'Query {table_name} table'),
                "operationId": f"get_{table_name}",
                "tags": [table_name],
                "parameters": [
                    {
                        "name": "select",
                        "in": "query",
                        "description": "Columns to select",
                        "required": False,
                        "schema": {"type": "string", "default": "*"}
                    },
                    {
                        "name": "order",
                        "in": "query", 
                        "description": "Column to order by (prefix with - for DESC)",
                        "required": False,
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum number of records to return",
                        "required": False,
                        "schema": {"type": "integer", "minimum": 1}
                    },
                    {
                        "name": "offset",
                        "in": "query",
                        "description": "Number of records to skip",
                        "required": False,
                        "schema": {"type": "integer", "minimum": 0}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful query",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": f"#/components/schemas/{table_name}"}
                                }
                            }
                        }
                    }
                }
            },
            
            # POST endpoint - Insert records
            "post": {
                "summary": f"Insert into {table_name}",
                "description": f"Insert one or more records into {table_name}",
                "operationId": f"insert_{table_name}",
                "tags": [table_name],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "oneOf": [
                                    {"$ref": f"#/components/schemas/{table_name}"},
                                    {
                                        "type": "array",
                                        "items": {"$ref": f"#/components/schemas/{table_name}"}
                                    }
                                ]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Successfully inserted",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{table_name}"}
                            }
                        }
                    }
                }
            }
        }
        
        # Add PATCH endpoint - Update records
        self.spec["paths"][f"/{table_name}"] ["patch"] = {
            "summary": f"Update {table_name}",
            "description": f"Update records in {table_name} matching filters",
            "operationId": f"update_{table_name}",
            "tags": [table_name],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{table_name}"}
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Successfully updated",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": f"#/components/schemas/{table_name}"}
                            }
                        }
                    }
                }
            }
        }
        
        # Generate schema from table info
        self._generate_table_schema(table_name, table_info)
    
    def _generate_table_schema(self, table_name: str, table_info: Dict) -> None:
        """Generate JSON Schema for a table"""
        properties = {}
        
        # Use known columns from table_docs
        for column in table_info.get('key_columns', []):
            # Infer type from column name
            if 'id' in column:
                properties[column] = {"type": "string", "format": "uuid"}
            elif 'email' in column:
                properties[column] = {"type": "string", "format": "email"}
            elif 'created_at' in column or 'updated_at' in column:
                properties[column] = {"type": "string", "format": "date-time"}
            elif 'price' in column or 'total' in column or 'score' in column:
                properties[column] = {"type": "number"}
            elif 'quantity' in column or 'count' in column:
                properties[column] = {"type": "integer"}
            elif 'active' in column or 'verified' in column:
                properties[column] = {"type": "boolean"}
            else:
                properties[column] = {"type": "string"}
        
        self.spec["components"]["schemas"][table_name] = {
            "type": "object",
            "description": table_info.get('description', ''),
            "properties": properties
        }
    
    def generate_full_spec(self) -> Dict:
        """Generate complete OpenAPI specification"""
        
        # Get table documentation
        table_docs = {
            'project1': SMOOTHED_TABLES,
            'project2': BLINGSTING_TABLES,
            'project3': SCRAPING_TABLES
        }
        
        tables = table_docs.get(self.project, {})
        
        # Generate spec for each table
        for table_name, table_info in tables.items():
            self.generate_table_spec(table_name, table_info)
        
        # Add common parameters
        self._add_common_parameters()
        
        # Add filter examples
        self._add_filter_examples()
        
        return self.spec
    
    def _add_common_parameters(self) -> None:
        """Add common query parameters"""
        self.spec["components"]["parameters"]["FilterParam"] = {
            "name": "filter",
            "in": "query",
            "description": "Filter syntax: column=operator.value",
            "required": False,
            "schema": {"type": "string"},
            "examples": {
                "equals": {"value": "status=eq.active"},
                "greater_than": {"value": "score=gt.80"},
                "pattern": {"value": "email=ilike.%gmail%"}
            }
        }
    
    def _add_filter_examples(self) -> None:
        """Add filter operation examples"""
        self.spec["components"]["schemas"]["FilterOperations"] = {
            "type": "object",
            "description": "Supabase filter operations",
            "properties": {
                "eq": {"type": "string", "description": "Equals"},
                "neq": {"type": "string", "description": "Not equals"},
                "gt": {"type": "string", "description": "Greater than"},
                "gte": {"type": "string", "description": "Greater or equal"},
                "lt": {"type": "string", "description": "Less than"},
                "lte": {"type": "string", "description": "Less or equal"},
                "like": {"type": "string", "description": "Pattern match (case-sensitive)"},
                "ilike": {"type": "string", "description": "Pattern match (case-insensitive)"},
                "is": {"type": "string", "description": "IS (null, true, false)"},
                "in": {"type": "string", "description": "IN array"}
            }
        }
    
    def save_spec(self, format: str = 'yaml') -> str:
        """Save specification to file"""
        spec = self.generate_full_spec()
        
        output_dir = Path(__file__).parent / 'openapi'
        output_dir.mkdir(exist_ok=True)
        
        if format == 'yaml':
            output_file = output_dir / f"{self.project}_api.yaml"
            with open(output_file, 'w') as f:
                yaml.dump(spec, f, sort_keys=False, default_flow_style=False)
        else:
            output_file = output_dir / f"{self.project}_api.json"
            with open(output_file, 'w') as f:
                json.dump(spec, f, indent=2)
        
        return str(output_file)
    
    def generate_client_code(self, language: str = 'typescript') -> str:
        """Generate client SDK code"""
        spec = self.generate_full_spec()
        
        if language == 'typescript':
            return self._generate_typescript_client(spec)
        elif language == 'python':
            return self._generate_python_client(spec)
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    def _generate_typescript_client(self, spec: Dict) -> str:
        """Generate TypeScript client from spec"""
        code = f"""// Auto-generated TypeScript client for {self.project} API
// Generated: {datetime.now().isoformat()}

export interface ApiConfig {{
  baseUrl: string;
  apiKey: string;
}}

"""
        # Generate interfaces for each schema
        for schema_name, schema in spec["components"]["schemas"].items():
            if schema_name != "FilterOperations":
                code += f"export interface {schema_name} {{\n"
                for prop, prop_spec in schema.get("properties", {}).items():
                    ts_type = self._json_to_typescript_type(prop_spec.get("type", "any"))
                    code += f"  {prop}?: {ts_type};\n"
                code += "}\n\n"
        
        # Generate client class
        code += f"""export class {self.project.title()}API {{
  constructor(private config: ApiConfig) {{}}
  
  private async request<T>(
    path: string,
    options?: RequestInit
  ): Promise<T> {{
    const response = await fetch(`${{this.config.baseUrl}}${{path}}`, {{
      ...options,
      headers: {{
        'apikey': this.config.apiKey,
        'Content-Type': 'application/json',
        ...options?.headers,
      }},
    }});
    
    if (!response.ok) {{
      throw new Error(`API error: ${{response.statusText}}`);
    }}
    
    return response.json();
  }}
"""
        
        # Generate methods for each table
        for path, methods in spec["paths"].items():
            table_name = path.replace("/", "")
            if table_name:
                code += f"""
  async get{table_name.title()}(filters?: Record<string, string>): Promise<{table_name}[]> {{
    const params = new URLSearchParams(filters);
    return this.request<{table_name}[]>('/{table_name}?${{params}}');
  }}
  
  async create{table_name.title()}(data: {table_name}): Promise<{table_name}> {{
    return this.request<{table_name}>('/{table_name}', {{
      method: 'POST',
      body: JSON.stringify(data),
    }});
  }}
"""
        
        code += "}\n"
        return code
    
    def _generate_python_client(self, spec: Dict) -> str:
        """Generate Python client from spec"""
        code = f"""# Auto-generated Python client for {self.project} API
# Generated: {datetime.now().isoformat()}

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests


"""
        # Generate dataclasses for each schema
        for schema_name, schema in spec["components"]["schemas"].items():
            if schema_name != "FilterOperations":
                code += f"@dataclass\nclass {schema_name}:\n"
                for prop, prop_spec in schema.get("properties", {}).items():
                    py_type = self._json_to_python_type(prop_spec.get("type", "Any"))
                    code += f"    {prop}: Optional[{py_type}] = None\n"
                code += "\n"
        
        # Generate client class
        code += f"""
class {self.project.title()}API:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({{
            'apikey': api_key,
            'Content-Type': 'application/json'
        }})
    
    def _request(self, method: str, path: str, **kwargs) -> Any:
        response = self.session.request(
            method,
            f"{{self.base_url}}{{path}}",
            **kwargs
        )
        response.raise_for_status()
        return response.json()
"""
        
        # Generate methods for each table
        for path, methods in spec["paths"].items():
            table_name = path.replace("/", "")
            if table_name:
                code += f"""
    def get_{table_name}(self, filters: Optional[Dict] = None) -> List[{table_name}]:
        return self._request('GET', '/{table_name}', params=filters or {{}})
    
    def create_{table_name}(self, data: {table_name}) -> {table_name}:
        return self._request('POST', '/{table_name}', json=data.__dict__)
"""
        
        return code
    
    def _json_to_typescript_type(self, json_type: str) -> str:
        """Convert JSON Schema type to TypeScript type"""
        type_map = {
            "string": "string",
            "number": "number",
            "integer": "number",
            "boolean": "boolean",
            "array": "any[]",
            "object": "any"
        }
        return type_map.get(json_type, "any")
    
    def _json_to_python_type(self, json_type: str) -> str:
        """Convert JSON Schema type to Python type"""
        type_map = {
            "string": "str",
            "number": "float",
            "integer": "int",
            "boolean": "bool",
            "array": "List",
            "object": "Dict"
        }
        return type_map.get(json_type, "Any")


# CLI Interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("OpenAPI Specification Generator")
        print("=" * 50)
        print("\nUsage:")
        print("  python openapi_generator.py generate [project]  # Generate OpenAPI spec")
        print("  python openapi_generator.py client [project] [language]  # Generate client SDK")
        print("  python openapi_generator.py serve [project]  # Start Swagger UI")
        print("\nProjects: smoothed, blingsting, scraping")
        print("Languages: typescript, python")
        sys.exit(1)
    
    command = sys.argv[1]
    project = sys.argv[2] if len(sys.argv) > 2 else 'project1'
    
    generator = SupabaseOpenAPIGenerator(project)
    
    if command == "generate":
        output_file = generator.save_spec('yaml')
        print(f"✓ Generated OpenAPI spec: {output_file}")
        
        # Also save JSON version
        output_file = generator.save_spec('json')
        print(f"✓ Generated JSON spec: {output_file}")
    
    elif command == "client" and len(sys.argv) > 3:
        language = sys.argv[3]
        code = generator.generate_client_code(language)
        
        output_dir = Path(__file__).parent / 'generated'
        output_dir.mkdir(exist_ok=True)
        
        ext = 'ts' if language == 'typescript' else 'py'
        output_file = output_dir / f"{project}_client.{ext}"
        
        with open(output_file, 'w') as f:
            f.write(code)
        
        print(f"✓ Generated {language} client: {output_file}")
    
    elif command == "serve":
        # Generate spec first
        spec_file = generator.save_spec('yaml')
        print(f"✓ Generated spec: {spec_file}")
        print("\nTo view in Swagger UI:")
        print("1. Install: npm install -g @apidevtools/swagger-cli")
        print(f"2. Run: swagger-cli serve {spec_file}")
        print("\nOr paste the spec at: https://editor.swagger.io")
    
    else:
        print(f"Unknown command: {command}")