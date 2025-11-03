# Frontend Components

## IndicatorCard.vue

A card component for displaying individual BRSR Core indicators with transparency features.

### Features

1. **Indicator Information Display**
   - Indicator name and code
   - Extracted value with unit
   - Pillar badge (E/S/G) with color coding

2. **Confidence Scoring**
   - Visual confidence badge with percentage
   - Color-coded by confidence level:
     - High (≥80%): Green
     - Medium (60-79%): Yellow
     - Low (<60%): Orange

3. **Validation Status**
   - Color-coded validation badges:
     - Valid: Green with checkmark
     - Invalid: Red with X
     - Pending: Gray with info icon

4. **Source Citation**
   - Clickable citation button in footer
   - Shows PDF name and page numbers
   - Emits event to open citation viewer
   - Smart page number formatting (shows range for multiple pages)

### Props

- `indicator` (Indicator, required): The indicator data to display
- `pdfName` (string, optional): PDF file name for citation
- `sourcePages` (number[], optional): Array of source page numbers
- `showCitation` (boolean, optional, default: true): Show/hide citation footer

### Events

- `citationClick`: Emitted when citation button is clicked, passes the Indicator object

### Usage

```vue
<template>
  <IndicatorCard
    :indicator="indicator"
    :pdf-name="RELIANCE/2024_BRSR.pdf"
    :source-pages="[45, 46]"
    @citation-click="handleCitationClick"
  />
</template>

<script setup lang="ts">
import IndicatorCard from '@/components/IndicatorCard.vue'
import type { Indicator } from '@/types'

const indicator: Indicator = {
  id: 1,
  code: 'GHG_SCOPE1',
  name: 'Total Scope 1 emissions',
  value: '1250',
  numericValue: 1250,
  unit: 'MT CO2e',
  confidence: 0.95,
  validationStatus: 'valid',
  attributeNumber: 1,
  pillar: 'E'
}

const handleCitationClick = (indicator: Indicator) => {
  console.log('View citation for:', indicator)
  // Open citation viewer modal/component
}
</script>
```

### Requirements Satisfied

- **17.1**: Display indicator with name, value, unit, and confidence badge
- **18.5**: Show source citations for transparency
- **19.1**: Citation badge with PDF name and page numbers, clickable to open viewer

### Technical Details

- Responsive card layout with hover effects
- Pillar badges with distinct colors (E=Green, S=Blue, G=Purple)
- Confidence and validation status with visual indicators
- Smart page number formatting for readability
- Accessible with keyboard navigation
- Tailwind CSS for styling

---

## CompanySearch.vue

A comprehensive company search component with the following features:

### Features

1. **Search Input with Debouncing**
   - Real-time search with 300ms debounce delay
   - Searches companies by name or symbol
   - Clear button to reset search

2. **Industry Filter**
   - Dropdown to filter companies by industry
   - Dynamically populated from available companies
   - Works in combination with search

3. **Company Cards Display**
   - Grid layout (responsive: 1 column mobile, 2 tablet, 3 desktop)
   - Shows company name, symbol, industry, and ISIN code
   - Hover effects and keyboard navigation support

4. **Navigation**
   - Clicking a company card navigates to the company dashboard
   - Emits 'select' event for parent components
   - Updates company store with selected company

5. **State Management**
   - Loading states with spinner
   - Error handling with user-friendly messages
   - Click-outside to close results

### Props

- `autoFocus` (boolean, optional): Auto-focus the search input on mount
- `showIndustryFilter` (boolean, optional, default: true): Show/hide industry filter

### Events

- `select`: Emitted when a company is selected, passes the Company object

### Usage

```vue
<template>
  <CompanySearch @select="handleCompanySelect" />
</template>

<script setup lang="ts">
import CompanySearch from '@/components/CompanySearch.vue'
import type { Company } from '@/types'

const handleCompanySelect = (company: Company) => {
  console.log('Selected:', company)
}
</script>
```

### Requirements Satisfied

- **20.1**: Search interface to find companies by name, symbol, or industry
- **20.2**: Display companies with comprehensive information
- **20.5**: Filters to view companies by industry

### Technical Details

- Uses Pinia store for state management
- Implements debounced search to reduce API calls
- Responsive design with Tailwind CSS
- Accessible with keyboard navigation and ARIA labels
- Click-outside handler to close results

---

## CitationViewer.vue

A component for displaying source citations with PDF information, page numbers, chunk text, confidence scores, and extraction timestamps. Supports multiple citations for a single indicator with interactive "View in PDF" functionality.

### Features

1. **Multiple Citations Support**
   - Display multiple citations for a single indicator
   - Each citation shows PDF name, page numbers, and extracted text
   - Scrollable list of citations

2. **Citation Details**
   - PDF file name with icon
   - Page numbers (formatted as ranges or lists)
   - Extracted chunk text in scrollable container
   - Confidence score badge (color-coded)
   - Extraction timestamp (relative time format)

3. **Interactive Actions**
   - "View in PDF" button for each citation
   - Opens PDF viewer at the specific page
   - Emits events for parent component handling

4. **State Management**
   - Loading state with spinner
   - Error state with retry button
   - Empty state when no citations available
   - Closeable option for modal/drawer usage

### Props

- `citations` (Citation[], required): Array of citation objects to display
- `loading` (boolean, optional, default: false): Show loading spinner
- `error` (string | null, optional, default: null): Error message to display
- `confidence` (number, optional): Confidence score (0.0-1.0) for the extraction
- `extractedAt` (string, optional): ISO timestamp of when the indicator was extracted
- `showConfidence` (boolean, optional, default: true): Whether to display the confidence badge
- `showTimestamp` (boolean, optional, default: true): Whether to display the extraction timestamp
- `closeable` (boolean, optional, default: false): Whether to show a close button in the header

### Events

- `viewPdf`: Emitted when "View in PDF" button is clicked, passes the Citation object
- `close`: Emitted when close button is clicked (if closeable is true)
- `retry`: Emitted when retry button is clicked in error state

### Usage

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

### Integration with IndicatorCard

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
```

### Requirements Satisfied

- **19.1**: Display citation badge with PDF name and page number
- **19.4**: Display extraction confidence score and timestamp
- **19.5**: Support multiple citations for single indicator

### Technical Details

- Color-coded confidence badges (Green: high, Yellow: medium, Orange: low)
- Scrollable chunk text with custom scrollbar styling
- Relative time formatting for timestamps (e.g., "2 hours ago")
- Smart page number formatting (ranges for consecutive pages)
- Responsive design with Tailwind CSS
- Accessible with ARIA labels and keyboard navigation
- Hover effects and smooth transitions


---

## AuthPrompt.vue

A modal component that prompts users to authenticate when attempting operations that require authentication (POST/PUT/DELETE operations).

### Features

1. **Authentication Prompt**
   - Clear message indicating authentication is required
   - Lock icon for visual clarity
   - Customizable message text

2. **Action Buttons**
   - "Sign In" button to initiate authentication
   - "Cancel" button to dismiss the prompt

3. **Modal Overlay**
   - Semi-transparent backdrop
   - Centered modal with smooth transitions
   - Accessible with keyboard navigation

### Props

- `message` (string, optional): Custom message to display. Defaults to "You need to sign in to perform this action."

### Events

- `sign-in`: Emitted when the "Sign In" button is clicked
- `cancel`: Emitted when the "Cancel" button is clicked

### Usage

```vue
<template>
  <div>
    <button @click="handleMutationOperation">
      Trigger Report Processing
    </button>

    <AuthPrompt
      v-if="showAuthPrompt"
      message="You need to sign in to trigger report processing."
      @sign-in="handleSignIn"
      @cancel="showAuthPrompt = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AuthPrompt from '@/components/AuthPrompt.vue'
import { useAuth } from '@/composables/useAuth'

const { isAuthenticated } = useAuth()
const showAuthPrompt = ref(false)

const handleMutationOperation = () => {
  if (!isAuthenticated.value) {
    showAuthPrompt.value = true
    return
  }
  
  // Perform the mutation operation
  console.log('Processing report...')
}

const handleSignIn = () => {
  // Redirect to login page or open login modal
  console.log('Redirecting to sign in...')
  showAuthPrompt.value = false
}
</script>
```

### Requirements Satisfied

- **3.2**: Display login prompt only when attempting mutations
- **3.5**: Clear indication when authentication is required

### Technical Details

- Fixed overlay with z-index for modal behavior
- Responsive design with Tailwind CSS
- Accessible with focus management
- Smooth transitions for better UX
- Can be used with the `useAuth` composable for authentication state management

