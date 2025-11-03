# ESG Scoring Module

This module provides comprehensive ESG score calculation functionality for the ESG Intelligence Platform.

## Overview

The scoring module calculates Environmental, Social, and Governance (ESG) scores from extracted BRSR Core indicators using weighted averages. It provides full transparency through detailed calculation metadata and source citations.

## Components

### 1. Pillar Calculator (`pillar_calculator.py`)

Calculates individual pillar scores (E, S, G) from extracted indicators.

**Key Functions:**
- `calculate_pillar_scores()`: Calculate E, S, G pillar scores using weighted averages
- `get_pillar_breakdown()`: Get detailed breakdown of pillar calculations for transparency
- `_normalize_indicator_value()`: Normalize indicator values to 0-100 scale

**Features:**
- Handles missing indicators gracefully
- Supports multiple indicator types (percentage, intensity, count, days)
- Provides detailed breakdown with indicator contributions

### 2. ESG Calculator (`esg_calculator.py`)

Calculates overall ESG score by combining pillar scores with configurable weights.

**Key Functions:**
- `calculate_esg_score()`: Calculate overall ESG score with configurable pillar weights
- `get_esg_score_with_citations()`: Calculate ESG score with full source citations
- `DEFAULT_PILLAR_WEIGHTS`: Default weights (E=0.33, S=0.33, G=0.34)

**Features:**
- Configurable pillar weights (default: E=0.33, S=0.33, G=0.34)
- Automatic weight adjustment for missing pillars
- Comprehensive calculation metadata
- Source citation integration for transparency
- Calculation methodology description

## Usage

### Basic ESG Score Calculation

```python
from src.scoring import calculate_esg_score
from src.models.brsr_models import BRSRIndicatorDefinition

# Load indicator definitions
indicator_definitions = load_brsr_indicators()

# Extracted indicator values
extracted_values = {
    "GHG_SCOPE1_TOTAL": 1250.0,
    "ENERGY_RENEWABLE_PERCENT": 65.0,
    "EMPLOYEE_WELLBEING_SPEND_PERCENT": 3.5,
    "GENDER_WAGE_PERCENT": 42.0,
    "CUSTOMER_DATA_BREACH_PERCENT": 0.5,
}

# Calculate ESG score
score, metadata = calculate_esg_score(indicator_definitions, extracted_values)

print(f"ESG Score: {score:.2f}/100")
print(f"Environmental: {metadata['pillar_scores']['environmental']:.2f}")
print(f"Social: {metadata['pillar_scores']['social']:.2f}")
print(f"Governance: {metadata['pillar_scores']['governance']:.2f}")
```

### Custom Pillar Weights

```python
# Custom weights favoring environmental performance
custom_weights = {
    "E": 0.5,  # 50% environmental
    "S": 0.3,  # 30% social
    "G": 0.2,  # 20% governance
}

score, metadata = calculate_esg_score(
    indicator_definitions,
    extracted_values,
    pillar_weights=custom_weights
)
```

### ESG Score with Citations

```python
from src.scoring import get_esg_score_with_citations

# Extracted indicators with citation information
extracted_indicators = [
    {
        "indicator_code": "ENERGY_RENEWABLE_PERCENT",
        "numeric_value": 65.0,
        "object_key": "RELIANCE/2024_BRSR.pdf",
        "source_pages": [45, 46],
        "source_chunk_ids": [123, 124],
        "confidence_score": 0.95,
    },
    # ... more indicators
]

score, metadata = get_esg_score_with_citations(
    indicator_definitions,
    extracted_indicators
)

# Access citations
for pillar_key, pillar_data in metadata['pillar_breakdown'].items():
    for indicator in pillar_data['indicators']:
        if 'citations' in indicator:
            print(f"{indicator['name']}: {indicator['citations']['source_pages']}")
```

## Calculation Methodology

### Pillar Score Calculation

1. **Group indicators by pillar** (E, S, G based on BRSR attributes)
2. **Normalize indicator values** to 0-100 scale:
   - Percentage indicators: Use value directly (capped at 100)
   - Intensity indicators: Use inverse scaling (lower is better)
   - Count indicators: Use inverse scaling (lower is better)
   - Days indicators: Use inverse scaling (lower is better)
3. **Calculate weighted average**: `Sum(normalized_value * weight) / Sum(weights)`
4. **Handle missing indicators**: Use only available indicators, adjust weights accordingly

### Overall ESG Score Calculation

1. **Calculate individual pillar scores** (E, S, G)
2. **Apply pillar weights**: Default E=0.33, S=0.33, G=0.34
3. **Adjust weights for missing pillars**: Proportionally redistribute weights
4. **Calculate weighted average**: `(E_score * E_weight) + (S_score * S_weight) + (G_score * G_weight)`

### Example Calculation

Given:
- Environmental score: 60.0
- Social score: 70.0
- Governance score: 80.0
- Weights: E=0.33, S=0.33, G=0.34

ESG Score = (60.0 × 0.33) + (70.0 × 0.33) + (80.0 × 0.34) = 70.1

## Metadata Structure

The calculation metadata includes:

```python
{
    "pillar_scores": {
        "environmental": 60.0,
        "social": 70.0,
        "governance": 80.0
    },
    "pillar_weights": {
        "environmental": 0.33,
        "social": 0.33,
        "governance": 0.34
    },
    "original_weights": {
        "environmental": 0.33,
        "social": 0.33,
        "governance": 0.34
    },
    "pillar_breakdown": {
        "E": {
            "score": 60.0,
            "indicators": [
                {
                    "code": "ENERGY_RENEWABLE_PERCENT",
                    "name": "Energy from renewable sources",
                    "value": 65.0,
                    "unit": "%",
                    "normalized": 65.0,
                    "weight": 1.0,
                    "contribution": 65.0,
                    "citations": {  # Only in get_esg_score_with_citations()
                        "object_key": "RELIANCE/2024_BRSR.pdf",
                        "source_pages": [45, 46],
                        "source_chunk_ids": [123, 124],
                        "confidence_score": 0.95
                    }
                }
            ],
            "total_weight": 2.8,
            "weighted_sum": 168.0
        },
        "S": {...},
        "G": {...}
    },
    "calculation_method": "Overall ESG score calculated as weighted average...",
    "calculated_at": "2024-10-27T12:34:56.789Z",
    "total_indicators_extracted": 8
}
```

## Testing

Run the test suite:

```bash
# Run all scoring tests
uv run pytest test_pillar_calculator.py test_esg_calculator.py -v

# Run only ESG calculator tests
uv run pytest test_esg_calculator.py -v

# Run example
uv run python example_esg_scoring.py
```

## Requirements Coverage

- **15.1**: Calculate pillar scores using weighted averages ✓
- **15.2**: Map BRSR attributes to E, S, G pillars ✓
- **15.3**: Calculate overall ESG score with configurable weights ✓
- **15.4**: Store calculation methodology in metadata ✓
- **15.5**: Include source citations for transparency ✓

## Future Enhancements

1. **Industry-specific normalization**: Use industry benchmarks for better normalization
2. **Time-series analysis**: Track score trends over multiple years
3. **Peer comparison**: Compare scores against industry peers
4. **Custom scoring models**: Support alternative ESG scoring methodologies
5. **Machine learning**: Use ML to optimize indicator weights based on outcomes
