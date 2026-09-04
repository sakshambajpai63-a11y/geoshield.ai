/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
      },
      colors: {
        // Citizen portal — cool mist, daylight
        mist: {
          50: "#F6F7F6",
          100: "#ECEEEC",
          200: "#D7DBD8",
        },
        teal: {
          600: "#1F6F78",
          700: "#195A61",
        },
        // Officer console — command-center slate
        slate: {
          900: "#12181C",
          800: "#1B2328",
          700: "#26313700",
        },
        // Status colors — used ONLY for risk level, never decoration
        status: {
          safe: "#2E7D4F",
          watch: "#B8842E",
          warning: "#CC5A26",
          danger: "#B0362E",
        },
      },
    },
  },
  plugins: [],
};
