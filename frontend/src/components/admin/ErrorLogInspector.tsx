'use client';

import React, { useState } from 'react';
import {
  Search,
  Filter,
  AlertCircle,
  AlertTriangle,
  Info,
  ShieldAlert,
  ChevronRight,
  X,
  RefreshCw,
  Terminal,
  CheckCircle,
} from 'lucide-react';
import { LogLevel, SystemLogEntry } from '@/types/adminHealth';

export interface ErrorLogInspectorProps {
  logs?: SystemLogEntry[];
  onRefresh?: () => void;
  activeLevel?: LogLevel | 'ALL';
  onLevelChange?: (level: LogLevel | 'ALL') => void;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  isLoading?: boolean;
}

export function ErrorLogInspector({
  logs = [],
  onRefresh,
  activeLevel: propLevel,
  onLevelChange,
  searchQuery: propQuery,
  onSearchChange,
  isLoading = false,
}: ErrorLogInspectorProps) {
  const [internalLevel, setInternalLevel] = useState<LogLevel | 'ALL'>('ALL');
  const [internalQuery, setInternalQuery] = useState<string>('');
  const [selectedLog, setSelectedLog] = useState<SystemLogEntry | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  React.useEffect(() => {
    setIsMounted(true);
  }, []);

  const activeLevel = propLevel !== undefined ? propLevel : internalLevel;
  const activeQuery = propQuery !== undefined ? propQuery : internalQuery;

  const handleLevelSelect = (level: LogLevel | 'ALL') => {
    if (onLevelChange) {
      onLevelChange(level);
    } else {
      setInternalLevel(level);
    }
  };

  const handleSearchInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (onSearchChange) {
      onSearchChange(val);
    } else {
      setInternalQuery(val);
    }
  };

  // Filter logs locally if propLevel / propQuery are not driven externally
  const filteredLogs = logs.filter((log) => {
    if (!log) return false;

    // Level filter
    if (activeLevel !== 'ALL') {
      const targetLvl = activeLevel.toLowerCase();
      const logLvl = log.level.toLowerCase();
      if (logLvl !== targetLvl) {
        return false;
      }
    }

    // Search query filter
    if (activeQuery && activeQuery.trim()) {
      const q = activeQuery.toLowerCase().trim();
      const msgMatch = (log.message || '').toLowerCase().includes(q);
      const detailMatch = (log.details || '').toLowerCase().includes(q);
      const sourceMatch = (log.source || '').toLowerCase().includes(q);
      const jobMatch = (log.jobId || '').toLowerCase().includes(q);
      const catMatch = (log.category || '').toLowerCase().includes(q);

      if (!msgMatch && !detailMatch && !sourceMatch && !jobMatch && !catMatch) {
        return false;
      }
    }

    return true;
  });

  const getLevelBadge = (level: LogLevel) => {
    switch (level) {
      case 'critical':
        return {
          bg: 'bg-red-500/10 text-red-400 border-red-500/30',
          icon: <ShieldAlert className="w-3.5 h-3.5" />,
          label: 'CRITICAL',
        };
      case 'error':
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          icon: <AlertCircle className="w-3.5 h-3.5" />,
          label: 'ERROR',
        };
      case 'warning':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          icon: <AlertTriangle className="w-3.5 h-3.5" />,
          label: 'WARN',
        };
      case 'info':
      default:
        return {
          bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
          icon: <Info className="w-3.5 h-3.5" />,
          label: 'INFO',
        };
    }
  };

  const levelTabs: { id: LogLevel | 'ALL'; label: string }[] = [
    { id: 'ALL', label: 'ALL' },
    { id: 'critical', label: 'CRITICAL' },
    { id: 'error', label: 'ERROR' },
    { id: 'warning', label: 'WARN' },
  ];

  return (
    <div className="w-full px-0 md:px-4 rounded-none md:rounded-2xl border-x-0 md:border border-slate-800 bg-slate-900/90 shadow-xl overflow-hidden">
      {/* Inspector Header & Controls */}
      <div className="p-4 sm:p-5 border-b border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Terminal className="w-5 h-5 text-indigo-400" />
              시스템 에러 로그 인스펙터
            </h3>
            <p className="text-xs text-slate-400">실시간 운영 로그 스트림 및 에러 스택 트레이스</p>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              로그 새로고침
            </button>
          )}
        </div>

        {/* Filters Bar: Level Tabs + Live Search Input */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Level Filter Tabs */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800 overflow-x-auto scrollbar-hide">
            {levelTabs.map((tab) => {
              const isActive = activeLevel === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleLevelSelect(tab.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Live Search Input */}
          <div className="relative flex-1 max-w-full md:max-w-xs">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              id="log-search-input"
              name="search"
              type="text"
              value={activeQuery}
              onChange={handleSearchInput}
              placeholder="로그, 작업, 세부 정보 검색..."
              className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all"
            />
            {activeQuery && (
              <button
                onClick={() => (onSearchChange ? onSearchChange('') : setInternalQuery(''))}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Logs Table View */}
      <div className="overflow-x-auto">
        {filteredLogs.length === 0 ? (
          <div className="py-12 px-4 text-center">
            <Filter className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-sm font-medium text-slate-400">조건에 맞는 로그 항목이 없습니다</p>
            <p className="text-xs text-slate-500 mt-1">활성 필터나 검색어를 조정해 보세요</p>
          </div>
        ) : (
          <table className="w-full text-left text-xs text-slate-300 border-collapse">
            <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800 font-semibold">
              <tr>
                <th className="py-3 px-4">등급 (Level)</th>
                <th className="py-3 px-4">시간 (Timestamp)</th>
                <th className="py-3 px-4">카테고리</th>
                <th className="py-3 px-4">메시지</th>
                <th className="py-3 px-4 hidden sm:table-cell">출처</th>
                <th className="py-3 px-4 hidden md:table-cell">작업 ID</th>
                <th className="py-3 px-4 text-right">작업</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filteredLogs.map((log) => {
                const badge = getLevelBadge(log.level);
                return (
                  <tr
                    key={log.id}
                    onClick={() => setSelectedLog(log)}
                    className="hover:bg-slate-800/50 transition-colors cursor-pointer group"
                  >
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${badge.bg}`}
                      >
                        {badge.icon}
                        {badge.label}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-slate-400">
                      {isMounted ? new Date(log.timestamp).toLocaleTimeString() : ''}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap font-semibold text-slate-200">
                      {log.category}
                    </td>
                    <td className="py-3 px-4 text-slate-200 max-w-xs sm:max-w-md truncate font-sans">
                      {log.message}
                    </td>
                    <td className="py-3 px-4 hidden sm:table-cell whitespace-nowrap text-slate-400">
                      {log.source}
                    </td>
                    <td className="py-3 px-4 hidden md:table-cell whitespace-nowrap text-indigo-400">
                      {log.jobId || '—'}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedLog(log);
                        }}
                        className="p-1 rounded-lg hover:bg-slate-700 text-slate-400 group-hover:text-indigo-400 transition-colors"
                        title="스택 트레이스 조사"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer Log Counter */}
      <div className="p-3 bg-slate-950/60 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <span>전체 {logs.length}개 로그 중 {filteredLogs.length}개 표시 중</span>
        <span className="text-[11px] text-slate-500">스택 세부 정보를 보려면 행을 클릭하세요</span>
      </div>

      {/* Expandable Stack Trace Modal / Drawer */}
      {selectedLog && (
        <div
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-2 sm:p-4 animate-in fade-in duration-200"
          onClick={() => setSelectedLog(null)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
          >
            {/* Modal Header */}
            <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950">
              <div className="flex items-center space-x-3">
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${
                    getLevelBadge(selectedLog.level).bg
                  }`}
                >
                  {getLevelBadge(selectedLog.level).icon}
                  {getLevelBadge(selectedLog.level).label}
                </span>
                <div>
                  <h4 className="text-sm sm:text-base font-bold text-slate-100">{selectedLog.category}</h4>
                  <p className="text-xs text-slate-400">Log ID: {selectedLog.id}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-4 sm:p-6 space-y-4 overflow-y-auto font-sans">
              {/* Metadata Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs">
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">발생 시간 (Timestamp)</span>
                  <span className="text-slate-200 font-mono font-medium">
                    {isMounted ? new Date(selectedLog.timestamp).toLocaleString() : ''}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">출처 (Source)</span>
                  <span className="text-slate-200 font-medium">{selectedLog.source}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">작업 ID (Job ID)</span>
                  <span className="text-indigo-400 font-mono font-medium">{selectedLog.jobId || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">상태 코드 (Status)</span>
                  <span className="text-slate-200 font-mono font-medium">
                    {selectedLog.statusCode ? `${selectedLog.statusCode}` : 'N/A'}
                  </span>
                </div>
              </div>

              {/* Message Banner */}
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  로그 메시지
                </label>
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm font-medium">
                  {selectedLog.message}
                </div>
              </div>

              {/* Stack Trace / Details Code Block */}
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  스택 트레이스 및 진단 세부 정보
                </label>
                {selectedLog.details ? (
                  <pre className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono text-emerald-400 whitespace-pre-wrap overflow-x-auto leading-relaxed max-h-60">
                    {selectedLog.details}
                  </pre>
                ) : (
                  <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-500 italic">
                    이 로그 항목에 기록된 세부 스택 트레이스가 없습니다.
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                {selectedLog.resolved ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    상태: 해결됨
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    상태: 활성 / 미해결
                  </>
                )}
              </span>
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl text-xs transition-colors"
              >
                인스펙터 닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ErrorLogInspector;
