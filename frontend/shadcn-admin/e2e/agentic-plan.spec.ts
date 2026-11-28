import { expect, test } from '@playwright/test'
import { executeAgenticPlan } from './support/agentic-plan'

test.describe('Agentic plan execution adapter', () => {
  test('executes a bounded same-origin plan and returns deterministic step results', async ({
    page,
  }, testInfo) => {
    await page.goto('/')

    const origin = new URL(page.url()).origin
    const scenario = {
      scenario_id: 'dashboard.sign-in-page',
      target_url: `${origin}/`,
    }
    const plan = {
      run_id: 'playwright-run-0001',
      scenario_id: scenario.scenario_id,
      target_origin: origin,
      execution_plan: [
        {
          step_index: 0,
          action: 'goto',
          value: '/sign-in',
          target_origin: origin,
        },
        {
          step_index: 1,
          action: 'expect_url',
          value: '/sign-in',
          target_origin: origin,
        },
        {
          step_index: 2,
          action: 'expect_visible',
          value: 'Sign in to Pharmaviyum',
          target_origin: origin,
        },
      ],
    }

    const result = await executeAgenticPlan(page, scenario, plan, [origin])
    if (result.status !== 'passed') {
      const screenshot = await page.screenshot({ fullPage: true })
      await testInfo.attach('agentic-failure.png', {
        body: screenshot,
        contentType: 'image/png',
      })
      const failedStep = result.steps.find((step) => step.status === 'failed')
      failedStep?.evidence_refs.push('attachment:agentic-failure.png')
    }
    await testInfo.attach('agentic-run-result.json', {
      body: Buffer.from(JSON.stringify(result, null, 2)),
      contentType: 'application/json',
    })

    expect(result.status, JSON.stringify(result)).toBe('passed')
    expect(result.steps.map((step) => step.status)).toEqual([
      'passed',
      'passed',
      'passed',
    ])
  })

  test('rejects an unapproved target before navigating', async ({ page }) => {
    await page.goto('/')
    const originalUrl = page.url()
    const scenario = {
      scenario_id: 'dashboard.external-target',
      target_url: 'https://example.com/',
    }
    const plan = {
      run_id: 'playwright-run-0002',
      scenario_id: scenario.scenario_id,
      target_origin: 'https://example.com',
      execution_plan: [
        {
          step_index: 0,
          action: 'goto',
          value: '/',
          target_origin: 'https://example.com',
        },
      ],
    }

    await expect(
      executeAgenticPlan(page, scenario, plan, [new URL(originalUrl).origin])
    ).rejects.toThrow('not in the configured test-origin allowlist')
    expect(page.url()).toBe(originalUrl)
  })

  test('rejects external navigation embedded in a plan', async ({ page }) => {
    await page.goto('/')
    const origin = new URL(page.url()).origin
    const scenario = {
      scenario_id: 'dashboard.external-step',
      target_url: `${origin}/`,
    }
    const plan = {
      run_id: 'playwright-run-0003',
      scenario_id: scenario.scenario_id,
      target_origin: origin,
      execution_plan: [
        {
          step_index: 0,
          action: 'goto',
          value: 'https://example.com/',
          target_origin: origin,
        },
      ],
    }

    await expect(
      executeAgenticPlan(page, scenario, plan, [origin])
    ).rejects.toThrow('same-origin absolute path')
  })

  test('rejects a plan that exceeds the bounded step count', async ({ page }) => {
    await page.goto('/')
    const origin = new URL(page.url()).origin
    const scenario = {
      scenario_id: 'dashboard.too-many-steps',
      target_url: `${origin}/`,
    }
    const plan = {
      run_id: 'playwright-run-0004',
      scenario_id: scenario.scenario_id,
      target_origin: origin,
      execution_plan: Array.from({ length: 9 }, (_, step_index) => ({
        step_index,
        action: 'expect_url',
        value: '/',
        target_origin: origin,
      })),
    }

    await expect(
      executeAgenticPlan(page, scenario, plan, [origin])
    ).rejects.toThrow('between 1 and 8 steps')
  })

  test('rejects credentials embedded in a scenario target URL', async ({ page }) => {
    await page.goto('/')
    const origin = new URL(page.url()).origin
    const scenario = {
      scenario_id: 'dashboard.credential-target',
      target_url: 'https://user:secret@example.com/',
    }
    const plan = {
      run_id: 'playwright-run-0005',
      scenario_id: scenario.scenario_id,
      target_origin: 'https://example.com',
      execution_plan: [
        {
          step_index: 0,
          action: 'goto',
          value: '/',
          target_origin: 'https://example.com',
        },
      ],
    }

    await expect(
      executeAgenticPlan(page, scenario, plan, [origin, 'https://example.com'])
    ).rejects.toThrow('must not contain credentials')
  })

})
