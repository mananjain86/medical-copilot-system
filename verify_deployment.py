#!/usr/bin/env python3
"""
Deployment verification script.
Run this before deploying to check if everything is configured correctly.
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, required=True):
    """Check if a file exists."""
    exists = Path(filepath).exists()
    status = "✅" if exists else ("❌" if required else "⚠️")
    req_text = "REQUIRED" if required else "OPTIONAL"
    print(f"{status} {filepath} ({req_text})")
    return exists

def check_env_var(var_name, required=True):
    """Check if an environment variable is set."""
    value = os.getenv(var_name)
    exists = value is not None and value != ""
    status = "✅" if exists else ("❌" if required else "⚠️")
    req_text = "REQUIRED" if required else "OPTIONAL"
    print(f"{status} {var_name} ({req_text})")
    return exists

def main():
    print("=" * 60)
    print("DEPLOYMENT VERIFICATION")
    print("=" * 60)
    
    all_good = True
    
    # Check required files
    print("\n📁 Checking Required Files...")
    required_files = [
        "app.py",
        "streamlit_app.py",
        "requirements.txt",
        "api/main.py",
        "Procfile",
        "runtime.txt",
        ".streamlit/config.toml",
        "DEPLOYMENT.md",
    ]
    
    for filepath in required_files:
        if not check_file_exists(filepath, required=True):
            all_good = False
    
    # Check optional files
    print("\n📄 Checking Optional Files...")
    optional_files = [
        "render.yaml",
        ".env.example",
        "DEPLOYMENT_CHECKLIST.md",
    ]
    
    for filepath in optional_files:
        check_file_exists(filepath, required=False)
    
    # Check .env file (should exist locally but not in git)
    print("\n🔐 Checking Environment Configuration...")
    env_exists = check_file_exists(".env", required=True)
    if not env_exists:
        all_good = False
    
    # Check .gitignore
    print("\n🚫 Checking .gitignore...")
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
        if ".env" in gitignore_content:
            print("✅ .env is in .gitignore (GOOD)")
        else:
            print("❌ .env is NOT in .gitignore (SECURITY RISK!)")
            all_good = False
    else:
        print("❌ .gitignore not found")
        all_good = False
    
    # Check environment variables
    print("\n🔑 Checking Environment Variables...")
    required_env_vars = [
        "DATABASE_URL",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]
    
    # Load .env if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not installed, skipping .env loading")
    
    for var in required_env_vars:
        if not check_env_var(var, required=True):
            all_good = False
    
    # Check Python version
    print("\n🐍 Checking Python Version...")
    py_version = sys.version_info
    print(f"   Current: Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version.major == 3 and py_version.minor >= 9:
        print("✅ Python version is compatible")
    else:
        print("⚠️  Python 3.9+ recommended")
    
    # Check dependencies
    print("\n📦 Checking Dependencies...")
    try:
        import streamlit
        print("✅ streamlit installed")
    except ImportError:
        print("❌ streamlit not installed")
        all_good = False
    
    try:
        import fastapi
        print("✅ fastapi installed")
    except ImportError:
        print("❌ fastapi not installed")
        all_good = False
    
    try:
        import psycopg2
        print("✅ psycopg2 installed")
    except ImportError:
        print("❌ psycopg2 not installed")
        all_good = False
    
    try:
        import uvicorn
        print("✅ uvicorn installed")
    except ImportError:
        print("❌ uvicorn not installed")
        all_good = False
    
    # Test database connection
    print("\n🗄️  Testing Database Connection...")
    try:
        from src.modules.C13.backend import get_connection
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            if result and result[0] == 1:
                print("✅ Database connection successful")
            else:
                print("❌ Database connection failed")
                all_good = False
        conn.close()
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        all_good = False
    
    # Final summary
    print("\n" + "=" * 60)
    if all_good:
        print("✅ ALL CHECKS PASSED - Ready for deployment!")
        print("\nNext steps:")
        print("1. Push code to GitHub")
        print("2. Deploy backend to Render")
        print("3. Deploy frontend to Streamlit Cloud")
        print("4. Follow DEPLOYMENT.md for detailed instructions")
    else:
        print("❌ SOME CHECKS FAILED - Fix issues before deploying")
        print("\nPlease address the issues marked with ❌ above")
    print("=" * 60)
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
