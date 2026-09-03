"use client";

import React, { useState } from 'react';
import { Network, ChevronDown, ChevronUp, CheckCircle2 } from 'lucide-react';

interface StepTracerData {
  scenario: string;
  steps: {
    question: string;
    answer: string;
  }[];
}

import { InteractiveWidgetBase } from './InteractiveWidgetBase';

export default function MDXStepTracer(props: { children?: React.ReactNode }) {
  return (
    <InteractiveWidgetBase<StepTracerData>
      fallbackName="단계별 추적(StepTracer) 위젯"
      render={(data) => <StepTracerUI data={data} />}
      validate={(data) => Boolean(data && Array.isArray(data.steps) && data.steps.length > 0)}
    >
      {props.children}
    </InteractiveWidgetBase>
  );
}

function StepTracerUI({ data }: { data: StepTracerData }) {
  const steps = Array.isArray(data.steps) ? data.steps : [];
  const [currentStep, setCurrentStep] = useState(0);

  const handleNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(prev => prev + 1);
    }
  };

  return (
    <div className="border-2 border-primary/20 bg-card rounded-2xl overflow-hidden shadow-lg shadow-primary/5 transition-all my-8">
      <div className="bg-primary/10 p-4 flex items-center gap-3 border-b border-primary/10">
        <div className="bg-primary/20 text-primary p-2 rounded-full flex-shrink-0">
          <Network className="w-5 h-5" />
        </div>
        <h3 className="font-bold text-lg text-foreground m-0">
          논리 흐름 추적 (Step-Tracer)
        </h3>
      </div>
      
      {data.scenario && (
        <div className="p-5 bg-muted/30 border-b border-border/50 text-foreground font-medium leading-relaxed">
          <span className="text-primary font-bold mr-2">📌 시나리오:</span>
          {data.scenario}
        </div>
      )}
      
      <div className="p-6 flex flex-col gap-4 relative">
        <div className="absolute left-10 top-6 bottom-6 w-0.5 bg-border z-0"></div>
        {data.steps.map((step, idx) => {
          const isRevealed = idx < currentStep;
          const isCurrent = idx === currentStep;
          const isFuture = idx > currentStep;
          
          return (
            <div key={idx} className="relative z-10 flex gap-4">
              <div className="flex-shrink-0 mt-1">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm transition-colors border-2 ${
                  isRevealed ? 'bg-primary border-primary text-primary-foreground' :
                  isCurrent ? 'bg-background border-primary text-primary' :
                  'bg-muted border-border text-muted-foreground'
                }`}>
                  {idx + 1}
                </div>
              </div>
              
              <div className={`flex-1 rounded-xl border-2 transition-all overflow-hidden ${
                isRevealed ? 'border-primary/30 bg-primary/5' :
                isCurrent ? 'border-primary shadow-md bg-card' :
                'border-border/50 bg-muted/20 opacity-50'
              }`}>
                <div className="p-4">
                  <p className="font-bold text-foreground m-0">{step.question}</p>
                </div>
                
                {isRevealed && (
                  <div className="p-4 bg-primary/10 border-t border-primary/10 text-foreground/90 font-medium">
                    <span className="text-primary font-bold mr-2">💡 해답:</span>
                    {step.answer}
                  </div>
                )}
                
                {isCurrent && (
                  <div className="p-4 bg-muted/30 border-t border-border flex justify-end">
                    <button
                      onClick={handleNext}
                      className="px-5 py-2 text-sm font-bold bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-1"
                    >
                      정답 확인하기 <ChevronDown className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
        
        {currentStep === data.steps.length && (
          <div className="relative z-10 flex gap-4 mt-2">
            <div className="flex-shrink-0 mt-1">
              <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center text-white shadow-md">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            </div>
            <div className="flex-1 p-4 rounded-xl border-2 border-green-500/30 bg-green-500/10 text-green-700 dark:text-green-400 font-bold">
              모든 논리 단계를 완료했습니다!
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
