import type { Config } from 'tailwindcss'

const config: Config = {
    darkMode: ['class'],
    content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  safelist: [
    // Agent border colors (left border for cards)
    'border-l-4',
    'border-l-blue-500',
    'border-l-green-500',
    'border-l-purple-500',
    'border-l-orange-500',
    'border-l-pink-500',
    'border-l-cyan-500',
    'border-l-gray-500',
    // Agent control panel borders (full border + glow)
    'border-2',
    'border-blue-500/30',
    'border-green-500/30',
    'border-purple-500/30',
    'border-orange-500/30',
    'border-pink-500/30',
    'border-cyan-500/30',
    'border-blue-500/50',
    'border-green-500/50',
    'border-purple-500/50',
    'border-orange-500/50',
    'border-pink-500/50',
    'border-cyan-500/50',
    'shadow-lg',
    'shadow-blue-500/20',
    'shadow-green-500/20',
    'shadow-purple-500/20',
    'shadow-orange-500/20',
    'shadow-pink-500/20',
    'shadow-cyan-500/20',
    'shadow-blue-500/30',
    'shadow-green-500/30',
    'shadow-purple-500/30',
    'shadow-orange-500/30',
    'shadow-pink-500/30',
    'shadow-cyan-500/30',
    'hover:border-blue-500',
    'hover:border-green-500',
    'hover:border-purple-500',
    'hover:border-orange-500',
    'hover:border-pink-500',
    'hover:border-cyan-500',
    'hover:shadow-blue-500/30',
    'hover:shadow-green-500/30',
    'hover:shadow-purple-500/30',
    'hover:shadow-orange-500/30',
    'hover:shadow-pink-500/30',
    'hover:shadow-cyan-500/30',
    'transition-all',
    // Agent text colors
    'text-blue-600',
    'text-blue-400',
    'text-green-600',
    'text-green-400',
    'text-purple-600',
    'text-purple-400',
    'text-orange-600',
    'text-orange-400',
    'text-pink-600',
    'text-pink-400',
    'text-cyan-600',
    'text-cyan-400',
    // Agent badge background colors
    'bg-blue-100',
    'bg-blue-900',
    'bg-green-100',
    'bg-green-900',
    'bg-purple-100',
    'bg-purple-900',
    'bg-orange-100',
    'bg-orange-900',
    'bg-pink-100',
    'bg-pink-900',
    'bg-cyan-100',
    'bg-cyan-900',
    // Agent badge text colors
    'text-blue-700',
    'text-blue-300',
    'text-green-700',
    'text-green-300',
    'text-purple-700',
    'text-purple-300',
    'text-orange-700',
    'text-orange-300',
    'text-pink-700',
    'text-pink-300',
    'text-cyan-700',
    'text-cyan-300',
  ],
  theme: {
  	extend: {
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		colors: {
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			}
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
}
export default config
