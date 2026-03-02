import type { ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'warning' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
}

const VARIANT_CLASSES: Record<string, string> = {
  primary: 'bg-primary text-white shadow-[0_4px_14px_rgba(143,84,255,0.35)] hover:bg-primary/90 active:scale-[0.98]',
  secondary: 'bg-white border border-gray-200 text-text-main hover:bg-gray-50 active:scale-[0.98]',
  danger: 'bg-white border border-red-100 text-red-500 hover:bg-red-50 active:scale-[0.98]',
  warning: 'bg-gradient-to-r from-warning to-orange-400 text-white shadow-[0_4px_14px_rgba(249,115,22,0.3)] hover:shadow-[0_6px_20px_rgba(249,115,22,0.4)] active:scale-[0.98]',
  ghost: 'text-text-sub hover:text-text-main hover:bg-gray-50 active:scale-[0.98]',
}

const SIZE_CLASSES: Record<string, string> = {
  sm: 'px-4 py-2 text-sm rounded-2xl',
  md: 'px-6 py-3 text-[15px] rounded-2xl',
  lg: 'px-8 py-4 text-base rounded-3xl',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  className = '',
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`
        inline-flex items-center justify-center gap-2 font-semibold
        transition-all duration-200 select-none
        disabled:opacity-50 disabled:cursor-not-allowed
        ${VARIANT_CLASSES[variant]}
        ${SIZE_CLASSES[size]}
        ${fullWidth ? 'w-full' : ''}
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  )
}
