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
  // Minimal stub that provides the same surface as `betterAuth` so callers
  // (middleware, routes) don't crash during local development when auth is
  // not configured. Important: keep `api.getSession()` returning `null` so
  // the app behaves unauthenticated by default.
  const stub = {
    api: {
      async getSession() {
        return null;
      },
      async createSession() {
        throw new Error("Auth is not configured in this environment.");
      },
    },
    // A handler property is expected by `toNextJsHandler(auth.handler)`.
    // Provide a simple handler that returns a 501 JSON response. This makes
    // `/api/auth/*` routes return a clear message instead of crashing.
    handler: async (request: any) => {
      // Lazily import NextResponse to avoid bundling server-only code in
      // environments where it's not available.
      try {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const { NextResponse } = require("next/server");
        return NextResponse.json(
          { error: "Auth not configured in this environment" },
          { status: 501 }
        );
      } catch (e) {
        // If NextResponse isn't available, return a minimal object.
        return {
          status: 501,
          json: async () => ({ error: "Auth not configured in this environment" }),
        };
      }
    },
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
