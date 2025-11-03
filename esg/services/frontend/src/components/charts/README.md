# Chart Components

This directory contains reusable chart components built with Chart.js and vue-chartjs for visualizing ESG data.

## Components

### Base Chart Components

#### BarChart.vue
A reusable bar chart component with support for horizontal and stacked layouts.

**Props:**
- `labels: string[]` - X-axis labels
- `datasets: Array` - Chart datasets with label, data, colors
- `title?: string` - Chart title
- `yAxisLabel?: string` - Y-axis label
- `xAxisLabel?: string` - X-axis label
- `horizontal?: boolean` - Horizontal bar chart
- `stacked?: boolean` - Stacked bars
- `tooltipCallback?: Function` - Custom tooltip formatter

#### LineChart.vue
A reusable line chart component with support for multiple datasets and filled areas.

**Props:**
- `labels: string[]` - X-axis labels
- `datasets: Array` - Chart datasets with label, data, colors, fill, tension
- `title?: string` - Chart title
- `yAxisLabel?: string` - Y-axis label
- `xAxisLabel?: string` - X-axis label
- `yMin?: number` - Y-axis minimum
- `yMax?: number` - Y-axis maximum
- `tooltipCallback?: Function` - Custom tooltip formatter

#### RadarChart.vue
A reusable radar chart component for comparing multiple dimensions.

**Props:**
- `labels: string[]` - Dimension labels
- `datasets: Array` - Chart datasets with label, data, colors
- `title?: string` - Chart title
- `max?: number` - Maximum value (default: 100)
- `tooltipCallback?: Function` - Custom tooltip formatter

### Specialized Chart Components

#### IndicatorTrendChart.vue
Displays trend of a single indicator across multiple years with source citations.

**Props:**
- `indicatorData: ExtractedIndicator[]` - Historical indicator data
- `indicatorName: string` - Indicator name
- `unit?: string` - Measurement unit
- `showCitations?: boolean` - Show citation panel (default: true)
- `loading?: boolean` - Loading state
- `error?: string` - Error message

**Events:**
- `citation-click` - Emitted when citation is clicked

#### PillarComparisonChart.vue
Radar chart comparing ESG pillar scores across companies with breakdown panel.

**Props:**
- `scores: ESGScore[]` - ESG scores to compare
- `companyNames?: string[]` - Company names for labels
- `showBreakdown?: boolean` - Show breakdown panel (default: true)
- `loading?: boolean` - Loading state
- `error?: string` - Error message

**Events:**
- `pillar-click` - Emitted when pillar is clicked in breakdown

#### MultiIndicatorChart.vue
Compares multiple indicators with switchable chart types and interactive legend.

**Props:**
- `indicators: IndicatorWithMeta[]` - Indicators to display
- `definitions?: BRSRIndicatorDefinition[]` - Indicator definitions
- `showLegend?: boolean` - Show legend panel (default: true)
- `loading?: boolean` - Loading state
- `error?: string` - Error message

**Events:**
- `indicator-click` - Emitted when indicator is clicked in legend

## Usage Examples

### Basic Bar Chart

```vue
<template>
  <BarChart
    :labels="['Q1', 'Q2', 'Q3', 'Q4']"
    :datasets="[
      {
        label: 'Revenue',
        data: [100, 150, 200, 180],
        backgroundColor: '#10B981'
      }
    ]"
    title="Quarterly Revenue"
    y-axis-label="Revenue ($M)"
  />
</template>

<script setup lang="ts">
import { BarChart } from '@/components/charts'
</script>
```

### Indicator Trend Chart

```vue
<template>
  <IndicatorTrendChart
    :indicator-data="historicalData"
    indicator-name="Total Scope 1 Emissions"
    unit="MT CO2e"
    @citation-click="handleCitationClick"
  />
</template>

<script setup lang="ts">
import { IndicatorTrendChart } from '@/components/charts'
import type { ExtractedIndicator, Citation } from '@/types'

const historicalData: ExtractedIndicator[] = [
  // ... indicator data for multiple years
]

const handleCitationClick = (citation: Citation) => {
  // Open PDF viewer or citation modal
}
</script>
```

### Pillar Comparison Chart

```vue
<template>
  <PillarComparisonChart
    :scores="companyScores"
    :company-names="['Company A', 'Company B']"
    @pillar-click="handlePillarClick"
  />
</template>

<script setup lang="ts">
import { PillarComparisonChart } from '@/components/charts'
import type { ESGScore } from '@/types'

const companyScores: ESGScore[] = [
  // ... ESG scores for companies
]

const handlePillarClick = (pillar: 'E' | 'S' | 'G') => {
  // Show detailed breakdown for pillar
}
</script>
```

### Multi-Indicator Chart

```vue
<template>
  <MultiIndicatorChart
    :indicators="indicators"
    @indicator-click="handleIndicatorClick"
  />
</template>

<script setup lang="ts">
import { MultiIndicatorChart } from '@/components/charts'

const indicators = [
  // ... indicators with metadata
]

const handleIndicatorClick = (indicator) => {
  // Show indicator details or citations
}
</script>
```

## Features

### Interactive Tooltips
All charts support custom tooltip callbacks that can display:
- Indicator values with units
- Confidence scores
- Source citations
- Contextual information

### Citation Integration
Specialized charts (IndicatorTrendChart, PillarComparisonChart, MultiIndicatorChart) integrate with the citation system:
- Display source document references
- Clickable citations that emit events
- Citation panels showing PDF names and page numbers

### Responsive Design
All charts are responsive and adapt to container size with proper aspect ratios.

### Accessibility
Charts use semantic colors and include proper labels for screen readers.

## Styling

Charts use Tailwind CSS for consistent styling with the rest of the application. Custom colors follow the ESG pillar color scheme:
- Environmental (E): Green (#10B981)
- Social (S): Blue (#3B82F6)
- Governance (G): Purple (#8B5CF6)

## Dependencies

- `chart.js` - Chart rendering library
- `vue-chartjs` - Vue 3 wrapper for Chart.js
- All required Chart.js components are registered in each component
