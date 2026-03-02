import { useNavigate } from 'react-router-dom'
import type { NavTab } from '../../types'

interface BottomNavProps {
  active?: NavTab
}

const NAV_ITEMS: { id: NavTab; label: string; icon: string; path: string }[] = [
  { id: 'home', label: 'Home', icon: 'home', path: '/' },
  { id: 'history', label: 'History', icon: 'history', path: '/history' },
  { id: 'profile', label: 'Profile', icon: 'person', path: '/profile' },
]

export default function BottomNav({ active = 'home' }: BottomNavProps) {
  const navigate = useNavigate()

  return (
    <nav className="w-full bg-white/90 backdrop-blur-xl border-t border-gray-100 shadow-[0_-4px_20px_rgba(0,0,0,0.03)]">
      <div className="flex items-center justify-around px-2 py-3 pb-safe">
        {NAV_ITEMS.map(item => {
          const isActive = item.id === active
          return (
            <button
              key={item.id}
              onClick={() => navigate(item.path)}
              className="flex flex-col items-center gap-0.5 px-4 py-1 rounded-xl transition-all duration-200 group"
            >
              <span
                className="material-symbols-outlined text-[22px] transition-transform duration-200 group-hover:-translate-y-0.5"
                style={{
                  color: isActive ? '#8f54ff' : '#9ca3af',
                  fontVariationSettings: `'FILL' ${isActive ? 1 : 0}, 'wght' ${isActive ? 600 : 400}, 'GRAD' 0, 'opsz' 24`,
                }}
              >
                {item.icon}
              </span>
              <span
                className="text-[11px] font-medium transition-colors duration-200"
                style={{ color: isActive ? '#8f54ff' : '#9ca3af' }}
              >
                {item.label}
              </span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
