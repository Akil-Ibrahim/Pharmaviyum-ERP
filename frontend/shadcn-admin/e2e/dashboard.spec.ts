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

    const result = {
      schemaVersion: '1.0',
      runId: `${process.env.GITHUB_RUN_ID ?? 'local'}:${testInfo.project.name}:${testInfo.testId}:retry-${testInfo.retry}`,
      scenarioId: 'dashboard.unauthenticated-access',
      testId: testInfo.testId,
      title: testInfo.title,
      status: testInfo.status ?? 'unknown',
      expectedStatus: testInfo.expectedStatus,
      retry: testInfo.retry,
      durationMs: testInfo.duration,
      finalUrl: page.url(),
      evidence,
    }

    await testInfo.attach('agentic-test-result.json', {
      body: Buffer.from(JSON.stringify(result, null, 2)),
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
