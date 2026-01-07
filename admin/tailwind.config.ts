import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#D4AF37',
        secondary: '#E8D5A3',
        success: '#2A9D8F',
        warning: '#D4AF37',
        error: '#E07A5F',
      },
    },
  },
  plugins: [],
}
export default config
