"""
Diagnostic utilities for C13 module.
"""
import streamlit as st
import os

def show_connection_test():
    """Display a database connection test button."""
    
    with st.expander("🔧 Database Connection Test", expanded=False):
        st.write("Click the button below to test your database connection:")
        
        if st.button("Test Connection"):
            try:
                # Show environment variables (masked)
                st.write("**Environment Variables:**")
                db_host = os.getenv("DB_HOST", "NOT SET")
                db_name = os.getenv("DB_NAME", "NOT SET")
                db_user = os.getenv("DB_USER", "NOT SET")
                db_url = os.getenv("DATABASE_URL", "NOT SET")
                
                st.write(f"- DB_HOST: `{db_host}`")
                st.write(f"- DB_NAME: `{db_name}`")
                st.write(f"- DB_USER: `{db_user}`")
                st.write(f"- DATABASE_URL: `{'SET' if db_url != 'NOT SET' else 'NOT SET'}`")
                
                # Try to connect
                st.write("\n**Testing connection...**")
                
                from backend import get_connection
                conn = get_connection()
                
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()[0]
                    st.success(f"✅ Connected successfully!")
                    st.info(f"PostgreSQL version: {version[:50]}...")
                    
                    cur.execute("SELECT COUNT(*) FROM patients")
                    count = cur.fetchone()[0]
                    st.success(f"✅ Found {count} patients in database")
                
                conn.close()
                
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")
                
                import traceback
                with st.expander("Full Error Traceback"):
                    st.code(traceback.format_exc())
                
                st.write("\n**Troubleshooting:**")
                st.write("1. Check that secrets are configured in Streamlit Cloud")
                st.write("2. Verify DATABASE_URL or DB_HOST/DB_NAME/DB_USER/DB_PASSWORD are set")
                st.write("3. Ensure Supabase database is running")
                st.write("4. Check that DB_SSLMODE='require' is set")
