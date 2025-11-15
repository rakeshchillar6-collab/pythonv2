// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // 1. Get theme and variant from cookies or headers
  let theme = request.cookies.get('theme')?.value || 'studio-classic';
  let variant = request.cookies.get('variant')?.value || 'light';
  let locale = request.cookies.get('locale')?.value || 'fa';

  // 2. Clone the request headers to be able to set new ones
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-theme', theme);
  requestHeaders.set('x-variant', variant);
  requestHeaders.set('x-locale', locale);

  // 3. Create a new response and set cookies if they weren't present
  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });

  if (!request.cookies.has('theme')) {
    response.cookies.set('theme', theme);
  }
  if (!request.cookies.has('variant')) {
    response.cookies.set('variant', variant);
  }
  if (!request.cookies.has('locale')) {
    response.cookies.set('locale', locale);
  }

  return response;
}
