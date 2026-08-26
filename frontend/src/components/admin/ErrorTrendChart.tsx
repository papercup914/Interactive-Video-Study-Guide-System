'use client';

import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { TimeSeriesPoint } from '@/types/adminHealth';

export interface ErrorTrendChartProps {
  data?: TimeSeriesPoint[];
}

export function ErrorTrendChart({ data = [] }: ErrorTrendChartProps) {
  const [mounted, setMounted] = useState<boolean>(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="w-full h-64 sm:h-80 bg-slate-900/80 rounded-2xl border border-slate-800 p-4 flex items-center justify-center">
        <div className="animate-pulse flex items-center gap-2 text-slate-500 text-sm">
          <span>차트 컴포넌트 불러오는 중...</span>
        </div>
      </div>
    );
  }

  const chartData = data && data.length > 0 ? data : [];

  return (
    <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl flex flex-col justify-between space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-100">에러 및 경고 발생 추이</h3>
          <p className="text-xs text-slate-400">선택된 기간 동안의 시계열 빈도 분포</p>
        </div>
        <div className="flex items-center space-x-2 text-xs">
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />
            에러
          </span>
          <span className="flex items-center gap-1.5 text-slate-300 ml-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
            경고
          </span>
        </div>
      </div>

      <div className="w-full h-64 sm:h-80">
        {chartData.length === 0 ? (
          <div className="w-full h-full flex items-center justify-center text-slate-500 text-sm">
            사용 가능한 시계열 데이터가 없습니다
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorErrors" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="colorWarnings" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis
                dataKey="formattedTime"
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: '#475569' }}
              />
              <YAxis
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: '#475569' }}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '0.75rem',
                  color: '#f8fafc',
                  fontSize: '12px',
                  boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)',
                }}
                itemStyle={{ color: '#f8fafc' }}
                labelStyle={{ color: '#cbd5e1', fontWeight: 600, marginBottom: '4px' }}
              />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ display: 'none' }} />
              <Area
                type="monotone"
                dataKey="errorCount"
                name="Errors"
                stroke="#ef4444"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorErrors)"
              />
              <Area
                type="monotone"
                dataKey="warningCount"
                name="Warnings"
                stroke="#f59e0b"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorWarnings)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

export default ErrorTrendChart;
