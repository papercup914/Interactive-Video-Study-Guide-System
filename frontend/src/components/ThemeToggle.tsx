"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Moon, Sun, BookOpen, PenTool } from "lucide-react";
import { cn } from "@/lib/utils";

export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="w-[140px] h-10"></div>; // Placeholder
  }

  return (
    <div className="flex items-center gap-1 bg-surface-container-low p-1 rounded-full border border-border-subtle">
      <button
        onClick={() => setTheme("light")}
        className={cn(
          "p-2 rounded-full transition-all flex items-center justify-center",
          theme === "light" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
        )}
        title="라이트 모드"
      >
        <Sun size={16} strokeWidth={2.5} />
      </button>
      <button
        onClick={() => setTheme("dark")}
        className={cn(
          "p-2 rounded-full transition-all flex items-center justify-center",
          theme === "dark" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
        )}
        title="다크 모드"
      >
        <Moon size={16} strokeWidth={2.5} />
      </button>
    </div>
  );
}
