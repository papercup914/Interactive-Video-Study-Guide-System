'use client';

import React, { useState, useEffect } from 'react';
import { AlertTriangle, Activity, CheckCircle2, Clock, ShieldAlert } from 'lucide-react';
import { SystemHealthSummary } from '@/types/adminHealth';

export interface HealthStatCardsProps {
  summary?: SystemHealthSummary | null;
}

export function HealthStatCards({ summary }: HealthStatCardsProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);
  const systemStatus = summary?.systemStatus ?? 'Healthy';
  const totalErrors = summary?.totalErrors ?? 0;
  const errorRate = summary?.errorRate ?? 0;
  const totalWarnings = summary?.totalWarnings ?? 0;
  const avgLatencyMs = summary?.avgLatencyMs ?? 0;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Critical':
        return {
          label: '치명적 시스템 경고',
          bg: 'bg-red-500/10 text-red-400 border-red-500/30',
          icon: <ShieldAlert className="w-5 h-5 text-red-400" />,
        };
      case 'Degraded':
        return {
          label: '성능 저하',
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          icon: <AlertTriangle className="w-5 h-5 text-amber-400" />,
        };
      case 'Healthy':
      default:
        return {
          label: '모든 시스템 정상',
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          icon: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
        };
    }
  };

  const statusBadge = getStatusBadge(systemStatus);

  return (
    <div className="space-y-4">
      {/* System Status Banner / Badge Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 bg-slate-900/90 rounded-2xl border border-slate-800 backdrop-blur-md gap-3">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-xl border ${statusBadge.bg}`}>
            {statusBadge.icon}
          </div>
          <div>
            <div className="text-xs uppercase tracking-wider text-slate-400 font-medium">시스템 상태</div>
            <div className="text-lg font-bold text-slate-100 flex items-center gap-2">
              {systemStatus}
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusBadge.bg}`}>
                {statusBadge.label}
              </span>
            </div>
          </div>
        </div>
        {summary?.lastUpdated && (
          <div className="text-xs text-slate-400 self-end sm:self-auto">
            업데이트됨: {isMounted ? new Date(summary.lastUpdated).toLocaleTimeString() : ''}
          </div>
        )}
      </div>

      {/* Responsive Grid of Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Errors Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">총 에러 발생</span>
            <div className="p-2.5 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-3xl font-extrabold text-slate-100 tracking-tight">{totalErrors}</div>
            <div className="text-xs text-slate-400 mt-1">치명적 & 에러 로그</div>
          </div>
        </div>

        {/* Error Rate Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">에러 발생률</span>
            <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-3xl font-extrabold text-slate-100 tracking-tight">{errorRate}%</div>
            <div className="text-xs text-slate-400 mt-1">전체 로그 대비 비율</div>
          </div>
        </div>

        {/* Active Warnings Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">활성 경고</span>
            <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-3xl font-extrabold text-slate-100 tracking-tight">{totalWarnings}</div>
            <div className="text-xs text-slate-400 mt-1">비차단성 경고 로그</div>
          </div>
        </div>

        {/* Avg Latency Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">평균 지연 시간</span>
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-3xl font-extrabold text-slate-100 tracking-tight">{avgLatencyMs} <span className="text-lg font-medium text-slate-400">ms</span></div>
            <div className="text-xs text-slate-400 mt-1">평균 시스템 응답 시간</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HealthStatCards;
