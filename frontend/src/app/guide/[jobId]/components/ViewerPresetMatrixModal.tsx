"use client";

import React from "react";
import { Sparkles, X, CheckCircle2, ChevronRight } from "lucide-react";
import { 
  LENGTH_PRESETS, 
  ANALOGY_PRESETS, 
  normalizeLength, 
  normalizeAnalogy 
} from "@/lib/presets";

export type PresetInfo = {
  id: string;
  title: string;
  url: string;
  date: string;
  length_preset: string;
  analogy_preset: string;
  chapter_count: number;
  provider: string;
  image_url?: string;
  video_duration?: string;
};

interface ViewerPresetMatrixModalProps {
  title: string;
  currentJobId: string;
  presets: Record<string, PresetInfo>;
  totalPresets: number;
  currentLengthPreset: string;
  currentAnalogyPreset: string;
  onClose: () => void;
  onSelectGuide: (jobId: string) => void;
  onCreatePreset: (length: string, analogy: string) => void;
}

/**
 * 가이드 상세 뷰어 전용 9종 프리셋 매트릭스 탐색 모달
 */
export function ViewerPresetMatrixModal({
  title,
  currentJobId,
  presets,
  totalPresets,
  currentLengthPreset,
  currentAnalogyPreset,
  onClose,
  onSelectGuide,
  onCreatePreset
}: ViewerPresetMatrixModalProps) {
  // 1. 모든 presets 항목들을 3x3 키로 정규화하여 맵 구축
  const normalizedMap: Record<string, PresetInfo> = {};
  if (presets && typeof presets === "object") {
    Object.values(presets).forEach((item) => {
      if (!item) return;
      const l = normalizeLength(item.length_preset);
      const a = normalizeAnalogy(item.analogy_preset);
      normalizedMap[`${l}__${a}`] = {
        ...item,
        length_preset: l,
        analogy_preset: a
      };
    });
  }

  // 2. 현재 열람 중인 jobId가 매트릭스에 없더라도 현재 위치에 주입
  const curL = normalizeLength(currentLengthPreset);
  const curA = normalizeAnalogy(currentAnalogyPreset);
  const currentKey = `${curL}__${curA}`;
  if (!normalizedMap[currentKey]) {
    normalizedMap[currentKey] = {
      id: currentJobId,
      title: title,
      url: "",
      date: new Date().toISOString(),
      length_preset: curL,
      analogy_preset: curA,
      chapter_count: 0,
      provider: "youtube"
    };
  }

  const effectiveTotal = Math.max(totalPresets || 0, Object.keys(normalizedMap).length, 1);

  // 3. 타이틀 클린업
  let rawTitle = title || "";
  if (!rawTitle || rawTitle === "YouTube 학습 가이드" || rawTitle === "AI 맞춤형 학습 가이드" || rawTitle.trim() === "- YouTube") {
    const firstWithTitle = Object.values(normalizedMap).find(it => it.title && it.title !== "YouTube 학습 가이드" && it.title !== "AI 맞춤형 학습 가이드" && it.title.trim() !== "- YouTube");
    if (firstWithTitle && firstWithTitle.title) {
      rawTitle = firstWithTitle.title;
    }
  }
  const displayTitle = rawTitle.replace(/^-\s*YouTube$/i, 'YouTube 학습 가이드').replace(/-\s*YouTube$/i, '').trim() || "YouTube 학습 가이드";

  return (
    <div className="fixed inset-0 bg-black/60 z-[110] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-surface w-full max-w-2xl rounded-2xl p-6 shadow-2xl border border-border-subtle" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="flex justify-between items-start mb-4 pb-3 border-b border-border-subtle">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-primary/10 text-primary text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                <Sparkles size={12} /> 9종 프리셋 탐색기
              </span>
              <span className="text-xs text-muted-foreground">총 {effectiveTotal}개 프리셋 보유</span>
            </div>
            <h3 className="font-bold text-base text-text-primary line-clamp-1">{displayTitle}</h3>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-text-primary p-1.5 rounded-lg hover:bg-surface-variant transition-colors">
            <X size={20} />
          </button>
        </div>

        <p className="text-xs text-muted-foreground mb-4">
          원하는 <b>요약 분량</b>과 <b>설명 방식</b>의 조합을 클릭하면 해당 맞춤형 학습 가이드로 즉시 이동합니다.
        </p>

        {/* 3x3 Preset Grid */}
        <div className="grid grid-cols-3 gap-3">
          {LENGTH_PRESETS.map((length) => (
            <div key={length} className="flex flex-col gap-2">
              <div className="bg-surface-variant text-center font-bold text-xs py-1.5 rounded-lg text-text-primary">
                {length}
              </div>
              <div className="flex flex-col gap-2">
                {ANALOGY_PRESETS.map((analogy) => {
                  const key = `${length}__${analogy}`;
                  const item = normalizedMap[key];
                  const isAvailable = Boolean(item);
                  const isCurrent = item?.id === currentJobId || (!item && key === currentKey);

                  return (
                    <button
                      key={analogy}
                      onClick={() => {
                        if (isAvailable && item && item.id !== currentJobId) {
                          onSelectGuide(item.id);
                        } else if (!isAvailable) {
                          onCreatePreset(length, analogy);
                        }
                      }}
                      className={`p-2.5 rounded-xl border text-left flex flex-col justify-between min-h-[76px] transition-all relative ${
                        isCurrent
                          ? "bg-primary/10 border-primary shadow-sm ring-2 ring-primary/20 cursor-default"
                          : isAvailable
                          ? "bg-surface border-border-subtle hover:border-primary hover:shadow-md cursor-pointer group/card"
                          : "bg-surface-container-lowest/50 border-dashed border-border-subtle/50 opacity-50 hover:opacity-80 hover:border-primary/40 cursor-pointer"
                      }`}
                    >
                      <div className="flex items-center justify-between w-full">
                        <span className={`font-semibold text-[11px] ${isCurrent ? "text-primary font-bold" : "text-text-primary group-hover/card:text-primary"} transition-colors`}>
                          {analogy}
                        </span>
                        {isCurrent ? (
                          <span className="text-[9px] font-bold bg-primary text-white px-1.5 py-0.2 rounded-full shrink-0">
                            현재 열람 중
                          </span>
                        ) : isAvailable ? (
                          <CheckCircle2 size={13} className="text-green-500 shrink-0" />
                        ) : (
                          <span className="text-[9px] text-muted-foreground">미생성</span>
                        )}
                      </div>
                      <div className="flex items-center justify-between mt-1 text-[10px]">
                        {isCurrent ? (
                          <span className="text-primary font-bold">{item?.chapter_count ? `${item.chapter_count}개 챕터` : '열람 중'}</span>
                        ) : isAvailable && item ? (
                          <>
                            <span className="text-muted-foreground">{item.chapter_count}개 챕터</span>
                            <span className="text-primary font-bold flex items-center">
                              보기 <ChevronRight size={10} />
                            </span>
                          </>
                        ) : (
                          <span className="text-muted-foreground text-[9px] hover:text-primary">클릭하여 생성</span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-3 border-t border-border-subtle flex justify-between items-center text-xs text-muted-foreground">
          <span>* 비유/분량에 따라 AI 설명 톤과 깊이가 최적화되어 있습니다.</span>
          <button
            onClick={onClose}
            className="bg-foreground text-background px-4 py-2 rounded-lg font-bold hover:opacity-90 transition-opacity"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}
