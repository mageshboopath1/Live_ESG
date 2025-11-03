# CitationViewer Component

A Vue 3 component for displaying source citations with PDF information, page numbers, chunk text, confidence scores, and extraction timestamps. Supports multiple citations for a single indicator with interactive "View in PDF" functionality.

## Features

- ✅ Display multiple citations for a single indicator
- ✅ Show PDF name and page numbers
- ✅ Display extracted chunk text with scrollable content
- ✅ Show confidence score with color-coded badges
- ✅ Display extraction timestamp with relative time formatting
- ✅ "View in PDF" button for each citation
- ✅ Loading, error, and empty states
- ✅ Closeable option for modal/drawer usage
- ✅ Responsive design with Tailwind CSS
- ✅ Accessible with ARIA labels and keyboard navigation

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `citations` | `Citation[]` | **required** | Array of citation objects to display |
| `loading` | `boolean` | `false` | Show loading spinner |
| `error` | `string \| null` | `null` | Error message to display |
| `confidence` | `number` | `undefined` | Confidence score (0.0-1.0) for the extraction |
| `extractedAt` | `string` | `undefined` | ISO timestamp of when the indicator was extracted |
| `showConfidence` | `boolean` | `true` | Whether to display the confidence badge |
| `showTimestamp` | `boolean` | `true` | Whether to display the extraction timestamp |
| `closeable` | `boolean` | `false` | Whether to show a close button in the header |

## Events

| Event | Payload | Description |
|-------|---------|-------------|
| `viewPdf` | `Citation` | Emitted when "View in PDF" button is clicked |
| `close` | - | Emitted when close button is clicked (if `closeable` is true) |
| `retry` | - | Emitted when retry button is clicked in error state |

## Citation Type

```typescript
interface Citation {
  pdfName: string      // Full path or name of the PDF file
  pages: number[]      // Array of page numbers where the data was found
  chunkText: string    // The extracted text chunk from the PDF
  url: string          // URL to access the PDF document
}
```

## Usage Examples

### Basic Usage

```vue
<template>
  <CitationViewer
    :citations="citations"
    :confidence="0.92"
    :extracted-at="extractedAt"
    @view-pdf="handleViewPdf"
  />
</template>

<script setup lang="ts">
import CitationViewer from '@/components/CitationViewer.vue'
import type { Citation } from '@/types'

const citations: Citation[] = [
  {
    pdfName: 'RELIANCE/2024_BRSR.pdf',
    pages: [45, 46],
    chunkText: 'Our total Scope 1 emissions for FY 2024 were 1,250 MT CO2e...',
    url: '/api/documents/RELIANCE/2024_BRSR.pdf/page/45'
  }
]

const extractedAt = '2024-01-15T10:30:00Z'

const handleViewPdf = (citation: Citation) => {
  // Open PDF viewer with the citation
  console.log('Opening PDF:', citation)
}
</script>
```

### With Loading State

```vue
<template>
  <CitationViewer
    :citations="citations"
    :loading="isLoading"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import CitationViewer from '@/components/CitationViewer.vue'

const citations = ref([])
const isLoading = ref(true)

// Fetch citations...
</script>
```

### With Error Handling

```vue
<template>
  <CitationViewer
    :citations="citations"
    :error="errorMessage"
    @retry="fetchCitations"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import CitationViewer from '@/components/CitationViewer.vue'

const citations = ref([])
const errorMessage = ref<string | null>(null)

const fetchCitations = async () => {
  try {
    // Fetch citations...
  } catch (error) {
    errorMessage.value = 'Failed to load citations'
  }
}
</script>
```

### In a Modal/Drawer

```vue
<template>
  <div v-if="showViewer" class="modal">
    <CitationViewer
      :citations="citations"
      :confidence="0.85"
      :extracted-at="extractedAt"
      closeable
      @close="showViewer = false"
      @view-pdf="handleViewPdf"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import CitationViewer from '@/components/CitationViewer.vue'

const showViewer = ref(false)
// ... rest of the code
</script>
```

### Minimal Display (No Confidence/Timestamp)

```vue
<template>
  <CitationViewer
    :citations="citations"
    :show-confidence="false"
    :show-timestamp="false"
  />
</template>
```

## Integration with IndicatorCard

The CitationViewer is designed to work seamlessly with the IndicatorCard component:

```vue
<template>
  <div>
    <IndicatorCard
      :indicator="indicator"
      :pdf-name="pdfName"
      :source-pages="sourcePages"
      @citation-click="showCitations = true"
    />

    <div v-if="showCitations" class="modal">
      <CitationViewer
        :citations="citations"
        :confidence="indicator.confidence"
        :extracted-at="extractedAt"
        closeable
        @close="showCitations = false"
        @view-pdf="openPdfViewer"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import IndicatorCard from '@/components/IndicatorCard.vue'
import CitationViewer from '@/components/CitationViewer.vue'
import apiClient from '@/services/api'

const showCitations = ref(false)
const citations = ref([])

const openPdfViewer = (citation: Citation) => {
  // Open PDF viewer component with the citation
  router.push({
    name: 'pdf-viewer',
    params: { objectKey: citation.pdfName },
    query: { page: citation.pages[0] }
  })
}
</script>
```

## Fetching Citations from API

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import CitationViewer from '@/components/CitationViewer.vue'
import apiClient from '@/services/api'
import type { Citation } from '@/types'

const citations = ref<Citation[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const confidence = ref<number>()
const extractedAt = ref<string>()

const fetchCitations = async (indicatorId: number) => {
  loading.value = true
  error.value = null
  
  try {
    const response = await apiClient.getIndicator(indicatorId)
    citations.value = response.citations
    confidence.value = response.indicator.confidence_score
    extractedAt.value = response.indicator.extracted_at
  } catch (err) {
    error.value = 'Failed to load citations. Please try again.'
    console.error('Error fetching citations:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchCitations(123) // Replace with actual indicator ID
})
</script>
```

## Styling

The component uses Tailwind CSS utility classes for styling. Key design features:

- **Color-coded confidence badges**: Green (high), yellow (medium), orange (low)
- **Scrollable chunk text**: Max height with custom scrollbar styling
- **Hover effects**: Smooth transitions on interactive elements
- **Responsive layout**: Adapts to different screen sizes
- **Accessible focus states**: Clear focus indicators for keyboard navigation

## Accessibility

- Semantic HTML structure
- ARIA labels for buttons and icons
- Keyboard navigation support
- Focus management for interactive elements
- Screen reader friendly content

## Requirements Satisfied

This component satisfies the following requirements from the ESG Intelligence Platform specification:

- **19.1**: Display citation badge with PDF name and page number
- **19.4**: Display extraction confidence score and timestamp
- **19.5**: Support multiple citations for single indicator

## Related Components

- **IndicatorCard**: Displays indicator data with citation button
- **PDFViewer**: Opens and displays PDF documents (to be implemented in task 37)
- **ScoreBreakdown**: Shows score derivation with citations

## Notes

- The component expects citations to be pre-fetched or passed as props
- PDF viewing functionality requires integration with a PDF viewer component
- Timestamps are formatted as relative time (e.g., "2 hours ago") for recent extractions
- Long chunk text is scrollable with a maximum height of 8rem (128px)
