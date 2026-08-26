import { createBrowserClient } from '@supabase/ssr';

/**
 * Creates and returns a Supabase client for Client Components.
 * Handles missing environment variables gracefully.
 */
export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

  if (!supabaseUrl || !supabaseAnonKey) {
    if (process.env.NODE_ENV === 'development') {
      console.warn(
        '⚠️ Supabase URL or Anon Key is missing. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.'
      );
    }
  }

  return createBrowserClient(supabaseUrl, supabaseAnonKey);
}
