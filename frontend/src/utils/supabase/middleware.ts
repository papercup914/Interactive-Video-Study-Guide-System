import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  });

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  // If Supabase credentials are missing or explicitly disabled, bypass authentication
  if (!supabaseUrl || !supabaseAnonKey || process.env.DISABLE_AUTH === 'true') {
    return supabaseResponse;
  }

  const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value, options }) =>
          request.cookies.set(name, value)
        );
        supabaseResponse = NextResponse.next({
          request,
        });
        cookiesToSet.forEach(({ name, value, options }) =>
          supabaseResponse.cookies.set(name, value, options)
        );
      },
    },
  });

  // IMPORTANT: Do not run code between createServerClient and
  // supabase.auth.getUser(). A simple mistake could make it very hard to debug
  // issues with users being randomly logged out.
  let user = null;
  try {
    const { data, error } = await supabase.auth.getUser();
    if (!error && data?.user) {
      user = data.user;
    }
  } catch (err) {
    console.error('Failed to get Supabase user in middleware:', err);
  }

  const pathname = request.nextUrl.pathname;
  const isLoginPage = pathname === '/login';
  const isAuthCallback = pathname.startsWith('/auth/callback');
  const isApiRoute = pathname.startsWith('/api/');

  // 백엔드 API 라우트는 FastAPI가 자체적으로 게스트/인증을 처리하므로 미들웨어에서 401로 차단하지 않고 통과
  if (isApiRoute) {
    return supabaseResponse;
  }

  // If user is NOT logged in and not accessing public/login pages
  if (!user && !isLoginPage && !isAuthCallback) {
    const url = request.nextUrl.clone();
    url.pathname = '/login';
    if (pathname !== '/') {
      url.searchParams.set('redirectTo', pathname);
    }
    return NextResponse.redirect(url);
  }

  // If user IS logged in and trying to access /login, redirect to /
  if (user && isLoginPage) {
    const redirectTo = request.nextUrl.searchParams.get('redirectTo') || '/';
    const url = request.nextUrl.clone();
    url.pathname = redirectTo;
    url.searchParams.delete('redirectTo');
    return NextResponse.redirect(url);
  }

  return supabaseResponse;
}
