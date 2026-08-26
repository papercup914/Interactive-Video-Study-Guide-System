'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/utils/supabase/client';
import { User as UserIcon, LogOut, Loader2 } from 'lucide-react';
import type { User } from '@supabase/supabase-js';

export function AuthStatusWidget() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const supabase = createClient();

    const fetchUser = async () => {
      try {
        const { data, error } = await supabase.auth.getUser();
        if (isMounted) {
          if (!error && data?.user) {
            setUser(data.user);
          } else {
            setUser(null);
          }
        }
      } catch (err) {
        console.error('Failed to get auth user:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchUser();

    const { data: authListener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        if (isMounted) {
          setUser(session?.user ?? null);
          setLoading(false);
        }
      }
    );

    return () => {
      isMounted = false;
      authListener?.subscription.unsubscribe();
    };
  }, []);

  const handleLogout = async () => {
    try {
      setLoggingOut(true);
      const supabase = createClient();
      await supabase.auth.signOut();
      router.push('/login');
      router.refresh();
    } catch (err) {
      console.error('Failed to log out:', err);
    } finally {
      setLoggingOut(false);
    }
  };

  if (loading) {
    return (
      <div className="h-9 w-9 flex items-center justify-center rounded-xl bg-slate-800/50 text-slate-400">
        <Loader2 className="w-4 h-4 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const email = user.email || 'User';
  const displayName = user.user_metadata?.full_name || user.user_metadata?.name || email.split('@')[0];
  const avatarUrl = user.user_metadata?.avatar_url;

  return (
    <div className="flex items-center gap-2 pl-2 border-l border-slate-800/80">
      <div className="flex items-center gap-2 py-1 px-2 rounded-xl bg-slate-800/60 border border-slate-700/50 text-xs text-slate-200">
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt={displayName}
            className="w-5 h-5 rounded-full object-cover border border-slate-600"
          />
        ) : (
          <div className="w-5 h-5 rounded-full bg-indigo-600/30 text-indigo-400 flex items-center justify-center">
            <UserIcon className="w-3 h-3" />
          </div>
        )}
        <span className="hidden sm:inline font-medium max-w-[120px] truncate">
          {displayName}
        </span>
      </div>

      <button
        onClick={handleLogout}
        disabled={loggingOut}
        title="로그아웃"
        className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-colors cursor-pointer"
      >
        {loggingOut ? (
          <Loader2 className="w-4 h-4 animate-spin text-rose-400" />
        ) : (
          <LogOut className="w-4 h-4" />
        )}
      </button>
    </div>
  );
}
