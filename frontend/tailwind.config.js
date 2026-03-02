/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#8f54ff',
        'primary-light': '#a77aff',
        'primary-soft': '#f3e8ff',
        secondary: '#d946ef',
        warning: '#f97316',
        surface: '#ffffff',
        'text-main': '#1f1b2e',
        'text-sub': '#9ca3af',
      },
      fontFamily: {
        sans: ['Urbanist', 'sans-serif'],
      },
      boxShadow: {
        card: '0 4px 20px rgba(0,0,0,0.03)',
        soft: '0 10px 40px -10px rgba(143,84,255,0.1)',
        'orb-glow': '0 0 60px rgba(143,84,255,0.3)',
        floating: '0 20px 40px -10px rgba(0,0,0,0.1)',
      },
      borderRadius: {
        '3xl': '28px',
        '4xl': '36px',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        blink: {
          '0%, 96%, 100%': { transform: 'scaleY(1)' },
          '98%': { transform: 'scaleY(0.1)' },
        },
        orbPulse: {
          '0%, 100%': { transform: 'scale(1)', boxShadow: '0 0 40px rgba(255,255,255,0.3), 0 0 60px rgba(143,84,255,0.2)' },
          '50%': { transform: 'scale(1.02)', boxShadow: '0 0 60px rgba(255,255,255,0.5), 0 0 80px rgba(143,84,255,0.4)' },
        },
        breathe: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.03)' },
        },
        gradientShift: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(30px) scale(0.95)' },
          '100%': { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pingRing: {
          '75%, 100%': { transform: 'scale(1.5)', opacity: '0' },
        },
      },
      animation: {
        float: 'float 8s ease-in-out infinite',
        blink: 'blink 4s infinite',
        'orb-pulse': 'orbPulse 3s ease-in-out infinite',
        breathe: 'breathe 4s ease-in-out infinite',
        'gradient-shift': 'gradientShift 6s ease infinite',
        'slide-up': 'slideUp 0.4s ease-out forwards',
        'fade-in': 'fadeIn 0.4s ease-out forwards',
        'ping-ring': 'pingRing 2s cubic-bezier(0,0,0.2,1) infinite',
      },
    },
  },
  plugins: [],
}
