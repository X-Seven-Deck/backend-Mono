#!/usr/bin/env python3
"""
Verify Enterprise Dashboard Tables in Supabase
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'shared' / 'libs'))

from supabase_client import get_supabase_client

def main():
    print("🔍 Verifying Enterprise Dashboard Tables in Supabase\n")
    
    # Get Supabase client
    try:
        supabase = get_supabase_client()
        print("✅ Connected to Supabase\n")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        sys.exit(1)
    
    # List of expected enterprise tables
    expected_tables = [
        'menu_categories',
        'menu_items',
        'item_modifiers',
        'item_modifier_assignments',
        'inventory_items',
        'inventory_transactions',
        'stock_alerts',
        'suppliers',
        'purchase_orders',
        'locations',
        'floor_plans',
        'tables',
        'kds_orders',
        'staff_members',
        'staff_schedules',
        'time_clock',
        'order_items',
        'payments',
        'daily_sales_summary',
        'item_performance'
    ]
    
    print("📊 Checking for enterprise tables:\n")
    
    existing_tables = []
    missing_tables = []
    
    for table in expected_tables:
        try:
            # Try to query the table (limit 0 to just check existence)
            result = supabase.table(table).select('*').limit(0).execute()
            print(f"✅ {table}")
            existing_tables.append(table)
        except Exception as e:
            error_msg = str(e)
            if 'does not exist' in error_msg or 'relation' in error_msg:
                print(f"❌ {table} - NOT FOUND")
                missing_tables.append(table)
            else:
                print(f"⚠️  {table} - Error: {error_msg}")
    
    print("\n" + "="*60)
    print(f"📈 Summary:")
    print(f"   Total Expected: {len(expected_tables)}")
    print(f"   Existing: {len(existing_tables)}")
    print(f"   Missing: {len(missing_tables)}")
    print("="*60)
    
    if missing_tables:
        print(f"\n❌ Missing tables: {', '.join(missing_tables)}")
        print("\n💡 Run migration to create missing tables")
        return 1
    else:
        print("\n✅ All enterprise dashboard tables exist!")
        print("🎉 Your dashboard is ready to use!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
