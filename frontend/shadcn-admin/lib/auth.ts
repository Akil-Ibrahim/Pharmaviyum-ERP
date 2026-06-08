import { db } from "@/db";
import * as schema from "@/db/schema";
import { generateRandomUUID } from "@/lib/generate-random-uuid";
import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";

// Initialize `auth` lazily and provide a safe stub when configuration is
// missing (so the dev frontend doesn't crash when DB or auth server isn't
// configured). This follows best-practice: fail-safe defaults in dev and
// explicit errors when attempting real operations.
let _auth: any = null;

function createRealAuth() {
  return betterAuth({
    baseURL: process.env.BETTER_AUTH_URL!,
    trustedOrigins: [process.env.BETTER_AUTH_URL!],
    database: drizzleAdapter(db, {
      provider: "pg",
      schema,
    }),
    emailAndPassword: {
      enabled: true,
      requireEmailVerification: false,
    },
    socialProviders: {
      github: {
        clientId: process.env.GITHUB_CLIENT_ID!,
        clientSecret: process.env.GITHUB_CLIENT_SECRET!,
      },
      google: {
        clientId: process.env.GOOGLE_CLIENT_ID!,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
        prompt: "select_account",
      },
    },
    advanced: {
      database: {
        generateId: generateRandomUUID,
      },
    },
  });
}

function createStubAuth() {
  const stub = {
    api: {
      async getSession() {
        // In dev without auth configured, behave like unauthenticated.
        return null;
      },
      async createSession() {
        throw new Error("Auth is not configured in this environment.");
      },
    },
    // Other helper methods can be added as needed.
  };
  return stub;
}

if (process.env.BETTER_AUTH_URL && process.env.DATABASE_URL) {
  try {
    _auth = createRealAuth();
  } catch (e) {
    // If real initialization fails, fall back to stub and log a warning.
    // Avoid throwing during module eval to keep dev server running.
    // eslint-disable-next-line no-console
    console.warn("better-auth initialization failed, using stub:", e);
    _auth = createStubAuth();
  }
} else {
  _auth = createStubAuth();
}

export const auth = _auth;
