/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				'deep-dark': '#0a0a0f',
				'card-bg': '#151520',
				'card-hover': '#1a1a2e',
				'neon-cyan': '#00d4ff',
				'neon-purple': '#7c3aed',
				'neon-green': '#10b981',
				'neon-red': '#ef4444',
				'neon-yellow': '#f59e0b',
				'text-primary': '#e0e0e0',
				'text-secondary': '#888888',
				'border-subtle': '#2a2a3e'
			},
			fontFamily: {
				mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
				sans: ['Inter', 'system-ui', 'sans-serif']
			},
			animation: {
				'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
				'fade-in': 'fade-in 0.3s ease-out',
				'slide-in': 'slide-in 0.3s ease-out'
			},
			keyframes: {
				'pulse-glow': {
					'0%, 100%': { opacity: 1, boxShadow: '0 0 20px rgba(0, 212, 255, 0.3)' },
					'50%': { opacity: 0.8, boxShadow: '0 0 10px rgba(0, 212, 255, 0.1)' }
				},
				'fade-in': {
					'0%': { opacity: 0 },
					'100%': { opacity: 1 }
				},
				'slide-in': {
					'0%': { transform: 'translateX(-10px)', opacity: 0 },
					'100%': { transform: 'translateX(0)', opacity: 1 }
				}
			}
		}
	},
	plugins: []
};
