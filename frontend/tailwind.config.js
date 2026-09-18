/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx}",
    "./components/**/*.{js,jsx}",
    "./features/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#14171F",
        mist: "#EEF1F5",
        surface: "#FFFFFF",
        primary: {
          50: "#EEF0F6",
          100: "#DCE0ED",
          200: "#B9C0DA",
          300: "#8D96BC",
          400: "#5A6694",
          500: "#3A4778",
          600: "#2B3A67",
          700: "#212C4E",
          800: "#1A2340",
          900: "#151B33",
        },
        signal: {
          50: "#FDF3E3",
          100: "#FAE4BE",
          400: "#EFB158",
          500: "#E8A33D",
          600: "#C7841F",
          700: "#9C6717",
        },
        success: {
          50: "#E9F5EE",
          500: "#3F8F5F",
          700: "#2C6A45",
        },
        warning: {
          50: "#FDF3E3",
          500: "#E8A33D",
          700: "#9C6717",
        },
        danger: {
          50: "#FBEBE9",
          500: "#C1483D",
          700: "#93342C",
        },
      },
      fontFamily: {
        head: ['"Libre Franklin"', "system-ui", "sans-serif"],
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: {
        xl: "0.625rem",
        "2xl": "0.875rem",
      },
    },
  },
  plugins: [],
};
