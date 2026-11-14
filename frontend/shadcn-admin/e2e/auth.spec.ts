import { expect, test } from '@playwright/test'

test.describe('Active shadcn-admin authentication', () => {
  test('renders the sign-in screen and accessible fields', async ({ page }) => {
    await page.goto('/sign-in')

    await expect(page.getByText('Sign in to Pharmaviyum')).toBeVisible()
    await expect(page.getByLabel('Login')).toBeVisible()
    await expect(page.getByLabel('Password')).toBeVisible()
    await expect(
      page.getByRole('link', { name: 'Forgot password?' })
    ).toHaveAttribute('href', '/forgot-password')
  })

  test('validates required login fields', async ({ page }) => {
    await page.goto('/sign-in')
    await page.getByRole('button', { name: 'Sign in' }).click()

    await expect(
      page.getByText('Please enter your username or email.')
    ).toBeVisible()
    await expect(page.getByText('Please enter your password.')).toBeVisible()
  })

  test('shows authentication API errors without leaving sign-in', async ({
    page,
  }) => {
    await page.route('**/api/v1/auth/token', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid credentials' }),
      })
    })

    await page.goto('/sign-in')
    await page.getByLabel('Login').fill('pharmacist@example.test')
    await page.getByLabel('Password').fill('incorrect-password')
    await page.getByRole('button', { name: 'Sign in' }).click()

    await expect(page.getByText('Invalid credentials')).toBeVisible()
    await expect(page).toHaveURL(/\/sign-in$/)
  })

  test('renders the forgot-password screen and validates email', async ({
    page,
  }) => {
    await page.goto('/forgot-password')

    await expect(page.getByText('Forgot Password')).toBeVisible()
    await page.getByRole('button', { name: 'Continue' }).click()
    await expect(page.getByText('Please enter your email.')).toBeVisible()
  })
})
