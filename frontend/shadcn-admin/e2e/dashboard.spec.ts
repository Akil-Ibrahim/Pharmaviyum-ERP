import { expect, test } from '@playwright/test'

type BrowserEvidence = {
  consoleErrors: string[]
  pageErrors: string[]
  failedRequests: string[]
}

const testWithEvidence = test.extend({
  page: async ({ page }, use, testInfo) => {
    const evidence: BrowserEvidence = {
      consoleErrors: [],
      pageErrors: [],
      failedRequests: [],
    }

    page.on('console', (message) => {
      if (message.type() === 'error') {
        evidence.consoleErrors.push(message.text())
      }
    })
    page.on('pageerror', (error) => {
      evidence.pageErrors.push(error.message)
    })
    page.on('requestfailed', (request) => {
      evidence.failedRequests.push(
        `${request.method()} ${request.url()}: ${request.failure()?.errorText ?? 'request failed'}`
      )
    })

    await use(page)

    await testInfo.attach('browser-evidence.json', {
      body: Buffer.from(JSON.stringify(evidence, null, 2)),
      contentType: 'application/json',
    })
  },
})

testWithEvidence.describe('Dashboard access control', () => {
  testWithEvidence('redirects unauthenticated visitors to sign-in', async ({
    page,
  }) => {
    await page.goto('/')

    await expect(page).toHaveURL(/\/sign-in(?:\?.*)?$/)
    await expect(page.getByText('Sign in to Pharmaviyum')).toBeVisible()
    await expect(page.getByRole('textbox', { name: 'Login' })).toBeVisible()
    await expect(page.getByRole('textbox', { name: 'Password' })).toBeVisible()
  })
})
