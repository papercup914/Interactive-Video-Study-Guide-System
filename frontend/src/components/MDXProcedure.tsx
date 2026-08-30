"use client";

import React, { useState } from 'react';
import { ListChecks, CheckCircle2, Circle, Eye, EyeOff } from 'lucide-react';

interface ProcedureData {
  checklists: {
    step: number;
    action: string;
    hint: string;
  }[];
}

const extractText = (node: any): string => {
  if (typeof node === 'string') return node;
  if (Array.isArray(node)) return node.map(extractText).join('');
  if (node && node.props && node.props.children) return extractText(node.props.children);
  return '';
};

export default function MDXProcedure(props: any) {
  const rawJson = extractText(props?.children).trim();
  const cleanJson = rawJson
    .replace(/```[\w-]*\n?/g, '')
    .replace(/```/g, '')
    .replace(/`/g, '')
    .replace(/,\s*([\]}])/g, '$1')
    .trim();
  let data: ProcedureData | null = null;
  
  try {
    data = JSON.parse(cleanJson);
  } catch (e) {
    console.warn("Failed to parse procedure JSON", e, rawJson);
    return <div className="p-4 bg-amber-500/10 text-amber-600 rounded-xl my-4 text-sm font-bold border border-amber-500/20">⚠️ AI가 생성한 인터랙티브 요소를 불러올 수 없습니다. (형식 오류)</div>;
  }

  if (!data || !data.checklists || data.checklists.length === 0) return null;

  return <ProcedureUI data={data} />;
}

function ProcedureUI({ data }: { data: ProcedureData }) {
  const [checked, setChecked] = useState<Set<number>>(new Set());
  const [showHints, setShowHints] = useState<Set<number>>(new Set());

  const toggleCheck = (idx: number) => {
    const newChecked = new Set(checked);
    if (newChecked.has(idx)) {
      newChecked.delete(idx);
    } else {
      newChecked.add(idx);
    }
    setChecked(newChecked);
  };

  const toggleHint = (idx: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const newHints = new Set(showHints);
    if (newHints.has(idx)) {
      newHints.delete(idx);
    } else {
      newHints.add(idx);
    }
    setShowHints(newHints);
  };

  const progress = Math.round((checked.size / data.checklists.length) * 100);

  return (
    <div className="border-2 border-primary/20 bg-card rounded-2xl overflow-hidden shadow-lg shadow-primary/5 transition-all my-8">
      <div className="bg-primary/10 p-4 flex items-center justify-between border-b border-primary/10">
        <div className="flex items-center gap-3">
          <div className="bg-primary/20 text-primary p-2 rounded-full flex-shrink-0">
            <ListChecks className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-lg text-foreground m-0">
            절차 마스터 (Checklist)
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-primary">{progress}% 완료</span>
          <div className="w-24 h-2 bg-primary/20 rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>
      
      <div className="p-4 flex flex-col gap-2">
        {data.checklists.map((item, idx) => {
          const isChecked = checked.has(idx);
          const isHintVisible = showHints.has(idx);
          
          return (
            <div 
              key={idx} 
              onClick={() => toggleCheck(idx)}
              className={`p-4 rounded-xl border-2 transition-all cursor-pointer flex gap-4 ${
                isChecked 
                  ? 'bg-primary/5 border-primary/30 opacity-70' 
                  : 'bg-background border-border/50 hover:border-primary/50 hover:bg-muted/30'
              }`}
            >
              <div className="mt-1 flex-shrink-0">
                {isChecked ? (
                  <CheckCircle2 className="w-6 h-6 text-primary" />
                ) : (
                  <Circle className="w-6 h-6 text-muted-foreground" />
                )}
              </div>
              
              <div className="flex-1">
                <div className="flex justify-between items-start gap-4">
                  <span className={`font-bold text-lg transition-all ${isChecked ? 'line-through text-muted-foreground' : 'text-foreground'}`}>
                    {item.step}. {item.action}
                  </span>
                  {item.hint && (
                    <button 
                      onClick={(e) => toggleHint(idx, e)}
                      className={`p-1.5 rounded-lg text-xs font-bold flex items-center gap-1 transition-colors ${
                        isHintVisible 
                          ? 'bg-amber-500 text-white' 
                          : 'bg-muted text-muted-foreground hover:bg-amber-500/20 hover:text-amber-600'
                      }`}
                    >
                      {isHintVisible ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                      힌트
                    </button>
                  )}
                </div>
                
                {isHintVisible && item.hint && (
                  <div className="mt-3 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-700 dark:text-amber-400 font-medium text-sm animate-in slide-in-from-top-1 fade-in">
                    💡 {item.hint}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      {progress === 100 && (
        <div className="p-4 bg-green-500/10 border-t border-green-500/20 text-green-700 dark:text-green-400 font-bold text-center flex items-center justify-center gap-2">
          <CheckCircle2 className="w-5 h-5" /> 모든 절차를 완벽하게 숙지했습니다!
        </div>
      )}
    </div>
  );
}
