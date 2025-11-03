#!/usr/bin/env python3
"""
Verification script for BRSR Core indicators seeding
Ensures all requirements are met:
- All 9 attributes are present
- Correct pillar assignments (E/S/G)
- Expected indicator count (55+ from Annexure I)
"""

import os
import sys
import psycopg2

# Database connection parameters
DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'moz'),
    'user': os.getenv('POSTGRES_USER', 'drfitz'),
    'password': os.getenv('POSTGRES_PASSWORD', 'h4i1hydr4'),
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

def verify_indicators():
    """Verify BRSR indicators meet all requirements"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("=" * 70)
        print("BRSR Core Indicators Verification")
        print("=" * 70)
        
        # Requirement 1.1 & 1.6: Verify indicator count
        cur.execute("SELECT COUNT(*) FROM brsr_indicators")
        total_count = cur.fetchone()[0]
        
        print(f"\n✓ Requirement 1.1 & 1.6: Indicator Count")
        print(f"  Total indicators: {total_count}")
        
        if total_count >= 55:
            print(f"  ✓ PASS: Expected 55+ indicators from Annexure I")
        else:
            print(f"  ✗ FAIL: Expected at least 55 indicators, found {total_count}")
            return False
        
        # Requirement 1.2: Verify all 9 attributes are present
        cur.execute("SELECT DISTINCT attribute_number FROM brsr_indicators ORDER BY attribute_number")
        attributes = [row[0] for row in cur.fetchall()]
        
        print(f"\n✓ Requirement 1.2: All 9 BRSR Attributes")
        print(f"  Attributes present: {attributes}")
        
        if len(attributes) == 9 and attributes == list(range(1, 10)):
            print(f"  ✓ PASS: All 9 attributes (1-9) are present")
        else:
            print(f"  ✗ FAIL: Expected 9 attributes (1-9), found: {attributes}")
            return False
        
        # Requirement 1.3: Verify correct pillar assignments
        cur.execute("SELECT pillar, COUNT(*) FROM brsr_indicators GROUP BY pillar ORDER BY pillar")
        pillars = dict(cur.fetchall())
        
        print(f"\n✓ Requirement 1.3: Pillar Assignments (E/S/G)")
        print(f"  Environmental (E): {pillars.get('E', 0)} indicators")
        print(f"  Social (S): {pillars.get('S', 0)} indicators")
        print(f"  Governance (G): {pillars.get('G', 0)} indicators")
        
        if 'E' in pillars and 'S' in pillars and 'G' in pillars:
            print(f"  ✓ PASS: All three pillars (E, S, G) are assigned")
        else:
            print(f"  ✗ FAIL: Missing pillar assignments")
            return False
        
        # Requirement 1.4: Verify attribute-pillar mapping
        cur.execute("""
            SELECT attribute_number, pillar, COUNT(*) 
            FROM brsr_indicators 
            GROUP BY attribute_number, pillar 
            ORDER BY attribute_number
        """)
        
        print(f"\n✓ Requirement 1.4: Attribute-Pillar Mapping")
        
        expected_mappings = {
            1: 'E', 2: 'E', 3: 'E', 4: 'E',  # Environmental
            5: 'S', 6: 'S', 7: 'S',           # Social
            8: 'G', 9: 'G'                    # Governance
        }
        
        all_correct = True
        for row in cur.fetchall():
            attr_num, pillar, count = row
            expected_pillar = expected_mappings.get(attr_num)
            status = "✓" if pillar == expected_pillar else "✗"
            print(f"  {status} Attribute {attr_num}: {pillar} (expected {expected_pillar}) - {count} indicators")
            if pillar != expected_pillar:
                all_correct = False
        
        if all_correct:
            print(f"  ✓ PASS: All attributes have correct pillar assignments")
        else:
            print(f"  ✗ FAIL: Some attributes have incorrect pillar assignments")
            return False
        
        # Additional verification: Check for required fields
        cur.execute("""
            SELECT COUNT(*) FROM brsr_indicators 
            WHERE indicator_code IS NOT NULL 
            AND parameter_name IS NOT NULL 
            AND pillar IS NOT NULL 
            AND weight IS NOT NULL
        """)
        complete_count = cur.fetchone()[0]
        
        print(f"\n✓ Data Completeness")
        print(f"  Indicators with all required fields: {complete_count}/{total_count}")
        
        if complete_count == total_count:
            print(f"  ✓ PASS: All indicators have required fields")
        else:
            print(f"  ✗ FAIL: Some indicators missing required fields")
            return False
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("✓ ALL REQUIREMENTS PASSED")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        return False


if __name__ == "__main__":
    success = verify_indicators()
    sys.exit(0 if success else 1)
