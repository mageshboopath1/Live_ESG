"""
Sample data fixtures for integration tests
"""

# Sample company data
SAMPLE_COMPANIES = [
    {
        "name": "Test Company A",
        "ticker": "TESTA",
        "sector": "Technology",
        "description": "A test technology company"
    },
    {
        "name": "Test Company B",
        "ticker": "TESTB",
        "sector": "Finance",
        "description": "A test finance company"
    }
]

# Sample BRSR indicator data (subset for testing)
SAMPLE_BRSR_INDICATORS = [
    {
        "indicator_code": "TEST_GHG_SCOPE1",
        "attribute_number": 1,
        "parameter_name": "Test Scope 1 emissions",
        "measurement_unit": "MT CO2e",
        "description": "Test indicator for Scope 1 emissions",
        "pillar": "E",
        "weight": 1.0,
        "data_assurance_approach": "Limited assurance",
        "brsr_reference": "Test Reference"
    },
    {
        "indicator_code": "TEST_WATER_WITHDRAWAL",
        "attribute_number": 2,
        "parameter_name": "Test water withdrawal",
        "measurement_unit": "Kilolitres",
        "description": "Test indicator for water withdrawal",
        "pillar": "E",
        "weight": 0.8,
        "data_assurance_approach": "Limited assurance",
        "brsr_reference": "Test Reference"
    },
    {
        "indicator_code": "TEST_EMPLOYEES_TOTAL",
        "attribute_number": 5,
        "parameter_name": "Test total employees",
        "measurement_unit": "Number",
        "description": "Test indicator for employee count",
        "pillar": "S",
        "weight": 0.7,
        "data_assurance_approach": "Reasonable assurance",
        "brsr_reference": "Test Reference"
    }
]

# Sample extracted indicator data
SAMPLE_EXTRACTED_INDICATORS = [
    {
        "company_id": 1,
        "indicator_code": "GHG_SCOPE1_TOTAL",
        "value": "1500.5",
        "unit": "MT CO2e",
        "fiscal_year": 2024,
        "confidence_score": 0.95
    },
    {
        "company_id": 1,
        "indicator_code": "WATER_WITHDRAWAL",
        "value": "50000",
        "unit": "Kilolitres",
        "fiscal_year": 2024,
        "confidence_score": 0.92
    }
]

# Sample ESG scores
SAMPLE_ESG_SCORES = [
    {
        "company_id": 1,
        "score_type": "E",
        "score_value": 75.5,
        "fiscal_year": 2024
    },
    {
        "company_id": 1,
        "score_type": "S",
        "score_value": 82.3,
        "fiscal_year": 2024
    },
    {
        "company_id": 1,
        "score_type": "G",
        "score_value": 68.7,
        "fiscal_year": 2024
    },
    {
        "company_id": 1,
        "score_type": "ESG",
        "score_value": 75.5,
        "fiscal_year": 2024
    }
]

# Sample document metadata
SAMPLE_DOCUMENTS = [
    {
        "company_id": 1,
        "file_path": "test/sample_report_2024.pdf",
        "file_name": "sample_report_2024.pdf",
        "file_size": 1024000,
        "fiscal_year": 2024,
        "report_type": "BRSR"
    }
]

# Sample PDF file path
SAMPLE_PDF_PATH = "tests/fixtures/sample_brsr_report.pdf"


def get_sample_company(index: int = 0):
    """Get a sample company by index"""
    return SAMPLE_COMPANIES[index] if index < len(SAMPLE_COMPANIES) else SAMPLE_COMPANIES[0]


def get_sample_indicator(index: int = 0):
    """Get a sample BRSR indicator by index"""
    return SAMPLE_BRSR_INDICATORS[index] if index < len(SAMPLE_BRSR_INDICATORS) else SAMPLE_BRSR_INDICATORS[0]


def get_sample_pdf_path():
    """Get path to sample PDF file for testing"""
    import os
    # Get absolute path relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "sample_brsr_report.pdf")


def get_sample_pdf_content():
    """Get sample PDF content as bytes for testing"""
    pdf_path = get_sample_pdf_path()
    with open(pdf_path, 'rb') as f:
        return f.read()


# Sample embeddings data
SAMPLE_EMBEDDINGS = [
    {
        "company_id": 1,
        "document_id": 1,
        "chunk_text": "The company reported total Scope 1 emissions of 1500.5 MT CO2e for fiscal year 2024.",
        "chunk_index": 0,
        "page_number": 5,
        "embedding": [0.1] * 1536  # Placeholder embedding vector
    },
    {
        "company_id": 1,
        "document_id": 1,
        "chunk_text": "Water withdrawal from all sources totaled 50,000 kilolitres during the reporting period.",
        "chunk_index": 1,
        "page_number": 8,
        "embedding": [0.2] * 1536  # Placeholder embedding vector
    }
]

# Sample user data for authentication tests
SAMPLE_USERS = [
    {
        "username": "test_user",
        "email": "test@example.com",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVqN8Yx8S",  # "password123"
        "is_active": True
    },
    {
        "username": "admin_user",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVqN8Yx8S",  # "password123"
        "is_active": True
    }
]

# Sample API keys for authentication tests
SAMPLE_API_KEYS = [
    {
        "key_name": "test_api_key",
        "key_hash": "test_key_hash_123",
        "user_id": 1,
        "is_active": True
    }
]

# Extended company data with more realistic information
EXTENDED_SAMPLE_COMPANIES = [
    {
        "name": "Reliance Industries Limited",
        "ticker": "RELIANCE",
        "sector": "Energy",
        "description": "Indian multinational conglomerate company",
        "market_cap": 1500000000000,
        "employees": 347000
    },
    {
        "name": "Tata Consultancy Services Limited",
        "ticker": "TCS",
        "sector": "Information Technology",
        "description": "IT services, consulting and business solutions",
        "market_cap": 1200000000000,
        "employees": 614795
    },
    {
        "name": "HDFC Bank Limited",
        "ticker": "HDFCBANK",
        "sector": "Banking",
        "description": "Private sector banking and financial services",
        "market_cap": 1100000000000,
        "employees": 177000
    }
]

# Sample ingestion metadata
SAMPLE_INGESTION_METADATA = [
    {
        "company_id": 1,
        "file_name": "RELIANCE_BRSR_2024.pdf",
        "file_path": "reports/2024/RELIANCE_BRSR_2024.pdf",
        "file_size": 2048000,
        "fiscal_year": 2024,
        "report_type": "BRSR",
        "status": "completed",
        "pages": 45
    },
    {
        "company_id": 2,
        "file_name": "TCS_BRSR_2024.pdf",
        "file_path": "reports/2024/TCS_BRSR_2024.pdf",
        "file_size": 1536000,
        "fiscal_year": 2024,
        "report_type": "BRSR",
        "status": "completed",
        "pages": 38
    }
]

# More comprehensive BRSR indicators covering all pillars
COMPREHENSIVE_BRSR_INDICATORS = [
    # Environmental (E) indicators
    {
        "indicator_code": "GHG_SCOPE1_TOTAL",
        "attribute_number": 1,
        "parameter_name": "Total Scope 1 emissions",
        "measurement_unit": "MT CO2e",
        "description": "Direct GHG emissions from owned or controlled sources",
        "pillar": "E",
        "weight": 1.0,
        "data_assurance_approach": "Limited assurance",
        "brsr_reference": "Principle 6, Question 7"
    },
    {
        "indicator_code": "GHG_SCOPE2_TOTAL",
        "attribute_number": 1,
        "parameter_name": "Total Scope 2 emissions",
        "measurement_unit": "MT CO2e",
        "description": "Indirect GHG emissions from purchased electricity",
        "pillar": "E",
        "weight": 0.9,
        "data_assurance_approach": "Limited assurance",
        "brsr_reference": "Principle 6, Question 7"
    },
    {
        "indicator_code": "WATER_WITHDRAWAL",
        "attribute_number": 2,
        "parameter_name": "Total water withdrawal",
        "measurement_unit": "Kilolitres",
        "description": "Water withdrawal by source",
        "pillar": "E",
        "weight": 0.8,
        "data_assurance_approach": "Limited assurance",
        "brsr_reference": "Principle 6, Question 8"
    },
    {
        "indicator_code": "WATER_CONSUMPTION",
        "attribute_number": 2,
        "parameter_name": "Total water consumption",
        "measurement_unit": "Kilolitres",
        "description": "Water consumption = withdrawal - discharge",
        "pillar": "E",
        "weight": 0.7,
        "data_assurance_approach": "Limited assurance",
        "brsr_reference": "Principle 6, Question 8"
    },
    {
        "indicator_code": "ENERGY_CONSUMPTION_TOTAL",
        "attribute_number": 3,
        "parameter_name": "Total energy consumption",
        "measurement_unit": "Joules",
        "description": "From renewable and non-renewable sources",
        "pillar": "E",
        "weight": 0.85,
        "data_assurance_approach": "Limited assurance",
        "brsr_reference": "Principle 6, Question 9"
    },
    {
        "indicator_code": "WASTE_GENERATED",
        "attribute_number": 4,
        "parameter_name": "Total waste generated",
        "measurement_unit": "Metric tonnes",
        "description": "All categories of waste generated",
        "pillar": "E",
        "weight": 0.75,
        "data_assurance_approach": "Limited assurance",
        "brsr_reference": "Principle 6, Question 10"
    },
    # Social (S) indicators
    {
        "indicator_code": "EMPLOYEES_TOTAL",
        "attribute_number": 5,
        "parameter_name": "Total number of employees",
        "measurement_unit": "Number",
        "description": "Permanent and other than permanent employees",
        "pillar": "S",
        "weight": 0.8,
        "data_assurance_approach": "Reasonable assurance",
        "brsr_reference": "Principle 3, Question 1"
    },
    {
        "indicator_code": "EMPLOYEES_WOMEN",
        "attribute_number": 5,
        "parameter_name": "Number of women employees",
        "measurement_unit": "Number",
        "description": "Women employees across all categories",
        "pillar": "S",
        "weight": 0.7,
        "data_assurance_approach": "Reasonable assurance",
        "brsr_reference": "Principle 3, Question 1"
    },
    {
        "indicator_code": "EMPLOYEE_TURNOVER",
        "attribute_number": 5,
        "parameter_name": "Employee turnover rate",
        "measurement_unit": "Percentage",
        "description": "Permanent employee turnover rate",
        "pillar": "S",
        "weight": 0.6,
        "data_assurance_approach": "Reasonable assurance",
        "brsr_reference": "Principle 3, Question 2"
    },
    {
        "indicator_code": "BOARD_WOMEN_PERCENTAGE",
        "attribute_number": 6,
        "parameter_name": "Percentage of women in Board",
        "measurement_unit": "Percentage",
        "description": "Women representation in Board of Directors",
        "pillar": "S",
        "weight": 0.75,
        "data_assurance_approach": "Reasonable assurance",
        "brsr_reference": "Principle 3, Question 3"
    },
    {
        "indicator_code": "CSR_SPENDING",
        "attribute_number": 7,
        "parameter_name": "CSR amount spent",
        "measurement_unit": "INR",
        "description": "Amount spent on CSR activities",
        "pillar": "S",
        "weight": 0.8,
        "data_assurance_approach": "Reasonable assurance",
        "brsr_reference": "Principle 8, Question 1"
    },
    # Governance (G) indicators
    {
        "indicator_code": "CUSTOMER_COMPLAINTS",
        "attribute_number": 8,
        "parameter_name": "Customer complaints received",
        "measurement_unit": "Number",
        "description": "Number of complaints from customers",
        "pillar": "G",
        "weight": 0.7,
        "data_assurance_approach": "Limited assurance",
        "brsr_reference": "Principle 9, Question 1"
    },
    {
        "indicator_code": "CUSTOMER_COMPLAINTS_RESOLVED",
        "attribute_number": 8,
        "parameter_name": "Customer complaints resolved",
        "measurement_unit": "Number",
        "description": "Number of complaints resolved",
        "pillar": "G",
        "weight": 0.65,
        "data_assurance_approach": "Limited assurance",
        "brsr_reference": "Principle 9, Question 1"
    },
    {
        "indicator_code": "CONCENTRATION_PURCHASES",
        "attribute_number": 9,
        "parameter_name": "Concentration of purchases",
        "measurement_unit": "Percentage",
        "description": "Purchases from trading houses as % of total",
        "pillar": "G",
        "weight": 0.6,
        "data_assurance_approach": "Limited assurance",
        "brsr_reference": "Principle 2, Question 1"
    }
]

# Sample extracted indicators with realistic values
REALISTIC_EXTRACTED_INDICATORS = [
    {
        "company_id": 1,
        "indicator_code": "GHG_SCOPE1_TOTAL",
        "value": "45678.90",
        "unit": "MT CO2e",
        "fiscal_year": 2024,
        "confidence_score": 0.95,
        "source_page": 12,
        "citation": "Total Scope 1 emissions for FY 2024 were 45,678.90 MT CO2e"
    },
    {
        "company_id": 1,
        "indicator_code": "WATER_WITHDRAWAL",
        "value": "125000",
        "unit": "Kilolitres",
        "fiscal_year": 2024,
        "confidence_score": 0.92,
        "source_page": 15,
        "citation": "Water withdrawal totaled 125,000 kilolitres"
    },
    {
        "company_id": 1,
        "indicator_code": "EMPLOYEES_TOTAL",
        "value": "347000",
        "unit": "Number",
        "fiscal_year": 2024,
        "confidence_score": 0.98,
        "source_page": 8,
        "citation": "Total employee count: 347,000"
    }
]

# Sample ESG scores with pillar breakdown
REALISTIC_ESG_SCORES = [
    {
        "company_id": 1,
        "score_type": "E",
        "score_value": 78.5,
        "fiscal_year": 2024,
        "calculation_date": "2024-03-15"
    },
    {
        "company_id": 1,
        "score_type": "S",
        "score_value": 82.3,
        "fiscal_year": 2024,
        "calculation_date": "2024-03-15"
    },
    {
        "company_id": 1,
        "score_type": "G",
        "score_value": 71.8,
        "fiscal_year": 2024,
        "calculation_date": "2024-03-15"
    },
    {
        "company_id": 1,
        "score_type": "ESG",
        "score_value": 77.5,
        "fiscal_year": 2024,
        "calculation_date": "2024-03-15"
    }
]


def get_sample_embedding(index: int = 0):
    """Get a sample embedding by index"""
    return SAMPLE_EMBEDDINGS[index] if index < len(SAMPLE_EMBEDDINGS) else SAMPLE_EMBEDDINGS[0]


def get_sample_user(index: int = 0):
    """Get a sample user by index"""
    return SAMPLE_USERS[index] if index < len(SAMPLE_USERS) else SAMPLE_USERS[0]


def get_extended_company(index: int = 0):
    """Get an extended sample company by index"""
    return EXTENDED_SAMPLE_COMPANIES[index] if index < len(EXTENDED_SAMPLE_COMPANIES) else EXTENDED_SAMPLE_COMPANIES[0]


def get_comprehensive_indicator(index: int = 0):
    """Get a comprehensive BRSR indicator by index"""
    return COMPREHENSIVE_BRSR_INDICATORS[index] if index < len(COMPREHENSIVE_BRSR_INDICATORS) else COMPREHENSIVE_BRSR_INDICATORS[0]


def get_realistic_extracted_indicator(index: int = 0):
    """Get a realistic extracted indicator by index"""
    return REALISTIC_EXTRACTED_INDICATORS[index] if index < len(REALISTIC_EXTRACTED_INDICATORS) else REALISTIC_EXTRACTED_INDICATORS[0]


def get_realistic_score(index: int = 0):
    """Get a realistic ESG score by index"""
    return REALISTIC_ESG_SCORES[index] if index < len(REALISTIC_ESG_SCORES) else REALISTIC_ESG_SCORES[0]


def get_sample_ingestion_metadata(index: int = 0):
    """Get sample ingestion metadata by index"""
    return SAMPLE_INGESTION_METADATA[index] if index < len(SAMPLE_INGESTION_METADATA) else SAMPLE_INGESTION_METADATA[0]
