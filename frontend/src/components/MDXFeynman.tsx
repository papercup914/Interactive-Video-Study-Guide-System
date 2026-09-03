"use client";

import React, { useState, useEffect } from 'react';
import { HelpCircle, Send, MessageSquare, AlertTriangle, Lightbulb } from 'lucide-react';

interface FeynmanData {
  tag_team_scenario: string;
  target_persona: string;
  initial_ai_message: string;
  concept_summary: string;
}

import { InteractiveWidgetBase } from './InteractiveWidgetBase';

export default function MDXFeynman(props: { children?: React.ReactNode }) {
  return (
    <InteractiveWidgetBase<FeynmanData>
      fallbackName="파인만 학습 위젯"
      render={(data) => <FeynmanUI data={data} />}
      validate={(data) => Boolean(data && typeof data === 'object')}
    >
      {props.children}
    </InteractiveWidgetBase>
  );
}

function FeynmanUI({ data }: { data: FeynmanData }) {
  const [inputText, setInputText] = useState('');
  const [strikes, setStrikes] = useState(0);
  const [showSos, setShowSos] = useState(false);
  const [chatHistory, setChatHistory] = useState<{role: 'ai' | 'user', text: string}[]>([
    { role: 'ai', text: data.initial_ai_message || '이 개념을 나만의 언어로 쉽게 설명해 볼까요?' }
  ]);
  const [errorMsg, setErrorMsg] = useState('');

  // Volatile State Protection (localStorage)
  const summaryPrefix = (data.concept_summary && typeof data.concept_summary === 'string') 
    ? data.concept_summary.substring(0, 20) 
    : 'default';
  const storageKey = `feynman_draft_${summaryPrefix}`;
  
  useEffect(() => {
    const saved = localStorage.getItem(storageKey);
    if (saved) setInputText(saved);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setInputText(val);
    localStorage.setItem(storageKey, val);
    if (errorMsg) setErrorMsg('');
  };

  const handleSubmit = () => {
    if (showSos) return;
    
    // Gibberish Bypass Prevention
    if (inputText.trim().length < 5) {
      setErrorMsg("조금만 더 자세히 설명해 주시겠어요? 막막하다면 SOS 버튼을 눌러주세요!");
      return;
    }

    const newUserMsg = { role: 'user' as const, text: inputText };
    
    // Two-Strike Rule
    if (strikes >= 1) {
      setChatHistory([...chatHistory, newUserMsg, { role: 'ai', text: "아하, 그렇게 생각하셨군요! 이 부분은 꽤 까다롭죠. 제가 정리한 설명을 한번 보여드릴게요." }]);
      setShowSos(true);
      setInputText('');
      localStorage.removeItem(storageKey);
    } else {
      setStrikes(strikes + 1);
      setChatHistory([...chatHistory, newUserMsg, { role: 'ai', text: "좋은 시도예요! (Yes, And..) 그 방향도 흥미롭지만, 상대방이 조금 더 쉽게 이해하려면 어떤 비유를 추가하면 좋을까요?" }]);
      setInputText('');
      localStorage.removeItem(storageKey);
    }
  };

  const handleSos = () => {
    setShowSos(true);
    setChatHistory([...chatHistory, { role: 'ai', text: "제가 도와드릴게요! 다음 설명을 참고해 보세요." }]);
    localStorage.removeItem(storageKey);
  };

  return (
    <div className="border-2 border-primary/20 bg-card rounded-2xl overflow-hidden shadow-lg shadow-primary/5 transition-all my-8">
      <div className="bg-primary/10 p-4 flex items-center gap-3 border-b border-primary/10">
        <div className="bg-primary/20 text-primary p-2 rounded-full flex-shrink-0">
          <MessageSquare className="w-5 h-5" />
        </div>
        <h3 className="font-bold text-lg text-foreground m-0">
          사고 실험: {data.target_persona} 눈높이에 맞춰보기
        </h3>
      </div>
      
      <div className="p-4 bg-muted/30 border-b border-border/50 text-sm text-muted-foreground italic flex items-center gap-2">
        <Lightbulb className="w-4 h-4 text-amber-500 flex-shrink-0" />
        {data.tag_team_scenario}
      </div>
      
      <div className="p-6">
        <div className="flex flex-col gap-4 mb-6">
          {chatHistory.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'ai' ? 'justify-start' : 'justify-end'}`}>
              <div className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'ai' ? 'bg-primary/10 text-foreground rounded-tl-sm' : 'bg-primary text-primary-foreground rounded-tr-sm'}`}>
                <p className="m-0 font-medium leading-relaxed">{msg.text}</p>
              </div>
            </div>
          ))}
        </div>

        {!showSos && (
          <div className="flex flex-col gap-3">
            <textarea 
              value={inputText}
              onChange={handleInputChange}
              placeholder="여기에 설명을 이어 적어주세요..."
              className="w-full min-h-[100px] p-4 rounded-xl border-2 border-border/50 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all bg-background resize-none font-medium"
            />
            {errorMsg && (
              <div className="text-red-500 text-sm flex items-center gap-1 font-bold">
                <AlertTriangle className="w-4 h-4" /> {errorMsg}
              </div>
            )}
            <div className="flex gap-3 justify-end mt-2">
              <button 
                onClick={handleSos}
                className="px-5 py-2.5 rounded-xl font-bold text-muted-foreground hover:bg-muted transition-colors flex items-center gap-2"
              >
                <HelpCircle className="w-4 h-4" />
                모르겠어요 (SOS)
              </button>
              <button 
                onClick={handleSubmit}
                className="px-6 py-2.5 rounded-xl font-bold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors flex items-center gap-2"
              >
                <Send className="w-4 h-4" />
                설명 전달하기
              </button>
            </div>
          </div>
        )}

        {showSos && (
          <div className="mt-4 p-5 rounded-xl bg-amber-500/10 border border-amber-500/20 animate-in slide-in-from-top-2 fade-in duration-300">
            <h4 className="font-bold mb-3 text-amber-600 dark:text-amber-400 flex items-center gap-2">
              <Lightbulb className="w-5 h-5" /> 
              핵심 개념 요약
            </h4>
            <p className="text-foreground/90 m-0 leading-relaxed font-medium">
              {data.concept_summary}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
