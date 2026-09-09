"use client";

import React from "react";
import { Link as LinkIcon, Sparkles } from "lucide-react";
import { OptionsToolbar } from "./OptionsToolbar";
import { SummaryInsightCard } from "./SummaryInsightCard";
import { PresetInfo } from "./ViewerPresetMatrixModal";

interface VideoPanelProps {
  isLeftPanelOpen: boolean;
  embedUrl: string | null;
  url: string;
  title: string;
  profileMessage: string;
  sections: string[];
  summaryInsight: {
    totalSections: number;
    leadText: string;
    topics: string[];
  } | null;
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

export function VideoPanel({
  isLeftPanelOpen,
  embedUrl,
  url,
  title,
  profileMessage,
  sections,
  summaryInsight,
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
}: VideoPanelProps) {
  return (
    <div className={`flex-shrink-0 bg-surface border-r border-border-subtle flex flex-col p-6 overflow-y-auto transition-all duration-300 ease-in-out ${isLeftPanelOpen ? 'w-full lg:w-[40%] opacity-100' : 'w-0 opacity-0 px-0 border-r-0 hidden lg:flex'}`}>
      {(embedUrl || url) && (
        <div className="aspect-video w-full bg-black rounded-lg relative overflow-hidden mb-6 shadow-sm border border-border-subtle group">
          {embedUrl ? (
            <iframe 
              src={embedUrl} 
              className="w-full h-full border-none"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
              allowFullScreen
            />
          ) : (
            <div className="flex items-center justify-center p-8 w-full h-full">
              <a href={url} target="_blank" rel="noopener noreferrer" className="bg-primary-container text-on-primary px-6 py-3 rounded-full font-bold shadow-md hover:scale-105 transition-transform flex items-center gap-2">
                원본 문서 보기 <LinkIcon size={18}/>
              </a>
            </div>
          )}
        </div>
      )}

      <div className="flex-1">
        <h1 className="font-headline-lg text-headline-lg text-text-primary mb-2 leading-tight">{title}</h1>
        {profileMessage && (
          <p className="font-body-lg text-body-lg text-muted-foreground mb-6 flex items-center gap-2">
            <Sparkles className="text-primary-container" size={16} /> {profileMessage}
          </p>
        )}
        
        {/* Options Toolbar */}
        <OptionsToolbar 
          lengthPreset={lengthPreset}
          analogyPreset={analogyPreset}
          siblingPresets={siblingPresets}
          jobId={jobId}
          totalSiblingPresets={totalSiblingPresets}
          isInteractiveMode={isInteractiveMode}
          isRegenerating={isRegenerating}
          onLengthPresetChange={onLengthPresetChange}
          onAnalogyPresetChange={onAnalogyPresetChange}
          onOpenPresetMatrix={onOpenPresetMatrix}
          onToggleInteractiveMode={onToggleInteractiveMode}
          onRegenerate={onRegenerate}
          onNavigateToSibling={onNavigateToSibling}
        />
        
        {/* 주제 함축 소개 & 핵심 학습 개요 카드 */}
        <SummaryInsightCard 
          sections={sections}
          summaryInsight={summaryInsight}
          profileMessage={profileMessage}
        />
      </div>
    </div>
  );
}
