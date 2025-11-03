# ScoreVisualization Component

A comprehensive Vue 3 component for visualizing ESG (Environmental, Social, Governance) scores with interactive charts and trend analysis.

## Features

- **Overall ESG Score Display**: Gauge chart showing the overall ESG score out of 100
- **Pillar Score Breakdown**: Individual visualizations for Environmental, Social, and Governance scores
- **Progress Bars**: Visual representation of each pillar's performance
- **Trend Indicators**: Shows score changes over time with directional arrows
- **Multi-Year Trend Chart**: Line chart displaying historical score trends across all pillars
- **Responsive Design**: Adapts to different screen sizes (desktop, tablet, mobile)
- **Color-Coded Scoring**: Dynamic colors based on score ranges (green for high, yellow for medium, red for low)

## Installation

The component requires Chart.js and vue-chartjs:

```bash
bun add chart.js vue-chartjs
```

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `score` | `ESGScore \| null` | Yes | - | Current ESG score object with pillar scores |
| `scoreHistory` | `ESGScore[]` | No | `[]` | Array of historical scores for trend analysis |
| `showTrend` | `boolean` | No | `true` | Whether to display the multi-year trend chart |

## ESGScore Type

```typescript
interface ESGScore {
  id: number
  company_id: number
  report_year: number
  environmental_score: number  // 0-100
  social_score: number         // 0-100
  governance_score: number     // 0-100
  overall_score: number        // 0-100
  calculation_metadata: CalculationMetadata
  calculated_at: string
}
```

## Usage Examples

### Basic Usage (Single Score)

```vue
<template>
  <ScoreVisualization :score="currentScore" :show-trend="false" />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ScoreVisualization from '@/components/ScoreVisualization.vue'
import type { ESGScore } from '@/types'

const currentScore = ref<ESGScore>({
  id: 1,
  company_id: 1,
  report_year: 2024,
  environmental_score: 78.5,
  social_score: 82.3,
  governance_score: 75.8,
  overall_score: 78.9,
  calculation_metadata: {
    weights: {
      environmental: 0.33,
      social: 0.33,
      governance: 0.34
    },
    indicators: {}
  },
  calculated_at: '2024-01-15T10:30:00Z'
})
</script>
```

### With Historical Trend Data

```vue
<template>
  <ScoreVisualization 
    :score="currentScore" 
    :score-history="scoreHistory"
    :show-trend="true"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ScoreVisualization from '@/components/ScoreVisualization.vue'
import type { ESGScore } from '@/types'

const currentScore = ref<ESGScore>({
  // ... current year score
})

const scoreHistory = ref<ESGScore[]>([
  // 2021 score
  {
    id: 1,
    company_id: 1,
    report_year: 2021,
    environmental_score: 72.5,
    social_score: 75.3,
    governance_score: 70.8,
    overall_score: 72.9,
    // ...
  },
  // 2022 score
  {
    id: 2,
    company_id: 1,
    report_year: 2022,
    environmental_score: 76.8,
    social_score: 80.1,
    governance_score: 75.2,
    overall_score: 77.4,
    // ...
  },
  // ... more years
])
</script>
```

### With Pinia Store

```vue
<template>
  <div>
    <div v-if="loading">Loading...</div>
    <div v-else-if="error">{{ error }}</div>
    <ScoreVisualization 
      v-else
      :score="selectedScore" 
      :score-history="scoreHistory"
      :show-trend="true"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useScoreStore } from '@/stores/scoreStore'
import ScoreVisualization from '@/components/ScoreVisualization.vue'

const scoreStore = useScoreStore()

const selectedScore = computed(() => scoreStore.selectedScore)
const scoreHistory = computed(() => scoreStore.scoreHistory)
const loading = computed(() => scoreStore.loading)
const error = computed(() => scoreStore.error)

onMounted(async () => {
  const companyId = 1
  await scoreStore.fetchScoreHistory(companyId)
  await scoreStore.fetchCompanyScore(companyId, 2024)
})
</script>
```

## Visual Components

### 1. Overall Score Gauge
- Semi-circular gauge chart showing overall ESG score
- Color-coded based on score range:
  - 80-100: Green (excellent)
  - 60-79: Yellow (good)
  - 40-59: Orange (fair)
  - 0-39: Red (needs improvement)
- Displays trend indicator if historical data is available

### 2. Pillar Score Cards
Three cards displaying individual pillar scores:
- **Environmental (E)**: Green theme with globe icon
- **Social (S)**: Blue theme with people icon
- **Governance (G)**: Purple theme with shield icon

Each card includes:
- Pillar name and icon
- Current score value
- Progress bar visualization
- Trend indicator (if historical data available)

### 3. Multi-Year Trend Chart
Line chart showing score evolution over time:
- Overall ESG score (primary line with fill)
- Environmental score (green line)
- Social score (blue line)
- Governance score (purple line)
- Interactive tooltips on hover
- Legend for easy identification

## Styling

The component uses Tailwind CSS utility classes and is fully responsive:
- Desktop: 3-column grid for pillar cards
- Tablet/Mobile: Single column layout
- Gauge size adjusts based on screen size
- Chart height adapts to viewport

## Color Scheme

| Element | Color | Tailwind Class |
|---------|-------|----------------|
| Environmental | Green | `bg-green-500` |
| Social | Blue | `bg-blue-500` |
| Governance | Purple | `bg-purple-500` |
| Positive Trend | Green | `bg-green-100 text-green-800` |
| Negative Trend | Red | `bg-red-100 text-red-800` |
| Neutral Trend | Gray | `bg-gray-100 text-gray-800` |

## Accessibility

- Semantic HTML structure
- ARIA labels where appropriate
- Color is not the only indicator (icons and text accompany colors)
- Keyboard navigation support for interactive elements
- Screen reader friendly

## Performance Considerations

- Chart.js components are lazy-loaded
- Computed properties for efficient reactivity
- Minimal re-renders with proper Vue 3 composition API usage
- Optimized chart options for smooth animations

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Requires ES6+ support
- Chart.js 4.x compatible

## Related Components

- `ScoreBreakdown.vue`: Detailed score derivation with indicator contributions
- `IndicatorCard.vue`: Individual indicator display with citations
- `ComparisonView.vue`: Multi-company score comparison

## Requirements Fulfilled

This component fulfills the following requirements from the ESG Intelligence Platform specification:

- **Requirement 17.2**: Indicator trend visualization across multiple years
- **Requirement 18.1**: Overall ESG score display with pillar breakdown

## See Also

- [ScoreVisualization.example.vue](./ScoreVisualization.example.vue) - Live examples
- [Score Store Documentation](../stores/scoreStore.ts) - State management
- [API Client Documentation](../services/api.ts) - Data fetching
