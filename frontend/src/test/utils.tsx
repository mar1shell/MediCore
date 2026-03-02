import { render, type RenderOptions } from '@testing-library/react'
import { MemoryRouter, type MemoryRouterProps } from 'react-router-dom'
import { SessionProvider } from '../context/SessionContext'
import type { ReactElement, ReactNode } from 'react'

interface WrapperOptions {
  routerProps?: MemoryRouterProps
}

function Providers({
  children,
  routerProps,
}: {
  children: ReactNode
  routerProps?: MemoryRouterProps
}) {
  return (
    <MemoryRouter {...routerProps}>
      <SessionProvider>{children}</SessionProvider>
    </MemoryRouter>
  )
}

export function renderWithProviders(
  ui: ReactElement,
  { routerProps, ...renderOptions }: WrapperOptions & RenderOptions = {},
) {
  return render(ui, {
    wrapper: ({ children }) => (
      <Providers routerProps={routerProps}>{children}</Providers>
    ),
    ...renderOptions,
  })
}
