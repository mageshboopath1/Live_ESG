#!/usr/bin/env python3
"""
Database initialization and BRSR Core indicator seeding
Main entry point for seeding BRSR indicators into the database
Complete implementation based on Annexure I - Format of BRSR Core
"""

import os
import psycopg2
from psycopg2.extras import execute_values

# Database connection parameters from .env
DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'moz'),
    'user': os.getenv('POSTGRES_USER', 'drfitz'),
    'password': os.getenv('POSTGRES_PASSWORD', 'h4i1hydr4'),
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

# BRSR Core Indicators based on Annexure I - Complete set covering all 9 attributes
# Format: (indicator_code, attribute_number, parameter_name, measurement_unit, 
#          description, pillar, weight, data_assurance_approach, brsr_reference)
BRSR_INDICATORS = [
    # Attribute 1: GHG Footprint (Environmental) - 4 parameters
    ('GHG_SCOPE1_TOTAL', 1, 'Total Scope 1 emissions (Break-up of the GHG into CO2, CH4, N2O, HFCs, PFCs, SF6, NF3, if available)', 'MT CO2e',
     'Direct GHG emissions from organizations owned or controlled sources', 'E', 1.0,
     'Fossil fuel consumption, emission factors, carbon capture, fugitive emissions',
     'Principle 6, Question 7 of Essential Indicators'),
    
    ('GHG_SCOPE2_TOTAL', 1, 'Total Scope 2 emissions (Break-up of the GHG (CO2e) into CO2, CH4, N2O, HFCs, PFCs, SF6, NF3, if available)', 'MT CO2e',
     'Indirect GHG emissions from the generation of energy that is purchased from a utility provider', 'E', 1.0,
     'Total consumption of purchased energy, GHG emission factor across all purchased energy sources',
     'Principle 6, Question 7 of Essential Indicators'),
    
    ('GHG_INTENSITY_REVENUE', 1, 'GHG Emission Intensity (Scope 1 + 2)', 'MT CO2e per INR',
     'Total Scope 1 and Scope 2 emissions per Total Revenue from Operations adjusted for PPP', 'E', 0.9,
     'Total emissions, revenue from audited P&L statement, PPP conversion',
     'Principle 6, Question 7 of Essential Indicators'),
    
    ('GHG_INTENSITY_OUTPUT', 1, 'GHG Emission Intensity (Scope 1 + 2)', 'MT CO2e per unit',
     'Total Scope 1 and Scope 2 emissions per Total Output of Product or Services', 'E', 0.9,
     'Total emissions, company and sector specific output metrics',
     'Principle 6, Question 7 of Essential Indicators'),
    
    # Attribute 2: Water Footprint (Environmental) - 7 parameters
    ('WATER_CONSUMPTION_TOTAL', 2, 'Total water consumption', 'Mn Lt or KL',
     'Water consumed that is no longer available for use by the ecosystem or local community', 'E', 1.0,
     'Input water flow meter logs minus output water flow meter logs (calibrated meters)',
     'Principle 6, Question 3 of Essential Indicators'),
    
    ('WATER_INTENSITY_REVENUE', 2, 'Water consumption intensity', 'Mn Lt or KL per INR',
     'Water consumption per revenue adjusted for PPP', 'E', 0.8,
     'Total water consumed, total revenue from operations, PPP conversion',
     'Principle 6, Question 3 of Essential Indicators'),
    
    ('WATER_INTENSITY_OUTPUT', 2, 'Water consumption intensity', 'Mn Lt or KL per unit',
     'Water consumption per unit of product or service', 'E', 0.8,
     'Water consumed, company and sector specific output metrics',
     'Principle 6, Question 3 of Essential Indicators'),
    
    ('WATER_DISCHARGE_UNTREATED', 2, 'Water Discharge by destination and levels of Treatment - Untreated', 'Mn Lt or KL',
     'Water discharged without treatment', 'E', 0.7,
     'Measurement of untreated water discharge',
     'Principle 6, Question 4 of Essential Indicators'),
    
    ('WATER_DISCHARGE_PRIMARY', 2, 'Water Discharge by destination and levels of Treatment - Primary Treatment', 'Mn Lt or KL',
     'Water discharged after primary treatment (removal of material that floats or settles out)', 'E', 0.6,
     'Filtration, screening, sedimentation',
     'Principle 6, Question 4 of Essential Indicators'),
    
    ('WATER_DISCHARGE_SECONDARY', 2, 'Water Discharge by destination and levels of Treatment - Secondary Treatment', 'Mn Lt or KL',
     'Water discharged after secondary treatment (removal of dissolved organic matter)', 'E', 0.6,
     'Oxidation, digestion',
     'Principle 6, Question 4 of Essential Indicators'),
    
    ('WATER_DISCHARGE_TERTIARY', 2, 'Water Discharge by destination and levels of Treatment - Tertiary Treatment', 'Mn Lt or KL',
     'Water discharged after tertiary treatment (disinfecting water)', 'E', 0.6,
     'Removal of pathogens, phosphorous, nitrogen',
     'Principle 6, Question 4 of Essential Indicators'),
    
    # Attribute 3: Energy Footprint (Environmental) - 4 parameters
    ('ENERGY_CONSUMPTION_TOTAL', 3, 'Total energy consumed', 'Joules or multiples',
     'Total energy from renewable and non-renewable sources', 'E', 1.0,
     'Non-renewable fuel + renewable fuel + purchased electricity/heating/cooling/steam + self-generated energy',
     'Principle 6, Question 1 of Essential Indicators'),
    
    ('ENERGY_RENEWABLE_PERCENT', 3, '% of energy consumed from renewable sources', '%',
     'Percentage of energy consumed from renewable sources', 'E', 1.0,
     'Energy consumed through renewable sources / total energy consumed',
     'Principle 6, Question 1 of Essential Indicators'),
    
    ('ENERGY_INTENSITY_REVENUE', 3, 'Energy intensity', 'Joules or multiples per INR',
     'Energy consumption per revenue adjusted for PPP', 'E', 0.8,
     'Total energy consumed, total revenue from operations, PPP conversion',
     'Principle 6, Question 1 of Essential Indicators'),
    
    ('ENERGY_INTENSITY_OUTPUT', 3, 'Energy intensity', 'Joules or multiples per unit',
     'Energy consumption per unit of product or service', 'E', 0.8,
     'Energy consumed, company and sector specific output metrics',
     'Principle 6, Question 1 of Essential Indicators'),
    
    # Attribute 4: Waste Management (Environmental) - 17 parameters
    ('WASTE_PLASTIC', 4, 'Plastic waste (A)', 'Kg or MT',
     'Absolute weight of packaging material discarded as defined under plastic waste management rules 2016', 'E', 0.8,
     'Weight of plastic waste (bags, bottles, pallets)',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_EWASTE', 4, 'E-waste (B)', 'Kg or MT',
     'Discarded computers, televisions, cell phones, VCRs, stereos, DVD players, copiers, fax machines', 'E', 0.8,
     'Weight of e-waste as per e-waste management rules 2016',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_BIOMEDICAL', 4, 'Bio-medical waste (C)', 'Kg or MT',
     'Solids and liquid waste generated during diagnosis, treatment or immunization', 'E', 0.7,
     'Weight of bio-medical waste as per bio-medical waste management rules 2016',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_CONSTRUCTION', 4, 'Construction and demolition waste (D)', 'Kg or MT',
     'Construction waste like concrete, plaster, metal rods/wires, wood, plastics', 'E', 0.7,
     'Weight of C&D waste as per C&D waste management rules 2016',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_BATTERY', 4, 'Battery waste (E)', 'Kg or MT',
     'Discarded batteries (Li-ion, Alkaline, Lead Acid) from vehicles, computers, mobiles, UPS', 'E', 0.7,
     'Weight of battery waste as per battery waste management rules 2016',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_RADIOACTIVE', 4, 'Radioactive waste (F)', 'Kg or MT',
     'Discarded material with radiation exposure from nuclear plants, hospitals, research labs', 'E', 0.6,
     'Weight of radioactive waste',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_HAZARDOUS_OTHER', 4, 'Other Hazardous waste (G)', 'Kg or MT',
     'Hazardous waste as per CPCB hazardous waste management rules', 'E', 0.7,
     'Weight of hazardous waste per CPCB rules',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_NON_HAZARDOUS', 4, 'Other Non-hazardous waste generated (H)', 'Kg or MT',
     'Waste not identified as hazardous by CPCB', 'E', 0.6,
     'Weight of non-hazardous waste',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_TOTAL', 4, 'Total waste generated (A+B+C+D+E+F+G+H)', 'Kg or MT',
     'Sum of all waste categories', 'E', 1.0,
     'Sum of plastic, e-waste, bio-medical, C&D, battery, radioactive, hazardous, non-hazardous',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_INTENSITY_REVENUE', 4, 'Waste intensity', 'Kg or MT per INR',
     'Waste generated per revenue adjusted for PPP', 'E', 0.8,
     'Total waste, revenue from P&L, PPP conversion',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_INTENSITY_OUTPUT', 4, 'Waste intensity', 'Kg or MT per unit',
     'Waste generated per unit of product or service', 'E', 0.8,
     'Total waste, sector-specific output metrics',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_RECYCLED_ABSOLUTE', 4, 'Total waste recovered through recycling, re-using or other recovery operations', 'Kg or MT',
     'Absolute quantity of waste recycled or recovered', 'E', 0.7,
     'Kg of waste recycled recovered / total waste generated',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_RECYCLED_INTENSITY', 4, 'Total waste recovered through recycling, re-using or other recovery operations', 'Intensity',
     'Intensity of waste recycled or recovered', 'E', 0.6,
     'Certificates from vendors for assurance of KPIs on waste management',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_DISPOSED_LANDFILL', 4, 'Total waste disposed by nature of disposal method - Landfill', 'Kg or MT',
     'Amount of material disposed to landfill', 'E', 0.6,
     'Amount of material in MT disposed to landfill',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_DISPOSED_INCINERATION', 4, 'Total waste disposed by nature of disposal method - Incineration', 'Kg or MT',
     'Amount of material disposed through incineration', 'E', 0.6,
     'Amount of material in MT disposed through incineration',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_DISPOSED_OTHER', 4, 'Total waste disposed by nature of disposal method - Any other method', 'Kg or MT',
     'Amount of material disposed through other methods', 'E', 0.5,
     'Amount of material in MT disposed through other methods',
     'Principle 6, Question 9 of Essential Indicators'),
    
    ('WASTE_DISPOSED_INTENSITY', 4, 'Total waste disposed by nature of disposal method', 'Intensity',
     'Intensity of waste disposed', 'E', 0.5,
     'Kg of waste disposed / total waste generated',
     'Principle 6, Question 9 of Essential Indicators'),
    
    # Attribute 5: Employee Wellbeing and Safety (Social) - 4 parameters
    ('EMPLOYEE_WELLBEING_SPEND_PERCENT', 5, 'Spending on measures towards well-being of employees and workers', '%',
     'Cost incurred as a % of total revenue of the company', 'S', 1.0,
     'Insurance, maternity/paternity benefits, day care facilities, health & safety measures',
     'Principle 3, Question 1(c) of Essential Indicators'),
    
    ('SAFETY_LTIFR', 5, 'Lost Time Injury Frequency Rate (LTIFR)', 'per million hours',
     'LTIFR per one million person-hours worked', 'S', 1.0,
     'Total lost time injuries * 1,000,000 / Total working hours',
     'Principle 3, Question 11 of Essential Indicators'),
    
    ('SAFETY_PERMANENT_DISABILITIES', 5, 'Number of Permanent Disabilities', 'count',
     'Total permanent disabilities from workplace incidents', 'S', 0.9,
     'Claims and incident reports',
     'Principle 3, Question 11 of Essential Indicators'),
    
    ('SAFETY_FATALITIES', 5, 'Number of fatalities', 'count',
     'Total fatalities of employees and workers', 'S', 1.0,
     'Claims reported to Factory Inspector',
     'Principle 3, Question 11 of Essential Indicators'),
    
    # Attribute 6: Gender Diversity (Social) - 4 parameters
    ('GENDER_WAGE_PERCENT', 6, 'Gross wages paid to females as % of wages paid', '%',
     'Wages paid to females as % of total wages', 'S', 1.0,
     'Employee master/register data',
     'Principle 5, Question 3(b) of Essential Indicators'),
    
    ('GENDER_POSH_COMPLAINTS_TOTAL', 6, 'Total Complaints on Sexual Harassment (POSH) reported', 'count',
     'Total complaints on sexual harassment reported', 'S', 1.0,
     'POSH committee records',
     'Principle 5, Question 7 of Essential Indicators'),
    
    ('GENDER_POSH_COMPLAINTS_PERCENT', 6, 'Complaints on POSH as a % of female employees/workers', '%',
     'POSH complaints as percentage of female employees/workers', 'S', 0.9,
     'POSH complaints / total female employees',
     'Principle 5, Question 7 of Essential Indicators'),
    
    ('GENDER_POSH_UPHELD', 6, 'Complaints on POSH upheld', 'count',
     'Number of POSH complaints upheld after investigation', 'S', 0.9,
     'POSH committee investigation outcomes',
     'Principle 5, Question 7 of Essential Indicators'),
    
    # Attribute 7: Inclusive Development (Social) - 3 parameters
    ('INCLUSIVE_MSME_SOURCING_PERCENT', 7, 'Input material sourced from MSMEs/small producers', '%',
     'Material sourced from MSMEs/small producers as % of total purchases', 'S', 1.0,
     'Procurement records including raw material, spares, services, capex',
     'Principle 8, Question 4 of Essential Indicators'),
    
    ('INCLUSIVE_INDIA_SOURCING_PERCENT', 7, 'Input material sourced from within India', '%',
     'Material sourced from within India as % of total purchases', 'S', 0.8,
     'Procurement records by geography',
     'Principle 8, Question 4 of Essential Indicators'),
    
    ('INCLUSIVE_SMALLER_TOWNS_WAGE_PERCENT', 7, 'Wages paid to persons employed in smaller towns', '%',
     'Wages paid in smaller towns as % of total wage cost', 'S', 1.0,
     'Employee location data categorized by RBI classification (rural/semi-urban/urban/metro)',
     'Principle 8, Question 5 of Essential Indicators'),
    
    # Attribute 8: Customer and Supplier Fairness (Governance) - 2 parameters
    ('CUSTOMER_DATA_BREACH_PERCENT', 8, 'Instances involving loss/breach of data of customers', '%',
     'Data breaches involving customer data as % of total cyber security events', 'G', 1.0,
     'Cyber security incident reports',
     'Principle 9, Question 7 of Essential Indicators'),
    
    ('SUPPLIER_PAYMENT_DAYS', 8, 'Number of days of accounts payable', 'days',
     'Average number of days to pay suppliers', 'G', 1.0,
     '(Accounts payable * 365) / Cost of goods/services procured from financial statements',
     'Principle 1, Question 8 of Essential Indicators'),
    
    # Attribute 9: Business Openness (Governance) - 10 parameters
    ('OPENNESS_TRADING_HOUSE_PURCHASES_PERCENT', 9, 'Purchases from trading houses as % of total purchases', '%',
     'Purchases from trading houses as % of total purchases', 'G', 0.8,
     'Financial statements and invoices',
     'Principle 1, Question 9 of Essential Indicators'),
    
    ('OPENNESS_TRADING_HOUSE_COUNT', 9, 'Number of trading houses where purchases are made from', 'count',
     'Total number of trading houses where purchases are made', 'G', 0.6,
     'Vendor master data',
     'Principle 1, Question 9 of Essential Indicators'),
    
    ('OPENNESS_TOP10_TRADING_HOUSE_PERCENT', 9, 'Purchases from top 10 trading houses as % of total purchases from trading houses', '%',
     'Purchases from top 10 trading houses as % of total trading house purchases', 'G', 0.7,
     'Concentration analysis of trading house purchases',
     'Principle 1, Question 9 of Essential Indicators'),
    
    ('OPENNESS_DEALER_SALES_PERCENT', 9, 'Sales to dealers/distributors as % of total sales', '%',
     'Sales to dealers/distributors as % of total sales', 'G', 0.8,
     'Sales records and invoices',
     'Principle 1, Question 9 of Essential Indicators'),
    
    ('OPENNESS_DEALER_COUNT', 9, 'Number of dealers/distributors to whom sales are made', 'count',
     'Total number of dealers/distributors to whom sales are made', 'G', 0.6,
     'Customer master data',
     'Principle 1, Question 9 of Essential Indicators'),
    
    ('OPENNESS_TOP10_DEALER_PERCENT', 9, 'Sales to top 10 dealers/distributors as % of total sales to dealers/distributors', '%',
     'Sales to top 10 dealers as % of total dealer sales', 'G', 0.7,
     'Concentration analysis of dealer sales',
     'Principle 1, Question 9 of Essential Indicators'),
    
    ('OPENNESS_RPT_PURCHASES_PERCENT', 9, 'Share of RPTs in Purchases', '%',
     'Related party transaction purchases as % of total purchases', 'G', 1.0,
     'RPT audited by financial auditors, refer financial audit report',
     'Principle 1, Question 9 of Essential Indicators'),
    
    ('OPENNESS_RPT_SALES_PERCENT', 9, 'Share of RPTs in Sales', '%',
     'Related party transaction sales as % of total sales', 'G', 1.0,
     'RPT audited by financial auditors, refer financial audit report',
     'Principle 1, Question 9 of Essential Indicators'),
    
    ('OPENNESS_RPT_LOANS_PERCENT', 9, 'Share of RPTs in Loans & advances', '%',
     'Related party transaction loans and advances as % of total', 'G', 0.9,
     'RPT audited by financial auditors, refer financial audit report',
     'Principle 1, Question 9 of Essential Indicators'),
    
    ('OPENNESS_RPT_INVESTMENTS_PERCENT', 9, 'Share of RPTs in Investments', '%',
     'Related party transaction investments as % of total investments', 'G', 0.9,
     'RPT audited by financial auditors, refer financial audit report',
     'Principle 1, Question 9 of Essential Indicators'),
]


def seed_indicators():
    """Seed BRSR Core indicators into the database with verification"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print(f"Connected to database: {DB_CONFIG['dbname']}")
        
        # Check if indicators already exist
        cur.execute("SELECT COUNT(*) FROM brsr_indicators")
        existing_count = cur.fetchone()[0]
        
        if existing_count > 0:
            print(f"Found {existing_count} existing indicators.")
            print("Updating indicators with complete Annexure I data...")
            
            # Use ON CONFLICT to update existing indicators
            insert_query = """
                INSERT INTO brsr_indicators 
                (indicator_code, attribute_number, parameter_name, measurement_unit, 
                 description, pillar, weight, data_assurance_approach, brsr_reference)
                VALUES %s
                ON CONFLICT (indicator_code) DO UPDATE SET
                    attribute_number = EXCLUDED.attribute_number,
                    parameter_name = EXCLUDED.parameter_name,
                    measurement_unit = EXCLUDED.measurement_unit,
                    description = EXCLUDED.description,
                    pillar = EXCLUDED.pillar,
                    weight = EXCLUDED.weight,
                    data_assurance_approach = EXCLUDED.data_assurance_approach,
                    brsr_reference = EXCLUDED.brsr_reference,
                    updated_at = NOW()
            """
        else:
            print("No existing indicators found. Inserting new indicators...")
            insert_query = """
                INSERT INTO brsr_indicators 
                (indicator_code, attribute_number, parameter_name, measurement_unit, 
                 description, pillar, weight, data_assurance_approach, brsr_reference)
                VALUES %s
            """
        
        # Insert/update indicators
        execute_values(cur, insert_query, BRSR_INDICATORS)
        conn.commit()
        
        # Verify count
        cur.execute("SELECT COUNT(*) FROM brsr_indicators")
        final_count = cur.fetchone()[0]
        
        print(f"\n✓ Successfully seeded/updated {final_count} BRSR Core indicators")
        print(f"  Expected: {len(BRSR_INDICATORS)} indicators from Annexure I")
        
        if final_count < len(BRSR_INDICATORS):
            print(f"  ⚠ Warning: Expected {len(BRSR_INDICATORS)} but found {final_count}")
        
        # Print summary by attribute
        cur.execute("""
            SELECT attribute_number, pillar, COUNT(*) 
            FROM brsr_indicators 
            GROUP BY attribute_number, pillar 
            ORDER BY attribute_number
        """)
        
        print("\n📊 Indicators by attribute:")
        attribute_names = {
            1: "GHG Footprint",
            2: "Water Footprint",
            3: "Energy Footprint",
            4: "Waste Management",
            5: "Employee Wellbeing and Safety",
            6: "Gender Diversity",
            7: "Inclusive Development",
            8: "Customer and Supplier Fairness",
            9: "Business Openness"
        }
        
        for row in cur.fetchall():
            attr_num, pillar, count = row
            attr_name = attribute_names.get(attr_num, f"Attribute {attr_num}")
            print(f"  Attribute {attr_num} - {attr_name} ({pillar}): {count} indicators")
        
        # Verify all 9 attributes are present
        cur.execute("SELECT DISTINCT attribute_number FROM brsr_indicators ORDER BY attribute_number")
        attributes = [row[0] for row in cur.fetchall()]
        
        print(f"\n✓ Attributes present: {attributes}")
        if len(attributes) == 9 and attributes == list(range(1, 10)):
            print("✓ All 9 BRSR Core attributes are represented")
        else:
            print(f"⚠ Warning: Expected 9 attributes (1-9), found: {attributes}")
        
        # Verify pillar distribution
        cur.execute("SELECT pillar, COUNT(*) FROM brsr_indicators GROUP BY pillar ORDER BY pillar")
        pillars = dict(cur.fetchall())
        
        print(f"\n📊 Pillar distribution:")
        print(f"  Environmental (E): {pillars.get('E', 0)} indicators")
        print(f"  Social (S): {pillars.get('S', 0)} indicators")
        print(f"  Governance (G): {pillars.get('G', 0)} indicators")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Error seeding indicators: {e}")
        raise


def main():
    """Main entry point"""
    print("=" * 70)
    print("BRSR Core Indicator Seeding - Complete Annexure I Implementation")
    print("=" * 70)
    seed_indicators()
    print("\n" + "=" * 70)
    print("Seeding complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
