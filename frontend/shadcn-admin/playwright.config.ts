import { defineConfig, devices } from '@playwright/test'

const isCI = Boolean(process.env.CI)
const externalBaseURL = process.env.PLAYWRIGHT_BASE_URL
const baseURL = externalBaseURL ?? 'http://127.0.0.1:4173'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  workers: isCI ? 1 : undefined,
  reporter: isCI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile-chromium',
      use: { ...devices['Pixel 5'] },
    },
  ],
  webServer: externalBaseURL
    ? undefined
    : {
        command:
          'bun run dev -- --host 127.0.0.1 --port 4173 --strictPort',
        url: baseURL,
        reuseExistingServer: !isCI,
        timeout: 120_000,
      },
})
