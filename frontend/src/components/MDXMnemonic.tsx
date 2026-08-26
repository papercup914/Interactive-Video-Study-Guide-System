"use client";

import React, { useState } from 'react';
import { Brain, Sparkles, RefreshCw, ChevronRight, ChevronLeft } from 'lucide-react';

interface MnemonicData {
  story: string;
  flashcards: {
    q: string;
    a: string;
  }[];
}

const extractText = (node: any): string => {
  if (typeof node === 'string') return node;
  if (Array.isArray(node)) return node.map(extractText).join('');
  if (node && node.props && node.props.children) return extractText(node.props.children);
  return '';
};

export default function MDXMnemonic(props: any) {
  const rawJson = extractText(props.children).trim();
  const cleanJson = rawJson.replace(/```[a-zA-Z]*\n?/g, '').replace(/```/g, '').replace(/`/g, '').trim();
  let data: MnemonicData | null = null;
  
  try {
    data = JSON.parse(cleanJson);
  } catch (e) {
    console.warn("Failed to parse mnemonic JSON", e, rawJson);
    return <div className="p-4 bg-amber-500/10 text-amber-600 rounded-xl my-4 text-sm font-bold border border-amber-500/20">⚠️ AI가 생성한 인터랙티브 요소를 불러올 수 없습니다. (형식 오류)</div>;
  }

  if (!data) return null;

  return <MnemonicUI data={data} />;
}

function MnemonicUI({ data }: { data: MnemonicData }) {
  const [currentCard, setCurrentCard] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);

  const handleNext = () => {
    setIsFlipped(false);
    setTimeout(() => {
      setCurrentCard((prev) => (prev + 1) % data.flashcards.length);
    }, 150);
  };

  const handlePrev = () => {
    setIsFlipped(false);
    setTimeout(() => {
      setCurrentCard((prev) => (prev - 1 + data.flashcards.length) % data.flashcards.length);
    }, 150);
  };

  return (
    <div className="border-2 border-primary/20 bg-card rounded-2xl overflow-hidden shadow-lg shadow-primary/5 transition-all my-8">
      <div className="bg-primary/10 p-4 flex items-center gap-3 border-b border-primary/10">
        <div className="bg-primary/20 text-primary p-2 rounded-full flex-shrink-0">
          <Brain className="w-5 h-5" />
        </div>
        <h3 className="font-bold text-lg text-foreground m-0 flex items-center gap-2">
          연상 기억법 (Mnemonic)
          <Sparkles className="w-4 h-4 text-amber-500 animate-pulse" />
        </h3>
      </div>
      
      {data.story && (
        <div className="p-6 bg-gradient-to-br from-primary/5 to-transparent border-b border-border/50">
          <h4 className="font-bold text-primary mb-2 flex items-center gap-2">
            📖 잊지 못할 스토리
          </h4>
          <p className="text-foreground/90 font-medium leading-relaxed italic m-0">
            "{data.story}"
          </p>
        </div>
      )}
      
      {data.flashcards && data.flashcards.length > 0 && (
        <div className="p-8 flex flex-col items-center bg-muted/10">
          <div className="mb-4 text-sm font-bold text-muted-foreground">
            플래시카드 {currentCard + 1} / {data.flashcards.length}
          </div>
          
          <div 
            className="w-full max-w-md aspect-[3/2] perspective-1000 cursor-pointer group"
            onClick={() => setIsFlipped(!isFlipped)}
          >
            <div className={`relative w-full h-full transition-transform duration-500 preserve-3d ${isFlipped ? 'rotate-y-180' : ''}`}>
              {/* Front */}
              <div className="absolute inset-0 backface-hidden bg-card border-2 border-border/50 rounded-2xl shadow-sm flex flex-col items-center justify-center p-6 text-center group-hover:border-primary/50 transition-colors">
                <span className="text-sm font-bold text-primary mb-4 uppercase tracking-wider">Question</span>
                <h3 className="text-xl font-bold text-foreground m-0">{data.flashcards[currentCard].q}</h3>
                <div className="absolute bottom-4 flex items-center gap-2 text-xs text-muted-foreground font-medium">
                  <RefreshCw className="w-3 h-3" /> 클릭하여 뒤집기
                </div>
              </div>
              
              {/* Back */}
              <div className="absolute inset-0 backface-hidden rotate-y-180 bg-primary border-2 border-primary rounded-2xl shadow-md flex flex-col items-center justify-center p-6 text-center text-primary-foreground">
                <span className="text-sm font-bold opacity-80 mb-4 uppercase tracking-wider">Answer</span>
                <h3 className="text-2xl font-bold m-0">{data.flashcards[currentCard].a}</h3>
              </div>
            </div>
          </div>
          
          {data.flashcards.length > 1 && (
            <div className="flex gap-4 mt-8">
              <button 
                onClick={handlePrev}
                className="p-3 rounded-full bg-background border-2 border-border/50 text-foreground hover:bg-muted hover:border-border transition-all"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button 
                onClick={handleNext}
                className="p-3 rounded-full bg-background border-2 border-border/50 text-foreground hover:bg-muted hover:border-border transition-all"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
