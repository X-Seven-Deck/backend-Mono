#!/usr/bin/env python3
"""
Enterprise Dashboard Schema Migration Script
Migrates the enterprise_dashboard_schema.sql to Supabase
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_sql_file(file_path: str) -> str:
    """Load SQL file content"""
    with open(file_path, 'r') as f:
        return f.read()

def main():
    # Get Supabase credentials from environment
    supabase_url = os.getenv('SUPABASE_URL', 'https://ydlmkvkfmmnitfhjqakt.supabase.co')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_key:
        print("❌ Error: SUPABASE_SERVICE_ROLE_KEY not found in environment")
        print("Please set it in your .env file or export it:")
        print("export SUPABASE_SERVICE_ROLE_KEY='your-service-role-key'")
        sys.exit(1)
    
    print(f"🔗 Connecting to Supabase: {supabase_url}")
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Load schema file
    schema_path = Path(__file__).parent.parent / 'shared' / 'schemas' / 'enterprise_dashboard_schema.sql'
    
    if not schema_path.exists():
        print(f"❌ Error: Schema file not found at {schema_path}")
        sys.exit(1)
    
    print(f"📄 Loading schema from: {schema_path}")
    sql_content = load_sql_file(str(schema_path))
    
    # Split SQL into individual statements
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
    
    print(f"📊 Found {len(statements)} SQL statements to execute")
    print("\n🚀 Starting migration...\n")
    
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements, 1):
        # Skip comments and empty statements
        if not statement or statement.startswith('--'):
            continue
        
        # Get first line for display
        first_line = statement.split('\n')[0][:80]
        
        try:
            print(f"[{i}/{len(statements)}] Executing: {first_line}...")
            
            # Execute SQL using Supabase RPC
            result = supabase.rpc('exec_sql', {'sql': statement}).execute()
            
            print(f"✅ Success")
            success_count += 1
            
        except Exception as e:
            error_msg = str(e)
            
            # Check if error is benign (already exists)
            if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                print(f"⚠️  Already exists (skipping)")
                success_count += 1
            else:
                print(f"❌ Error: {error_msg}")
                error_count += 1
    
    print("\n" + "="*60)
    print(f"✅ Migration completed!")
    print(f"   Success: {success_count}")
    print(f"   Errors: {error_count}")
    print("="*60)
    
    if error_count > 0:
        print("\n⚠️  Some statements failed. This is normal if tables already exist.")
        print("   Check the errors above to ensure they're benign.")
    
    return 0 if error_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
