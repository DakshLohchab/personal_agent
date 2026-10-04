import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17221f",
        moss: "#426454",
        cream: "#f4f1e8",
        ember: "#c9694b",
      },
    },
  },
  plugins: [],
};

export default config;
