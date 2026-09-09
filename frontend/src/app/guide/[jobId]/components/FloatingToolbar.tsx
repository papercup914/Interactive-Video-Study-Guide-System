"use client";

import React from "react";
import { Sparkles } from "lucide-react";

export type SelectionState = {
  text: string;
  section: string;
  contextText: string;
  x: number;
  y: number;
  show: boolean;
};

interface FloatingToolbarProps {
  selection: SelectionState;
  qaModalOpen: boolean;
  onAnnotate: (type: 'highlight' | 'scribble' | 'margin-note') => void;
  onOpenQA: () => void;
}

export function FloatingToolbar({
  selection,
  qaModalOpen,
  onAnnotate,
  onOpenQA
}: FloatingToolbarProps) {
  if (!selection.show || qaModalOpen) {
    return null;
  }

  return (
    <div
      className="floating-toolbar absolute z-[200] bg-primary-container text-on-primary shadow-xl rounded-full px-2 py-1.5 font-bold flex items-center gap-1 hover:scale-105 transition-transform transform -translate-x-1/2 -translate-y-full"
      style={{ left: selection.x, top: selection.y - 10 }}
    >
      <button 
        onClick={() => onAnnotate('highlight')} 
        className="p-2 hover:bg-white/20 rounded-full transition-colors flex items-center gap-1 text-sm whitespace-nowrap" 
        title="형광펜 칠하기"
      >
        🟨 형광펜
      </button>
      <div className="w-[1px] h-4 bg-white/30 mx-1"></div>
      <button 
        onClick={() => onAnnotate('scribble')} 
        className="p-2 hover:bg-white/20 rounded-full transition-colors flex items-center gap-1 text-sm whitespace-nowrap" 
        title="동그라미 치기"
      >
        🔴 동그라미
      </button>
      <div className="w-[1px] h-4 bg-white/30 mx-1"></div>
      <button 
        onClick={() => onAnnotate('margin-note')} 
        className="p-2 hover:bg-white/20 rounded-full transition-colors flex items-center gap-1 text-sm whitespace-nowrap" 
        title="포스트잇 남기기"
      >
        📝 포스트잇
      </button>
      <div className="w-[1px] h-4 bg-white/30 mx-1"></div>
      <button 
        onClick={onOpenQA} 
        className="p-2 hover:bg-white/20 rounded-full transition-colors flex items-center gap-1 text-sm whitespace-nowrap" 
        title="AI에게 질문하기"
      >
        <Sparkles size={16} /> Q&A
      </button>
    </div>
  );
}
