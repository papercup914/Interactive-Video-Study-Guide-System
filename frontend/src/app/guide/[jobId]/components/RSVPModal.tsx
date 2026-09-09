"use client";

import React from "react";
import { Sparkles, X, Rewind, Pause, Play } from "lucide-react";

interface RSVPModalProps {
  section: string;
  rsvp: {
    aligned: { left: string; pivot: string; right: string };
    isPlaying: boolean;
    wpm: number;
    progress: number;
    toggle: () => void;
    reset: () => void;
    seek: (progress: number) => void;
    setWpm: (wpm: number) => void;
  };
  onClose: () => void;
}

export function RSVPModal({ section, rsvp, onClose }: RSVPModalProps) {
  return (
    <div className="fixed inset-0 bg-surface/95 backdrop-blur-md z-[300] flex flex-col ">
      {/* Header */}
      <div className="p-4 md:p-6 flex items-center justify-between border-b border-border-subtle">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2 text-text-primary">
            <Sparkles className="text-primary-container"/> 속독 모드 (RSVP)
          </h2>
          <p className="text-sm text-muted-foreground">{section}</p>
        </div>
        <button onClick={onClose} className="p-2 bg-surface-container-low rounded-full hover:bg-error/10 hover:text-error transition-colors">
          <X size={24} />
        </button>
      </div>

      {/* Main Area */}
      <div className="flex-1 flex flex-col items-center justify-center p-4 relative cursor-pointer" onClick={rsvp.toggle}>
         <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl px-4 flex justify-center items-center pointer-events-none">
            <div className="w-full flex items-baseline">
               {/* Left Pad */}
               <div className="flex-1 text-right text-5xl md:text-7xl font-bold text-text-primary opacity-80">
                  {rsvp.aligned.left}
               </div>
               {/* Pivot */}
               <div className="text-5xl md:text-7xl font-bold text-primary-container">
                  {rsvp.aligned.pivot}
               </div>
               {/* Right Pad */}
               <div className="flex-1 text-left text-5xl md:text-7xl font-bold text-text-primary opacity-80">
                  {rsvp.aligned.right}
               </div>
            </div>
         </div>
         {!rsvp.isPlaying && (
            <div className="absolute top-2/3 mt-12 flex items-center gap-2 text-muted-foreground font-semibold animate-pulse pointer-events-none">
              화면을 탭하여 시작/일시정지
            </div>
         )}
      </div>

      {/* Controls */}
      <div className="p-6 md:p-8 bg-surface border-t border-border-subtle flex flex-col gap-6 max-w-3xl w-full mx-auto rounded-t-2xl shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.1)]">
         <div className="flex items-center justify-between gap-4">
            <button onClick={rsvp.reset} className="text-muted-foreground hover:text-text-primary">
              <Rewind size={24} />
            </button>
            <button onClick={rsvp.toggle} className="w-16 h-16 rounded-full bg-primary-container text-on-primary flex items-center justify-center shadow-md shadow-primary-container/20 hover:scale-105 active:scale-95 transition-all">
              {rsvp.isPlaying ? <Pause size={32} /> : <Play size={32} className="ml-1" />}
            </button>
            <div className="flex flex-col items-center gap-1 w-32">
              <span className="text-xs font-bold text-muted-foreground">속도: {rsvp.wpm} WPM</span>
              <input type="range" min="150" max="800" step="10" value={rsvp.wpm} onChange={(e) => rsvp.setWpm(Number(e.target.value))} className="w-full accent-primary-container" />
            </div>
         </div>
         
         {/* Progress Bar */}
         <div className="flex items-center gap-3">
           <span className="text-xs font-bold text-muted-foreground w-12 text-right">{(rsvp.progress * 100).toFixed(0)}%</span>
           <div className="flex-1 h-3 bg-surface-container-highest rounded-full overflow-hidden relative cursor-pointer group" onClick={(e) => {
             const rect = e.currentTarget.getBoundingClientRect();
             const x = e.clientX - rect.left;
             rsvp.seek(x / rect.width);
           }}>
             <div className="absolute inset-0 bg-primary-container/10 group-hover:bg-primary-container/20 transition-colors"></div>
             <div className="h-full bg-primary-container transition-all duration-150 ease-out" style={{ width: `${rsvp.progress * 100}%` }}></div>
           </div>
         </div>
      </div>
    </div>
  );
}
