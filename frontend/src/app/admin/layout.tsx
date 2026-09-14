"use client";

import React, { useState, useEffect, createContext, useContext } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Shield, 
  ShieldCheck, 
  KeyRound, 
  Eye, 
  EyeOff, 
  Activity, 
  Zap, 
  LayoutDashboard, 
  ArrowLeft, 
  Lock,
  Unlock,
  AlertCircle,
  Sliders
} from "lucide-react";

interface AdminAuthContextType {
  adminSecret: string;
  isAuthorized: boolean;
  logout: () => void;
  getAdminHeaders: () => Record<string, string>;
}

const AdminAuthContext = createContext<AdminAuthContextType>({
  adminSecret: "",
  isAuthorized: false,
  logout: () => {},
  getAdminHeaders: () => ({}),
});

export const useAdminAuth = () => useContext(AdminAuthContext);

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [adminSecret, setAdminSecret] = useState<string>("");
  const [inputSecret, setInputSecret] = useState<string>("");
  const [showSecret, setShowSecret] = useState<boolean>(false);
  const [isAuthorized, setIsAuthorized] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [isVerifying, setIsVerifying] = useState<boolean>(false);

  // 로컬스토리지에서 기존 키 확인
  useEffect(() => {
    try {
      const savedKey = localStorage.getItem("admin_secret_key");
      if (savedKey && savedKey.trim()) {
        verifySecretOnServer(savedKey.trim(), false);
      } else {
        setLoading(false);
      }
    } catch (e) {
      setLoading(false);
    }
  }, []);

  const verifySecretOnServer = async (keyToVerify: string, isManual: boolean) => {
    setIsVerifying(true);
    setErrorMsg("");
    try {
      const res = await fetch("/api/admin/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Secret": keyToVerify
        },
        body: JSON.stringify({ secret: keyToVerify })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.valid) {
          setAdminSecret(keyToVerify);
          setIsAuthorized(true);
          localStorage.setItem("admin_secret_key", keyToVerify);
        } else {
          setErrorMsg("패스코드가 일치하지 않습니다.");
          if (!isManual) {
            localStorage.removeItem("admin_secret_key");
          }
        }
      } else {
        // 서버 응답 오류인 경우에도 로컬 안전키와 기본 일치 검사 폴백
        if (keyToVerify === "studyguide-admin-2026") {
          setAdminSecret(keyToVerify);
          setIsAuthorized(true);
          localStorage.setItem("admin_secret_key", keyToVerify);
        } else {
          setErrorMsg("관리자 인증에 실패했습니다.");
        }
      }
    } catch (err: any) {
      // 오프라인이거나 개발 모드일 때 안전 폴백
      if (keyToVerify === "studyguide-admin-2026") {
        setAdminSecret(keyToVerify);
        setIsAuthorized(true);
        localStorage.setItem("admin_secret_key", keyToVerify);
      } else {
        setErrorMsg("인증 서버 통신 실패 또는 잘못된 패스코드입니다.");
      }
    } finally {
      setIsVerifying(false);
      setLoading(false);
    }
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputSecret.trim()) {
      setErrorMsg("관리자 패스코드를 입력해주세요.");
      return;
    }
    verifySecretOnServer(inputSecret.trim(), true);
  };

  const handleLogout = () => {
    localStorage.removeItem("admin_secret_key");
    setAdminSecret("");
    setInputSecret("");
    setIsAuthorized(false);
  };

  const getAdminHeaders = () => {
    return {
      "X-Admin-Secret": adminSecret || localStorage.getItem("admin_secret_key") || ""
    };
  };

  const navItems = [
    { href: "/admin", label: "관리자 허브", icon: LayoutDashboard, exact: true },
    { href: "/admin/batch", label: "일괄 사전 생성", icon: Zap },
    { href: "/admin/health", label: "시스템 상태 & 로그", icon: Activity },
    { href: "/admin/generation-config", label: "생성 매커니즘 제어", icon: Sliders },
  ];

  return (
    <AdminAuthContext.Provider value={{ adminSecret, isAuthorized, logout: handleLogout, getAdminHeaders }}>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white font-sans">
        {/* Top Sticky Admin Navbar */}
        <nav className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-6 py-2.5 transition-all">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
            {/* Logo & Portal Title */}
            <div className="flex items-center space-x-3">
              <Link 
                href="/admin" 
                className="flex items-center space-x-2 text-white font-bold hover:text-indigo-400 transition-colors group"
              >
                <div className="p-1.5 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 group-hover:border-indigo-400 transition-colors">
                  <Shield className="w-5 h-5 text-indigo-400" />
                </div>
                <span className="text-base font-extrabold tracking-tight hidden sm:inline">
                  StudyGuide <span className="text-indigo-400">Admin</span>
                </span>
              </Link>

              {/* Badges */}
              <div className="flex items-center space-x-1.5 text-xs">
                <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-medium">
                  v2.0
                </span>
                {isAuthorized ? (
                  <span className="hidden md:inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                    <ShieldCheck className="w-3 h-3" /> 인증됨
                  </span>
                ) : (
                  <span className="hidden md:inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                    <Lock className="w-3 h-3" /> 잠금 상태
                  </span>
                )}
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center space-x-1 sm:space-x-2">
              {navItems.map((item) => {
                const isActive = item.exact 
                  ? pathname === item.href 
                  : pathname.startsWith(item.href);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      isActive
                        ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                        : "text-slate-300 hover:text-white hover:bg-slate-800/70"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span className="hidden xs:inline sm:inline">{item.label}</span>
                  </Link>
                );
              })}
            </div>

            {/* Right Actions: Main App link & Lock */}
            <div className="flex items-center space-x-2">
              <Link
                href="/"
                className="hidden lg:flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 px-2.5 py-1.5 rounded-lg hover:bg-slate-800 transition-colors"
                title="메인 학습 뷰어로 돌아가기"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>메인 앱</span>
              </Link>

              {isAuthorized ? (
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/40 text-slate-300 hover:text-rose-300 border border-slate-700/80 hover:border-rose-800/50 transition-all"
                  title="관리자 세션 잠금(로그아웃)"
                >
                  <Lock className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">잠금</span>
                </button>
              ) : null}
            </div>
          </div>
        </nav>

        {/* Content Body with Guard */}
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-32 space-y-4">
              <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-slate-400 font-medium">관리자 세션 검증 중...</p>
            </div>
          ) : !isAuthorized ? (
            /* Admin Passcode Modal / Gate */
            <div className="max-w-md mx-auto my-12 p-6 sm:p-8 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-2xl shadow-black/60 relative backdrop-blur-xl">
              <div className="flex flex-col items-center text-center space-y-3 mb-6">
                <div className="p-3.5 rounded-2xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
                  <KeyRound className="w-7 h-7 text-indigo-400 animate-pulse" />
                </div>
                <div>
                  <h2 className="text-xl font-extrabold text-white tracking-tight">
                    관리자 인증 필요
                  </h2>
                  <p className="text-xs sm:text-sm text-slate-400 mt-1">
                    운영 및 개발자 대시보드에 접근하려면 관리자 패스코드를 입력하세요.
                  </p>
                </div>
              </div>

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    관리자 패스코드 (Secret Key)
                  </label>
                  <div className="relative">
                    <input
                      type={showSecret ? "text" : "password"}
                      value={inputSecret}
                      onChange={(e) => {
                        setInputSecret(e.target.value);
                        setErrorMsg("");
                      }}
                      placeholder="패스코드를 입력하세요"
                      autoFocus
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowSecret(!showSecret)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors"
                    >
                      {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {errorMsg && (
                    <div className="flex items-center gap-1.5 mt-2 text-xs text-rose-400">
                      <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                      <span>{errorMsg}</span>
                    </div>
                  )}
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={isVerifying}
                    className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-sm font-bold shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {isVerifying ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>확인 중...</span>
                      </>
                    ) : (
                      <>
                        <Unlock className="w-4 h-4" />
                        <span>관리자 모드 접속</span>
                      </>
                    )}
                  </button>
                </div>
              </form>

              <div className="mt-6 pt-4 border-t border-slate-800/80 text-center">
                <p className="text-[11px] text-slate-500">
                  💡 기본 패스코드: <code className="text-slate-400 font-mono bg-slate-800 px-1 py-0.5 rounded">studyguide-admin-2026</code>
                </p>
                <div className="mt-3">
                  <Link
                    href="/"
                    className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-300"
                  >
                    <ArrowLeft className="w-3 h-3" /> 메인 화면으로 돌아가기
                  </Link>
                </div>
              </div>
            </div>
          ) : (
            /* Authorized content */
            children
          )}
        </main>
      </div>
    </AdminAuthContext.Provider>
  );
}
