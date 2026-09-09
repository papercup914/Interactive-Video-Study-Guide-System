"use client";

import React from "react";
import { Sparkles, BookOpen, CheckCircle2, ChevronRight, Loader2 } from "lucide-react";
import { LENGTH_PRESETS, ANALOGY_PRESETS } from "@/lib/presets";
import { PresetInfo } from "./ViewerPresetMatrixModal";

interface OptionsToolbarProps {
  lengthPreset: string;
  analogyPreset: string;
  siblingPresets: Record<string, PresetInfo>;
  jobId: string;
  totalSiblingPresets: number;
  isInteractiveMode: boolean;
  isRegenerating: boolean;
  onLengthPresetChange: (val: string) => void;
  onAnalogyPresetChange: (val: string) => void;
  onOpenPresetMatrix: () => void;
  onToggleInteractiveMode: () => void;
  onRegenerate: () => void;
  onNavigateToSibling: (siblingJobId: string) => void;
}

export function OptionsToolbar({
  lengthPreset,
  analogyPreset,
  siblingPresets,
  jobId,
  totalSiblingPresets,
  isInteractiveMode,
  isRegenerating,
  onLengthPresetChange,
  onAnalogyPresetChange,
  onOpenPresetMatrix,
  onToggleInteractiveMode,
  onRegenerate,
  onNavigateToSibling
}: OptionsToolbarProps) {
  const currentKey = `${lengthPreset}__${analogyPreset}`;
  const matchedSibling = siblingPresets[currentKey];
  const isMatchedAvailable = Boolean(matchedSibling);
  const isOtherExisting = isMatchedAvailable && matchedSibling.id !== jobId;
  const isUncreated = !isMatchedAvailable;

  return (
    <div className="bg-surface-container border border-border-subtle rounded-2xl p-3.5 mb-6 flex flex-wrap items-center gap-3 md:gap-4 shadow-sm">
      {/* 요약 분량 드롭다운 */}
      <div className="flex items-center gap-2 bg-surface px-3 py-1.5 rounded-xl border border-border-subtle/80 shadow-xs">
        <span className="font-body-sm text-xs font-semibold text-muted-foreground whitespace-nowrap">요약 분량</span>
        <select 
          className="bg-transparent border-none font-body-sm text-xs md:text-sm font-bold text-text-primary cursor-pointer focus:ring-0 py-0 pl-1 pr-6"
          value={lengthPreset}
          onChange={(e) => onLengthPresetChange(e.target.value)}
        >
          {LENGTH_PRESETS.map((lp) => (
            <option key={lp} value={lp}>{lp}</option>
          ))}
        </select>
      </div>

      {/* 설명 방식 드롭다운 */}
      <div className="flex items-center gap-2 bg-surface px-3 py-1.5 rounded-xl border border-border-subtle/80 shadow-xs">
        <span className="font-body-sm text-xs font-semibold text-muted-foreground whitespace-nowrap">설명 방식</span>
        <select 
          className="bg-transparent border-none font-body-sm text-xs md:text-sm font-bold text-text-primary cursor-pointer focus:ring-0 py-0 pl-1 pr-6"
          value={analogyPreset}
          onChange={(e) => onAnalogyPresetChange(e.target.value)}
        >
          {ANALOGY_PRESETS.map((ap) => (
            <option key={ap} value={ap}>{ap}</option>
          ))}
        </select>
      </div>

      {/* 9종 프리셋 탐색기 모달 트리거 버튼 */}
      <button 
        type="button"
        onClick={onOpenPresetMatrix}
        className="flex items-center gap-1.5 px-3 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-xl font-bold text-xs transition-colors border border-primary/20 cursor-pointer shadow-xs"
        title="9종 맞춤형 프리셋 전체보기"
      >
        <Sparkles size={14} className="text-primary" />
        <span className="hidden sm:inline">9종 프리셋 탐색기</span>
        <span className="sm:hidden">9종 탐색기</span>
        <span className="bg-primary text-white text-[10px] px-1.5 py-0.2 rounded-full font-extrabold ml-0.5">
          {totalSiblingPresets}/9
        </span>
      </button>

      {/* 인터랙티브 학습 모드 On/Off 토글 버튼 */}
      <button 
        type="button"
        onClick={onToggleInteractiveMode}
        className={`flex items-center gap-1.5 px-3 py-2 rounded-xl font-bold text-xs transition-colors border cursor-pointer shadow-xs ${
          isInteractiveMode 
            ? "bg-primary/10 hover:bg-primary/20 text-primary border-primary/20" 
            : "bg-surface-variant text-muted-foreground border-border-subtle hover:text-text-primary"
        }`}
        title={isInteractiveMode ? "파인만/퀴즈 등 인터랙티브 위젯을 숨기고 본문 읽기에 집중합니다." : "파인만/퀴즈 등 인터랙티브 학습 위젯을 다시 표시합니다."}
      >
        {isInteractiveMode ? <Sparkles size={14} className="text-primary" /> : <BookOpen size={14} />}
        <span>{isInteractiveMode ? "💡 인터랙티브 ON" : "📖 몰입 읽기 ON"}</span>
      </button>

      {/* 다른 생성된 프리셋이 선택되었을 때의 바로 이동 버튼 */}
      {isOtherExisting && (
        <button 
          onClick={() => onNavigateToSibling(matchedSibling.id)}
          className="ml-auto bg-primary text-white px-4 py-2 rounded-xl font-bold text-xs hover:bg-primary/90 transition-all flex items-center gap-1.5 shadow-sm hover:shadow"
        >
          <CheckCircle2 size={14} className="text-green-300" />
          <span>해당 버전으로 즉시 이동</span>
          <ChevronRight size={12} />
        </button>
      )}

      {/* 미생성 프리셋이 선택되었을 때의 재생성/새로 생성 버튼 */}
      {isUncreated && (
        <button 
          onClick={onRegenerate}
          disabled={isRegenerating}
          className="ml-auto bg-primary-container text-on-primary px-4 py-2 rounded-xl font-bold text-xs hover:bg-hover-indigo transition-colors flex items-center gap-2 disabled:opacity-50 shadow-sm"
        >
          {isRegenerating ? <Loader2 className="animate-spin" size={14}/> : <Sparkles size={14}/>}
          <span>새 버전으로 생성하기</span>
        </button>
      )}
    </div>
  );
}
