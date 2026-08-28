"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { 
  Play, 
  RotateCw, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  CloudUpload, 
  StopCircle, 
  Video, 
  Layers, 
  Sliders, 
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Sparkles,
  RefreshCw,
  Terminal,
  Copy,
  Check,
  Info,
  AlertTriangle
} from "lucide-react";

interface BatchLogItem {
  timestamp: string;
  message: string;
  level: "info" | "warn" | "error" | "success";
}

interface BatchVideoItem {
  id: string;
  batch_job_id: string;
  video_id: string;
  url: string;
  title: string;
  duration: string;
  status: "pending" | "processing" | "completed" | "skipped" | "failed";
  error: string | null;
  sync_status: "pending" | "synced" | "failed";
  presets_generated: number;
}

interface BatchJob {
  id: string;
  url: string;
  title: string;
  total_videos: number;
  completed_videos: number;
  failed_videos: number;
  skipped_videos: number;
  status: "pending" | "collecting" | "processing" | "completed" | "failed" | "cancelled";
  sync_status: "idle" | "syncing" | "synced" | "failed";
  sync_error: string | null;
  provider: string;
  force_refresh: boolean;
  exclude_shorts: boolean;
  max_limit: number;
  remote_url?: string;
  sync_key?: string;
  error: string | null;
  logs?: BatchLogItem[];
  created_at: string;
}

export default function BatchGeneratorPage() {
  // Input Form States
  const [url, setUrl] = useState("");
  const [provider, setProvider] = useState("Google Gemini");
  const [maxLimit, setMaxLimit] = useState(30);
  const [excludeShorts, setExcludeShorts] = useState(true);
  const [forceRefresh, setForceRefresh] = useState(false);
  const [remoteUrl, setRemoteUrl] = useState("");
  const [syncKey, setSyncKey] = useState("");
  
  // Execution & Polling States
  const [activeBatchId, setActiveBatchId] = useState<string | null>(null);
  const [currentBatch, setCurrentBatch] = useState<BatchJob | null>(null);
  const [videoList, setVideoList] = useState<BatchVideoItem[]>([]);
  const [allBatches, setAllBatches] = useState<BatchJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [copiedLogs, setCopiedLogs] = useState(false);

  const logEndRef = useRef<HTMLDivElement | null>(null);

  // Load stored remote config from localStorage
  useEffect(() => {
    const savedRemoteUrl = localStorage.getItem("BATCH_REMOTE_URL") || "";
    const savedSyncKey = localStorage.getItem("BATCH_SYNC_KEY") || "";
    if (savedRemoteUrl) setRemoteUrl(savedRemoteUrl);
    if (savedSyncKey) setSyncKey(savedSyncKey);
  }, []);

  // Fetch recent batches list
  const fetchBatchList = useCallback(async () => {
    try {
      const res = await fetch("/api/admin/batch/list/all");
      if (res.ok) {
        const data = await res.json();
        setAllBatches(data.batches || []);
        if (!activeBatchId && data.batches && data.batches.length > 0) {
          setActiveBatchId(data.batches[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch batch list", err);
    }
  }, [activeBatchId]);

  useEffect(() => {
    fetchBatchList();
  }, [fetchBatchList]);

  // Poll current active batch detail
  const fetchBatchDetail = useCallback(async (batchId: string) => {
    try {
      const res = await fetch(`/api/admin/batch/${batchId}`);
      if (res.ok) {
        const data = await res.json();
        setCurrentBatch(data.batch);
        setVideoList(data.videos || []);
      }
    } catch (err) {
      console.error("Failed to fetch batch detail", err);
    }
  }, []);

  useEffect(() => {
    if (!activeBatchId) return;
    fetchBatchDetail(activeBatchId);
    
    // Poll every 2 seconds if in progress
    const interval = setInterval(() => {
      if (currentBatch?.status === "processing" || currentBatch?.status === "collecting" || currentBatch?.status === "pending") {
        fetchBatchDetail(activeBatchId);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [activeBatchId, currentBatch?.status, fetchBatchDetail]);

  // Auto-scroll logs
  useEffect(() => {
    if (autoScroll && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [currentBatch?.logs, autoScroll]);

  // Start Batch Generation
  const handleStartBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      alert("유튜브 채널 또는 재생목록 URL을 입력해주세요.");
      return;
    }

    if (remoteUrl) localStorage.setItem("BATCH_REMOTE_URL", remoteUrl);
    if (syncKey) localStorage.setItem("BATCH_SYNC_KEY", syncKey);

    setLoading(true);
    try {
      const res = await fetch("/api/admin/batch/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: url.trim(),
          provider,
          max_limit: Number(maxLimit),
          exclude_shorts: excludeShorts,
          force_refresh: forceRefresh,
          remote_url: remoteUrl.trim() || undefined,
          sync_key: syncKey.trim() || undefined
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "배치 시작에 실패했습니다.");
      }

      setActiveBatchId(data.batch_id);
      fetchBatchList();
      fetchBatchDetail(data.batch_id);
      setUrl("");
    } catch (err: any) {
      alert(`오류: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Cancel Batch
  const handleCancelBatch = async () => {
    if (!activeBatchId || !confirm("정말 이 배치 작업을 중단하시겠습니까?")) return;
    try {
      await fetch(`/api/admin/batch/${activeBatchId}/cancel`, { method: "POST" });
      fetchBatchDetail(activeBatchId);
      fetchBatchList();
    } catch (err) {
      alert("작업 취소 실패");
    }
  };

  // Manual Remote Sync Push
  const handleManualSync = async () => {
    if (!activeBatchId) return;
    setSyncing(true);
    try {
      const res = await fetch(`/api/admin/batch/${activeBatchId}/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          remote_url: remoteUrl || undefined,
          sync_key: syncKey || undefined
        })
      });
      const data = await res.json();
      if (res.ok && data.status === "synced") {
        alert(`운영 서버 동기화 성공! (총 ${data.synced_count}개 프리셋 전송 완료)`);
      } else {
        alert(`동기화 알림: ${data.message || data.error || JSON.stringify(data)}`);
      }
      fetchBatchDetail(activeBatchId);
    } catch (err: any) {
      alert(`동기화 통신 오류: ${err.message}`);
    } finally {
      setSyncing(false);
    }
  };

  // Copy Logs
  const handleCopyLogs = () => {
    if (!currentBatch?.logs) return;
    const text = currentBatch.logs
      .map((l) => `[${new Date(l.timestamp).toLocaleTimeString()}] [${l.level.toUpperCase()}] ${l.message}`)
      .join("\n");
    navigator.clipboard.writeText(text);
    setCopiedLogs(true);
    setTimeout(() => setCopiedLogs(false), 2000);
  };

  // Progress Calculation
  const total = currentBatch?.total_videos || 0;
  const processed = (currentBatch?.completed_videos || 0) + (currentBatch?.skipped_videos || 0) + (currentBatch?.failed_videos || 0);
  const progressPercent = total > 0 ? Math.min(100, Math.round((processed / total) * 100)) : (currentBatch?.status === "collecting" ? 10 : 0);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-6 md:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Navigation & Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              <span>관리자 콘솔</span>
              <ChevronRight size={14} className="text-slate-400" />
              <span className="text-indigo-600 font-bold">유튜브 일괄 사전 생성</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 flex items-center gap-3 tracking-tight">
              <Sparkles className="text-amber-500 fill-amber-500" size={28} />
              로컬 일괄 사전 생성 & 운영 서버 동기화
            </h1>
            <p className="text-sm text-slate-600 mt-1">
              내 컴퓨터의 리소스로 3×3 (총 9개 프리셋) 가이드를 대량 선행 생성하여 AWS 운영 서버로 안전하게 동기화합니다.
            </p>
          </div>

          <div className="flex items-center gap-2.5 self-start md:self-auto">
            <Link 
              href="/admin/health" 
              className="px-4 py-2 text-xs font-bold rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-all"
            >
              📊 시스템 헬스 로그
            </Link>
            <Link 
              href="/admin/batch" 
              className="px-4 py-2 text-xs font-bold rounded-xl bg-indigo-600 text-white shadow-sm shadow-indigo-200 hover:bg-indigo-700 transition-all"
            >
              ⚡ 일괄 사전 생성
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Request Form & Remote Sync Config */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
                <Video size={20} className="text-indigo-600" />
                새 일괄 생성 작업 등록
              </h2>

              <form onSubmit={handleStartBatch} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    유튜브 채널 또는 재생목록 URL <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="url"
                    required
                    placeholder="https://www.youtube.com/@채널명 또는 playlist?list=..."
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 transition-all"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      LLM Provider
                    </label>
                    <select
                      value={provider}
                      onChange={(e) => setProvider(e.target.value)}
                      className="w-full px-3 py-2.5 bg-white border border-slate-300 rounded-xl text-xs font-semibold text-slate-900 focus:outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100"
                    >
                      <option value="Google Gemini" className="bg-white text-slate-900 py-1">Google Gemini 2.5 Flash</option>
                      <option value="OpenAI (GPT-4o)" className="bg-white text-slate-900 py-1">OpenAI GPT-4o</option>
                      <option value="cerebras/gpt-oss-120b" className="bg-white text-slate-900 py-1">Cerebras OSS 120B (초고속)</option>
                      <option value="nvidia/nemotron-3-ultra-550b-a55b" className="bg-white text-slate-900 py-1">Nvidia Nemotron 550B</option>
                      <option value="glm-5.2" className="bg-white text-slate-900 py-1">GLM-5.2</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      최대 생성 개수
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={200}
                      value={maxLimit}
                      onChange={(e) => setMaxLimit(Number(e.target.value))}
                      className="w-full px-3 py-2.5 bg-white border border-slate-300 rounded-xl text-xs font-semibold text-slate-900 focus:outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100"
                    />
                  </div>
                </div>

                {/* Option Toggles */}
                <div className="space-y-2.5 pt-3 pb-1 border-t border-slate-100">
                  <label className="flex items-center gap-2.5 cursor-pointer text-xs font-medium text-slate-700 select-none">
                    <input
                      type="checkbox"
                      checked={excludeShorts}
                      onChange={(e) => setExcludeShorts(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span>쇼츠(Shorts) 영상 제외 (60초 이하 또는 세로영상)</span>
                  </label>

                  <label className="flex items-center gap-2.5 cursor-pointer text-xs font-medium text-slate-700 select-none">
                    <input
                      type="checkbox"
                      checked={forceRefresh}
                      onChange={(e) => setForceRefresh(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span>이미 존재하는 가이드 덮어쓰기 (Force Overwrite)</span>
                  </label>
                </div>

                {/* Remote Sync Config */}
                <div className="pt-3 border-t border-slate-100 space-y-2.5 bg-slate-50/80 p-3.5 rounded-xl border border-slate-200/60">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 uppercase tracking-wider">
                    <ShieldCheck size={16} className="text-emerald-600" />
                    운영 서버(AWS) 동기화 설정 (선택)
                  </div>
                  <div>
                    <input
                      type="url"
                      placeholder="운영 백엔드 주소 (예: http://54.180.x.x:8000)"
                      value={remoteUrl}
                      onChange={(e) => setRemoteUrl(e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-indigo-600"
                    />
                  </div>
                  <div>
                    <input
                      type="password"
                      placeholder="동기화 시크릿 키 (ADMIN_SYNC_SECRET)"
                      value={syncKey}
                      onChange={(e) => setSyncKey(e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-indigo-600"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-2 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm rounded-xl flex items-center justify-center gap-2 shadow-md shadow-indigo-100 transition-all disabled:opacity-50 cursor-pointer active:scale-[0.99]"
                >
                  {loading ? <RotateCw className="animate-spin" size={18} /> : <Play size={18} />}
                  3×3=9개 프리셋 일괄 생성 시작
                </button>
              </form>
            </div>

            {/* Recent Batches History */}
            <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">최근 배치 작업 내역</h3>
                <button 
                  onClick={fetchBatchList} 
                  className="text-xs font-semibold text-slate-500 hover:text-indigo-600 flex items-center gap-1 transition-colors cursor-pointer"
                >
                  <RefreshCw size={12} /> 새로고침
                </button>
              </div>
              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {allBatches.length === 0 ? (
                  <p className="text-xs text-slate-400 py-6 text-center font-medium">등록된 배치 작업이 없습니다.</p>
                ) : (
                  allBatches.map((b) => (
                    <div
                      key={b.id}
                      onClick={() => setActiveBatchId(b.id)}
                      className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                        activeBatchId === b.id
                          ? "border-indigo-600 bg-indigo-50/60 font-semibold text-slate-900 shadow-xs"
                          : "border-slate-200 bg-white hover:border-slate-300 text-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="truncate max-w-[210px] font-bold">{b.title || b.url}</span>
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                          b.status === "completed" ? "bg-emerald-100 text-emerald-700" :
                          b.status === "processing" ? "bg-blue-100 text-blue-700 animate-pulse" :
                          b.status === "collecting" ? "bg-amber-100 text-amber-700 animate-pulse" :
                          b.status === "failed" ? "bg-rose-100 text-rose-700" : "bg-slate-100 text-slate-600"
                        }`}>
                          {b.status}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 flex justify-between font-normal">
                        <span>완료: {b.completed_videos} / {b.total_videos} 영상</span>
                        <span>{new Date(b.created_at).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Active Batch Monitor & Video Table & Live Logs */}
          <div className="lg:col-span-7 space-y-6">
            {currentBatch ? (
              <div className="space-y-6">
                
                {/* Status Card */}
                <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm space-y-6">
                  
                  {/* Header & Status */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-lg font-extrabold text-slate-900">{currentBatch.title}</h2>
                        <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                          currentBatch.status === "completed" ? "bg-emerald-100 text-emerald-700" :
                          currentBatch.status === "processing" ? "bg-blue-100 text-blue-700 animate-pulse" :
                          currentBatch.status === "collecting" ? "bg-amber-100 text-amber-700 animate-pulse" :
                          "bg-rose-100 text-rose-700"
                        }`}>
                          {currentBatch.status.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 truncate max-w-md mt-1 font-mono">{currentBatch.url}</p>
                    </div>

                    <div className="flex items-center gap-2">
                      {(currentBatch.status === "processing" || currentBatch.status === "collecting") && (
                        <button
                          onClick={handleCancelBatch}
                          className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
                        >
                          <StopCircle size={14} /> 작업 중단
                        </button>
                      )}
                      <button
                        onClick={handleManualSync}
                        disabled={syncing || currentBatch.status === "processing" || currentBatch.status === "collecting"}
                        className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm shadow-emerald-200 transition-all cursor-pointer"
                      >
                        {syncing ? <RotateCw className="animate-spin" size={14} /> : <CloudUpload size={14} />}
                        운영 서버로 푸시
                      </button>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-2 bg-slate-50/80 p-4 rounded-xl border border-slate-100">
                    <div className="flex justify-between text-xs font-bold text-slate-700">
                      <span>진행률: {processed} / {total} 비디오 처리됨</span>
                      <span className="text-indigo-600 font-extrabold">{progressPercent}%</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                      <div
                        className="bg-indigo-600 h-full transition-all duration-500 rounded-full"
                        style={{ width: `${progressPercent}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-4 gap-3">
                    <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 text-center">
                      <div className="text-xs text-slate-500 font-bold">총 비디오</div>
                      <div className="text-xl font-extrabold text-slate-900 mt-0.5">{currentBatch.total_videos}</div>
                    </div>
                    <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-3.5 text-center">
                      <div className="text-xs text-emerald-700 font-bold">생성 완료 (9개)</div>
                      <div className="text-xl font-extrabold text-emerald-700 mt-0.5">{currentBatch.completed_videos}</div>
                    </div>
                    <div className="bg-amber-50/60 border border-amber-200 rounded-xl p-3.5 text-center">
                      <div className="text-xs text-amber-700 font-bold">건너뜀 (기존존재)</div>
                      <div className="text-xl font-extrabold text-amber-700 mt-0.5">{currentBatch.skipped_videos}</div>
                    </div>
                    <div className="bg-rose-50/60 border border-rose-200 rounded-xl p-3.5 text-center">
                      <div className="text-xs text-rose-700 font-bold">실패</div>
                      <div className="text-xl font-extrabold text-rose-700 mt-0.5">{currentBatch.failed_videos}</div>
                    </div>
                  </div>

                  {/* Video Items Table */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        비디오별 처리 상태
                      </h3>
                      <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                        비디오당 3×3=9개 프리셋 생성
                      </span>
                    </div>

                    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white max-h-[300px] overflow-y-auto shadow-xs">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-100/90 text-slate-700 font-bold sticky top-0 border-b border-slate-200 z-10">
                          <tr>
                            <th className="p-3.5">영상 제목</th>
                            <th className="p-3.5 w-24">재생시간</th>
                            <th className="p-3.5 w-24">프리셋 수</th>
                            <th className="p-3.5 w-20">상태</th>
                            <th className="p-3.5 w-20">동기화</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {videoList.length === 0 ? (
                            <tr>
                              <td colSpan={5} className="p-6 text-center text-slate-400 font-medium">
                                수집된 비디오가 없습니다.
                              </td>
                            </tr>
                          ) : (
                            videoList.map((v) => (
                              <tr key={v.id} className="hover:bg-slate-50/80 transition-colors">
                                <td className="p-3.5">
                                  <div className="font-bold text-slate-900 truncate max-w-xs">{v.title}</div>
                                  <a
                                    href={v.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-[11px] text-slate-500 hover:text-indigo-600 font-mono flex items-center gap-1 mt-0.5"
                                  >
                                    {v.video_id} <ExternalLink size={10} />
                                  </a>
                                  {v.error && (
                                    <div className="text-[11px] text-rose-600 font-medium mt-1 truncate max-w-xs">
                                      오류: {v.error}
                                    </div>
                                  )}
                                </td>
                                <td className="p-3.5 text-slate-600 font-mono">{v.duration || "-"}</td>
                                <td className="p-3.5">
                                  <span className={`px-2.5 py-1 rounded-md font-mono text-[11px] font-bold ${
                                    v.presets_generated >= 9 ? "bg-emerald-100 text-emerald-800" :
                                    v.presets_generated > 0 ? "bg-blue-100 text-blue-800" :
                                    "bg-slate-100 text-slate-500"
                                  }`}>
                                    {v.presets_generated} / 9
                                  </span>
                                </td>
                                <td className="p-3.5">
                                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                                    v.status === "completed" ? "bg-emerald-100 text-emerald-700" :
                                    v.status === "processing" ? "bg-blue-100 text-blue-700 animate-pulse" :
                                    v.status === "skipped" ? "bg-amber-100 text-amber-700" :
                                    v.status === "failed" ? "bg-rose-100 text-rose-700" :
                                    "bg-slate-100 text-slate-600"
                                  }`}>
                                    {v.status}
                                  </span>
                                </td>
                                <td className="p-3.5">
                                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                                    v.sync_status === "synced" ? "bg-emerald-100 text-emerald-700" :
                                    v.sync_status === "failed" ? "bg-rose-100 text-rose-700" : "text-slate-400"
                                  }`}>
                                    {v.sync_status === "synced" ? "✓ 완료" : v.sync_status === "failed" ? "✗ 실패" : "대기"}
                                  </span>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>

                </div>

                {/* Live Terminal Log Console */}
                <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-3 text-slate-200">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <Terminal size={18} className="text-emerald-400" />
                      <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                        실시간 실행 로그 스트림
                        {(currentBatch.status === "processing" || currentBatch.status === "collecting") && (
                          <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
                        )}
                      </h3>
                    </div>

                    <div className="flex items-center gap-3 text-xs">
                      <label className="flex items-center gap-1.5 text-slate-400 hover:text-slate-200 cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={autoScroll}
                          onChange={(e) => setAutoScroll(e.target.checked)}
                          className="w-3.5 h-3.5 rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-0"
                        />
                        <span>자동 스크롤</span>
                      </label>
                      <button
                        onClick={handleCopyLogs}
                        className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg flex items-center gap-1 transition-colors cursor-pointer"
                      >
                        {copiedLogs ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                        {copiedLogs ? "복사됨" : "로그 복사"}
                      </button>
                    </div>
                  </div>

                  {/* Logs Viewport */}
                  <div className="font-mono text-xs max-h-60 overflow-y-auto space-y-1.5 pr-2 select-text">
                    {!currentBatch.logs || currentBatch.logs.length === 0 ? (
                      <p className="text-slate-500 italic py-4 text-center">아직 출력된 로그가 없습니다...</p>
                    ) : (
                      currentBatch.logs.map((log, idx) => (
                        <div key={idx} className="flex items-start gap-2.5 leading-relaxed hover:bg-slate-900/60 p-0.5 rounded transition-colors">
                          <span className="text-slate-500 shrink-0 text-[11px]">
                            [{new Date(log.timestamp).toLocaleTimeString()}]
                          </span>
                          <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold shrink-0 uppercase ${
                            log.level === "success" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                            log.level === "warn" ? "bg-amber-950 text-amber-400 border border-amber-800" :
                            log.level === "error" ? "bg-rose-950 text-rose-400 border border-rose-800" :
                            "bg-blue-950 text-blue-400 border border-blue-800"
                          }`}>
                            {log.level}
                          </span>
                          <span className={`break-all ${
                            log.level === "error" ? "text-rose-300 font-semibold" :
                            log.level === "success" ? "text-emerald-300" :
                            log.level === "warn" ? "text-amber-300" :
                            "text-slate-300"
                          }`}>
                            {log.message}
                          </span>
                        </div>
                      ))
                    )}
                    <div ref={logEndRef} />
                  </div>
                </div>

              </div>
            ) : (
              <div className="bg-white border border-slate-200/90 rounded-2xl p-12 text-center text-slate-500 flex flex-col items-center justify-center min-h-[420px] shadow-sm">
                <Layers size={48} className="text-slate-300 mb-3" />
                <h3 className="text-base font-bold text-slate-800">선택된 배치 작업이 없습니다.</h3>
                <p className="text-xs text-slate-500 mt-1">
                  왼쪽 폼에서 유튜브 채널 또는 재생목록 URL을 입력하여 새 일괄 생성을 시작하세요.
                </p>
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
