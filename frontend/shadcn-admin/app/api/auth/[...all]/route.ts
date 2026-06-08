/**
 * Auth API route - not used with FastAPI JWT backend
 * Kept for compatibility, returns 501 Not Implemented
 */

import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json(
    { error: "Auth is handled by FastAPI backend" },
    { status: 501 }
  );
}

export async function POST() {
  return NextResponse.json(
    { error: "Auth is handled by FastAPI backend" },
    { status: 501 }
  );
}
