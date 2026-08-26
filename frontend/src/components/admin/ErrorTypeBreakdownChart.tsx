'use client';

import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { CategoryBreakdown } from '@/types/adminHealth';

export interface ErrorTypeBreakdownChartProps {
  data?: CategoryBreakdown[];
}

export function ErrorTypeBreakdownChart({ data = [] }: ErrorTypeBreakdownChartProps) {
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

  // Filter non-zero items for clear donut chart display
  const activeData = (data || []).filter((item) => item && item.count > 0);
  const displayData = activeData.length > 0 ? activeData : (data || []);

  return (
    <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl flex flex-col justify-between space-y-4">
      <div>
        <h3 className="text-base font-bold text-slate-100">카테고리별 분석</h3>
        <p className="text-xs text-slate-400">에러 유형 및 하위 시스템 장애 분포</p>
      </div>

      <div className="w-full h-64 sm:h-80">
        {displayData.length === 0 ? (
          <div className="w-full h-full flex items-center justify-center text-slate-500 text-sm">
            기록된 카테고리 로그 데이터가 없습니다
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const item = payload[0].payload as CategoryBreakdown;
                    return (
                      <div className="bg-slate-900 border border-slate-700 rounded-xl p-3 shadow-xl text-xs">
                        <div className="font-semibold text-slate-200 flex items-center gap-2">
                          <span
                            className="w-2.5 h-2.5 rounded-full inline-block"
                            style={{ backgroundColor: item.color }}
                          />
                          {item.category}
                        </div>
                        <div className="mt-1 text-slate-400">
                          발생 횟수: <span className="text-slate-100 font-medium">{item.count}</span> ({item.percentage}%)
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend
                verticalAlign="bottom"
                height={48}
                formatter={(value: string, entry: unknown) => {
                  const payload = (entry as { payload?: CategoryBreakdown }).payload;
                  return (
                    <span className="text-xs text-slate-300 ml-1">
                      {value} {payload ? `(${payload.count})` : ''}
                    </span>
                  );
                }}
              />
              <Pie
                data={displayData}
                dataKey="count"
                nameKey="category"
                cx="50%"
                cy="45%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={3}
                stroke="#0f172a"
                strokeWidth={2}
              >
                {displayData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color || '#6b7280'} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

export default ErrorTypeBreakdownChart;
