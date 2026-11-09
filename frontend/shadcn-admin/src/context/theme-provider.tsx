import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { getCookie, setCookie, removeCookie } from '@/lib/cookies'

type Theme = 'dark' | 'light' | 'system'
export type ThemePreset =
  | 'default'
  | 'neutral'
  | 'stone'
  | 'zinc'
  | 'slate'
  | 'gray'
  | 'mauve'
  | 'olive'
  | 'mist'
  | 'taupe'
  | 'red'
  | 'orange'
  | 'amber'
  | 'yellow'
  | 'lime'
  | 'green'
  | 'emerald'
  | 'teal'
  | 'cyan'
  | 'sky'
  | 'blue'
  | 'indigo'
  | 'violet'
  | 'purple'
  | 'fuchsia'
  | 'pink'
  | 'rose'
export type NavigationIconColor =
  | 'blue'
  | 'slate'
  | 'green'
  | 'violet'
  | 'orange'
  | 'rose'
  | 'cyan'

export const NAVIGATION_ICON_COLORS: Record<NavigationIconColor, string> = {
  blue: '#2563eb',
  slate: '#64748b',
  green: '#16a34a',
  violet: '#7c3aed',
  orange: '#ea580c',
  rose: '#e11d48',
  cyan: '#0891b2',
}

type ResolvedTheme = Exclude<Theme, 'system'>

const DEFAULT_THEME = 'system'
const THEME_COOKIE_NAME = 'vite-ui-theme'
const PRESET_COOKIE_NAME = 'pharmaviyum-theme-preset'
const NAVIGATION_ICON_COLOR_COOKIE_NAME = 'pharmaviyum-navigation-icon-color'
const THEME_COOKIE_MAX_AGE = 60 * 60 * 24 * 365

type ThemeProviderProps = {
  children: React.ReactNode
  defaultTheme?: Theme
  storageKey?: string
}

type ThemeProviderState = {
  defaultTheme: Theme
  resolvedTheme: ResolvedTheme
  theme: Theme
  setTheme: (theme: Theme) => void
  resetTheme: () => void
  preset: ThemePreset
  setPreset: (preset: ThemePreset) => void
  navigationIconColor: NavigationIconColor
  setNavigationIconColor: (color: NavigationIconColor) => void
}

const initialState: ThemeProviderState = {
  defaultTheme: DEFAULT_THEME,
  resolvedTheme: 'light',
  theme: DEFAULT_THEME,
  setTheme: () => null,
  resetTheme: () => null,
  preset: 'blue',
  setPreset: () => null,
  navigationIconColor: 'blue',
  setNavigationIconColor: () => null,
}

const ThemeContext = createContext<ThemeProviderState>(initialState)

export function ThemeProvider({
  children,
  defaultTheme = DEFAULT_THEME,
  storageKey = THEME_COOKIE_NAME,
  ...props
}: ThemeProviderProps) {
  const [preset, _setPreset] = useState<ThemePreset>(() => {
    const savedPreset = getCookie(PRESET_COOKIE_NAME) as ThemePreset | null
    return savedPreset || 'blue'
  })
  const [navigationIconColor, _setNavigationIconColor] =
    useState<NavigationIconColor>(() => {
      const savedColor = getCookie(NAVIGATION_ICON_COLOR_COOKIE_NAME)
      return (savedColor as NavigationIconColor) || 'blue'
    })
  const [theme, _setTheme] = useState<Theme>(
    () => (getCookie(storageKey) as Theme) || defaultTheme
  )

  const resolvedTheme = useMemo((): ResolvedTheme => {
    if (theme === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
    }
    return theme as ResolvedTheme
  }, [theme])

  useEffect(() => {
    const root = window.document.documentElement
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

    const applyTheme = (currentResolvedTheme: ResolvedTheme) => {
      root.classList.remove('light', 'dark')
      root.classList.add(currentResolvedTheme)
      root.dataset.colorTheme = preset
    }

    const handleChange = () => {
      if (theme === 'system') {
        const systemTheme = mediaQuery.matches ? 'dark' : 'light'
        applyTheme(systemTheme)
      }
    }

    applyTheme(resolvedTheme)
    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [theme, resolvedTheme, preset])

  const setTheme = (theme: Theme) => {
    setCookie(storageKey, theme, THEME_COOKIE_MAX_AGE)
    _setTheme(theme)
  }

  const setPreset = (nextPreset: ThemePreset) => {
    setCookie(PRESET_COOKIE_NAME, nextPreset, THEME_COOKIE_MAX_AGE)
    _setPreset(nextPreset)
  }

  const setNavigationIconColor = (color: NavigationIconColor) => {
    setCookie(NAVIGATION_ICON_COLOR_COOKIE_NAME, color, THEME_COOKIE_MAX_AGE)
    _setNavigationIconColor(color)
  }

  const resetTheme = () => {
    removeCookie(storageKey)
    removeCookie(PRESET_COOKIE_NAME)
    removeCookie(NAVIGATION_ICON_COLOR_COOKIE_NAME)
    _setTheme(DEFAULT_THEME)
    _setPreset('blue')
    _setNavigationIconColor('blue')
  }

  const contextValue = {
    defaultTheme,
    resolvedTheme,
    resetTheme,
    theme,
    setTheme,
    preset,
    setPreset,
    navigationIconColor,
    setNavigationIconColor,
  }

  return (
    <ThemeContext value={contextValue} {...props}>
      {children}
    </ThemeContext>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within a ThemeProvider')
  return context
}
