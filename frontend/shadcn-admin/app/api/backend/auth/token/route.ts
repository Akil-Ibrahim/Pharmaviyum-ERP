/**
 * Frontend proxy for backend auth token endpoint
 * Forwards requests from browser to backend API
 */

// Use Docker service name 'backend' for internal requests
const BACKEND_URL = 'http://backend:8000';

export async function POST(request: Request) {
  try {
    // Parse form data from request
    const body = await request.text();
    
    console.log(`[Auth Proxy] Forwarding to: ${BACKEND_URL}/api/v1/auth/token`);
    
    // Forward to backend auth endpoint
    const response = await fetch(`${BACKEND_URL}/api/v1/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body,
    });

    console.log(`[Auth Proxy] Backend response status: ${response.status}`);

    // Return backend response
    const data = await response.json();
    return new Response(JSON.stringify(data), {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    console.error('[Auth Proxy] Error:', error);
    return new Response(
      JSON.stringify({ detail: 'Failed to authenticate' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}
