"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { 
  Activity, 
  RefreshCw, 
  Database, 
  Cpu, 
  Radio, 
  CheckCircle2, 
  AlertCircle, 
  XCircle, 
  Clock, 
  RotateCw, 
  Trash2, 
  StopCircle, 
  Play, 
  Users, 
  FileText, 
  ExternalLink, 
  Zap, 
  Search, 
  Filter, 
  Info,
  ChevronRight,
  Server,
  Layers,
  Sparkles,
  AlertTriangle,
  Sliders
} from "lucide-react";
import { useAdminAuth } from "./layout";

interface InfrastructureStatus {
  database: string;
  redis: string;
  celery: string;
}

interface OverviewStats {
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  processing_jobs: number;
  cancelled_jobs: number;
  today_jobs: number;
  total_guides: number;
  active_users_today: number;
}

interface AdminJobItem {
  id: string;
  user_id: string | null;
  status: string;
  progress: string;
  url: string;
  title: string;
  error: string | null;
  created_at: string;
}

interface UserUsageItem {
  id: string;
  user_id: string;
  date: string;
  generation_count: number;
  updated_at: string;
}

interface AdminGuideItem {
  id: string;
  user_id: string | null;
  video_id: string | null;
  url: string;
  title: string;
  image_url: string | null;
  provider: string | null;
  generation_time_sec: number | null;
  created_at: string;
}

export default function AdminHubPage() {
  const { isAuthorized, getAdminHeaders } = useAdminAuth();

  // Navigation Tabs: 'jobs' | 'quota' | 'guides'
  const [activeTab, setActiveTab] = useState<"jobs" | "quota" | "guides">("jobs");

  // State: Overview & Infra
  const [infra, setInfra] = useState<InfrastructureStatus>({
    database: "checking...",
    redis: "checking...",
    celery: "checking..."
  });
  const [stats, setStats] = useState<OverviewStats>({
    total_jobs: 0,
    completed_jobs: 0,
    failed_jobs: 0,
    processing_jobs: 0,
    cancelled_jobs: 0,
    today_jobs: 0,
    total_guides: 0,
    active_users_today: 0
  });

  // State: Jobs tab
  const [jobs, setJobs] = useState<AdminJobItem[]>([]);
  const [jobFilter, setJobFilter] = useState<string>("all");
  const [jobSearch, setJobSearch] = useState<string>("");
  const [selectedErrorJob, setSelectedErrorJob] = useState<AdminJobItem | null>(null);

  // State: Quota tab
  const [usages, setUsages] = useState<UserUsageItem[]>([]);

  // State: Guides tab
  const [guides, setGuides] = useState<AdminGuideItem[]>([]);
  const [guideSearch, setGuideSearch] = useState<string>("");

  // Loading & Feedback states
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [actionNotice, setActionNotice] = useState<{ msg: string; type: "success" | "error" } | null>(null);
  const [autoRefreshSec, setAutoRefreshSec] = useState<number>(15);

  const showToast = (msg: string, type: "success" | "error" = "success") => {
    setActionNotice({ msg, type });
    setTimeout(() => {
      setActionNotice(null);
    }, 4000);
  };

  // 1. Fetch Overview (Infra + Stats)
  const fetchOverview = useCallback(async () => {
    if (!isAuthorized) return;
    try {
      const res = await fetch("/api/admin/overview", {
        headers: getAdminHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        if (data.infrastructure) setInfra(data.infrastructure);
        if (data.stats) setStats(data.stats);
      }
    } catch (e) {
      console.error("Overview fetch error:", e);
    }
  }, [isAuthorized, getAdminHeaders]);

  // 2. Fetch Jobs
  const fetchJobs = useCallback(async () => {
    if (!isAuthorized) return;
    try {
      const params = new URLSearchParams();
      if (jobFilter !== "all") params.append("status", jobFilter);
      if (jobSearch.trim()) params.append("search", jobSearch.trim());
      params.append("limit", "50");

      const res = await fetch(`/api/admin/jobs?${params.toString()}`, {
        headers: getAdminHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setJobs(data.items || []);
      }
    } catch (e) {
      console.error("Jobs fetch error:", e);
    }
  }, [isAuthorized, jobFilter, jobSearch, getAdminHeaders]);

  // 3. Fetch User Usages
  const fetchUsages = useCallback(async () => {
    if (!isAuthorized) return;
    try {
      const res = await fetch("/api/admin/users/usage", {
        headers: getAdminHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setUsages(data.items || []);
      }
    } catch (e) {
      console.error("Usages fetch error:", e);
    }
  }, [isAuthorized, getAdminHeaders]);

  // 4. Fetch Guides
  const fetchGuides = useCallback(async () => {
    if (!isAuthorized) return;
    try {
      const params = new URLSearchParams();
      if (guideSearch.trim()) params.append("search", guideSearch.trim());
      params.append("limit", "50");

      const res = await fetch(`/api/admin/guides?${params.toString()}`, {
        headers: getAdminHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setGuides(data.items || []);
      }
    } catch (e) {
      console.error("Guides fetch error:", e);
    }
  }, [isAuthorized, guideSearch, getAdminHeaders]);

  // Total Refresh
  const handleRefreshAll = async () => {
    setRefreshing(true);
    await Promise.all([
      fetchOverview(),
      activeTab === "jobs" ? fetchJobs() : Promise.resolve(),
      activeTab === "quota" ? fetchUsages() : Promise.resolve(),
      activeTab === "guides" ? fetchGuides() : Promise.resolve(),
    ]);
    setRefreshing(false);
  };

  useEffect(() => {
    if (isAuthorized) {
      setLoading(true);
      Promise.all([fetchOverview(), fetchJobs(), fetchUsages(), fetchGuides()]).finally(() => {
        setLoading(false);
      });
    }
  }, [isAuthorized]);

  // Tab switch fetch
  useEffect(() => {
    if (isAuthorized) {
      if (activeTab === "jobs") fetchJobs();
      if (activeTab === "quota") fetchUsages();
      if (activeTab === "guides") fetchGuides();
    }
  }, [activeTab, fetchJobs, fetchUsages, fetchGuides, isAuthorized]);

  // Auto Refresh Interval
  useEffect(() => {
    if (!isAuthorized || autoRefreshSec <= 0) return;
    const timer = setInterval(() => {
      fetchOverview();
      if (activeTab === "jobs") fetchJobs();
      if (activeTab === "quota") fetchUsages();
    }, autoRefreshSec * 1000);
    return () => clearInterval(timer);
  }, [isAuthorized, autoRefreshSec, activeTab, fetchOverview, fetchJobs, fetchUsages]);

  // Job Actions
  const handleRetryJob = async (jobId: string) => {
    try {
      const res = await fetch(`/api/admin/jobs/${jobId}/retry`, {
        method: "POST",
        headers: getAdminHeaders()
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || `작업 ${jobId} 재시도 등록 완료`);
        fetchJobs();
        fetchOverview();
      } else {
        showToast(data.detail || "재시도 요청 실패", "error");
      }
    } catch (e: any) {
      showToast(e.message || "통신 오류", "error");
    }
  };

  const handleCancelJob = async (jobId: string) => {
    if (!confirm(`정말로 작업 ${jobId}를 중단하시겠습니까?`)) return;
    try {
      const res = await fetch(`/api/admin/jobs/${jobId}/cancel`, {
        method: "POST",
        headers: getAdminHeaders()
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || `작업 ${jobId} 취소 완료`);
        fetchJobs();
        fetchOverview();
      } else {
        showToast(data.detail || "취소 요청 실패", "error");
      }
    } catch (e: any) {
      showToast(e.message || "통신 오류", "error");
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm(`작업 ${jobId}를 데이터베이스에서 영구 삭제하시겠습니까?`)) return;
    try {
      const res = await fetch(`/api/admin/jobs/${jobId}`, {
        method: "DELETE",
        headers: getAdminHeaders()
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || `작업 ${jobId} 삭제 완료`);
        fetchJobs();
        fetchOverview();
      } else {
        showToast(data.detail || "삭제 실패", "error");
      }
    } catch (e: any) {
      showToast(e.message || "통신 오류", "error");
    }
  };

  // Quota Action
  const handleResetQuota = async (userId: string) => {
    if (!confirm(`사용자 '${userId}'의 오늘 생성 쿼터를 0회로 초기화하시겠습니까?`)) return;
    try {
      const res = await fetch(`/api/admin/users/${encodeURIComponent(userId)}/reset-quota`, {
        method: "POST",
        headers: getAdminHeaders()
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || `사용자 ${userId} 쿼터 초기화 완료`);
        fetchUsages();
        fetchOverview();
      } else {
        showToast(data.detail || "초기화 실패", "error");
      }
    } catch (e: any) {
      showToast(e.message || "통신 오류", "error");
    }
  };

  // Guide Action
  const handleDeleteGuide = async (guideId: string) => {
    if (!confirm(`학습 가이드 '${guideId}'를 삭제하시겠습니까?`)) return;
    try {
      const res = await fetch(`/api/admin/guides/${guideId}`, {
        method: "DELETE",
        headers: getAdminHeaders()
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || "가이드 삭제 완료");
        fetchGuides();
        fetchOverview();
      } else {
        showToast(data.detail || "삭제 실패", "error");
      }
    } catch (e: any) {
      showToast(e.message || "통신 오류", "error");
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Toast Notification */}
      {actionNotice && (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-2xl border transition-all animate-in fade-in slide-in-from-bottom-5 ${
          actionNotice.type === "success" 
            ? "bg-slate-900 border-emerald-500/50 text-emerald-300" 
            : "bg-slate-900 border-rose-500/50 text-rose-300"
        }`}>
          {actionNotice.type === "success" ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : (
            <AlertCircle className="w-5 h-5 text-rose-400" />
          )}
          <span className="text-xs sm:text-sm font-semibold">{actionNotice.msg}</span>
        </div>
      )}

      {/* Top Header & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2.5">
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-2">
              관리자 통합 대시보드
            </h1>
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-semibold">
              Live Control
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            실시간 Celery AI 파이프라인 제어, 사용자 쿼터 조정 및 데이터베이스 모니터링
          </p>
        </div>

        {/* Refresh & Interval Selector */}
        <div className="flex items-center space-x-2 self-start sm:self-auto">
          <select
            value={autoRefreshSec}
            onChange={(e) => setAutoRefreshSec(Number(e.target.value))}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value={0}>자동 갱신 꺼짐</option>
            <option value={10}>10초마다 갱신</option>
            <option value={15}>15초마다 갱신</option>
            <option value={30}>30초마다 갱신</option>
          </select>

          <button
            onClick={handleRefreshAll}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all disabled:opacity-50"
          >
            <RotateCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-indigo-400" : ""}`} />
            <span>새로고침</span>
          </button>
        </div>
      </div>

      {/* 1. Infrastructure Health Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        {/* Neon PostgreSQL */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Neon PostgreSQL</p>
              <h3 className="text-sm font-bold text-white capitalize flex items-center gap-1.5 mt-0.5">
                {infra.database === "connected" ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    정상 연결됨
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-rose-400" />
                    {infra.database}
                  </>
                )}
              </h3>
            </div>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">Cloud DB</span>
        </div>

        {/* Redis Message Broker */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Redis Broker</p>
              <h3 className="text-sm font-bold text-white capitalize flex items-center gap-1.5 mt-0.5">
                {infra.redis === "connected" ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    정상 가동 중
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-rose-400" />
                    {infra.redis}
                  </>
                )}
              </h3>
            </div>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">Port 6379</span>
        </div>

        {/* Celery AI Worker */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Celery Worker</p>
              <h3 className="text-sm font-bold text-white capitalize flex items-center gap-1.5 mt-0.5">
                {infra.celery.startsWith("active") ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    {infra.celery}
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-amber-400" />
                    {infra.celery}
                  </>
                )}
              </h3>
            </div>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">Async Engine</span>
        </div>
      </div>

      {/* Generation Mechanism Control Quick Banner */}
      <div className="relative overflow-hidden p-5 rounded-2xl bg-gradient-to-r from-indigo-950/60 via-slate-900 to-purple-950/40 border border-indigo-500/30 shadow-xl shadow-indigo-950/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start sm:items-center space-x-3.5">
            <div className="p-3 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex-shrink-0">
              <Sliders className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-extrabold text-white tracking-tight">
                  학습 가이드 생성 매커니즘 제어 센터
                </h3>
                <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold uppercase">
                  Engine Config
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-1 max-w-2xl">
                AI 모델(Gemini/GPT/Claude), 목차 생성 알고리즘, 서술형 본문 프롬프트, 4대 인터랙티브 위젯 규칙, 품질 검증 가드레일 및 실시간 시뮬레이터를 즉시 제어합니다.
              </p>
            </div>
          </div>
          <Link
            href="/admin/generation-config"
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 transition-all group flex-shrink-0"
          >
            <span>매커니즘 제어 포털 열기</span>
            <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </div>

      {/* 2. Key Summary Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/60">
          <p className="text-xs font-semibold text-slate-400">총 학습 가이드</p>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-black text-white">{stats.total_guides}</span>
            <span className="text-xs text-indigo-400 font-medium">완성본</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/60">
          <p className="text-xs font-semibold text-slate-400">오늘 생성 요청</p>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-black text-white">{stats.today_jobs}</span>
            <span className="text-xs text-emerald-400 font-medium">당일 누적</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/60">
          <p className="text-xs font-semibold text-slate-400">현재 진행 중 작업</p>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-black text-amber-300">{stats.processing_jobs}</span>
            <span className="text-xs text-amber-400/80 font-medium">실시간 대기열</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/60">
          <p className="text-xs font-semibold text-slate-400">실패한 작업</p>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-black text-rose-400">{stats.failed_jobs}</span>
            <span className="text-xs text-slate-500 font-medium">
              총 {stats.total_jobs}건 중
            </span>
          </div>
        </div>
      </div>

      {/* 3. Main Navigation Tabs (Jobs / Quota / Guides) */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("jobs")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
            activeTab === "jobs"
              ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800/60"
          }`}
        >
          <Cpu className="w-4 h-4" />
          <span>작업 & 큐 모니터링 ({jobs.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("quota")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
            activeTab === "quota"
              ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800/60"
          }`}
        >
          <Users className="w-4 h-4" />
          <span>사용자 쿼터 관리 ({usages.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("guides")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
            activeTab === "guides"
              ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
              : "text-slate-400 hover:text-white hover:bg-slate-800/60"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>학습 가이드 DB ({guides.length})</span>
        </button>
      </div>

      {/* TAB CONTENT 1: JOBS */}
      {activeTab === "jobs" && (
        <div className="space-y-4">
          {/* Controls: Search & Filter */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={jobSearch}
                onChange={(e) => setJobSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchJobs()}
                placeholder="작업 ID, 영상 제목, URL 검색..."
                className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-xs text-slate-400">상태:</span>
              <select
                value={jobFilter}
                onChange={(e) => setJobFilter(e.target.value)}
                className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="all">전체 상태</option>
                <option value="processing">진행 중 (Processing)</option>
                <option value="completed">완료됨 (Completed)</option>
                <option value="failed">실패함 (Failed)</option>
                <option value="cancelled">취소됨 (Cancelled)</option>
              </select>
            </div>
          </div>

          {/* Jobs Table */}
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">작업 ID / 사용자</th>
                  <th className="py-3 px-4">영상 제목 / URL</th>
                  <th className="py-3 px-4">상태 / 진행률</th>
                  <th className="py-3 px-4">생성 일시</th>
                  <th className="py-3 px-4 text-right">제어 액션</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {jobs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      조건에 맞는 작업이 없습니다.
                    </td>
                  </tr>
                ) : (
                  jobs.map((job) => {
                    const isFailed = job.status === "failed";
                    const isProcessing = ["processing", "transcribing", "generating_outline", "generating_chapters", "pending"].includes(job.status);
                    const isCompleted = job.status === "completed";

                    return (
                      <tr key={job.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4">
                          <div className="font-mono text-indigo-400 font-bold">{job.id}</div>
                          <div className="text-[11px] text-slate-500 mt-0.5">
                            {job.user_id ? `User: ${job.user_id}` : "비로그인 (Anonymous)"}
                          </div>
                        </td>

                        <td className="py-3 px-4 max-w-xs sm:max-w-sm truncate">
                          <div className="font-semibold text-white truncate" title={job.title}>
                            {job.title || "제목 정보 없음"}
                          </div>
                          {job.url && (
                            <a
                              href={job.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[11px] text-slate-400 hover:text-indigo-400 flex items-center gap-1 mt-0.5 truncate"
                            >
                              <ExternalLink className="w-2.5 h-2.5 flex-shrink-0" />
                              <span className="truncate">{job.url}</span>
                            </a>
                          )}
                        </td>

                        <td className="py-3 px-4">
                          <div className="flex items-center gap-1.5">
                            {isCompleted && (
                              <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold text-[11px]">
                                Completed
                              </span>
                            )}
                            {isProcessing && (
                              <span className="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold text-[11px] flex items-center gap-1">
                                <RotateCw className="w-2.5 h-2.5 animate-spin" />
                                {job.status}
                              </span>
                            )}
                            {isFailed && (
                              <button
                                onClick={() => setSelectedErrorJob(job)}
                                className="px-2 py-0.5 rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20 font-semibold text-[11px] hover:bg-rose-500/20 transition-all flex items-center gap-1"
                                title="에러 상세 보기"
                              >
                                <AlertTriangle className="w-3 h-3" /> Failed (에러확인)
                              </button>
                            )}
                            {job.status === "cancelled" && (
                              <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 border border-slate-700 font-semibold text-[11px]">
                                Cancelled
                              </span>
                            )}
                          </div>
                          {job.progress && (
                            <div className="text-[11px] text-slate-400 mt-1 max-w-[180px] truncate" title={job.progress}>
                              {job.progress}
                            </div>
                          )}
                        </td>

                        <td className="py-3 px-4 text-slate-400 text-[11px] whitespace-nowrap">
                          {job.created_at ? new Date(job.created_at).toLocaleString("ko-KR") : "-"}
                        </td>

                        <td className="py-3 px-4 text-right whitespace-nowrap space-x-1.5">
                          {isFailed && (
                            <button
                              onClick={() => handleRetryJob(job.id)}
                              className="px-2.5 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 text-[11px] font-bold transition-all inline-flex items-center gap-1"
                              title="비동기 재시도"
                            >
                              <RotateCw className="w-3 h-3" /> 재시도
                            </button>
                          )}
                          {isProcessing && (
                            <button
                              onClick={() => handleCancelJob(job.id)}
                              className="px-2.5 py-1 rounded-lg bg-amber-600/20 hover:bg-amber-600/40 text-amber-300 border border-amber-500/30 text-[11px] font-bold transition-all inline-flex items-center gap-1"
                              title="작업 취소"
                            >
                              <StopCircle className="w-3 h-3" /> 취소
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteJob(job.id)}
                            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-rose-900/30 text-slate-400 hover:text-rose-300 border border-slate-700 hover:border-rose-800/40 text-[11px] font-bold transition-all inline-flex items-center gap-1"
                            title="레코드 삭제"
                          >
                            <Trash2 className="w-3 h-3" /> 삭제
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB CONTENT 2: USER QUOTAS */}
      {activeTab === "quota" && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">사용자 일일 생성 쿼터 관리</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                당일 생성 쿼터(기본 1인 3회)를 초과한 사용자를 확인하고 원클릭으로 0회 초기화(리셋)할 수 있습니다.
              </p>
            </div>
            <span className="text-xs font-mono bg-indigo-950/60 text-indigo-300 px-3 py-1 rounded-lg border border-indigo-800/40">
              오늘: {new Date().toISOString().split("T")[0]}
            </span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">사용자 ID</th>
                  <th className="py-3 px-4">기준 일자</th>
                  <th className="py-3 px-4">당일 생성 횟수</th>
                  <th className="py-3 px-4">상태</th>
                  <th className="py-3 px-4 text-right">쿼터 초기화</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {usages.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      오늘 생성 기록이 있는 사용자가 아직 없습니다.
                    </td>
                  </tr>
                ) : (
                  usages.map((u) => {
                    const isExceeded = u.generation_count >= 3;
                    return (
                      <tr key={u.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-white">
                          {u.user_id}
                        </td>
                        <td className="py-3 px-4 text-slate-400">{u.date}</td>
                        <td className="py-3 px-4">
                          <span className="font-bold text-sm text-indigo-300">
                            {u.generation_count}
                          </span>
                          <span className="text-slate-500 text-xs"> / 3회</span>
                        </td>
                        <td className="py-3 px-4">
                          {isExceeded ? (
                            <span className="px-2 py-0.5 rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold text-[11px]">
                              한도 초과 (429 차단)
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold text-[11px]">
                              이용 가능
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => handleResetQuota(u.user_id)}
                            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition-all inline-flex items-center gap-1.5"
                          >
                            <RotateCw className="w-3 h-3" /> 0회로 초기화
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB CONTENT 3: STUDY GUIDES */}
      {activeTab === "guides" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/80">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={guideSearch}
                onChange={(e) => setGuideSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchGuides()}
                placeholder="가이드 ID, 제목, 영상 검색..."
                className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <span className="text-xs text-slate-400">
              총 <strong>{guides.length}</strong>건 표시 중
            </span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">가이드 ID</th>
                  <th className="py-3 px-4">가이드 제목</th>
                  <th className="py-3 px-4">소요시간 / 프로바이더</th>
                  <th className="py-3 px-4">생성 일시</th>
                  <th className="py-3 px-4 text-right">제어 액션</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {guides.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      저장된 학습 가이드가 없습니다.
                    </td>
                  </tr>
                ) : (
                  guides.map((g) => (
                    <tr key={g.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-indigo-400">
                        {g.id}
                      </td>
                      <td className="py-3 px-4 max-w-sm truncate">
                        <div className="font-semibold text-white truncate" title={g.title}>
                          {g.title}
                        </div>
                        {g.url && (
                          <span className="text-[11px] text-slate-500 truncate block mt-0.5">
                            {g.url}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-slate-300">
                          {g.generation_time_sec ? `${g.generation_time_sec}초` : "-"}
                        </div>
                        <div className="text-[11px] text-slate-500">
                          {g.provider || "Gemini"}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-[11px] whitespace-nowrap">
                        {g.created_at ? new Date(g.created_at).toLocaleString("ko-KR") : "-"}
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap space-x-2">
                        <Link
                          href={`/guide/${g.id}`}
                          target="_blank"
                          className="px-2.5 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 text-[11px] font-bold transition-all inline-flex items-center gap-1"
                        >
                          <ExternalLink className="w-3 h-3" /> 뷰어로 열기
                        </Link>
                        <button
                          onClick={() => handleDeleteGuide(g.id)}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-rose-950/30 text-slate-400 hover:text-rose-300 border border-slate-700 hover:border-rose-800/40 text-[11px] font-bold transition-all inline-flex items-center gap-1"
                        >
                          <Trash2 className="w-3 h-3" /> 삭제
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 4. Subsystem Quick Link Banners */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-800">
        <Link
          href="/admin/batch"
          className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/40 transition-all flex items-center justify-between group"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 group-hover:border-indigo-400 transition-colors">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors flex items-center gap-1.5">
                유튜브 일괄 사전 생성기 (Batch Pregen)
                <ChevronRight className="w-3.5 h-3.5" />
              </h4>
              <p className="text-xs text-slate-400 mt-0.5">
                유튜브 채널 또는 재생목록 전체를 백그라운드에서 한 번에 사전 생성
              </p>
            </div>
          </div>
        </Link>

        <Link
          href="/admin/health"
          className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/40 transition-all flex items-center justify-between group"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-rose-600/10 text-rose-400 border border-rose-500/20 group-hover:border-rose-400 transition-colors">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white group-hover:text-rose-300 transition-colors flex items-center gap-1.5">
                시스템 상태 & 에러 로그 인스펙터
                <ChevronRight className="w-3.5 h-3.5" />
              </h4>
              <p className="text-xs text-slate-400 mt-0.5">
                실시간 에러 발생 추이 시계열 차트 및 에러 카테고리별 로그 정밀 분석
              </p>
            </div>
          </div>
        </Link>
      </div>

      {/* Error Details Modal */}
      {selectedErrorJob && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-2xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2 text-rose-400 font-bold text-sm">
                <AlertCircle className="w-5 h-5" />
                <span>작업 실패 상세 에러 로그 ({selectedErrorJob.id})</span>
              </div>
              <button
                onClick={() => setSelectedErrorJob(null)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-lg hover:bg-slate-800"
              >
                닫기
              </button>
            </div>

            <div className="text-xs space-y-2 text-slate-300">
              <div>
                <span className="text-slate-500 font-semibold">영상 제목: </span>
                <span className="font-medium text-white">{selectedErrorJob.title || "제목 없음"}</span>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">영상 URL: </span>
                <a href={selectedErrorJob.url} target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline">
                  {selectedErrorJob.url}
                </a>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">
                에러 스택 트레이스 (Stack Trace)
              </label>
              <pre className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-rose-300 overflow-x-auto max-h-72 whitespace-pre-wrap leading-relaxed">
                {selectedErrorJob.error || "에러 메시지가 기록되지 않았습니다."}
              </pre>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
              <button
                onClick={() => {
                  handleRetryJob(selectedErrorJob.id);
                  setSelectedErrorJob(null);
                }}
                className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-600/30 flex items-center gap-1.5"
              >
                <RotateCw className="w-3.5 h-3.5" /> 이 작업 재시도
              </button>
              <button
                onClick={() => setSelectedErrorJob(null)}
                className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs"
              >
                창 닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
