'use client'

import { AnimatePresence } from 'framer-motion'

// Wraps the app with AnimatePresence so page-level exit animations work.
// Must be a Client Component — layout.tsx stays a Server Component.
export function Providers({ children }: { children: React.ReactNode }) {
  return <AnimatePresence mode="wait">{children}</AnimatePresence>
}
