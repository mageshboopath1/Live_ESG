"""
Example usage of ESG score calculation.

This script demonstrates how to use the ESG scoring module to calculate
overall ESG scores from extracted BRSR Core indicators.

Requirements: 15.3, 15.4, 15.5
"""

from src.models.brsr_models import BRSRIndicatorDefinition, Pillar
from src.scoring import (
    calculate_esg_score,
    get_esg_score_with_citations,
    DEFAULT_PILLAR_WEIGHTS,
)


def main():
    """Demonstrate ESG score calculation."""
    
    print("=" * 80)
    print("ESG Score Calculation Example")
    print("=" * 80)
    print()
    
    # Sample indicator definitions
    indicator_definitions = [
        # Environmental indicators
        BRSRIndicatorDefinition(
            indicator_code="GHG_SCOPE1_TOTAL",
            attribute_number=1,
            parameter_name="Total Scope 1 emissions",
            measurement_unit="MT CO2e",
            description="Direct GHG emissions from owned sources",
            pillar=Pillar.ENVIRONMENTAL,
            weight=1.0,
            data_assurance_approach="Fossil fuel consumption records",
            brsr_reference="Principle 6, Question 7",
        ),
        BRSRIndicatorDefinition(
            indicator_code="ENERGY_RENEWABLE_PERCENT",
            attribute_number=3,
            parameter_name="Energy from renewable sources",
            measurement_unit="%",
            description="Percentage of total energy from renewable sources",
            pillar=Pillar.ENVIRONMENTAL,
            weight=1.0,
            data_assurance_approach="Energy consumption records",
            brsr_reference="Principle 6, Question 1",
        ),
        BRSRIndicatorDefinition(
            indicator_code="WATER_RECYCLED_PERCENT",
            attribute_number=2,
            parameter_name="Water recycled and reused",
            measurement_unit="%",
            description="Percentage of water recycled and reused",
            pillar=Pillar.ENVIRONMENTAL,
            weight=0.8,
            data_assurance_approach="Water meters and treatment records",
            brsr_reference="Principle 6, Question 3",
        ),
        # Social indicators
        BRSRIndicatorDefinition(
            indicator_code="EMPLOYEE_WELLBEING_SPEND_PERCENT",
            attribute_number=5,
            parameter_name="Spending on employee wellbeing",
            measurement_unit="%",
            description="Wellbeing spend as percentage of revenue",
            pillar=Pillar.SOCIAL,
            weight=1.0,
            data_assurance_approach="Financial records",
            brsr_reference="Principle 3, Question 1(c)",
        ),
        BRSRIndicatorDefinition(
            indicator_code="GENDER_WAGE_PERCENT",
            attribute_number=6,
            parameter_name="Gross wages paid to females",
            measurement_unit="%",
            description="Female wages as percentage of total wages",
            pillar=Pillar.SOCIAL,
            weight=1.0,
            data_assurance_approach="Payroll data",
            brsr_reference="Principle 5, Question 3(b)",
        ),
        BRSRIndicatorDefinition(
            indicator_code="SAFETY_FATALITIES",
            attribute_number=5,
            parameter_name="Number of fatalities",
            measurement_unit="count",
            description="Total number of workplace fatalities",
            pillar=Pillar.SOCIAL,
            weight=1.0,
            data_assurance_approach="Incident reports",
            brsr_reference="Principle 3, Question 11",
        ),
        # Governance indicators
        BRSRIndicatorDefinition(
            indicator_code="CUSTOMER_DATA_BREACH_PERCENT",
            attribute_number=8,
            parameter_name="Customer data breach incidents",
            measurement_unit="%",
            description="Data breaches as percentage of cyber events",
            pillar=Pillar.GOVERNANCE,
            weight=1.0,
            data_assurance_approach="Security incident reports",
            brsr_reference="Principle 9, Question 7",
        ),
        BRSRIndicatorDefinition(
            indicator_code="SUPPLIER_PAYMENT_DAYS",
            attribute_number=8,
            parameter_name="Days of accounts payable",
            measurement_unit="days",
            description="Average days to pay suppliers",
            pillar=Pillar.GOVERNANCE,
            weight=1.0,
            data_assurance_approach="Financial statements",
            brsr_reference="Principle 1, Question 8",
        ),
    ]
    
    # Sample extracted values for a company
    extracted_values = {
        "GHG_SCOPE1_TOTAL": 1250.0,
        "ENERGY_RENEWABLE_PERCENT": 65.0,
        "WATER_RECYCLED_PERCENT": 40.0,
        "EMPLOYEE_WELLBEING_SPEND_PERCENT": 3.5,
        "GENDER_WAGE_PERCENT": 42.0,
        "SAFETY_FATALITIES": 0.0,
        "CUSTOMER_DATA_BREACH_PERCENT": 0.5,
        "SUPPLIER_PAYMENT_DAYS": 45.0,
    }
    
    print("Company: RELIANCE Industries")
    print("Report Year: 2024")
    print(f"Total Indicators Extracted: {len(extracted_values)}")
    print()
    
    # Calculate ESG score with default weights
    print("-" * 80)
    print("1. ESG Score with Default Weights")
    print("-" * 80)
    
    score, metadata = calculate_esg_score(indicator_definitions, extracted_values)
    
    print(f"\nOverall ESG Score: {score:.2f}/100")
    print()
    print("Pillar Scores:")
    print(f"  Environmental (E): {metadata['pillar_scores']['environmental']:.2f}/100")
    print(f"  Social (S):        {metadata['pillar_scores']['social']:.2f}/100")
    print(f"  Governance (G):    {metadata['pillar_scores']['governance']:.2f}/100")
    print()
    print("Pillar Weights:")
    print(f"  Environmental: {metadata['pillar_weights']['environmental']:.2%}")
    print(f"  Social:        {metadata['pillar_weights']['social']:.2%}")
    print(f"  Governance:    {metadata['pillar_weights']['governance']:.2%}")
    print()
    print(f"Calculation Method:\n  {metadata['calculation_method']}")
    print()
    
    # Calculate ESG score with custom weights (favoring environmental)
    print("-" * 80)
    print("2. ESG Score with Custom Weights (Environmental Focus)")
    print("-" * 80)
    
    custom_weights = {
        "E": 0.5,   # 50% weight on environmental
        "S": 0.3,   # 30% weight on social
        "G": 0.2,   # 20% weight on governance
    }
    
    score_custom, metadata_custom = calculate_esg_score(
        indicator_definitions,
        extracted_values,
        pillar_weights=custom_weights
    )
    
    print(f"\nOverall ESG Score: {score_custom:.2f}/100")
    print()
    print("Custom Pillar Weights:")
    print(f"  Environmental: {metadata_custom['pillar_weights']['environmental']:.2%}")
    print(f"  Social:        {metadata_custom['pillar_weights']['social']:.2%}")
    print(f"  Governance:    {metadata_custom['pillar_weights']['governance']:.2%}")
    print()
    
    # Show detailed breakdown for one pillar
    print("-" * 80)
    print("3. Detailed Environmental Pillar Breakdown")
    print("-" * 80)
    print()
    
    env_breakdown = metadata['pillar_breakdown']['E']
    print(f"Environmental Score: {env_breakdown['score']:.2f}/100")
    print(f"Total Weight: {env_breakdown['total_weight']}")
    print()
    print("Contributing Indicators:")
    for ind in env_breakdown['indicators']:
        print(f"  • {ind['name']}")
        print(f"    Code: {ind['code']}")
        print(f"    Value: {ind['value']} {ind['unit']}")
        print(f"    Normalized: {ind['normalized']:.2f}/100")
        print(f"    Weight: {ind['weight']}")
        print(f"    Contribution: {ind['contribution']:.2f}")
        print()
    
    # Example with citations
    print("-" * 80)
    print("4. ESG Score with Source Citations")
    print("-" * 80)
    print()
    
    # Sample extracted indicators with citation information
    extracted_indicators = [
        {
            "indicator_code": "ENERGY_RENEWABLE_PERCENT",
            "numeric_value": 65.0,
            "object_key": "RELIANCE/2024_BRSR.pdf",
            "source_pages": [45, 46],
            "source_chunk_ids": [123, 124],
            "confidence_score": 0.95,
        },
        {
            "indicator_code": "GENDER_WAGE_PERCENT",
            "numeric_value": 42.0,
            "object_key": "RELIANCE/2024_BRSR.pdf",
            "source_pages": [78],
            "source_chunk_ids": [234],
            "confidence_score": 0.88,
        },
        {
            "indicator_code": "CUSTOMER_DATA_BREACH_PERCENT",
            "numeric_value": 0.5,
            "object_key": "RELIANCE/2024_BRSR.pdf",
            "source_pages": [102, 103],
            "source_chunk_ids": [345, 346],
            "confidence_score": 0.92,
        },
    ]
    
    score_cited, metadata_cited = get_esg_score_with_citations(
        indicator_definitions,
        extracted_indicators
    )
    
    print(f"Overall ESG Score: {score_cited:.2f}/100")
    print()
    print("Sample Indicator with Citations:")
    
    # Show first indicator with citations
    for pillar_key, pillar_data in metadata_cited['pillar_breakdown'].items():
        if pillar_data['indicators']:
            ind = pillar_data['indicators'][0]
            if 'citations' in ind:
                print(f"  • {ind['name']}")
                print(f"    Value: {ind['value']} {ind['unit']}")
                print(f"    Source PDF: {ind['citations']['object_key']}")
                print(f"    Pages: {ind['citations']['source_pages']}")
                print(f"    Confidence: {ind['citations']['confidence_score']:.2%}")
                break
    
    print()
    print("=" * 80)
    print("Example Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
