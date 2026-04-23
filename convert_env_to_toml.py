#!/usr/bin/env python3
"""
Convert .env file to Streamlit TOML secrets format.
This helps you quickly generate the correct format for Streamlit Cloud.
"""

import os
from pathlib import Path

def convert_env_to_toml(env_file=".env", output_file=None):
    """Convert .env file to TOML format for Streamlit secrets."""
    
    env_path = Path(env_file)
    if not env_path.exists():
        print(f"❌ Error: {env_file} not found")
        return
    
    print("=" * 60)
    print("STREAMLIT CLOUD SECRETS (TOML FORMAT)")
    print("=" * 60)
    print("\nCopy the content below to Streamlit Cloud:")
    print("Dashboard → Your App → Settings → Secrets\n")
    print("-" * 60)
    
    toml_lines = []
    toml_lines.append("# Streamlit Cloud Secrets")
    toml_lines.append("# Generated from .env file\n")
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                if line.startswith('#'):
                    toml_lines.append(line)
                continue
            
            # Parse key=value
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if already present
                value = value.strip('"').strip("'")
                
                # Convert to TOML format: key = "value"
                toml_line = f'{key} = "{value}"'
                toml_lines.append(toml_line)
    
    toml_content = '\n'.join(toml_lines)
    
    # Print to console
    print(toml_content)
    print("-" * 60)
    
    # Optionally save to file
    if output_file:
        output_path = Path(output_file)
        output_path.write_text(toml_content)
        print(f"\n✅ Also saved to: {output_file}")
    
    print("\n" + "=" * 60)
    print("INSTRUCTIONS:")
    print("=" * 60)
    print("1. Copy everything between the dashed lines above")
    print("2. Go to Streamlit Cloud: https://share.streamlit.io")
    print("3. Select your app → Settings → Secrets")
    print("4. Paste the content")
    print("5. Click 'Save'")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    
    # Check if output file specified
    output = None
    if len(sys.argv) > 1:
        output = sys.argv[1]
    
    convert_env_to_toml(output_file=output)
