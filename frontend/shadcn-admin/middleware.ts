import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Public routes that don't require authentication
  const publicRoutes = ["/sign-in", "/api/auth", "/api/backend"];
  const isPublicRoute =
    pathname === "/" ||
    publicRoutes.some((route) => pathname.startsWith(route));

  // Check if user has auth token in cookies (set after successful login)
  const authToken = request.cookies.get("auth_token")?.value;
  const hasSession = !!authToken;

  // Alias legacy dashboard path to the current dashboard route
  if (pathname === "/dashboard") {
    return NextResponse.redirect(new URL("/dashboard2", request.url));
  }

  // If accessing a protected route without a session, redirect to sign-in
  if (!isPublicRoute && !hasSession) {
    const signInUrl = new URL("/sign-in", request.url);
    signInUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(signInUrl);
  }

  // If accessing sign-in page while authenticated, redirect to dashboard
  if (pathname === "/sign-in" && hasSession) {
    return NextResponse.redirect(new URL("/dashboard2", request.url));
  }

  // If accessing root page while authenticated, redirect to dashboard
  if (pathname === "/" && hasSession) {
    return NextResponse.redirect(new URL("/dashboard2", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};

