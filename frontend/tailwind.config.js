/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          main: "#0F1014",
          sidebar: "#14151A",
          card: "#17191F",
          cardHover: "#1E2028",
        },
        border: {
          DEFAULT: "#2B2D37",
          active: "#404453",
        },
        primary: {
          DEFAULT: "#3157D5",
          hover: "#2646AC",
        },
        secondary: {
          DEFAULT: "#E9785B",
          hover: "#D26448",
        },
        tertiary: "#E8E3D8",
        status: {
          green: "#10B981",
          yellow: "#F59E0B",
          red: "#EF4444",
        },
      },
      fontFamily: {
        headline: ['"Space Grotesk"', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
};
