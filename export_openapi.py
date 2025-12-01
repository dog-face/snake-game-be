#!/usr/bin/env python3
"""
Export OpenAPI specification from FastAPI backend.

This script exports the auto-generated OpenAPI spec to a YAML or JSON file
for comparison with the frontend spec.
"""

import json
import sys
from pathlib import Path
import yaml

try:
    from app.main import app
except ImportError:
    print("Error: Could not import app. Make sure you're running from the project root.")
    print("Try: python export_openapi.py")
    sys.exit(1)

def export_openapi(output_format='yaml', output_file=None):
    """Export OpenAPI spec from FastAPI app"""
    spec = app.openapi()
    
    if output_file is None:
        if output_format == 'yaml':
            output_file = 'openapi_backend.yaml'
        else:
            output_file = 'openapi_backend.json'
    
    output_path = Path(output_file)
    
    if output_format == 'yaml':
        try:
            with open(output_path, 'w') as f:
                yaml.dump(spec, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            print(f"✓ OpenAPI spec exported to {output_path}")
        except ImportError:
            print("Error: PyYAML not installed. Install with: pip install pyyaml")
            print("Falling back to JSON format...")
            output_path = Path('openapi_backend.json')
            with open(output_path, 'w') as f:
                json.dump(spec, f, indent=2)
            print(f"✓ OpenAPI spec exported to {output_path} (JSON)")
    else:
        with open(output_path, 'w') as f:
            json.dump(spec, f, indent=2)
        print(f"✓ OpenAPI spec exported to {output_path}")
    
    print(f"\nSpec details:")
    print(f"  - OpenAPI version: {spec.get('openapi', 'unknown')}")
    print(f"  - Title: {spec.get('info', {}).get('title', 'unknown')}")
    print(f"  - Version: {spec.get('info', {}).get('version', 'unknown')}")
    print(f"  - Paths: {len(spec.get('paths', {}))}")
    
    return output_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Export OpenAPI spec from FastAPI backend')
    parser.add_argument(
        '-f', '--format',
        choices=['json', 'yaml'],
        default='yaml',
        help='Output format (default: yaml)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: openapi_backend.yaml or openapi_backend.json)'
    )
    
    args = parser.parse_args()
    
    export_openapi(output_format=args.format, output_file=args.output)

