-- Migration 002: BRSR Core Indicators
-- Description: Create BRSR Core indicators table with indexes and seed data
-- Date: 2024-01-02
-- Author: ESG Platform Team

-- Create BRSR indicators table
CREATE TABLE IF NOT EXISTS brsr_indicators (
    id SERIAL PRIMARY KEY,
    indicator_code TEXT NOT NULL UNIQUE,
    attribute_number INT NOT NULL CHECK (attribute_number >= 1 AND attribute_number <= 9),
    parameter_name TEXT NOT NULL,
    measurement_unit TEXT,
    description TEXT,
    pillar TEXT NOT NULL CHECK (pillar IN ('E', 'S', 'G')),
    weight DECIMAL(5,4) NOT NULL DEFAULT 1.0,
    data_assurance_approach TEXT,
    brsr_reference TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_brsr_attribute ON brsr_indicators(attribute_number);
CREATE INDEX IF NOT EXISTS idx_brsr_pillar ON brsr_indicators(pillar);
CREATE INDEX IF NOT EXISTS idx_brsr_code ON brsr_indicators(indicator_code);

-- Add composite index on (company_name, report_year) to document_embeddings table
-- This is CRITICAL for filtered vector retrieval performance
CREATE INDEX IF NOT EXISTS idx_doc_emb_company_year ON document_embeddings(company_name, report_year);

-- Add index on object_key for document lookups
CREATE INDEX IF NOT EXISTS idx_doc_emb_object_key ON document_embeddings(object_key);

-- Add pgvector HNSW index on embedding column with cosine distance
-- Note: pgvector has a 2000 dimension limit for vector type indexes
-- Since gemini-embedding-001 produces 3072-dimensional vectors, we cast to halfvec
-- This provides efficient similarity search with minimal accuracy loss
CREATE INDEX IF NOT EXISTS idx_doc_emb_vector ON document_embeddings 
USING hnsw ((embedding::halfvec(3072)) halfvec_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Add comments for documentation
COMMENT ON TABLE brsr_indicators IS 'BRSR Core indicator definitions based on SEBI framework with 9 attributes';
COMMENT ON COLUMN brsr_indicators.indicator_code IS 'Unique identifier for the indicator (e.g., GHG_SCOPE1_TOTAL)';
COMMENT ON COLUMN brsr_indicators.attribute_number IS 'BRSR Core attribute number (1-9): 1=GHG, 2=Water, 3=Energy, 4=Waste, 5=Employee Wellbeing, 6=Gender Diversity, 7=Inclusive Development, 8=Customer Fairness, 9=Business Openness';
COMMENT ON COLUMN brsr_indicators.pillar IS 'ESG pillar: E (Environmental), S (Social), G (Governance)';
COMMENT ON COLUMN brsr_indicators.weight IS 'Weight for score calculation (0.0-1.0)';
COMMENT ON COLUMN brsr_indicators.data_assurance_approach IS 'Method for data verification and assurance';
COMMENT ON COLUMN brsr_indicators.brsr_reference IS 'Cross-reference to BRSR Essential Indicators questions';

-- Seed BRSR Core indicators data
-- Attribute 1: GHG Footprint (Environmental)
INSERT INTO brsr_indicators (indicator_code, attribute_number, parameter_name, measurement_unit, description, pillar, weight, data_assurance_approach, brsr_reference) VALUES
('GHG_SCOPE1_TOTAL', 1, 'Total Scope 1 emissions', 'MT CO2e', 'Direct GHG emissions from organization owned or controlled sources', 'E', 1.0, 'Fossil fuel consumption, emission factors (IPCC or lab testing), carbon capture, fugitive emissions', 'Principle 6, Question 7 of Essential Indicators'),
('GHG_SCOPE2_TOTAL', 1, 'Total Scope 2 emissions', 'MT CO2e', 'Indirect GHG emissions from purchased energy', 'E', 1.0, 'Purchased energy consumption, emission factors from suppliers', 'Principle 6, Question 7 of Essential Indicators'),
('GHG_INTENSITY_REVENUE', 1, 'GHG Emission Intensity (Revenue)', 'MT CO2e per Rupee', 'Total Scope 1 and 2 emissions per revenue adjusted for PPP', 'E', 0.8, 'Total emissions, revenue from audited P&L, PPP conversion', 'Principle 6, Question 7 of Essential Indicators'),
('GHG_INTENSITY_OUTPUT', 1, 'GHG Emission Intensity (Output)', 'MT CO2e per Unit', 'Total Scope 1 and 2 emissions per unit of product or service', 'E', 0.8, 'Total emissions, sector-specific output metrics', 'Principle 6, Question 7 of Essential Indicators');

-- Attribute 2: Water Footprint (Environmental)
INSERT INTO brsr_indicators (indicator_code, attribute_number, parameter_name, measurement_unit, description, pillar, weight, data_assurance_approach, brsr_reference) VALUES
('WATER_CONSUMPTION_TOTAL', 2, 'Total water consumption', 'KL', 'Water consumed that is no longer available for ecosystem or community', 'E', 1.0, 'Input water flow meters minus output water flow meters (calibrated)', 'Principle 6, Question 3 of Essential Indicators'),
('WATER_INTENSITY_REVENUE', 2, 'Water consumption intensity (Revenue)', 'KL per Rupee', 'Water consumption per revenue adjusted for PPP', 'E', 0.7, 'Total water consumed, revenue from audited P&L, PPP conversion', 'Principle 6, Question 3 of Essential Indicators'),
('WATER_INTENSITY_OUTPUT', 2, 'Water consumption intensity (Output)', 'KL per Unit', 'Water consumption per unit of product or service', 'E', 0.7, 'Total water consumed, sector-specific output metrics', 'Principle 6, Question 3 of Essential Indicators'),
('WATER_DISCHARGE_UNTREATED', 2, 'Water discharge - Untreated', 'KL', 'Water discharged without treatment', 'E', 0.6, 'Flow meter measurements by treatment level', 'Principle 6, Question 4 of Essential Indicators'),
('WATER_DISCHARGE_PRIMARY', 2, 'Water discharge - Primary treatment', 'KL', 'Water with primary treatment (filtration, screening, sedimentation)', 'E', 0.5, 'Flow meter measurements by treatment level', 'Principle 6, Question 4 of Essential Indicators'),
('WATER_DISCHARGE_SECONDARY', 2, 'Water discharge - Secondary treatment', 'KL', 'Water with secondary treatment (oxidation, digestion)', 'E', 0.5, 'Flow meter measurements by treatment level', 'Principle 6, Question 4 of Essential Indicators'),
('WATER_DISCHARGE_TERTIARY', 2, 'Water discharge - Tertiary treatment', 'KL', 'Water with tertiary treatment (disinfection, pathogen removal)', 'E', 0.5, 'Flow meter measurements by treatment level', 'Principle 6, Question 4 of Essential Indicators');

-- Attribute 3: Energy Footprint (Environmental)
INSERT INTO brsr_indicators (indicator_code, attribute_number, parameter_name, measurement_unit, description, pillar, weight, data_assurance_approach, brsr_reference) VALUES
('ENERGY_CONSUMPTION_TOTAL', 3, 'Total energy consumed', 'Joules', 'Total energy from renewable and non-renewable sources', 'E', 1.0, 'Sum of fuel consumed, purchased energy, self-generated energy', 'Principle 6, Question 1 of Essential Indicators'),
('ENERGY_RENEWABLE_PERCENT', 3, 'Energy from renewable sources', '%', 'Percentage of energy consumed from renewable sources', 'E', 0.9, 'Renewable energy consumed divided by total energy consumed', 'Principle 6, Question 1 of Essential Indicators'),
('ENERGY_INTENSITY_REVENUE', 3, 'Energy intensity (Revenue)', 'Joules per Rupee', 'Energy consumption per revenue adjusted for PPP', 'E', 0.7, 'Total energy consumed, revenue from audited P&L, PPP conversion', 'Principle 6, Question 1 of Essential Indicators'),
('ENERGY_INTENSITY_OUTPUT', 3, 'Energy intensity (Output)', 'Joules per Unit', 'Energy consumption per unit of product or service', 'E', 0.7, 'Total energy consumed, sector-specific output metrics', 'Principle 6, Question 1 of Essential Indicators');

-- Attribute 4: Waste Management (Environmental)
INSERT INTO brsr_indicators (indicator_code, attribute_number, parameter_name, measurement_unit, description, pillar, weight, data_assurance_approach, brsr_reference) VALUES
('WASTE_PLASTIC', 4, 'Plastic waste', 'MT', 'Packaging material discarded as per Plastic Waste Management Rules 2016', 'E', 0.8, 'Absolute weight of discarded packaging materials', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_EWASTE', 4, 'E-waste', 'MT', 'Discarded electronic equipment as per E-waste Management Rules 2016', 'E', 0.8, 'Weight of discarded computers, phones, electronics', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_BIOMEDICAL', 4, 'Bio-medical waste', 'MT', 'Medical waste as per Bio-medical Waste Management Rules 2016', 'E', 0.7, 'Waste from diagnosis, treatment, immunization, research', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_CONSTRUCTION', 4, 'Construction and demolition waste', 'MT', 'Construction waste as per C&D Waste Management Rules 2016', 'E', 0.7, 'Concrete, plaster, metal, wood, plastics from construction', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_BATTERY', 4, 'Battery waste', 'MT', 'Discarded batteries as per Battery Waste Management Rules 2016', 'E', 0.7, 'Li-ion, alkaline, lead acid batteries from vehicles and electronics', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_RADIOACTIVE', 4, 'Radioactive waste', 'MT', 'Material with radiation exposure from nuclear facilities, hospitals, labs', 'E', 0.9, 'Contaminated materials from nuclear and medical applications', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_HAZARDOUS_OTHER', 4, 'Other hazardous waste', 'MT', 'Hazardous waste as per CPCB rules', 'E', 0.8, 'Hazardous materials per CPCB classification', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_NONHAZARDOUS', 4, 'Other non-hazardous waste', 'MT', 'Non-hazardous waste not classified above', 'E', 0.6, 'Waste not identified as hazardous per CPCB', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_TOTAL', 4, 'Total waste generated', 'MT', 'Sum of all waste categories', 'E', 1.0, 'Sum of all waste types', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_INTENSITY_REVENUE', 4, 'Waste intensity (Revenue)', 'MT per Rupee', 'Total waste per revenue adjusted for PPP', 'E', 0.7, 'Total waste, revenue from audited P&L, PPP conversion', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_INTENSITY_OUTPUT', 4, 'Waste intensity (Output)', 'MT per Unit', 'Total waste per unit of product or service', 'E', 0.7, 'Total waste, sector-specific output metrics', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_RECYCLED_ABSOLUTE', 4, 'Waste recovered through recycling', 'MT', 'Absolute quantity of waste recycled or recovered', 'E', 0.8, 'Certificates from vendors for recycling operations', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_RECYCLED_INTENSITY', 4, 'Waste recovery intensity', '%', 'Percentage of waste recycled or recovered', 'E', 0.8, 'Waste recycled divided by total waste generated', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_DISPOSED_LANDFILL', 4, 'Waste disposed to landfill', 'MT', 'Waste sent to landfill', 'E', 0.6, 'Amount of material disposed to landfill', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_DISPOSED_INCINERATION', 4, 'Waste disposed through incineration', 'MT', 'Waste disposed through burning', 'E', 0.6, 'Amount of material incinerated', 'Principle 6, Question 9 of Essential Indicators'),
('WASTE_DISPOSED_OTHER', 4, 'Waste disposed by other methods', 'MT', 'Waste disposed by methods other than landfill or incineration', 'E', 0.6, 'Amount of material disposed by alternative methods', 'Principle 6, Question 9 of Essential Indicators');

-- Attribute 5: Employee Wellbeing and Safety (Social)
INSERT INTO brsr_indicators (indicator_code, attribute_number, parameter_name, measurement_unit, description, pillar, weight, data_assurance_approach, brsr_reference) VALUES
('EMPLOYEE_WELLBEING_SPEND_PERCENT', 5, 'Spending on employee wellbeing', '%', 'Cost incurred on wellbeing measures as percentage of total revenue', 'S', 0.9, 'Insurance policies, infant care, mental health facilities, invoices', 'Principle 3, Question 1(c) of Essential Indicators'),
('SAFETY_LTIFR', 5, 'Lost Time Injury Frequency Rate', 'Rate per million hours', 'Number of lost time injuries per million person-hours worked', 'S', 1.0, 'Total lost time injuries divided by total working hours times 1,000,000', 'Principle 3, Question 11 of Essential Indicators'),
('SAFETY_FATALITIES', 5, 'Number of fatalities', 'Count', 'Total number of work-related fatalities', 'S', 1.0, 'Claims reported to Factory Inspector', 'Principle 3, Question 11 of Essential Indicators'),
('SAFETY_PERMANENT_DISABILITIES', 5, 'Number of permanent disabilities', 'Count', 'Total number of permanent disabilities from work incidents', 'S', 0.9, 'Claims reported to Factory Inspector', 'Principle 3, Question 11 of Essential Indicators');

-- Attribute 6: Gender Diversity (Social)
INSERT INTO brsr_indicators (indicator_code, attribute_number, parameter_name, measurement_unit, description, pillar, weight, data_assurance_approach, brsr_reference) VALUES
('GENDER_WAGES_FEMALE_PERCENT', 6, 'Gross wages paid to females', '%', 'Female wages as percentage of total wages paid', 'S', 0.9, 'Employee master register, payroll data', 'Principle 5, Question 3(b) of Essential Indicators'),
('GENDER_POSH_COMPLAINTS_TOTAL', 6, 'Total POSH complaints', 'Count', 'Total complaints on sexual harassment reported', 'S', 1.0, 'POSH committee records', 'Principle 5, Question 7 of Essential Indicators'),
('GENDER_POSH_COMPLAINTS_PERCENT', 6, 'POSH complaints as % of female employees', '%', 'POSH complaints as percentage of female employees/workers', 'S', 1.0, 'POSH complaints divided by female employee count', 'Principle 5, Question 7 of Essential Indicators'),
('GENDER_POSH_COMPLAINTS_UPHELD', 6, 'POSH complaints upheld', 'Count', 'Number of POSH complaints upheld after investigation', 'S', 0.9, 'POSH committee investigation outcomes', 'Principle 5, Question 7 of Essential Indicators');

-- Attribute 7: Inclusive Development (Social)
INSERT INTO brsr_indicators (indicator_code, attribute_number, parameter_name, measurement_unit, description, pillar, weight, data_assurance_approach, brsr_reference) VALUES
('INCLUSIVE_MSME_SOURCING_PERCENT', 7, 'Input material from MSMEs/small producers', '%', 'Procurement from MSMEs and small producers as percentage of total purchases', 'S', 0.9, 'Procurement records, vendor classifications, invoice values', 'Principle 8, Question 4 of Essential Indicators'),
('INCLUSIVE_LOCAL_SOURCING_PERCENT', 7, 'Input material sourced from within India', '%', 'Domestic procurement as percentage of total purchases', 'S', 0.8, 'Procurement records, vendor locations, invoice values', 'Principle 8, Question 4 of Essential Indicators'),
('INCLUSIVE_SMALLER_TOWNS_WAGES_PERCENT', 7, 'Wages paid in smaller towns', '%', 'Wages to employees in smaller towns as percentage of total wage cost', 'S', 0.9, 'Employee location data per RBI classification (rural/semi-urban/urban/metro)', 'Principle 8, Question 5 of Essential Indicators');

-- Attribute 8: Customer and Supplier Fairness (Governance)
INSERT INTO brsr_indicators (indicator_code, attribute_number, parameter_name, measurement_unit, description, pillar, weight, data_assurance_approach, brsr_reference) VALUES
('CUSTOMER_DATA_BREACH_PERCENT', 8, 'Customer data breaches', '%', 'Data breaches involving customer data as percentage of total cyber security events', 'G', 1.0, 'Cyber security incident reports', 'Principle 9, Question 7 of Essential Indicators'),
('SUPPLIER_PAYMENT_DAYS', 8, 'Days of accounts payable', 'Days', 'Average number of days to pay suppliers', 'G', 0.8, 'Accounts payable times 365 divided by cost of goods/services procured', 'Principle 1, Question 8 of Essential Indicators');

-- Attribute 9: Business Openness (Governance)
INSERT INTO brsr_indicators (indicator_code, attribute_number, parameter_name, measurement_unit, description, pillar, weight, data_assurance_approach, brsr_reference) VALUES
('OPENNESS_TRADING_HOUSES_PURCHASES_PERCENT', 9, 'Purchases from trading houses', '%', 'Purchases from trading houses as percentage of total purchases', 'G', 0.7, 'Financial statements, invoices, RPT audit', 'Principle 1, Question 9 of Essential Indicators'),
('OPENNESS_TRADING_HOUSES_COUNT', 9, 'Number of trading houses', 'Count', 'Total number of trading houses used for purchases', 'G', 0.6, 'Vendor master data', 'Principle 1, Question 9 of Essential Indicators'),
('OPENNESS_TOP10_TRADING_HOUSES_PERCENT', 9, 'Purchases from top 10 trading houses', '%', 'Purchases from top 10 trading houses as percentage of total trading house purchases', 'G', 0.7, 'Purchase concentration analysis', 'Principle 1, Question 9 of Essential Indicators'),
('OPENNESS_DEALERS_SALES_PERCENT', 9, 'Sales to dealers/distributors', '%', 'Sales to dealers as percentage of total sales', 'G', 0.7, 'Sales records, distributor agreements', 'Principle 1, Question 9 of Essential Indicators'),
('OPENNESS_DEALERS_COUNT', 9, 'Number of dealers/distributors', 'Count', 'Total number of dealers/distributors', 'G', 0.6, 'Distributor master data', 'Principle 1, Question 9 of Essential Indicators'),
('OPENNESS_TOP10_DEALERS_PERCENT', 9, 'Sales to top 10 dealers', '%', 'Sales to top 10 dealers as percentage of total dealer sales', 'G', 0.7, 'Sales concentration analysis', 'Principle 1, Question 9 of Essential Indicators'),
('OPENNESS_RPT_PURCHASES_PERCENT', 9, 'Related party transactions - Purchases', '%', 'RPT purchases as percentage of total purchases', 'G', 0.9, 'RPT audited by financial auditors, audit report', 'Principle 1, Question 9 of Essential Indicators'),
('OPENNESS_RPT_SALES_PERCENT', 9, 'Related party transactions - Sales', '%', 'RPT sales as percentage of total sales', 'G', 0.9, 'RPT audited by financial auditors, audit report', 'Principle 1, Question 9 of Essential Indicators'),
('OPENNESS_RPT_LOANS_PERCENT', 9, 'Related party transactions - Loans & advances', '%', 'RPT loans and advances as percentage of total', 'G', 0.9, 'RPT audited by financial auditors, audit report', 'Principle 1, Question 9 of Essential Indicators'),
('OPENNESS_RPT_INVESTMENTS_PERCENT', 9, 'Related party transactions - Investments', '%', 'RPT investments as percentage of total investments', 'G', 0.9, 'RPT audited by financial auditors, audit report', 'Principle 1, Question 9 of Essential Indicators');
