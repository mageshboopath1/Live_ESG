/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        dark: {
          bg: '#000000',
          card: '#1a1a1a',
          cardHover: '#222222',
          border: '#333333',
          text: {
            primary: '#ffffff',
            secondary: '#a0a0a0',
            muted: '#666666',
          },
        },
        accent: {
          green: {
            light: '#c4f54d',
            DEFAULT: '#a8e63d',
            dark: '#8bc34a',
          },
          orange: {
            light: '#ffb74d',
            DEFAULT: '#ff9800',
            dark: '#f57c00',
          },
          blue: {
            light: '#64b5f6',
            DEFAULT: '#2196f3',
            dark: '#1976d2',
          },
          pink: {
            light: '#f48fb1',
            DEFAULT: '#e91e63',
            dark: '#c2185b',
          },
        },
      },
    },
  },
  plugins: [],
}
