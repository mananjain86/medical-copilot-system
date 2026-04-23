"""
Helper to load secrets from Streamlit Cloud or local .env file.
This ensures environment variables are available for the backend.
"""
import os
from pathlib import Path

def load_secrets():
    """Load secrets from Streamlit or .env file."""
    
    # Try to load from Streamlit secrets first (when deployed)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and st.secrets:
            # Copy Streamlit secrets to environment variables
            for key, value in st.secrets.items():
                if key not in os.environ:
                    os.environ[key] = str(value)
            return True
    except (ImportError, FileNotFoundError):
        pass
    
    # Fallback to .env file (local development)
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            return True
    except ImportError:
        pass
    
    return False

# Auto-load on import
load_secrets()
