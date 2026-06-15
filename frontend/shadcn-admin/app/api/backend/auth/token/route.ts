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

    // Return backend response and set cookie so SSR can detect session
    const data = await response.json();

    // If backend returned access_token, set it as a cookie on the response
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (response.ok && data && data.access_token) {
      const token = data.access_token;
      // Set cookie for 24 hours; not HttpOnly because client code reads it
      headers['Set-Cookie'] = `auth_token=${token}; Path=/; Max-Age=86400`;
    }

    return new Response(JSON.stringify(data), {
      status: response.status,
      headers,
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
