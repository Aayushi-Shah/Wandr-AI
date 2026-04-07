import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'wandr — AI Travel Planning',
  description: 'Plan your perfect trip with multi-agent AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-white text-gray-900 antialiased">
          <Providers>{children}</Providers>
        </body>
    </html>
  )
}
