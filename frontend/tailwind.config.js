import forms from "@tailwindcss/forms"
import typography from "@tailwindcss/typography"

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary:   "#0A0E1A",
          secondary: "#111827",
          tertiary:  "#1A2235",
          card:      "#0F1626",
          hover:     "#161E30",
        },
        accent: {
          indigo:  "#6366F1",
          cyan:    "#06B6D4",
          emerald: "#10B981",
          amber:   "#F59E0B",
          red:     "#EF4444",
          purple:  "#8B5CF6",
        },
        border: {
          DEFAULT: "#1F2937",
          light:   "#374151",
          glow:    "#6366F133",
        },
        text: {
          primary:   "#F9FAFB",
          secondary: "#9CA3AF",
          muted:     "#6B7280",
          accent:    "#6366F1",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backgroundImage: {
        "hero-gradient":
          "linear-gradient(135deg, #6366F1 0%, #06B6D4 50%, #10B981 100%)",
        "card-gradient":
          "linear-gradient(145deg, #0F1626 0%, #111827 100%)",
        "glow-indigo":
          "radial-gradient(circle at center, #6366F133 0%, transparent 70%)",
      },
      boxShadow: {
        "glow-indigo": "0 0 30px #6366F140",
        "glow-cyan":   "0 0 30px #06B6D440",
        "card":        "0 4px 24px rgba(0,0,0,0.4)",
        "card-hover":  "0 8px 40px rgba(0,0,0,0.6)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "shimmer":    "shimmer 2s linear infinite",
        "float":      "float 6s ease-in-out infinite",
        "glow":       "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%":      { transform: "translateY(-10px)" },
        },
        glow: {
          "0%":   { boxShadow: "0 0 20px #6366F140" },
          "100%": { boxShadow: "0 0 40px #6366F180" },
        },
      },
    },
  },
  plugins: [forms, typography],
}
