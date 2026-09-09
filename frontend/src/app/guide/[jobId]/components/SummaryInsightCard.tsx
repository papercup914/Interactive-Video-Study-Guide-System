"use client";

import React from "react";
import { BookOpen } from "lucide-react";

interface SummaryInsightCardProps {
  sections: string[];
  summaryInsight: {
    totalSections: number;
    leadText: string;
    topics: string[];
  } | null;
  profileMessage?: string;
}

export function SummaryInsightCard({
  sections,
  summaryInsight,
  profileMessage
}: SummaryInsightCardProps) {
  return (
    <div className="bg-surface-container border border-border-subtle rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex items-center justify-between gap-2 mb-3 pb-2.5 border-b border-border-subtle/60">
        <div className="flex items-center gap-2">
          <span className="p-1.5 rounded-lg bg-primary/10 text-primary font-bold">
            <BookOpen size={16} />
          </span>
          <h3 className="font-bold text-sm text-text-primary">
            핵심 주제 및 학습 개요
          </h3>
        </div>
        {sections.length > 0 && (
          <span className="text-[11px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
            총 {sections.length}개 챕터
          </span>
        )}
      </div>

      {summaryInsight?.leadText ? (
        <p className="text-xs md:text-sm text-text-secondary leading-relaxed mb-4 break-keep font-medium">
          {summaryInsight.leadText}
        </p>
      ) : (
        <p className="text-xs text-muted-foreground leading-relaxed mb-4 font-medium">
          {profileMessage || "본 영상의 핵심 원리와 실무 활용법을 체계적으로 분석한 맞춤형 학습 가이드입니다."}
        </p>
      )}

      {/* 챕터 핵심 커리큘럼 로드맵 */}
      {sections.length > 0 && (
        <div className="flex flex-col gap-1.5 pt-2.5 border-t border-border-subtle/40">
          <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">주요 학습 커리큘럼</span>
          <div className="flex flex-wrap gap-1.5">
            {sections.slice(0, 5).map((sec, idx) => (
              <a
                key={idx}
                href={`#chapter-${idx}`}
                className="text-[11px] bg-surface hover:bg-surface-variant text-text-primary px-2.5 py-1 rounded-lg border border-border-subtle transition-colors truncate max-w-[200px]"
                title={sec}
              >
                {idx + 1}. {sec}
              </a>
            ))}
            {sections.length > 5 && (
              <span className="text-[11px] text-muted-foreground px-1.5 py-1 font-semibold">
                +{sections.length - 5}개 더보기
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
