import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Avatar from './Avatar'

describe('Avatar', () => {
  it('renders initials for a two-word name', () => {
    render(<Avatar name="John Smith" />)
    expect(screen.getByText('JS')).toBeTruthy()
  })

  it('renders single initial for a one-word name', () => {
    render(<Avatar name="Alice" />)
    expect(screen.getByText('A')).toBeTruthy()
  })

  it('only uses the first two words for initials', () => {
    render(<Avatar name="Maria Angela Rodriguez" />)
    expect(screen.getByText('MA')).toBeTruthy()
  })

  it('renders uppercase initials regardless of input case', () => {
    render(<Avatar name="john doe" />)
    expect(screen.getByText('JD')).toBeTruthy()
  })

  it('applies sm size classes', () => {
    const { container } = render(<Avatar name="AB" size="sm" />)
    expect((container.firstChild as HTMLElement).className).toContain('w-9')
  })

  it('applies md size classes (default)', () => {
    const { container } = render(<Avatar name="AB" />)
    expect((container.firstChild as HTMLElement).className).toContain('w-12')
  })

  it('applies lg size classes', () => {
    const { container } = render(<Avatar name="AB" size="lg" />)
    expect((container.firstChild as HTMLElement).className).toContain('w-14')
  })

  it('assigns a deterministic colour based on first char', () => {
    const { container: c1 } = render(<Avatar name="Alice" />)
    const { container: c2 } = render(<Avatar name="Alice" />)
    const cls1 = (c1.firstChild as HTMLElement).className
    const cls2 = (c2.firstChild as HTMLElement).className
    // Same name → same colour classes
    expect(cls1).toBe(cls2)
  })

  it('assigns different colours for names that hash differently', () => {
    // 'A' (65) % 5 = 0 → bg-blue-50; 'E' (69) % 5 = 4 → bg-amber-50
    const { container: cA } = render(<Avatar name="Alice" />)
    const { container: cE } = render(<Avatar name="Eve" />)
    const clsA = (cA.firstChild as HTMLElement).className
    const clsE = (cE.firstChild as HTMLElement).className
    expect(clsA).not.toBe(clsE)
  })
})
