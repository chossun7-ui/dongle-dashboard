/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // 변경/추가/삭제용 의미 색상
        diff: {
          added: "#22c55e",
          removed: "#ef4444",
          changed: "#f59e0b",
          unchanged: "#94a3b8",
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
