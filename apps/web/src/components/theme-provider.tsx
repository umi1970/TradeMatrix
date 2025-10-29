'use client'

import { ThemeProvider as NextThemesProvider } from 'next-themes'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    // @ts-ignore - next-themes doesn't properly expose children in types
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      enableColorScheme={false}
    >
      {children}
    </NextThemesProvider>
  )
}
