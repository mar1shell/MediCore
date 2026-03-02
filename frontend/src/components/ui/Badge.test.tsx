import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Badge from './Badge'

describe('Badge', () => {
  it('renders its children', () => {
    render(<Badge>Active</Badge>)
    expect(screen.getByText('Active')).toBeTruthy()
  })

  it('applies active styles by default', () => {
    const { container } = render(<Badge>Active</Badge>)
    expect((container.firstChild as HTMLElement).className).toContain('bg-green-100')
  })

  it('applies followup variant styles', () => {
    const { container } = render(<Badge variant="followup">Follow-Up</Badge>)
    expect((container.firstChild as HTMLElement).className).toContain('bg-purple-50')
  })

  it('applies action variant styles', () => {
    const { container } = render(<Badge variant="action">Action Required</Badge>)
    expect((container.firstChild as HTMLElement).className).toContain('bg-warning/10')
  })

  it('applies conflict variant styles', () => {
    const { container } = render(<Badge variant="conflict">Conflict</Badge>)
    expect((container.firstChild as HTMLElement).className).toContain('bg-red-50')
  })

  it('applies source variant styles', () => {
    const { container } = render(<Badge variant="source">Source</Badge>)
    expect((container.firstChild as HTMLElement).className).toContain('bg-gray-100')
  })

  it('renders as an inline-flex span', () => {
    render(<Badge>Test</Badge>)
    const el = screen.getByText('Test')
    expect(el.tagName.toLowerCase()).toBe('span')
    expect(el.className).toContain('inline-flex')
  })
})
