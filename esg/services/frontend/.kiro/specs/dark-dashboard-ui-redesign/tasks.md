# Implementation Plan

- [x] 1. Set up dark theme foundation and color system
  - Extend Tailwind configuration with dark theme color palette including background colors (blacks, dark grays), text colors (whites, light grays), and accent colors (green, orange, blue, pink)
  - Create custom CSS utilities for dark theme in main.css
  - Update global body styles to support dark background
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Redesign AppHeader component with modern dark navigation
  - Update AppHeader.vue template with dark background and border styling
  - Implement circular logo icon in top-left corner
  - Create pill-shaped navigation buttons for Check Box, Monitoring, and Support items
  - Add search icon button to navigation bar
  - Implement user profile section with avatar and notification badge in top-right
  - Apply hover effects and transitions to navigation elements
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 10.1_

- [x] 3. Create new Sidebar component for quick actions
  - Create Sidebar.vue component with vertical layout
  - Implement icon buttons for favorites (heart), calendar, insights (diamond), and settings
  - Add create/add button at bottom of sidebar
  - Implement hover effects and tooltips for sidebar icons
  - Add active state highlighting for current section
  - Implement collapsible behavior for mobile devices
  - Wire sidebar into App.vue layout
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 9.5_

- [x] 4. Create FilterControls component
  - Create FilterControls.vue component with horizontal layout
  - Implement three dropdown filters (Date, Product, Profile) with pill-shaped dark buttons
  - Add chevron/dropdown indicators to filter buttons
  - Create dropdown menu components with dark theme styling
  - Implement print/export icon button
  - Add event emitters for filter changes
  - Style dropdowns with dark backgrounds and borders
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 10.1_

- [ ] 5. Redesign MetricCard component with KPI visualizations
  - Update IndicatorCard.vue or create new MetricCard.vue component
  - Implement large percentage display with bold typography
  - Add trend indicators (up/down arrows) with color coding (green for positive, red for negative)
  - Display category labels below percentage values
  - Integrate mini line chart visualization using SVG or chart library
  - Add three-dot menu icon for card actions
  - Apply dark card background with rounded corners and hover effects
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 10.1, 10.2_

- [ ] 6. Create TimelineVisualization component
  - Create TimelineVisualization.vue component
  - Implement horizontal timeline layout with vertical date axis
  - Render project items as colored pill-shaped bars
  - Apply color coding (green, orange, white) for different project categories
  - Display avatar icons within timeline bars
  - Create legend showing Customer, Product, and Web category totals
  - Implement responsive scaling for different screen sizes
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.4_

- [ ] 7. Create DataVisualization component with dot matrix and bubble charts
  - Create DataVisualization.vue component with support for multiple visualization types
  - Implement dot matrix visualization using SVG grid of colored circles
  - Implement bubble chart with varying circle sizes
  - Apply color coding (green for valid, orange for invalid, white for resources)
  - Create legend component with color indicators and category counts
  - Add interactive hover states for data points
  - Implement smooth transitions for data updates
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 10.1, 10.4_

- [ ] 8. Update HomeView with new dashboard layout
  - Restructure HomeView.vue template to use dashboard grid layout
  - Integrate FilterControls component below page title
  - Arrange MetricCard components in responsive grid (3 columns desktop, 2 tablet, 1 mobile)
  - Add TimelineVisualization component to dashboard
  - Add DataVisualization components for dot matrix and bubble charts
  - Update page title styling for dark theme
  - Ensure all existing functionality is preserved
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2_

- [ ] 9. Apply dark theme to remaining views
  - Update CompanyView.vue with dark theme styling (backgrounds, text colors, card styles)
  - Update ComparisonView.vue with dark theme styling
  - Update ScoreView.vue with dark theme styling
  - Update ErrorView.vue and NotFoundView.vue with dark theme styling
  - Ensure all existing components within views maintain functionality
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 10. Update existing components with dark theme
  - Update CompanySearch.vue with dark input fields and dropdown styling
  - Update ScoreBreakdown.vue with dark card backgrounds
  - Update ScoreVisualization.vue with dark theme colors
  - Update CitationViewer.vue with dark backgrounds
  - Update PDFViewer.vue with dark theme styling
  - Update LoadingSpinner.vue with light colors for dark backgrounds
  - Update ToastNotification.vue with dark theme styling and accent colors
  - Update ErrorBoundary.vue with dark theme error messages
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 11. Update chart components with dark theme
  - Update BarChart.vue with dark backgrounds and light-colored bars
  - Update LineChart.vue with dark backgrounds and vibrant line colors
  - Update RadarChart.vue with dark backgrounds and accent colors
  - Update IndicatorTrendChart.vue with dark theme styling
  - Update PillarComparisonChart.vue with dark theme styling
  - Update MultiIndicatorChart.vue with dark theme styling
  - Ensure chart legends use light text on dark backgrounds
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 12. Implement responsive design behaviors
  - Add CSS media queries for mobile (< 768px), tablet (768-1024px), and desktop (> 1024px) breakpoints
  - Implement single column card layout for mobile devices
  - Add sidebar collapse/toggle functionality for mobile
  - Ensure filter controls are usable on mobile (stack vertically or horizontal scroll)
  - Adjust font sizes for different screen sizes
  - Test and fix visualization readability on smaller screens
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 13. Add animations and transitions
  - Implement smooth hover transitions for all interactive elements (buttons, cards, links)
  - Add card appearance animations when loading data
  - Create visual feedback animations for button clicks
  - Implement smooth transitions for dropdown menus and modals
  - Add subtle fade-in animations for page transitions
  - Optimize animations to maintain 60fps performance
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 14. Update AppFooter with dark theme
  - Update AppFooter.vue with dark background and light text
  - Ensure footer links have appropriate hover states
  - Maintain existing footer functionality and content
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 15. Accessibility and contrast compliance
  - Verify all text-background color combinations meet WCAG 2.1 AA contrast ratios (4.5:1 for normal text, 3:1 for large text)
  - Ensure all interactive elements have visible focus indicators on dark backgrounds
  - Test keyboard navigation through all new and updated components
  - Verify screen reader compatibility with ARIA labels where needed
  - Add alt text to all icon buttons and images
  - _Requirements: 1.4_

- [ ] 16. Final integration and polish
  - Test all views and components together in the full application
  - Verify all existing functionality works correctly (navigation, data fetching, state management)
  - Check for any visual inconsistencies or styling issues
  - Ensure smooth transitions between all pages
  - Verify responsive behavior across all breakpoints
  - Test in multiple browsers (Chrome, Firefox, Safari, Edge)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2, 9.3, 9.4, 9.5_
