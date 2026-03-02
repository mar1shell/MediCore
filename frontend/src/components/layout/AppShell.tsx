import type { ReactNode } from 'react'
import BottomNav from '../ui/BottomNav'
import type { NavTab } from '../../types'

interface AppShellProps {
  children: ReactNode
  activeTab?: NavTab
  showNav?: boolean
  className?: string
}

export default function AppShell({
  children,
  activeTab = 'home',
  showNav = true,
  className = '',
}: AppShellProps) {
  return (
    <div className="min-h-dvh flex items-start justify-center bg-gradient-to-b from-[#fdfbfd] to-[#f7f9ff]">
      <div className="relative w-full max-w-md min-h-dvh flex flex-col overflow-hidden">
        {/* Ambient background blobs */}
        <div
          className="pointer-events-none absolute top-0 right-0 w-64 h-64 rounded-full opacity-50 blur-[120px]"
          style={{ background: '#f3e8ff' }}
        />
        <div
          className="pointer-events-none absolute bottom-32 left-0 w-48 h-48 rounded-full opacity-30 blur-[100px]"
          style={{ background: '#e0e7ff' }}
        />

        {/* Page content */}
        <main className={`flex-1 flex flex-col relative z-10 ${className}`}>
          {children}
        </main>

        {/* Bottom navigation */}
        {showNav && (
          <div className="relative z-10">
            <BottomNav active={activeTab} />
          </div>
        )}
      </div>
    </div>
  )
}
