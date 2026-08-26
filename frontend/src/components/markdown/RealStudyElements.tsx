import React from 'react';
import { cn } from '@/lib/utils';

export function Highlight({ children }: { children: React.ReactNode }) {
  return (
    <span className="relative inline-block px-1 mx-1 font-bold z-0">
      <span className="absolute inset-0 bg-[#eaff00]/70 dark:bg-[#d4ff00]/50 transform -skew-x-12 -rotate-1 rounded-sm -z-10"></span>
      {children}
    </span>
  );
}

export function Scribble({ children }: { children: React.ReactNode }) {
  return (
    <span className="relative inline-block font-bold z-0 px-1 mx-1">
      <svg className="absolute inset-0 w-full h-full overflow-visible -z-10 text-red-600 dark:text-red-400" preserveAspectRatio="none" viewBox="0 0 100 100">
        <path 
          d="M 15,85 C 30,105 105,105 105,60 C 105,10 80,-5 50,-5 C 10,-5 -5,10 -5,50 C -5,85 5,110 20,110" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="1.5" 
          strokeLinecap="round" 
          vectorEffect="non-scaling-stroke" 
          style={{ transform: 'rotate(-1deg)' }} 
        />
      </svg>
      {children}
    </span>
  );
}

export function MarginNote({ text, children }: { text: string, children: React.ReactNode }) {
  return (
    <span className="relative group inline-block">
      <span className="underline decoration-wavy decoration-yellow-400 underline-offset-4 font-bold">{children}</span>
      
      {/* Margin Note element */}
      <span className="hidden lg:flex absolute top-0 -right-[220px] w-[200px] bg-yellow-200 dark:bg-yellow-700/80 p-3 rounded-br-xl shadow-md transform rotate-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 eink-border pointer-events-none">
        <span className="absolute -top-2 left-1/2 -translate-x-1/2 w-8 h-3 bg-red-400/50 rounded-full rotate-[-5deg]"></span>
        <span className="font-handwriting text-lg leading-tight text-slate-800 dark:text-slate-100">{text}</span>
      </span>
      
      {/* Mobile Tooltip Fallback */}
      <span className="lg:hidden absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-[200px] bg-yellow-200 dark:bg-yellow-700 p-2 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
        <span className="font-handwriting text-lg leading-tight text-slate-800 dark:text-slate-100">{text}</span>
      </span>
    </span>
  );
}
