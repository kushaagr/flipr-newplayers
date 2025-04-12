/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      "./templates/**/*.html",
      "./static/js/**/*.js" // If you have JS files using Tailwind classes
    ],
    theme: {
      extend: {},
    },
    plugins: [],
  }