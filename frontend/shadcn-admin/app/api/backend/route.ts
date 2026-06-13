/**
 * Backend proxy route
 * Forwards requests from frontend to backend API
 * Useful for CORS handling and server-side proxying
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const path = url.searchParams.get('path') || '';

  try {
    const response = await fetch(`${BACKEND_URL}${path}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Backend request failed', details: String(error) },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const path = url.searchParams.get('path') || '';
  const contentType = request.headers.get('content-type') || '';
  let body: any = {};

  if (contentType.includes('application/json')) {
    body = await request.json().catch(() => ({}));
  } else if (contentType.includes('application/x-www-form-urlencoded')) {
    const text = await request.text();
    body = Object.fromEntries(new URLSearchParams(text));
  }

  try {
    const response = await fetch(`${BACKEND_URL}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': contentType || 'application/json',
      },
      body: contentType.includes('application/json')
        ? JSON.stringify(body)
        : new URLSearchParams(body),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Backend request failed', details: String(error) },
      { status: 500 }
    );
  }
}
