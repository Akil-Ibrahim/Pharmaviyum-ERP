/**
 * E2E tests for Patient Management
 */
import { test, expect } from '@playwright/test';

test.describe('Patients Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'pharmacist@test.com');
    await page.fill('input[name="password"]', 'testpassword123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });
  
  test('should create new patient', async ({ page }) => {
    await page.goto('/patients');
    await page.click('button:has-text("Add Patient")');
    
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="phone"]', '+84912345678');
    
    await page.click('button[type="submit"]');
    await expect(page.locator('tbody')).toContainText('John Doe');
  });
});
