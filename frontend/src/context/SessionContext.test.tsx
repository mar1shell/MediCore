import { describe, it, expect } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { SessionProvider, useSession } from './SessionContext'
import { MOCK_ENTITIES, MOCK_SESSION_ID, MOCK_SAFETY_CHECK_UNSAFE, MOCK_SAFETY_CHECK_SAFE } from '../test/fixtures'

// Helper component that exposes context values as data attributes for assertions
function ContextInspector() {
  const ctx = useSession()
  return (
    <div>
      <span data-testid="session-id">{ctx.sessionId ?? 'null'}</span>
      <span data-testid="diagnosis">{ctx.entities?.diagnosis ?? 'null'}</span>
      <span data-testid="safety-count">{ctx.safetyChecks.length}</span>
      <button onClick={() => ctx.setSession(MOCK_SESSION_ID, MOCK_ENTITIES)}>setSession</button>
      <button onClick={() => ctx.addSafetyCheck(MOCK_SAFETY_CHECK_UNSAFE)}>addSafety</button>
      <button onClick={() => ctx.setSafetyChecks([MOCK_SAFETY_CHECK_SAFE, MOCK_SAFETY_CHECK_UNSAFE])}>setSafetyChecks</button>
      <button onClick={() => ctx.clearSession()}>clear</button>
    </div>
  )
}

function renderInspector() {
  return render(
    <SessionProvider>
      <ContextInspector />
    </SessionProvider>,
  )
}

describe('SessionContext', () => {
  it('starts with empty state', () => {
    renderInspector()
    expect(screen.getByTestId('session-id').textContent).toBe('null')
    expect(screen.getByTestId('diagnosis').textContent).toBe('null')
    expect(screen.getByTestId('safety-count').textContent).toBe('0')
  })

  it('setSession stores sessionId and entities and resets safety checks', () => {
    renderInspector()

    // First add a safety check, then call setSession — it should reset
    act(() => screen.getByRole('button', { name: 'addSafety' }).click())
    expect(screen.getByTestId('safety-count').textContent).toBe('1')

    act(() => screen.getByRole('button', { name: 'setSession' }).click())
    expect(screen.getByTestId('session-id').textContent).toBe(MOCK_SESSION_ID)
    expect(screen.getByTestId('diagnosis').textContent).toBe('Upper Respiratory Infection')
    expect(screen.getByTestId('safety-count').textContent).toBe('0')
  })

  it('addSafetyCheck appends to the list', () => {
    renderInspector()

    act(() => screen.getByRole('button', { name: 'addSafety' }).click())
    act(() => screen.getByRole('button', { name: 'addSafety' }).click())
    expect(screen.getByTestId('safety-count').textContent).toBe('2')
  })

  it('setSafetyChecks replaces the list', () => {
    renderInspector()

    act(() => screen.getByRole('button', { name: 'addSafety' }).click())
    act(() => screen.getByRole('button', { name: 'setSafetyChecks' }).click())
    // setSafetyChecks sets [MOCK_SAFETY_CHECK_SAFE, MOCK_SAFETY_CHECK_UNSAFE] → 2 items
    expect(screen.getByTestId('safety-count').textContent).toBe('2')
  })

  it('clearSession resets all state', () => {
    renderInspector()

    act(() => screen.getByRole('button', { name: 'setSession' }).click())
    act(() => screen.getByRole('button', { name: 'addSafety' }).click())
    act(() => screen.getByRole('button', { name: 'clear' }).click())

    expect(screen.getByTestId('session-id').textContent).toBe('null')
    expect(screen.getByTestId('safety-count').textContent).toBe('0')
  })

  it('useSession throws when used outside provider', () => {
    const originalError = console.error
    console.error = () => {}
    expect(() => render(<ContextInspector />)).toThrow(
      'useSession must be used within SessionProvider',
    )
    console.error = originalError
  })
})
