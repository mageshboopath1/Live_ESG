# PDFViewer Component

## Overview

The `PDFViewer` component is a Vue 3 component that provides a full-featured PDF viewing experience with navigation, zoom controls, and text highlighting capabilities. It uses PDF.js library to render PDF documents in the browser.

## Features

- **PDF Rendering**: Renders PDF documents from URLs (including presigned MinIO URLs)
- **Page Navigation**: Navigate between pages with previous/next buttons or direct page input
- **Zoom Controls**: Zoom in/out with buttons or fit to width
- **Text Highlighting**: Automatically highlight specific text chunks on the page
- **Responsive Design**: Adapts to different screen sizes
- **Loading & Error States**: Provides user feedback during loading and error scenarios
- **Keyboard Support**: Navigate with arrow keys and enter

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `pdfUrl` | `string` | Required | URL to the PDF document (can be presigned MinIO URL) |
| `initialPage` | `number` | `1` | Page number to display initially |
| `highlightText` | `string` | `undefined` | Text to highlight on the current page |
| `closeable` | `boolean` | `false` | Show close button in header |

## Events

| Event | Payload | Description |
|-------|---------|-------------|
| `close` | - | Emitted when close button is clicked |
| `pageChange` | `page: number` | Emitted when the current page changes |

## Usage

### Basic Usage

```vue
<template>
  <PDFViewer
    :pdf-url="pdfUrl"
    :initial-page="1"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PDFViewer from '@/components/PDFViewer.vue'

const pdfUrl = ref('/api/documents/RELIANCE/2024_BRSR.pdf')
</script>
```

### With Text Highlighting

```vue
<template>
  <PDFViewer
    :pdf-url="citation.url"
    :initial-page="citation.pages[0]"
    :highlight-text="citation.chunkText"
    closeable
    @close="handleClose"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PDFViewer from '@/components/PDFViewer.vue'
import type { Citation } from '@/types'

const citation = ref<Citation>({
  pdfName: 'RELIANCE/2024_BRSR.pdf',
  pages: [45],
  chunkText: 'Our total Scope 1 emissions for FY 2024 were 1,250 MT CO2e',
  url: '/api/documents/RELIANCE/2024_BRSR.pdf'
})

const handleClose = () => {
  // Handle close action
}
</script>
```

### In a Modal Dialog

```vue
<template>
  <div v-if="showViewer" class="modal-overlay">
    <div class="modal-container">
      <PDFViewer
        :pdf-url="pdfUrl"
        :initial-page="currentPage"
        :highlight-text="highlightText"
        closeable
        @close="showViewer = false"
        @page-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PDFViewer from '@/components/PDFViewer.vue'

const showViewer = ref(false)
const pdfUrl = ref('')
const currentPage = ref(1)
const highlightText = ref('')

const handlePageChange = (page: number) => {
  console.log('Current page:', page)
}
</script>

<style scoped>
.modal-overlay {
  @apply fixed inset-0 bg-black bg-opacity-50 z-50;
  @apply flex items-center justify-center p-4;
}

.modal-container {
  @apply w-full max-w-6xl h-[90vh] bg-white rounded-lg overflow-hidden;
}
</style>
```

## Integration with CitationViewer

The PDFViewer is designed to work seamlessly with the CitationViewer component:

```vue
<template>
  <div>
    <!-- Citation Viewer -->
    <CitationViewer
      :citations="citations"
      @view-pdf="handleViewPdf"
    />
    
    <!-- PDF Viewer Modal -->
    <div v-if="showPdfViewer" class="modal-overlay">
      <div class="modal-container">
        <PDFViewer
          :pdf-url="selectedCitation.url"
          :initial-page="selectedCitation.pages[0]"
          :highlight-text="selectedCitation.chunkText"
          closeable
          @close="showPdfViewer = false"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import CitationViewer from '@/components/CitationViewer.vue'
import PDFViewer from '@/components/PDFViewer.vue'
import type { Citation } from '@/types'

const citations = ref<Citation[]>([])
const showPdfViewer = ref(false)
const selectedCitation = ref<Citation | null>(null)

const handleViewPdf = (citation: Citation) => {
  selectedCitation.value = citation
  showPdfViewer.value = true
}
</script>
```

## Features in Detail

### Navigation Controls

- **Previous/Next Buttons**: Navigate sequentially through pages
- **Page Input**: Jump directly to a specific page number
- **Keyboard Support**: Use arrow keys for navigation (when input is focused)

### Zoom Controls

- **Zoom In/Out**: Increase or decrease the scale by 25% increments
- **Fit to Width**: Automatically scale the PDF to fit the container width
- **Scale Range**: 50% to 300% zoom levels

### Text Highlighting

The component can automatically highlight text on the current page:

1. Searches for exact text matches in the page content
2. Falls back to partial matches by combining adjacent text items
3. Displays a yellow highlight box with animation
4. Automatically re-highlights when changing pages (if highlightText is set)

### Performance Considerations

- **PDF.js Worker**: Uses CDN-hosted worker for better performance
- **Canvas Rendering**: Renders pages at base scale (1.0) and uses CSS transform for zoom
- **Lazy Loading**: Only renders the current page, not all pages at once
- **Memory Management**: Properly destroys PDF document on component unmount

## Styling

The component uses Tailwind CSS utility classes and can be customized by:

1. Modifying the scoped styles in the component
2. Overriding styles from parent components
3. Using Tailwind configuration for theme customization

## Browser Compatibility

- Modern browsers with Canvas API support
- PDF.js requires ES6+ support
- Tested on Chrome, Firefox, Safari, and Edge

## Dependencies

- `pdfjs-dist`: PDF.js library for rendering PDFs
- Vue 3 with Composition API
- Tailwind CSS for styling

## Troubleshooting

### PDF Not Loading

- Verify the PDF URL is accessible
- Check CORS settings if loading from external sources
- Ensure the PDF file is not corrupted

### Text Highlighting Not Working

- Text highlighting works best with text-based PDFs
- Scanned PDFs (images) may not have extractable text
- Complex layouts may affect highlight accuracy

### Performance Issues

- Large PDFs may take time to load
- Consider implementing page caching for frequently accessed documents
- Use lower zoom levels for better performance

## Future Enhancements

- [ ] Page thumbnails sidebar
- [ ] Text selection and copy
- [ ] Annotation support
- [ ] Print functionality
- [ ] Download button
- [ ] Full-screen mode
- [ ] Touch gestures for mobile
- [ ] Search across all pages
