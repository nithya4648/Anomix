module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        critical: '#dc2626',
        warning: '#f59e0b',
        info: '#3b82f6',
        success: '#10b981',
        ui: {
          background: '#030712',
          surface: '#0f172a',
          border: '#1e293b',
          text: {
            primary: '#f1f5f9',
            secondary: '#cbd5e1',
            tertiary: '#64748b',
          },
        },
      },
    },
  },
  plugins: [],
}
