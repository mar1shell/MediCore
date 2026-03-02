const COLOR_PAIRS = [
  { bg: 'bg-blue-50', text: 'text-blue-600' },
  { bg: 'bg-purple-50', text: 'text-purple-600' },
  { bg: 'bg-teal-50', text: 'text-teal-600' },
  { bg: 'bg-rose-50', text: 'text-rose-600' },
  { bg: 'bg-amber-50', text: 'text-amber-600' },
]

interface AvatarProps {
  name: string
  size?: 'sm' | 'md' | 'lg'
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map(w => w[0].toUpperCase())
    .join('')
}

function getColorPair(name: string) {
  const idx = name.charCodeAt(0) % COLOR_PAIRS.length
  return COLOR_PAIRS[idx]
}

const SIZE_CLASSES = {
  sm: 'w-9 h-9 text-sm',
  md: 'w-12 h-12 text-base',
  lg: 'w-14 h-14 text-lg',
}

export default function Avatar({ name, size = 'md' }: AvatarProps) {
  const { bg, text } = getColorPair(name)
  return (
    <div className={`${SIZE_CLASSES[size]} ${bg} ${text} rounded-full flex items-center justify-center font-bold flex-shrink-0`}>
      {getInitials(name)}
    </div>
  )
}
