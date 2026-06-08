/**
 * Auth library - now using FastAPI JWT backend instead of Better Auth
 * Frontend communicates with FastAPI /api/v1/auth/token endpoint
 */

// Placeholder export for compatibility
// Real auth is handled in lib/api.ts and contexts/auth-context.tsx
export const auth = {
  api: {
    async getSession() {
      return null;
    },
  },
};
