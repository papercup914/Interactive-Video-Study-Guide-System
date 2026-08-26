"use client";

import React, { useState } from "react";
import { useTask } from "@/app/contexts/TaskContext";
import { Loader2, CheckCircle, XCircle, ChevronUp, ChevronDown, ExternalLink, X } from "lucide-react";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";

export function TaskWidget() {
  const { status, progressText, errorMessage, isGenerating, jobId, clearTask, cancelTask } = useTask();
  const [expanded, setExpanded] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status === "completed" && pathname === `/guide/${jobId}`) {
      clearTask();
    }
  }, [status, pathname, jobId, clearTask]);

  if (status === "idle") return null;

  return (
    <div className="fixed bottom-4 right-4 left-4 md:left-auto md:w-80 z-50 transition-all duration-300">
      <div className={`bg-card border border-border shadow-2xl rounded-2xl overflow-hidden eink-border transition-all duration-300 ${expanded ? "p-4" : "p-3"}`}>
        
        {/* Header (Always visible) */}
        <div 
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center gap-3">
            {status === "processing" && <Loader2 className="animate-spin text-primary" size={20} />}
            {status === "completed" && <CheckCircle className="text-green-500" size={20} />}
            {status === "failed" && <XCircle className="text-destructive" size={20} />}
            {status === "cancelled" && <XCircle className="text-muted-foreground" size={20} />}
            
            <div className="flex flex-col">
              <span className="font-semibold text-sm">
                {status === "processing" ? "가이드 생성 중..." : 
                 status === "completed" ? "생성 완료!" : 
                 status === "cancelled" ? "생성 중단됨" : "생성 실패"}
              </span>
              {!expanded && status === "processing" && (
                <span className="text-xs text-muted-foreground truncate max-w-[150px] md:max-w-[200px]">
                  {progressText}
                </span>
              )}
              {!expanded && status === "failed" && errorMessage && (
                <span className="text-xs text-destructive truncate max-w-[150px] md:max-w-[200px]">
                  {errorMessage}
                </span>
              )}
            </div>
          </div>
          
          <button className="text-muted-foreground hover:text-foreground p-1 rounded-full hover:bg-muted transition-colors">
            {expanded ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
          </button>
        </div>

        {/* Expanded Content */}
        {expanded && (
          <div className="mt-4 pt-4 border-t border-border/50 animate-in fade-in slide-in-from-top-2">
            <p className="text-sm text-muted-foreground mb-4">
              {progressText}
            </p>
            {status === "failed" && errorMessage && (
              <div className="p-2 mb-4 bg-destructive/10 border border-destructive/20 rounded-lg text-xs text-destructive break-words">
                {errorMessage}
              </div>
            )}
            
            {status === "processing" && (
              <>
                <div className="w-full bg-muted rounded-full h-1.5 mb-2 overflow-hidden">
                  <div className="bg-primary h-1.5 rounded-full animate-pulse w-full"></div>
                </div>
                <button 
                  onClick={(e) => { e.stopPropagation(); cancelTask(); }}
                  className="w-full mt-3 bg-destructive/10 text-destructive text-sm font-semibold py-2 rounded-xl hover:bg-destructive/20 transition-opacity flex items-center justify-center gap-1"
                >
                  <X size={16} /> 작업 중단하기
                </button>
              </>
            )}

            {status === "completed" && (
              <div className="flex gap-2">
                <button 
                  onClick={() => {
                    clearTask();
                    router.push(`/guide/${jobId}`);
                  }}
                  className="flex-1 flex items-center justify-center gap-2 bg-primary text-primary-foreground text-sm font-semibold py-2 rounded-xl hover:opacity-90 transition-opacity eink-border"
                >
                  가이드 보기 <ExternalLink size={16} />
                </button>
                <button 
                  onClick={() => clearTask()}
                  className="flex-1 flex items-center justify-center bg-muted text-foreground text-sm font-semibold py-2 rounded-xl hover:bg-muted/80 transition-opacity"
                >
                  닫기
                </button>
              </div>
            )}

            {(status === "failed" || status === "cancelled") && (
              <button 
                onClick={() => clearTask()}
                className="w-full bg-muted text-foreground text-sm font-semibold py-2 rounded-xl hover:bg-muted/80 transition-opacity"
              >
                닫기
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
