import { expect, type Page } from '@playwright/test'

const MAX_STEPS = 8
const STEP_TIMEOUT_MS = 5_000
const NAVIGATION_TIMEOUT_MS = 10_000
const SCENARIO_ID_PATTERN = /^[a-z0-9][a-z0-9._-]{2,99}$/

export type AgenticAction = 'goto' | 'expect_url' | 'expect_visible'
export type AgenticStepStatus = 'passed' | 'failed' | 'skipped'
export type AgenticRunStatus = 'passed' | 'failed' | 'inconclusive'

export type AgenticScenarioInput = {
  scenario_id: string
  target_url: string
}

export type AgenticPlannedStep = {
  step_index: number
  action: AgenticAction
  value: string
  target_origin: string
}

export type AgenticPlanInput = {
  run_id: string
  scenario_id: string
  target_origin: string
  execution_plan: AgenticPlannedStep[]
}

export type AgenticStepResult = {
  step_index: number
  action: AgenticAction
  status: AgenticStepStatus
  duration_ms: number
  observed?: string
  error?: string
  evidence_refs: string[]
}

export type AgenticRunResult = {
  run_id: string
  scenario_id: string
  status: AgenticRunStatus
  started_at: string
  finished_at: string
  steps: AgenticStepResult[]
}

function assertRecord(value: unknown, label: string): asserts value is Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error(`${label} must be an object`)
  }
}

function normalizeOrigin(value: string): string {
  const url = new URL(value)
  if (!['http:', 'https:'].includes(url.protocol)) {
    throw new Error('Only HTTP(S) test origins are permitted')
  }
  if (url.username || url.password) {
    throw new Error('Test origins must not contain URL credentials')
  }
  if (url.pathname !== '/' || url.search || url.hash) {
    throw new Error('Allowed origins must not contain a path, query, or fragment')
  }
  return url.origin
}

function resolveSameOriginPath(value: string, origin: string): URL {
  if (!value.startsWith('/') || value.startsWith('//')) {
    throw new Error('Browser navigation and URL assertions require a same-origin absolute path')
  }
  const resolved = new URL(value, origin)
  if (resolved.origin !== origin) {
    throw new Error('Browser step resolved outside the approved test origin')
  }
  return resolved
}

function validateInputs(
  scenarioInput: unknown,
  planInput: unknown,
  allowedOrigins: readonly string[]
) {
  assertRecord(scenarioInput, 'Scenario')
  assertRecord(planInput, 'Execution plan')

  const scenarioId = scenarioInput.scenario_id
  const targetUrlValue = scenarioInput.target_url
  const runId = planInput.run_id
  const planScenarioId = planInput.scenario_id
  const targetOriginValue = planInput.target_origin
  const rawSteps = planInput.execution_plan

  if (typeof scenarioId !== 'string' || !SCENARIO_ID_PATTERN.test(scenarioId)) {
    throw new Error('Scenario identifier is invalid')
  }
  if (typeof targetUrlValue !== 'string') {
    throw new Error('Scenario target_url must be a string')
  }
  if (typeof runId !== 'string' || runId.length < 8 || runId.length > 100) {
    throw new Error('Run identifier is invalid')
  }
  if (planScenarioId !== scenarioId) {
    throw new Error('Execution plan scenario_id does not match the scenario')
  }
  if (typeof targetOriginValue !== 'string') {
    throw new Error('Execution plan target_origin must be a string')
  }
  if (!Array.isArray(rawSteps) || rawSteps.length < 1 || rawSteps.length > MAX_STEPS) {
    throw new Error(`Execution plan must contain between 1 and ${MAX_STEPS} steps`)
  }
  if (allowedOrigins.length === 0) {
    throw new Error('An explicit test-origin allowlist is required')
  }

  const targetUrl = new URL(targetUrlValue)
  if (targetUrl.username || targetUrl.password) {
    throw new Error('Scenario target URLs must not contain credentials')
  }
  const targetOrigin = normalizeOrigin(targetUrl.origin)
  const planOrigin = normalizeOrigin(targetOriginValue)
  const allowlist = new Set(allowedOrigins.map(normalizeOrigin))

  if (targetOrigin !== planOrigin || !allowlist.has(targetOrigin)) {
    throw new Error('Scenario target is not in the configured test-origin allowlist')
  }

  const steps = rawSteps.map((rawStep, index) => {
    assertRecord(rawStep, `Execution plan step ${index}`)
    const { step_index: stepIndex, action, value, target_origin: stepOrigin } = rawStep
    if (stepIndex !== index) {
      throw new Error('Execution plan step indexes must be contiguous and ordered')
    }
    if (!['goto', 'expect_url', 'expect_visible'].includes(String(action))) {
      throw new Error(`Execution plan step ${index} uses an unsupported action`)
    }
    if (typeof value !== 'string' || value.length < 1 || value.length > 2_048 || value !== value.trim()) {
      throw new Error(`Execution plan step ${index} has an invalid value`)
    }
    if (stepOrigin !== targetOrigin) {
      throw new Error(`Execution plan step ${index} has a mismatched target origin`)
    }
    if (action === 'goto' || action === 'expect_url') {
      resolveSameOriginPath(value, targetOrigin)
    }
    return {
      step_index: stepIndex,
      action: action as AgenticAction,
      value,
      target_origin: targetOrigin,
    }
  })

  return {
    runId,
    scenarioId,
    targetUrl,
    targetOrigin,
    steps,
  }
}

/**
 * Executes only the bounded action vocabulary emitted by the LangGraph planner.
 * The browser is restricted to one explicitly approved origin; no scripts,
 * arbitrary selectors, downloads, form submissions, or business-data writes run here.
 */
export async function executeAgenticPlan(
  page: Page,
  scenarioInput: unknown,
  planInput: unknown,
  allowedOrigins: readonly string[]
): Promise<AgenticRunResult> {
  const validated = validateInputs(scenarioInput, planInput, allowedOrigins)
  const startedAt = new Date()
  const results: AgenticStepResult[] = []

  page.setDefaultTimeout(STEP_TIMEOUT_MS)
  page.setDefaultNavigationTimeout(NAVIGATION_TIMEOUT_MS)

  // Enforce the origin boundary on main-frame navigations, including redirects
  // and navigations initiated by page scripts.
  await page.route('**/*', async (route) => {
    const request = route.request()
    if (request.isNavigationRequest() && request.frame() === page.mainFrame()) {
      if (new URL(request.url()).origin !== validated.targetOrigin) {
        await route.abort('blockedbyclient')
        return
      }
    }
    await route.continue()
  })

  for (const step of validated.steps) {
    const stepStartedAt = Date.now()
    try {
      if (step.action === 'goto') {
        const destination = resolveSameOriginPath(step.value, validated.targetOrigin)
        await page.goto(destination.toString(), { waitUntil: 'domcontentloaded' })
        if (new URL(page.url()).origin !== validated.targetOrigin) {
          throw new Error('Browser left the approved test origin after navigation')
        }
      } else if (step.action === 'expect_url') {
        const expected = resolveSameOriginPath(step.value, validated.targetOrigin)
        await expect(page).toHaveURL(
          (actual) =>
            actual.origin === validated.targetOrigin &&
            actual.pathname === expected.pathname &&
            actual.search === expected.search,
          { timeout: STEP_TIMEOUT_MS }
        )
      } else {
        await expect(page.getByText(step.value).first()).toBeVisible({
          timeout: STEP_TIMEOUT_MS,
        })
      }

      results.push({
        step_index: step.step_index,
        action: step.action,
        status: 'passed',
        duration_ms: Date.now() - stepStartedAt,
        observed: page.url(),
        evidence_refs: [],
      })
    } catch (error) {
      results.push({
        step_index: step.step_index,
        action: step.action,
        status: 'failed',
        duration_ms: Date.now() - stepStartedAt,
        observed: page.url(),
        error: error instanceof Error ? error.message.slice(0, 2_048) : 'Unknown browser step failure',
        evidence_refs: [],
      })
      break
    }
  }

  for (const step of validated.steps.slice(results.length)) {
    results.push({
      step_index: step.step_index,
      action: step.action,
      status: 'skipped',
      duration_ms: 0,
      error: 'Skipped after an earlier step failed',
      evidence_refs: [],
    })
  }

  const finishedAt = new Date()
  const status: AgenticRunStatus =
    results.some((step) => step.status === 'failed')
      ? 'failed'
      : results.length === 0 || results.some((step) => step.status === 'skipped')
        ? 'inconclusive'
        : 'passed'

  return {
    run_id: validated.runId,
    scenario_id: validated.scenarioId,
    status,
    started_at: startedAt.toISOString(),
    finished_at: finishedAt.toISOString(),
    steps: results,
  }
}
