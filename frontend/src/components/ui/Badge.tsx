interface BadgeProps {
  variant?: 'active' | 'followup' | 'action' | 'conflict' | 'source'
  children: React.ReactNode
}

const STYLES: Record<string, string> = {
  active: 'bg-green-100 text-green-700 border border-green-200',
  followup: 'bg-purple-50 text-primary border border-primary/20',
  action: 'bg-warning/10 text-warning border border-warning/25 uppercase tracking-wide text-[10px]',
  conflict: 'bg-red-50 text-red-500 border border-red-100',
  source: 'bg-gray-100 text-text-sub border border-gray-200',
}

export default function Badge({ variant = 'active', children }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${STYLES[variant]}`}>
      {children}
    </span>
  )
}
