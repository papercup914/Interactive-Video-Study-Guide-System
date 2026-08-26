'use client';

import React from 'react';
import { Activity, RefreshCw, Clock, ShieldCheck } from 'lucide-react';
import { useAdminHealth } from '@/hooks/useAdminHealth';
import { HealthStatCards } from '@/components/admin/HealthStatCards';
import { ErrorTrendChart } from '@/components/admin/ErrorTrendChart';
import { ErrorTypeBreakdownChart } from '@/components/admin/ErrorTypeBreakdownChart';
import { ErrorLogInspector } from '@/components/admin/ErrorLogInspector';

export default function AdminHealthPage() {
  const {
    data,
    loading,
    refresh,
    timeRange,
    setTimeRange,
    level,
    setLevel,
    searchQuery,
    setSearchQuery,
  } = useAdminHealth({ autoRefreshMs: 15000 });

  const timeRanges: ('24h' | '7d' | '30d')[] = ['24h', '7d', '30d'];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Dashboard Top Navigation Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-2xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight text-white flex items-center gap-2">
                시스템 상태 및 에러 모니터
                <span className="text-xs px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                  관리자 라우트
                </span>
              </h1>
              <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
                실시간 운영 로그, 에러 빈도 분석 및 시스템 진단
              </p>
            </div>
          </div>
        </div>

        {/* Time Range Selector & Manual Refresh Button */}
        <div className="flex items-center space-x-3 self-start md:self-auto">
          {/* Time Range Selector */}
          <div className="flex items-center p-1 bg-slate-900 border border-slate-800 rounded-xl space-x-1">
            <Clock className="w-3.5 h-3.5 text-slate-500 ml-2 mr-1" />
            {timeRanges.map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  timeRange === range
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                {range}
              </button>
            ))}
          </div>

          {/* Manual Refresh Button */}
          <button
            onClick={refresh}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50 active:scale-95"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? '새로고침 중...' : '새로고침'}</span>
          </button>
        </div>
      </header>

      {/* 1. Summary Health Stat Cards */}
      <section>
        <HealthStatCards summary={data?.summary} />
      </section>

      {/* 2. Visualizations Grid (AreaChart & DonutChart) */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ErrorTrendChart data={data?.timeSeries} />
        <ErrorTypeBreakdownChart data={data?.categoryBreakdown} />
      </section>

      {/* 3. Interactive Error Log Inspector */}
      <section>
        <ErrorLogInspector
          logs={data?.logs}
          onRefresh={refresh}
          activeLevel={level}
          onLevelChange={setLevel}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          isLoading={loading}
        />
      </section>

      {/* Footer */}
      <footer className="pt-6 border-t border-slate-800 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Interactive Video Study Guide System — 상태 진단 서브시스템</span>
        </div>
        <div>
          <span>Route: /admin/health</span>
        </div>
      </footer>
    </div>
  );
}
