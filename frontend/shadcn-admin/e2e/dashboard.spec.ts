import { expect, test } from '@playwright/test'

test.describe('Dashboard access control', () => {
  test('redirects unauthenticated visitors to sign-in', async ({ page }) => {
    await page.goto('/')

    await expect(page).toHaveURL(/\/sign-in(?:\?.*)?$/)
    await expect(page.getByText('Sign in to Pharmaviyum')).toBeVisible()
  })
})
