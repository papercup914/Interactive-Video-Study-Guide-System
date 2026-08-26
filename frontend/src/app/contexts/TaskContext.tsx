"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";

interface TaskContextType {
  jobId: string | null;
  isGenerating: boolean;
  progressText: string;
  errorMessage: string | null;
  status: "idle" | "processing" | "completed" | "failed" | "cancelled";
  startTask: (id: string) => void;
  clearTask: () => void;
  cancelTask: () => void;
}

const TaskContext = createContext<TaskContextType | undefined>(undefined);

export function TaskProvider({ children }: { children: ReactNode }) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progressText, setProgressText] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "processing" | "completed" | "failed" | "cancelled">("idle");
  const router = useRouter();

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    if (isGenerating && jobId) {
      intervalId = setInterval(async () => {
        try {
          const res = await fetch(`/api/guide/status/${jobId}`);
          if (res.ok) {
            const data = await res.json();
            setProgressText(data.progress || "진행 중...");
            
            if (data.status === "completed") {
              setStatus("completed");
              setIsGenerating(false);
              clearInterval(intervalId);
            } else if (data.status === "failed") {
              setStatus("failed");
              setIsGenerating(false);
              if (data.error) {
                const firstLine = data.error.split("\n")[0];
                setErrorMessage(firstLine);
              }
              clearInterval(intervalId);
            } else if (data.status === "cancelled") {
              setStatus("cancelled");
              setIsGenerating(false);
              clearInterval(intervalId);
            } else {
              setStatus("processing");
            }
          } else {
            // Error handling for non-200
            try {
              const err = await res.json();
              if (err.detail === "Job not found") {
                clearInterval(intervalId);
                setIsGenerating(false);
                setStatus("failed");
                setProgressText("작업을 찾을 수 없습니다. (서버 재시작 등)");
              }
            } catch (e) {
              // Ignore proxy 500 errors
            }
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 2000);
    }

    return () => clearInterval(intervalId);
  }, [isGenerating, jobId]);

  const startTask = (id: string) => {
    setJobId(id);
    setIsGenerating(true);
    setStatus("processing");
    setProgressText("요청을 준비 중입니다...");
  };

  const clearTask = () => {
    setJobId(null);
    setIsGenerating(false);
    setStatus("idle");
    setProgressText("");
    setErrorMessage(null);
  };

  const cancelTask = async () => {
    if (jobId) {
      try {
        await fetch(`/api/guide/${jobId}/cancel`, { method: "POST" });
        setStatus("cancelled");
        setIsGenerating(false);
        setProgressText("작업이 중단되었습니다.");
      } catch (e) {
        console.error("Cancel failed", e);
      }
    }
  };

  return (
    <TaskContext.Provider value={{ jobId, isGenerating, progressText, errorMessage, status, startTask, clearTask, cancelTask }}>
      {children}
    </TaskContext.Provider>
  );
}

export function useTask() {
  const context = useContext(TaskContext);
  if (context === undefined) {
    throw new Error("useTask must be used within a TaskProvider");
  }
  return context;
}
