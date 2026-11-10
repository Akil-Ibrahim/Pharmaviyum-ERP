import { beforeEach, describe, expect, it } from 'vitest'
import { render } from 'vitest-browser-react'
import { userEvent } from 'vitest/browser'
import { clearCookies } from '@/test-utils/cookies'
import { getCookie } from '@/lib/cookies'
import { ThemeProvider, useTheme } from './theme-provider'

function NavigationColorProbe() {
  const { navigationIconColor, setNavigationIconColor } = useTheme()

  return (
    <div>
      <span>{navigationIconColor}</span>
      <button onClick={() => setNavigationIconColor('emerald')}>
        Select emerald
      </button>
    </div>
  )
}

describe('ThemeProvider navigation icon color', () => {
  beforeEach(() => {
    clearCookies()
  })

  it('keeps navigation icon color independent and persists the selected value', async () => {
    const screen = await render(
      <ThemeProvider>
        <NavigationColorProbe />
      </ThemeProvider>
    )

    await expect.element(screen.getByText('blue')).toBeInTheDocument()
    await userEvent.click(
      screen.getByRole('button', { name: 'Select emerald' })
    )

    await expect.element(screen.getByText('emerald')).toBeInTheDocument()
    expect(getCookie('pharmaviyum-navigation-icon-color')).toBe('emerald')
  })
})
