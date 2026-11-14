# Active frontend end-to-end tests

The active frontend is `frontend/shadcn-admin`. Playwright Test configuration and browser-level end-to-end tests live with that application rather than the legacy `frontend/e2e` tree.

## Run locally

```bash
cd frontend/shadcn-admin
bun install --frozen-lockfile
bunx playwright install chromium
bun run test:e2e
```

The suite builds the active frontend and starts its Vite preview server automatically on `127.0.0.1:4173`. Set `PLAYWRIGHT_BASE_URL` only when testing an already-running application at a different origin.

## Coverage

- Sign-in screen rendering and accessible controls
- Required credential validation
- Authentication API error handling using a mocked API response
- Forgot-password screen rendering and email validation
- Chromium desktop and Pixel 5 mobile emulation

Tests do not use production credentials or call the production API. Network-dependent authentication requests are intercepted by Playwright.

CI installs the Chromium browser and runs the active frontend E2E suite after the production build.
