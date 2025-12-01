#!/usr/bin/env python3
"""
Compare backend and frontend OpenAPI specifications.

This script helps identify differences between the backend auto-generated spec
and the frontend spec.
"""

import json
import sys
from pathlib import Path
import yaml

def load_spec(file_path):
    """Load OpenAPI spec from YAML or JSON file"""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}")
        return None
    
    with open(path, 'r') as f:
        if path.suffix in ['.yaml', '.yml']:
            try:
                return yaml.safe_load(f)
            except ImportError:
                print("Error: PyYAML not installed. Install with: pip install pyyaml")
                return None
        else:
            return json.load(f)

def compare_paths(backend_spec, frontend_spec):
    """Compare API paths between specs"""
    backend_paths = set(backend_spec.get('paths', {}).keys())
    frontend_paths = set(frontend_spec.get('paths', {}).keys())
    
    print("\n=== Path Comparison ===")
    only_backend = backend_paths - frontend_paths
    only_frontend = frontend_paths - backend_paths
    common = backend_paths & frontend_paths
    
    if only_backend:
        print(f"\nPaths only in backend ({len(only_backend)}):")
        for path in sorted(only_backend):
            print(f"  + {path}")
    
    if only_frontend:
        print(f"\nPaths only in frontend ({len(only_frontend)}):")
        for path in sorted(only_frontend):
            print(f"  - {path}")
    
    if common:
        print(f"\nCommon paths ({len(common)}):")
        for path in sorted(common):
            print(f"  ✓ {path}")
    
    return {
        'only_backend': only_backend,
        'only_frontend': only_frontend,
        'common': common
    }

def compare_components(backend_spec, frontend_spec):
    """Compare components/schemas between specs"""
    backend_schemas = set(backend_spec.get('components', {}).get('schemas', {}).keys())
    frontend_schemas = set(frontend_spec.get('components', {}).get('schemas', {}).keys())
    
    print("\n=== Schema Comparison ===")
    only_backend = backend_schemas - frontend_schemas
    only_frontend = frontend_schemas - backend_schemas
    common = backend_schemas & frontend_schemas
    
    if only_backend:
        print(f"\nSchemas only in backend ({len(only_backend)}):")
        for schema in sorted(only_backend):
            print(f"  + {schema}")
    
    if only_frontend:
        print(f"\nSchemas only in frontend ({len(only_frontend)}):")
        for schema in sorted(only_frontend):
            print(f"  - {schema}")
    
    if common:
        print(f"\nCommon schemas ({len(common)}):")
        for schema in sorted(common):
            print(f"  ✓ {schema}")

def main():
    backend_file = Path('openapi_backend.yaml')
    frontend_file = Path('../snake-game-fe/openapi.yaml')
    
    if not backend_file.exists():
        print(f"Error: Backend spec not found: {backend_file}")
        print("Run: python export_openapi.py first")
        sys.exit(1)
    
    if not frontend_file.exists():
        print(f"Error: Frontend spec not found: {frontend_file}")
        print("Expected location: ../snake-game-fe/openapi.yaml")
        sys.exit(1)
    
    print("Loading specs...")
    backend_spec = load_spec(backend_file)
    frontend_spec = load_spec(frontend_file)
    
    if not backend_spec or not frontend_spec:
        sys.exit(1)
    
    print("\n" + "="*60)
    print("OpenAPI Spec Comparison")
    print("="*60)
    
    print(f"\nBackend spec: {backend_file}")
    print(f"  - OpenAPI: {backend_spec.get('openapi', 'unknown')}")
    print(f"  - Title: {backend_spec.get('info', {}).get('title', 'unknown')}")
    print(f"  - Version: {backend_spec.get('info', {}).get('version', 'unknown')}")
    
    print(f"\nFrontend spec: {frontend_file}")
    print(f"  - OpenAPI: {frontend_spec.get('openapi', 'unknown')}")
    print(f"  - Title: {frontend_spec.get('info', {}).get('title', 'unknown')}")
    print(f"  - Version: {frontend_spec.get('info', {}).get('version', 'unknown')}")
    
    compare_paths(backend_spec, frontend_spec)
    compare_components(backend_spec, frontend_spec)
    
    print("\n" + "="*60)
    print("Comparison complete!")
    print("="*60)

if __name__ == "__main__":
    main()

