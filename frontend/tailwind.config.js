/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#070a13',
          900: '#0b101e',
          850: '#10172a',
          800: '#162038',
          700: '#1f2d4d',
        },
        cyan: {
          400: '#22d3ee',
          500: '#06b6d4',
          glow: '#00f0ff',
        },
        emerald: {
          500: '#10b981',
          400: '#34d399',
        },
        coral: {
          500: '#f43f5e',
          400: '#fb7185',
        }
      }
    },
  },
  plugins: [],
}
