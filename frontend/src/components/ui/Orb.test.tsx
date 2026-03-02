import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import Orb from './Orb'

describe('Orb', () => {
  it('renders without crashing in idle (default) variant', () => {
    const { container } = render(<Orb />)
    expect(container.firstChild).toBeTruthy()
  })

  it('renders listening variant — ping ring must appear', () => {
    const { container } = render(<Orb variant="listening" />)
    // The ping ring is a <span> with animate-ping-ring class
    const pingRing = container.querySelector('.animate-ping-ring')
    expect(pingRing).toBeTruthy()
  })

  it('does NOT render ping ring for non-listening variants', () => {
    const { container } = render(<Orb variant="idle" />)
    expect(container.querySelector('.animate-ping-ring')).toBeNull()
  })

  it('renders analyzing variant — concentric rings must appear', () => {
    const { container } = render(<Orb variant="analyzing" />)
    // The two concentric rings both have animate-pulse class
    const pulsingRings = container.querySelectorAll('.animate-pulse')
    expect(pulsingRings.length).toBeGreaterThanOrEqual(2)
  })

  it('renders alert variant without ping ring but with animated ambient glow', () => {
    const { container } = render(<Orb variant="alert" />)
    expect(container.querySelector('.animate-ping-ring')).toBeNull()
    // Ambient glow has animate-pulse
    const glowEl = container.querySelector('.blur-\\[60px\\]')
    expect(glowEl).toBeTruthy()
  })

  it('applies gradient-shift animation class in alert variant', () => {
    const { container } = render(<Orb variant="alert" />)
    // animate-gradient-shift is on the sphere element
    const sphere = container.querySelector('.animate-gradient-shift')
    expect(sphere).toBeTruthy()
  })

  it('applies correct size class for sm', () => {
    const { container } = render(<Orb size="sm" />)
    const outerDiv = container.firstChild as HTMLElement
    expect(outerDiv.className).toContain('w-16')
  })

  it('applies correct size class for md', () => {
    const { container } = render(<Orb size="md" />)
    const outerDiv = container.firstChild as HTMLElement
    expect(outerDiv.className).toContain('w-48')
  })

  it('applies correct size class for lg (default)', () => {
    const { container } = render(<Orb />)
    const outerDiv = container.firstChild as HTMLElement
    expect(outerDiv.className).toContain('w-56')
  })

  it('renders two eye elements (animate-blink)', () => {
    const { container } = render(<Orb />)
    const eyes = container.querySelectorAll('.animate-blink')
    expect(eyes).toHaveLength(2)
  })
})
