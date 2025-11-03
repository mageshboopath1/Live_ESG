# FilterControls Component

A modern dark-themed filter control component with dropdown menus for date, product, and profile filtering, plus an export button.

## Features

- **Three Filter Dropdowns**: Date, Product, and Profile filters with customizable options
- **Dark Theme Styling**: Pill-shaped buttons with dark backgrounds and borders
- **Dropdown Menus**: Smooth animated dropdowns with dark theme styling
- **Export Button**: Icon button for print/export functionality
- **Responsive Design**: Adapts to mobile, tablet, and desktop screens
- **Keyboard Navigation**: Full keyboard support with Escape key to close dropdowns
- **Click Outside**: Automatically closes dropdowns when clicking outside
- **Accessibility**: ARIA labels and focus indicators for screen readers

## Usage

### Basic Example

```vue
<template>
  <FilterControls
    v-model:selected-date="selectedDate"
    v-model:selected-product="selectedProduct"
    v-model:selected-profile="selectedProfile"
    @export="handleExport"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FilterControls from '@/components/FilterControls.vue'

const selectedDate = ref('30d')
const selectedProduct = ref('all')
const selectedProfile = ref('all')

const handleExport = () => {
  console.log('Export data')
}
</script>
```

### Custom Options

```vue
<template>
  <FilterControls
    v-model:selected-date="selectedDate"
    v-model:selected-product="selectedProduct"
    v-model:selected-profile="selectedProfile"
    :date-options="customDateOptions"
    :product-options="customProductOptions"
    :profile-options="customProfileOptions"
    @export="handleExport"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FilterControls from '@/components/FilterControls.vue'

const selectedDate = ref('q1')
const selectedProduct = ref('esg')
const selectedProfile = ref('environmental')

const customDateOptions = [
  { label: 'Q1 2024', value: 'q1' },
  { label: 'Q2 2024', value: 'q2' },
  { label: 'Q3 2024', value: 'q3' },
  { label: 'Q4 2024', value: 'q4' }
]

const customProductOptions = [
  { label: 'ESG Scores', value: 'esg' },
  { label: 'Reports', value: 'reports' },
  { label: 'Analytics', value: 'analytics' }
]

const customProfileOptions = [
  { label: 'Environmental', value: 'environmental' },
  { label: 'Social', value: 'social' },
  { label: 'Governance', value: 'governance' }
]

const handleExport = () => {
  console.log('Export data with filters:', {
    date: selectedDate.value,
    product: selectedProduct.value,
    profile: selectedProfile.value
  })
}
</script>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `dateOptions` | `FilterOption[]` | Default date options | Array of date filter options |
| `productOptions` | `FilterOption[]` | Default product options | Array of product filter options |
| `profileOptions` | `FilterOption[]` | Default profile options | Array of profile filter options |
| `selectedDate` | `string` | `'30d'` | Currently selected date value |
| `selectedProduct` | `string` | `'all'` | Currently selected product value |
| `selectedProfile` | `string` | `'all'` | Currently selected profile value |

### FilterOption Interface

```typescript
interface FilterOption {
  label: string  // Display label
  value: string  // Value identifier
}
```

### Default Options

**Date Options:**
- Last 7 days (`'7d'`)
- Last 30 days (`'30d'`)
- Last 90 days (`'90d'`)
- Last year (`'1y'`)
- All time (`'all'`)

**Product Options:**
- All Products (`'all'`)
- ESG Scores (`'esg'`)
- Reports (`'reports'`)
- Analytics (`'analytics'`)

**Profile Options:**
- All Profiles (`'all'`)
- Environmental (`'environmental'`)
- Social (`'social'`)
- Governance (`'governance'`)

## Events

| Event | Payload | Description |
|-------|---------|-------------|
| `update:selectedDate` | `string` | Emitted when date filter changes |
| `update:selectedProduct` | `string` | Emitted when product filter changes |
| `update:selectedProfile` | `string` | Emitted when profile filter changes |
| `export` | - | Emitted when export button is clicked |

## Styling

The component uses Tailwind CSS with custom dark theme utilities:

- **Filter Buttons**: `bg-dark-card` with `hover:bg-dark-cardHover`
- **Dropdown Menus**: `bg-dark-card` with `border-dark-border`
- **Active Items**: Highlighted with `text-accent-green`
- **Export Button**: Icon button with hover effects

## Responsive Behavior

- **Desktop (> 768px)**: Horizontal layout with all filters in a row
- **Mobile (< 768px)**: Vertical stack layout with full-width buttons

## Accessibility

- ARIA attributes for dropdown states (`aria-expanded`, `aria-haspopup`)
- Keyboard navigation support (Escape to close)
- Focus indicators for keyboard users
- Screen reader friendly labels

## Requirements Satisfied

- **3.1**: Horizontal row layout below page title
- **3.2**: Dropdown menus on filter click
- **3.3**: Dark pill-shaped buttons with dropdown indicators
- **3.4**: Print/export icon button
- **3.5**: Event emitters for filter changes
- **10.1**: Smooth transitions on hover

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Related Components

- `CompanySearch.vue` - Search component with filters
- `Sidebar.vue` - Navigation sidebar
- `AppHeader.vue` - Application header
