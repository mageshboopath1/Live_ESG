# ScoreBreakdown Component

## Overview

The `ScoreBreakdown` component provides a transparent, hierarchical visualization of ESG score calculation. It displays how the overall ESG score is derived from pillar scores (Environmental, Social, Governance), and how each pillar score is calculated from individual BRSR Core indicators.

## Features

- **Hierarchical Breakdown**: Shows Overall → Pillars → Indicators structure
- **Weight Transparency**: Displays weights applied at each level
- **Source Citations**: Shows PDF sources and page numbers for each indicator
- **Interactive Indicators**: Clickable indicators to view detailed source information
- **Calculation Methodology**: Expandable section explaining the scoring formula
- **Loading/Error States**: Handles loading and error scenarios gracefully
- **Responsive Design**: Works on desktop and tablet devices

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `breakdown` | `ScoreBreakdown \| null` | Yes | - | The score breakdown data structure |
| `overallScore` | `number` | No | `0` | The overall ESG score (0-100) |
| `loading` | `boolean` | No | `false` | Whether data is loading |
| `error` | `string \| null` | No | `null` | Error message to display |

## Events

| Event | Payload | Description |
|-------|---------|-------------|
| `indicatorClick` | `IndicatorContribution` | Emitted when user clicks on an indicator |

## Types

```typescript
interface ScoreBreakdown {
  pillars: PillarBreakdown[]
}

interface PillarBreakdown {
  name: string                      // 'Environmental', 'Social', or 'Governance'
  score: number                     // Pillar score (0-100)
  weight: number                    // Weight in overall calculation (0-1)
  indicators: IndicatorContribution[]
}

interface IndicatorContribution {
  code: string                      // Indicator code (e.g., 'GHG_SCOPE1')
  value: number                     // Indicator value
  weight: number                    // Weight in pillar calculation (0-1)
  citations: Citation[]             // Source citations
}

interface Citation {
  pdfName: string                   // PDF file path
  pages: number[]                   // Page numbers
  chunkText: string                 // Extracted text
  url: string                       // URL to view PDF page
}
```

## Usage

### Basic Usage

```vue
<template>
  <ScoreBreakdown
    :breakdown="scoreBreakdown"
    :overall-score="75.2"
    @indicator-click="handleIndicatorClick"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ScoreBreakdown from '@/components/ScoreBreakdown.vue'
import type { ScoreBreakdown as ScoreBreakdownType, IndicatorContribution } from '@/types'

const scoreBreakdown = ref<ScoreBreakdownType | null>(null)

const handleIndicatorClick = (indicator: IndicatorContribution) => {
  console.log('Indicator clicked:', indicator)
  // Navigate to citation viewer or show modal
}
</script>
```

### With Store Integration

```vue
<template>
  <ScoreBreakdown
    :breakdown="scoreStore.scoreBreakdown"
    :overall-score="scoreStore.selectedScore?.overall_score || 0"
    :loading="scoreStore.loading"
    :error="scoreStore.error"
    @indicator-click="navigateToIndicator"
  />
</template>

<script setup lang="ts">
import { useScoreStore } from '@/stores/scoreStore'
import { useRouter } from 'vue-router'
import ScoreBreakdown from '@/components/ScoreBreakdown.vue'
import type { IndicatorContribution } from '@/types'

const scoreStore = useScoreStore()
const router = useRouter()

const navigateToIndicator = (indicator: IndicatorContribution) => {
  // Navigate to indicator detail page or open citation viewer
  router.push({
    name: 'indicator-detail',
    params: { code: indicator.code }
  })
}
</script>
```

### Loading State

```vue
<template>
  <ScoreBreakdown
    :breakdown="null"
    :loading="true"
  />
</template>
```

### Error State

```vue
<template>
  <ScoreBreakdown
    :breakdown="null"
    :error="'Failed to load score breakdown'"
  />
</template>
```

## Component Structure

### Overall Score Section
- Displays the final ESG score with a prominent badge
- Explains the calculation methodology

### Pillar Breakdown Cards
Each pillar card shows:
- Pillar icon and name (Environmental, Social, Governance)
- Pillar score (0-100)
- Weight in overall calculation
- List of contributing indicators

### Indicator Items
Each indicator item displays:
- Indicator code (e.g., `GHG_SCOPE1`)
- Indicator value (formatted with commas for large numbers)
- Weight in pillar calculation
- Citation information (PDF name and page numbers)
- Click arrow indicating interactivity

### Calculation Methodology
Expandable section that explains:
- How indicators are weighted within pillars
- How pillar scores are calculated
- How the overall ESG score is derived
- The mathematical formula used

## Styling

The component uses Tailwind CSS with custom color schemes for each pillar:
- **Environmental**: Green (`green-500`, `green-100`, etc.)
- **Social**: Blue (`blue-500`, `blue-100`, etc.)
- **Governance**: Purple (`purple-500`, `purple-100`, etc.)

### Responsive Behavior
- Desktop (lg+): 3-column grid for pillars
- Tablet/Mobile: Single column layout
- All interactive elements have hover and focus states

## Accessibility

- All interactive elements are keyboard accessible
- Proper ARIA labels for buttons
- Focus states for keyboard navigation
- Semantic HTML structure

## Integration with API

The component expects data from the `/api/scores/breakdown/{company_id}/{year}` endpoint:

```typescript
// API Response
{
  "pillars": [
    {
      "name": "Environmental",
      "score": 75.2,
      "weight": 0.33,
      "indicators": [
        {
          "code": "GHG_SCOPE1",
          "value": 1250.5,
          "weight": 0.25,
          "citations": [
            {
              "pdfName": "RELIANCE/2024_BRSR.pdf",
              "pages": [45, 46],
              "chunkText": "Our total Scope 1 emissions...",
              "url": "/api/documents/RELIANCE/2024_BRSR.pdf/page/45"
            }
          ]
        }
      ]
    }
  ]
}
```

## Requirements Satisfied

This component satisfies the following requirements from the spec:

- **18.2**: Display hierarchical breakdown showing how overall score is derived from pillar scores
- **18.3**: Show weights applied to each indicator and pillar in the calculation
- **18.4**: Display indicator contributions with values and source citations
- **18.5**: Make each indicator clickable to view source document

## Example

See `ScoreBreakdown.example.vue` for a complete working example with mock data.

## Related Components

- `ScoreVisualization.vue`: Displays score gauges and trends
- `IndicatorCard.vue`: Displays individual indicator details
- `CitationViewer.vue`: Shows detailed citation information
- `PDFViewer.vue`: Displays PDF documents with highlighting
