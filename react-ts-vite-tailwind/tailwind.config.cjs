/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: {
      fontFamily: {
        sf: ['"SF Pro Display"', 'sans-serif'],
      },
    },},
  plugins: [],
}
