import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17202A",
        panel: "#F7F9FB",
        line: "#DDE5ED",
        mint: "#1F8A70",
        coral: "#D95F43",
        amber: "#B7791F"
      },
      boxShadow: {
        soft: "0 12px 30px rgba(24, 37, 51, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;

