import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'TradeMatrix.ai',
  description: 'AI-Powered Trading Analysis & Automation Platform',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  )
}
