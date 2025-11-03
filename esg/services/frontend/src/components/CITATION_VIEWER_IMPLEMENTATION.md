# Citation Viewer Component Implementation Summary

## Task 36: Build Citation Viewer Component ✅

### Implementation Date
Completed: 2024

### Files Created

1. **CitationViewer.vue** - Main component
   - Location: `services/frontend/src/components/CitationViewer.vue`
   - Lines of code: ~350
   - Features: Full citation display with all required functionality

2. **CitationViewer.example.vue** - Usage examples
   - Location: `services/frontend/src/components/CitationViewer.example.vue`
   - Contains 8 different usage examples
   - Demonstrates all component features and states

3. **CitationViewer.README.md** - Component documentation
   - Location: `services/frontend/src/components/CitationViewer.README.md`
   - Comprehensive documentation with API reference
   - Integration examples and usage patterns

4. **Updated README.md** - Main components documentation
   - Added CitationViewer section to main components README
   - Includes quick reference and integration examples

### Features Implemented

#### Core Features
- ✅ Display multiple citations for a single indicator
- ✅ Show PDF name with file icon
- ✅ Display page numbers (formatted intelligently)
- ✅ Show extracted chunk text in scrollable container
- ✅ Display confidence score with color-coded badges
- ✅ Show extraction timestamp with relative time formatting
- ✅ "View in PDF" button for each citation
- ✅ Support for closeable mode (modal/drawer usage)

#### State Management
- ✅ Loading state with spinner animation
- ✅ Error state with retry functionality
- ✅ Empty state when no citations available
- ✅ Proper error handling and user feedback

#### UI/UX Features
- ✅ Responsive design with Tailwind CSS
- ✅ Hover effects and smooth transitions
- ✅ Color-coded confidence badges (high/medium/low)
- ✅ Smart page number formatting (ranges, lists, ellipsis)
- ✅ Scrollable chunk text with custom scrollbar
- ✅ Accessible with ARIA labels
- ✅ Keyboard navigation support

### Requirements Satisfied

| Requirement | Status | Description |
|-------------|--------|-------------|
| 19.1 | ✅ | Display citation badge with PDF name and page number |
| 19.4 | ✅ | Display extraction confidence score and timestamp |
| 19.5 | ✅ | Support multiple citations for single indicator |

### Component API

#### Props
```typescript
interface Props {
  citations: Citation[]           // Required: Array of citations
  loading?: boolean               // Optional: Show loading state
  error?: string | null           // Optional: Error message
  confidence?: number             // Optional: Confidence score (0-1)
  extractedAt?: string            // Optional: ISO timestamp
  showConfidence?: boolean        // Optional: Show confidence badge
  showTimestamp?: boolean         // Optional: Show timestamp
  closeable?: boolean             // Optional: Show close button
}
```

#### Events
```typescript
emit('viewPdf', citation: Citation)  // When "View in PDF" clicked
emit('close')                        // When close button clicked
emit('retry')                        // When retry button clicked
```

### Integration Points

1. **IndicatorCard Component**
   - CitationViewer opens when citation button is clicked
   - Receives indicator confidence and extraction timestamp
   - Displays all citations for the indicator

2. **API Service**
   - Uses `apiClient.getCitations(indicatorId)` to fetch citations
   - Uses `apiClient.getIndicator(indicatorId)` for full indicator data
   - Integrates with document URL endpoints

3. **PDF Viewer Component** (Task 37)
   - "View in PDF" button will trigger PDF viewer
   - Passes PDF path and page number to viewer
   - Enables source verification workflow

### Code Quality

- ✅ TypeScript with full type safety
- ✅ Vue 3 Composition API with `<script setup>`
- ✅ No TypeScript diagnostics or errors
- ✅ Follows project coding standards
- ✅ Comprehensive inline documentation
- ✅ Accessible and semantic HTML

### Testing Considerations

The component includes an example file with 8 test scenarios:
1. Multiple citations display
2. Single citation display
3. Loading state
4. Error state with retry
5. Empty state
6. Closeable mode
7. Minimal display (no confidence/timestamp)
8. Long text citation with scrolling

### Usage Example

```vue
<template>
  <CitationViewer
    :citations="citations"
    :confidence="0.92"
    :extracted-at="extractedAt"
    @view-pdf="openPdfViewer"
  />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import CitationViewer from '@/components/CitationViewer.vue'
import apiClient from '@/services/api'

const citations = ref([])
const extractedAt = ref('')

onMounted(async () => {
  const data = await apiClient.getIndicator(indicatorId)
  citations.value = data.citations
  extractedAt.value = data.indicator.extracted_at
})

const openPdfViewer = (citation) => {
  // Open PDF viewer at specific page
  router.push({
    name: 'pdf-viewer',
    params: { objectKey: citation.pdfName },
    query: { page: citation.pages[0] }
  })
}
</script>
```

### Design Decisions

1. **Multiple Citations Support**: Designed to handle 1-N citations per indicator, as some indicators may be derived from multiple document sections.

2. **Scrollable Chunk Text**: Limited height (8rem) with scrolling to prevent overly long citations from dominating the UI.

3. **Smart Page Formatting**: Automatically formats page numbers as ranges (e.g., "45-48") for consecutive pages, or lists for non-consecutive pages.

4. **Relative Timestamps**: Shows "2 hours ago" for recent extractions, full dates for older ones, improving readability.

5. **Color-Coded Confidence**: Visual indicators (green/yellow/orange) help users quickly assess data quality.

6. **Closeable Option**: Supports both embedded and modal usage patterns.

### Next Steps

The component is ready for integration with:
- Task 37: PDF Viewer Component (for "View in PDF" functionality)
- Task 32: Company Dashboard View (to display citations for indicators)
- Task 35: Score Breakdown Component (to show citations in score derivation)

### Notes

- The component expects the Citation type to be defined in `@/types/indicator.ts`
- API integration requires the endpoints defined in `@/services/api.ts`
- PDF viewing functionality will be completed in Task 37
- All TypeScript types are properly defined and validated
- Component follows Vue 3 best practices and Composition API patterns
