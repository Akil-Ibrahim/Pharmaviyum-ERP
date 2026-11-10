import { clearCookies } from '@/test-utils/cookies'
import { beforeEach, describe, expect, it } from 'vitest'
import { render } from 'vitest-browser-react'
import { userEvent } from 'vitest/browser'
import { getCookie } from '@/lib/cookies'
import {
  getNavIconColorValue,
  ThemeProvider,
  useTheme,
} from './theme-provider'

function NavigationColorProbe() {
  const { navigationIconColor, setNavigationIconColor } = useTheme()

  return (
    <div>
      <span>{navigationIconColor}</span>
      <button onClick={() => setNavigationIconColor('emerald')}>
        Select emerald
      </button>
      <button onClick={() => setNavigationIconColor('#123456')}>
        Select custom HEX
      </button>
    </div>
  )
}

describe('ThemeProvider navigation icon color', () => {
  beforeEach(() => {
    clearCookies()
  })

  it('keeps preset navigation icon color independent and persists the selected value', async () => {
    const screen = await render(
      <ThemeProvider>
        <NavigationColorProbe />
      </ThemeProvider>
    )

    await expect
      .element(screen.getByText('blue', { exact: true }))
      .toBeInTheDocument()
    await userEvent.click(
      screen.getByRole('button', { name: 'Select emerald' })
    )

    await expect
      .element(screen.getByText('emerald', { exact: true }))
      .toBeInTheDocument()
    expect(getCookie('pharmaviyum-navigation-icon-color')).toBe('emerald')
  })

  it('persists a custom HEX navigation icon color', async () => {
    const screen = await render(
      <ThemeProvider>
        <NavigationColorProbe />
      </ThemeProvider>
    )

    await userEvent.click(
      screen.getByRole('button', { name: 'Select custom HEX' })
    )

    await expect
      .element(screen.getByText('#123456', { exact: true }))
      .toBeInTheDocument()
    expect(getCookie('pharmaviyum-navigation-icon-color')).toBe('#123456')
    expect(getNavIconColorValue('#123456')).toBe('#123456')
  })

  it('resolves a named preset to its color value', () => {
    expect(getNavIconColorValue('emerald')).toBe('#059669')
  })
})
