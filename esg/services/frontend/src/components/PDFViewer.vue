<template>
  <div class="pdf-viewer">
    <!-- Header -->
    <div class="viewer-header">
      <div class="header-left">
        <h3 class="viewer-title">{{ documentTitle }}</h3>
        <span v-if="currentPage && totalPages" class="page-info">
          Page {{ currentPage }} of {{ totalPages }}
        </span>
      </div>
      <button
        v-if="closeable"
        class="close-button"
        @click="handleClose"
        aria-label="Close PDF viewer"
      >
        <svg class="close-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <!-- Navigation Controls -->
      <div class="nav-controls">
        <button
          class="toolbar-button"
          :disabled="!canGoPrevious"
          @click="previousPage"
          aria-label="Previous page"
        >
          <svg class="button-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
        
        <input
          v-model.number="pageInput"
          type="number"
          class="page-input"
          :min="1"
          :max="totalPages"
          @keyup.enter="goToPage"
          @blur="goToPage"
          aria-label="Page number"
        />
        
        <button
          class="toolbar-button"
          :disabled="!canGoNext"
          @click="nextPage"
          aria-label="Next page"
        >
          <svg class="button-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>

      <!-- Zoom Controls -->
      <div class="zoom-controls">
        <button
          class="toolbar-button"
          :disabled="scale <= minScale"
          @click="zoomOut"
          aria-label="Zoom out"
        >
          <svg class="button-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7"
            />
          </svg>
        </button>
        
        <span class="zoom-level">{{ zoomPercentage }}%</span>
        
        <button
          class="toolbar-button"
          :disabled="scale >= maxScale"
          @click="zoomIn"
          aria-label="Zoom in"
        >
          <svg class="button-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"
            />
          </svg>
        </button>
        
        <button
          class="toolbar-button"
          @click="fitToWidth"
          aria-label="Fit to width"
        >
          <svg class="button-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p class="loading-text">Loading PDF...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <svg class="error-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p class="error-text">{{ error }}</p>
      <button class="retry-button" @click="loadPdf">Retry</button>
    </div>

    <!-- PDF Canvas Container -->
    <div v-else class="canvas-container" ref="containerRef">
      <div class="canvas-wrapper" :style="canvasWrapperStyle">
        <canvas ref="canvasRef" class="pdf-canvas"></canvas>
        <!-- Highlight overlay -->
        <div
          v-if="highlightBox"
          class="highlight-overlay"
          :style="highlightStyle"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`

// Props
interface Props {
  pdfUrl: string
  initialPage?: number
  highlightText?: string
  closeable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  initialPage: 1,
  highlightText: undefined,
  closeable: false
})

// Emits
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'pageChange', page: number): void
}>()

// Refs
const canvasRef = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
const pdfDocument = ref<any>(null)
const currentPage = ref<number>(1)
const totalPages = ref<number>(0)
const scale = ref<number>(1.5)
const pageInput = ref<number>(1)
const loading = ref<boolean>(false)
const error = ref<string | null>(null)
const highlightBox = ref<{ x: number; y: number; width: number; height: number } | null>(null)

// Constants
const minScale = 0.5
const maxScale = 3.0
const scaleStep = 0.25

// Computed
const documentTitle = computed(() => {
  const parts = props.pdfUrl.split('/')
  return parts[parts.length - 1] || 'Document'
})

const canGoPrevious = computed(() => currentPage.value > 1)
const canGoNext = computed(() => currentPage.value < totalPages.value)
const zoomPercentage = computed(() => Math.round(scale.value * 100))

const canvasWrapperStyle = computed(() => ({
  transform: `scale(${scale.value})`,
  transformOrigin: 'top center'
}))

const highlightStyle = computed(() => {
  if (!highlightBox.value) return {}
  return {
    left: `${highlightBox.value.x}px`,
    top: `${highlightBox.value.y}px`,
    width: `${highlightBox.value.width}px`,
    height: `${highlightBox.value.height}px`
  }
})

// Methods
const loadPdf = async () => {
  loading.value = true
  error.value = null
  
  try {
    // Load the PDF document
    const loadingTask = pdfjsLib.getDocument(props.pdfUrl)
    pdfDocument.value = await loadingTask.promise
    totalPages.value = pdfDocument.value.numPages
    
    // Navigate to initial page
    currentPage.value = Math.min(Math.max(props.initialPage, 1), totalPages.value)
    pageInput.value = currentPage.value
    
    await renderPage(currentPage.value)
    
    // Try to highlight text if provided
    if (props.highlightText) {
      await highlightTextOnPage(props.highlightText)
    }
  } catch (err: any) {
    console.error('Error loading PDF:', err)
    error.value = err.message || 'Failed to load PDF document'
  } finally {
    loading.value = false
  }
}

const renderPage = async (pageNumber: number) => {
  if (!pdfDocument.value || !canvasRef.value) return
  
  try {
    const page = await pdfDocument.value.getPage(pageNumber)
    const canvas = canvasRef.value
    const context = canvas.getContext('2d')
    
    if (!context) return
    
    // Get viewport at base scale
    const viewport = page.getViewport({ scale: 1.0 })
    
    // Set canvas dimensions
    canvas.width = viewport.width
    canvas.height = viewport.height
    
    // Render the page
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    }
    
    await page.render(renderContext).promise
    
    // Clear previous highlight
    highlightBox.value = null
  } catch (err: any) {
    console.error('Error rendering page:', err)
    error.value = err.message || 'Failed to render page'
  }
}

const highlightTextOnPage = async (searchText: string) => {
  if (!pdfDocument.value || !canvasRef.value) return
  
  try {
    const page = await pdfDocument.value.getPage(currentPage.value)
    const textContent = await page.getTextContent()
    const viewport = page.getViewport({ scale: 1.0 })
    
    // Search for text in the page
    let foundText = false
    const searchLower = searchText.toLowerCase().trim()
    
    for (const item of textContent.items) {
      if ('str' in item && item.str.toLowerCase().includes(searchLower)) {
        // Calculate highlight box position
        const transform = item.transform
        const x = transform[4]
        const y = viewport.height - transform[5]
        const width = item.width
        const height = item.height
        
        highlightBox.value = { x, y: y - height, width, height }
        foundText = true
        break
      }
    }
    
    if (!foundText) {
      // Try to find partial matches by combining text items
      let combinedText = ''
      let startItem: any = null
      let endItem: any = null
      
      for (let i = 0; i < textContent.items.length; i++) {
        const item = textContent.items[i]
        if ('str' in item) {
          combinedText += item.str + ' '
          
          if (combinedText.toLowerCase().includes(searchLower)) {
            if (!startItem) startItem = item
            endItem = item
            
            // Calculate bounding box for combined text
            const transform = startItem.transform
            const x = transform[4]
            const y = viewport.height - transform[5]
            const width = endItem.transform[4] + endItem.width - x
            const height = Math.max(startItem.height, endItem.height)
            
            highlightBox.value = { x, y: y - height, width, height }
            foundText = true
            break
          }
        }
      }
    }
  } catch (err) {
    console.error('Error highlighting text:', err)
  }
}

const previousPage = async () => {
  if (canGoPrevious.value) {
    currentPage.value--
    pageInput.value = currentPage.value
    await renderPage(currentPage.value)
    emit('pageChange', currentPage.value)
    
    if (props.highlightText) {
      await highlightTextOnPage(props.highlightText)
    }
  }
}

const nextPage = async () => {
  if (canGoNext.value) {
    currentPage.value++
    pageInput.value = currentPage.value
    await renderPage(currentPage.value)
    emit('pageChange', currentPage.value)
    
    if (props.highlightText) {
      await highlightTextOnPage(props.highlightText)
    }
  }
}

const goToPage = async () => {
  const targetPage = Math.min(Math.max(pageInput.value, 1), totalPages.value)
  if (targetPage !== currentPage.value) {
    currentPage.value = targetPage
    pageInput.value = targetPage
    await renderPage(currentPage.value)
    emit('pageChange', currentPage.value)
    
    if (props.highlightText) {
      await highlightTextOnPage(props.highlightText)
    }
  }
}

const zoomIn = () => {
  if (scale.value < maxScale) {
    scale.value = Math.min(scale.value + scaleStep, maxScale)
  }
}

const zoomOut = () => {
  if (scale.value > minScale) {
    scale.value = Math.max(scale.value - scaleStep, minScale)
  }
}

const fitToWidth = async () => {
  if (!containerRef.value || !canvasRef.value) return
  
  await nextTick()
  const containerWidth = containerRef.value.clientWidth
  const canvasWidth = canvasRef.value.width
  
  if (canvasWidth > 0) {
    scale.value = (containerWidth - 40) / canvasWidth // 40px for padding
  }
}

const handleClose = () => {
  emit('close')
}

// Watchers
watch(() => props.pdfUrl, () => {
  loadPdf()
})

watch(() => props.initialPage, (newPage) => {
  if (newPage !== currentPage.value && pdfDocument.value) {
    currentPage.value = newPage
    pageInput.value = newPage
    renderPage(newPage)
  }
})

watch(() => props.highlightText, (newText) => {
  if (newText && pdfDocument.value) {
    highlightTextOnPage(newText)
  } else {
    highlightBox.value = null
  }
})

// Lifecycle
onMounted(() => {
  loadPdf()
})

onUnmounted(() => {
  if (pdfDocument.value) {
    pdfDocument.value.destroy()
  }
})
</script>

<style scoped>
.pdf-viewer {
  @apply bg-white rounded-lg shadow-sm border border-gray-200;
  @apply flex flex-col h-full;
}

/* Header */
.viewer-header {
  @apply flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50;
  @apply flex-shrink-0;
}

.header-left {
  @apply flex items-center gap-3 flex-1 min-w-0;
}

.viewer-title {
  @apply text-lg font-semibold text-gray-900 truncate;
}

.page-info {
  @apply text-sm text-gray-600 flex-shrink-0;
}

.close-button {
  @apply p-1 rounded-md hover:bg-gray-200 transition-colors;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.close-icon {
  @apply w-5 h-5 text-gray-600;
}

/* Toolbar */
.toolbar {
  @apply flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-white;
  @apply flex-shrink-0;
}

.nav-controls,
.zoom-controls {
  @apply flex items-center gap-2;
}

.toolbar-button {
  @apply p-2 rounded-md hover:bg-gray-100 transition-colors;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500;
  @apply disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent;
}

.button-icon {
  @apply w-5 h-5 text-gray-700;
}

.page-input {
  @apply w-16 px-2 py-1 text-center text-sm border border-gray-300 rounded-md;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent;
}

.zoom-level {
  @apply text-sm font-medium text-gray-700 min-w-[3rem] text-center;
}

/* Loading State */
.loading-container {
  @apply flex flex-col items-center justify-center flex-1 py-12 px-4;
}

.spinner {
  @apply w-10 h-10 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin;
}

.loading-text {
  @apply mt-4 text-sm text-gray-600;
}

/* Error State */
.error-container {
  @apply flex flex-col items-center justify-center flex-1 py-12 px-4;
}

.error-icon {
  @apply w-12 h-12 text-red-500;
}

.error-text {
  @apply mt-4 text-sm text-gray-700 text-center;
}

.retry-button {
  @apply mt-4 px-4 py-2 bg-blue-600 text-white rounded-md;
  @apply hover:bg-blue-700 transition-colors;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
}

/* Canvas Container */
.canvas-container {
  @apply flex-1 overflow-auto bg-gray-100 p-4;
}

.canvas-wrapper {
  @apply mx-auto transition-transform duration-200;
  @apply relative;
}

.pdf-canvas {
  @apply shadow-lg bg-white;
  @apply block mx-auto;
}

/* Highlight Overlay */
.highlight-overlay {
  @apply absolute bg-yellow-300 bg-opacity-40 border-2 border-yellow-500;
  @apply pointer-events-none;
  @apply animate-pulse;
}

/* Scrollbar styling */
.canvas-container::-webkit-scrollbar {
  @apply w-3 h-3;
}

.canvas-container::-webkit-scrollbar-track {
  @apply bg-gray-200;
}

.canvas-container::-webkit-scrollbar-thumb {
  @apply bg-gray-400 rounded;
}

.canvas-container::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-500;
}

/* Remove spinner arrows from number input */
.page-input::-webkit-inner-spin-button,
.page-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.page-input[type='number'] {
  -moz-appearance: textfield;
}
</style>
