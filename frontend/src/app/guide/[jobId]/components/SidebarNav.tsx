"use client";

import React from "react";
import { ArrowLeft, List } from "lucide-react";

interface SidebarNavProps {
  sections: string[];
  router: any;
  isFloating?: boolean;
}

export function SidebarNav({ sections, router, isFloating = false }: SidebarNavProps) {
  return (
    <div className={`sticky top-24 premium-glass rounded-[2rem] p-6 shadow-sm max-h-[80vh] overflow-y-auto ${isFloating ? '' : 'w-64'}`}>
      <button 
        onClick={() => router.push("/")}
        className="flex items-center gap-2 text-muted-foreground hover:text-foreground hover:bg-muted p-2 rounded-full transition-all mb-6 font-bold text-sm w-full"
      >
        <ArrowLeft size={16} /> 서재로 돌아가기
      </button>
      
      <h3 className="font-bold flex items-center gap-2 mb-4 text-primary">
        <List size={18} /> 목차 (Outline)
      </h3>
      <ul className="space-y-2 text-sm">
        {sections.map((section, idx) => (
          <li key={idx}>
            <a 
              href={`#chapter-${idx}`}
              className="block text-muted-foreground hover:text-primary hover:bg-muted p-2 rounded-md transition-colors truncate "
              title={section}
            >
              {idx + 1}. {section}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
