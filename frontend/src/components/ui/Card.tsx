import type { HTMLAttributes } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'warning'
  padding?: 'sm' | 'md' | 'lg'
}

const VARIANT_CLASSES: Record<string, string> = {
  default: 'bg-white border border-gray-100/60 shadow-card',
  glass: 'bg-white/70 backdrop-blur-xl border border-white/60 shadow-card',
  warning: 'bg-orange-50/80 gradient-border-warning',
}

const PADDING_CLASSES: Record<string, string> = {
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-5',
}

export default function Card({
  variant = 'default',
  padding = 'md',
  className = '',
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={`rounded-3xl ${VARIANT_CLASSES[variant]} ${PADDING_CLASSES[padding]} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
