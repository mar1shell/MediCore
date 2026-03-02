import type { OrbVariant } from '../../types'

interface OrbProps {
  variant?: OrbVariant
  size?: 'sm' | 'md' | 'lg'
}

const GRADIENTS: Record<OrbVariant, string> = {
  idle: 'radial-gradient(circle at 30% 30%, #c4a0ff, #8f54ff, #5a2adb)',
  listening: 'radial-gradient(circle at 35% 25%, #d8b4fe 0%, #a855f7 40%, #581c87 100%)',
  analyzing: 'radial-gradient(circle at 30% 30%, #a270ff, #4e9fff, #3b2a60)',
  alert: 'radial-gradient(circle at 35% 35%, #fb7185, #d946ef, #7e22ce)',
}

const GLOW_COLORS: Record<OrbVariant, string> = {
  idle: 'rgba(143,84,255,0.35)',
  listening: 'rgba(168,85,247,0.45)',
  analyzing: 'rgba(78,159,255,0.35)',
  alert: 'rgba(217,70,239,0.45)',
}

const SHADOW_COLORS: Record<OrbVariant, string> = {
  idle: 'rgba(143,84,255,0.25)',
  listening: 'rgba(168,85,247,0.3)',
  analyzing: 'rgba(78,159,255,0.3)',
  alert: 'rgba(217,70,239,0.35)',
}

const SPHERE_ANIMATIONS: Record<OrbVariant, string> = {
  idle: 'animate-float',
  listening: 'animate-float animate-orb-pulse',
  analyzing: 'animate-float animate-breathe',
  alert: 'animate-float animate-gradient-shift',
}

const SIZES = {
  sm: { container: 'w-16 h-16', sphere: 'w-12 h-12', eye: 'w-1.5 h-4', gap: 'gap-1.5' },
  md: { container: 'w-48 h-48', sphere: 'w-36 h-36', eye: 'w-2.5 h-7', gap: 'gap-2.5' },
  lg: { container: 'w-56 h-56', sphere: 'w-44 h-44', eye: 'w-3 h-8', gap: 'gap-3' },
}

export default function Orb({ variant = 'idle', size = 'lg' }: OrbProps) {
  const sz = SIZES[size]
  const glowColor = GLOW_COLORS[variant]
  const shadowColor = SHADOW_COLORS[variant]
  const gradient = GRADIENTS[variant]
  const animation = SPHERE_ANIMATIONS[variant]

  return (
    <div className={`relative flex items-center justify-center ${sz.container}`}>
      {/* Ping ring — only in listening mode */}
      {variant === 'listening' && (
        <span
          className="absolute rounded-full opacity-20 animate-ping-ring"
          style={{
            width: '110%',
            height: '110%',
            border: `1px solid ${glowColor}`,
          }}
        />
      )}

      {/* Concentric rings — analyzing mode */}
      {variant === 'analyzing' && (
        <>
          <span className="absolute rounded-full opacity-10 animate-pulse" style={{ width: '125%', height: '125%', border: '1px solid rgba(143,84,255,0.4)' }} />
          <span className="absolute rounded-full opacity-5 animate-pulse" style={{ width: '150%', height: '150%', border: '1px solid rgba(143,84,255,0.3)' }} />
        </>
      )}

      {/* Ambient glow behind orb — alert mode */}
      {variant === 'alert' && (
        <span
          className="absolute rounded-full blur-[60px] animate-pulse"
          style={{ width: '90%', height: '90%', background: 'rgba(217,70,239,0.3)' }}
        />
      )}

      {/* The sphere */}
      <div
        className={`${sz.sphere} rounded-full relative overflow-hidden orb-sphere ${animation}`}
        style={{
          background: gradient,
          backgroundSize: variant === 'alert' ? '200% 200%' : undefined,
          boxShadow: `
            inset -10px -10px 20px rgba(0,0,0,0.3),
            inset 10px 10px 20px rgba(255,255,255,0.35),
            0 0 40px ${glowColor},
            0 0 80px ${shadowColor}
          `,
        }}
      >
        {/* Top-left highlight */}
        <div
          className="absolute rounded-full blur-md"
          style={{
            top: '12%',
            left: '12%',
            width: '35%',
            height: '20%',
            background: 'rgba(255,255,255,0.55)',
            transform: 'rotate(-30deg)',
          }}
        />

        {/* Eyes container */}
        <div className={`absolute inset-0 flex items-center justify-center ${sz.gap}`}>
          <div
            className={`${sz.eye} bg-white rounded-full eye-glow animate-blink`}
            style={{ transformOrigin: 'center' }}
          />
          <div
            className={`${sz.eye} bg-white rounded-full eye-glow animate-blink`}
            style={{ transformOrigin: 'center', animationDelay: '0.15s' }}
          />
        </div>

        {/* Bottom inner shadow for depth */}
        <div
          className="absolute inset-x-0 bottom-0 rounded-b-full"
          style={{ height: '40%', background: 'linear-gradient(to top, rgba(0,0,0,0.2), transparent)' }}
        />
      </div>

      {/* Ground shadow */}
      <div
        className="absolute -bottom-4 rounded-full blur-xl opacity-40"
        style={{
          width: '60%',
          height: '14px',
          background: `radial-gradient(ellipse at center, ${glowColor} 0%, transparent 70%)`,
        }}
      />
    </div>
  )
}
