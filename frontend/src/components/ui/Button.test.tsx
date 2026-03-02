import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Button from './Button'

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeTruthy()
  })

  it('calls onClick when clicked', () => {
    const handler = vi.fn()
    render(<Button onClick={handler}>Click</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(handler).toHaveBeenCalledOnce()
  })

  it('does not call onClick when disabled', () => {
    const handler = vi.fn()
    render(<Button onClick={handler} disabled>Click</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(handler).not.toHaveBeenCalled()
  })

  it('applies primary variant classes by default', () => {
    render(<Button>Primary</Button>)
    const btn = screen.getByRole('button')
    expect(btn.className).toContain('bg-primary')
  })

  it('applies secondary variant classes', () => {
    render(<Button variant="secondary">Sec</Button>)
    const btn = screen.getByRole('button')
    expect(btn.className).toContain('bg-white')
    expect(btn.className).toContain('border-gray-200')
  })

  it('applies danger variant classes', () => {
    render(<Button variant="danger">Danger</Button>)
    expect(screen.getByRole('button').className).toContain('text-red-500')
  })

  it('applies warning variant classes', () => {
    render(<Button variant="warning">Warning</Button>)
    expect(screen.getByRole('button').className).toContain('from-warning')
  })

  it('applies ghost variant classes', () => {
    render(<Button variant="ghost">Ghost</Button>)
    expect(screen.getByRole('button').className).toContain('text-text-sub')
  })

  it('applies sm size classes', () => {
    render(<Button size="sm">Sm</Button>)
    expect(screen.getByRole('button').className).toContain('rounded-2xl')
  })

  it('applies lg size classes', () => {
    render(<Button size="lg">Lg</Button>)
    expect(screen.getByRole('button').className).toContain('rounded-3xl')
  })

  it('applies w-full when fullWidth=true', () => {
    render(<Button fullWidth>Full</Button>)
    expect(screen.getByRole('button').className).toContain('w-full')
  })

  it('passes extra className prop', () => {
    render(<Button className="px-10">Extra</Button>)
    expect(screen.getByRole('button').className).toContain('px-10')
  })

  it('forwards additional HTML button props (type, aria-label)', () => {
    render(<Button type="submit" aria-label="submit-btn">Submit</Button>)
    const btn = screen.getByRole('button')
    expect(btn.getAttribute('type')).toBe('submit')
    expect(btn.getAttribute('aria-label')).toBe('submit-btn')
  })
})
