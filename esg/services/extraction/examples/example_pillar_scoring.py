#!/usr/bin/env python3
"""
Example usage of pillar score calculation.

This script demonstrates how to use the pillar calculator in the extraction workflow.
It shows:
1. Loading BRSR indicator definitions from the database
2. Simulating extracted indicator values
3. Calculating pillar scores
4. Getting detailed breakdown for transparency

Requirements: 15.1, 15.2, 15.4, 15.5
"""

import logging
from src.db.repository import load_brsr_indicators
from src.scoring import calculate_pillar_scores
from src.scoring.pillar_calculator import get_pillar_breakdown

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main example function."""
    logger.info("=== Pillar Score Calculation Example ===\n")
    
    # Step 1: Load BRSR indicator definitions from database
    logger.info("Step 1: Loading BRSR indicator definitions...")
    try:
        indicators = load_brsr_indicators()
        logger.info(f"Loaded {len(indicators)} BRSR Core indicators\n")
    except Exception as e:
        logger.error(f"Failed to load indicators: {e}")
        logger.info("Using sample data for demonstration...")
        # In a real scenario, this would fail and exit
        return
    
    # Step 2: Simulate extracted indicator values
    # In a real workflow, these would come from the LLM extraction process
    logger.info("Step 2: Simulating extracted indicator values...")
    extracted_values = {
        # Environmental indicators
        "GHG_SCOPE1_TOTAL": 1250.0,
        "GHG_SCOPE2_TOTAL": 850.0,
        "ENERGY_RENEWABLE_PERCENT": 45.0,
        "WATER_CONSUMPTION_TOTAL": 50000.0,
        "WASTE_TOTAL": 120.0,
        "WASTE_RECYCLED_PLASTIC": 30.0,
        
        # Social indicators
        "EMPLOYEE_WELLBEING_SPEND_PERCENT": 2.5,
        "SAFETY_LTIFR": 0.8,
        "SAFETY_FATALITIES": 0.0,
        "GENDER_WAGE_PERCENT": 35.0,
        "GENDER_POSH_COMPLAINTS_TOTAL": 2.0,
        
        # Governance indicators
        "CUSTOMER_DATA_BREACH_PERCENT": 0.5,
        "SUPPLIER_PAYMENT_DAYS": 60.0,
        "OPENNESS_RPT_PURCHASES_PERCENT": 5.0,
        "OPENNESS_RPT_SALES_PERCENT": 3.0,
    }
    
    logger.info(f"Extracted {len(extracted_values)} indicator values\n")
    
    # Step 3: Calculate pillar scores
    logger.info("Step 3: Calculating pillar scores...")
    env_score, soc_score, gov_score = calculate_pillar_scores(
        indicators,
        extracted_values
    )
    
    logger.info("\n=== PILLAR SCORES ===")
    logger.info(f"Environmental (E): {env_score:.2f}/100" if env_score else "Environmental (E): No data")
    logger.info(f"Social (S):        {soc_score:.2f}/100" if soc_score else "Social (S): No data")
    logger.info(f"Governance (G):    {gov_score:.2f}/100" if gov_score else "Governance (G): No data")
    
    # Step 4: Get detailed breakdown for transparency
    logger.info("\nStep 4: Generating detailed breakdown for transparency...")
    breakdown = get_pillar_breakdown(indicators, extracted_values)
    
    logger.info("\n=== DETAILED BREAKDOWN ===")
    for pillar_key, pillar_data in breakdown.items():
        pillar_name = {
            "E": "Environmental",
            "S": "Social",
            "G": "Governance"
        }[pillar_key]
        
        logger.info(f"\n{pillar_name} Pillar:")
        if pillar_data["score"] is None:
            logger.info("  No data available")
            continue
        
        logger.info(f"  Score: {pillar_data['score']:.2f}/100")
        logger.info(f"  Total Weight: {pillar_data['total_weight']:.2f}")
        logger.info(f"  Indicators ({len(pillar_data['indicators'])}):")
        
        for ind in pillar_data["indicators"]:
            logger.info(f"    - {ind['code']}")
            logger.info(f"      Name: {ind['name']}")
            logger.info(f"      Value: {ind['value']} {ind['unit']}")
            logger.info(f"      Normalized: {ind['normalized']:.2f}/100")
            logger.info(f"      Weight: {ind['weight']}")
            logger.info(f"      Contribution: {ind['contribution']:.2f}")
    
    # Step 5: Calculate overall ESG score (simple average for now)
    logger.info("\n=== OVERALL ESG SCORE ===")
    available_scores = [s for s in [env_score, soc_score, gov_score] if s is not None]
    if available_scores:
        overall_score = sum(available_scores) / len(available_scores)
        logger.info(f"Overall ESG Score: {overall_score:.2f}/100")
        logger.info(f"(Simple average of {len(available_scores)} available pillar scores)")
    else:
        logger.info("Cannot calculate overall score - no pillar data available")
    
    logger.info("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
