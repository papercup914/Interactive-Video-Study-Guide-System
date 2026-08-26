"use client";

import React, { useState } from 'react';
import { CheckCircle2, XCircle, HelpCircle } from 'lucide-react';

interface QuizData {
  question: string;
  options: string[];
  answerIndex: number;
  feedback: string[];
}

const extractText = (node: any): string => {
  if (typeof node === 'string') return node;
  if (Array.isArray(node)) return node.map(extractText).join('');
  if (node && node.props && node.props.children) return extractText(node.props.children);
  return '';
};

export default function MDXQuiz(props: any) {
  // Backwards compatibility for old quiz format
  if (props.question && props.options && props.answer) {
    const data = {
      question: props.question,
      options: props.options.split('|').map((o: string) => o.trim()),
      answerIndex: parseInt(props.answer, 10),
      feedback: props.explanation ? Array(10).fill(props.explanation) : []
    };
    return (
      <div className="flex flex-col gap-8 my-8">
        <SingleQuiz data={data} index={0} total={1} />
      </div>
    );
  }

  // Extract text handling potential nested <p> tags from react-markdown
  const rawJson = extractText(props.children).trim();
  
  let quizDataList: QuizData[] = [];
  try {
    quizDataList = JSON.parse(rawJson);
  } catch (e) {
    // If it fails to parse, it might be the old format or malformed
    console.error("Failed to parse quiz JSON", e, rawJson);
    return null;
  }

  if (!quizDataList || quizDataList.length === 0) return null;

  return (
    <div className="flex flex-col gap-8 my-8">
      {quizDataList.map((quiz, idx) => (
        <SingleQuiz key={idx} data={quiz} index={idx} total={quizDataList.length} />
      ))}
    </div>
  );
}

function SingleQuiz({ data, index, total }: { data: QuizData, index: number, total: number }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);

  const { question, options, answerIndex, feedback } = data;

  const handleSelect = (idx: number) => {
    if (showExplanation) return;
    setSelected(idx);
    setShowExplanation(true);
  };

  return (
    <div className="border-2 border-primary/20 bg-card rounded-2xl overflow-hidden shadow-lg shadow-primary/5 transition-all">
      <div className="bg-primary/10 p-4 flex items-center gap-3 border-b border-primary/10">
        <div className="bg-primary/20 text-primary p-2 rounded-full flex-shrink-0">
          <HelpCircle className="w-5 h-5" />
        </div>
        <h3 className="font-bold text-lg text-foreground m-0">
          이해 점검 퀴즈 {total > 1 ? `${index + 1}/${total}` : ''}
        </h3>
      </div>
      
      <div className="p-6">
        <p className="text-[1.1rem] font-medium mb-6 text-foreground">{question}</p>
        
        <div className="flex flex-col gap-3">
          {options.map((opt, idx) => {
            const isSelected = selected === idx;
            const isCorrect = idx === answerIndex;
            const showCorrect = showExplanation && isCorrect;
            const showWrong = showExplanation && isSelected && !isCorrect;
            
            let btnClass = "w-full text-left p-4 rounded-xl border-2 transition-all flex items-center justify-between ";
            
            if (!showExplanation) {
              btnClass += "border-border/50 hover:border-primary hover:bg-primary/5 bg-background";
            } else if (showCorrect) {
              btnClass += "border-green-500 bg-green-500/10 text-green-700 dark:text-green-400";
            } else if (showWrong) {
              btnClass += "border-red-500 bg-red-500/10 text-red-700 dark:text-red-400";
            } else {
              btnClass += "border-border/50 opacity-50 bg-background";
            }

            return (
              <button
                key={idx}
                onClick={() => handleSelect(idx)}
                disabled={showExplanation}
                className={btnClass}
              >
                <span className="font-medium">{opt}</span>
                {showCorrect && <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 ml-2" />}
                {showWrong && <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 ml-2" />}
              </button>
            );
          })}
        </div>

        {showExplanation && feedback && feedback[selected!] && (
          <div className="mt-6 p-5 rounded-xl bg-primary/5 border border-primary/20 animate-in slide-in-from-top-2 fade-in duration-300">
            <h4 className={`font-bold mb-3 flex items-center gap-2 ${selected === answerIndex ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {selected === answerIndex ? <><CheckCircle2 className="w-5 h-5" /> 정답입니다!</> : <><XCircle className="w-5 h-5" /> 오답입니다!</>}
            </h4>
            <p className="text-foreground/90 m-0 leading-relaxed font-medium">
              <span className="text-primary font-bold mr-2 inline-block mb-1">💡 AI의 해설:</span>
              <br/>
              {feedback[selected!]}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
