"use client";

import React from "react";
import { Sparkles, X, Save, MessageSquare, AlertTriangle, Trash2, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { Note } from "@/lib/markdownProcessor";
import { SelectionState } from "./FloatingToolbar";

interface QAModalProps {
  selection: SelectionState;
  question: string;
  answer: string;
  isAsking: boolean;
  onClose: () => void;
  onQuestionChange: (q: string) => void;
  onAsk: (q?: string) => void;
  onResetAnswer: () => void;
  onSaveNote: () => void;
}

export function QAModal({
  selection,
  question,
  answer,
  isAsking,
  onClose,
  onQuestionChange,
  onAsk,
  onResetAnswer,
  onSaveNote
}: QAModalProps) {
  const sampleQuestions = [
    "이 단어의 정확한 뜻이 무엇인가요?",
    "이 부분을 자동차에 비유해서 설명해줄 수 있나요?",
    "이 개념의 핵심 요약이 무엇인가요?",
    "초등학생도 이해할 수 있게 다시 설명해주세요."
  ];

  return (
    <div className="ask-modal-container fixed inset-0 bg-black/40 backdrop-blur-sm z-[150] flex items-center justify-center p-4">
      <div className="bg-surface border border-border-subtle w-full max-w-2xl rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] ">
        <div className="flex items-center justify-between p-4 border-b border-border-subtle bg-surface-container-low">
          <h3 className="font-bold flex items-center gap-2 text-text-primary">
            <Sparkles className="text-primary-container" size={18}/> 궁금한 점 해결하기
          </h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-text-primary transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-4 overflow-y-auto flex-1">
          <div className="mb-6">
            <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">선택한 텍스트</p>
            <div className="bg-surface-container-low p-3 rounded-lg border-l-4 border-primary-container italic text-sm text-muted-foreground">
              "{selection.text}"
            </div>
          </div>

          {!answer ? (
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">추천 질문</p>
                <div className="flex flex-wrap gap-2">
                  {sampleQuestions.map(q => (
                    <button 
                      key={q}
                      onClick={() => { onQuestionChange(q); onAsk(q); }}
                      className="bg-background border border-border text-sm px-3 py-1.5 rounded-full hover:border-primary hover:text-primary transition-colors text-left "
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider mt-4">직접 질문하기</p>
                <div className="flex gap-2">
                  <input 
                    type="text" 
                    className="flex-1 border border-border rounded-lg px-3 py-2 bg-background focus:ring-2 focus:ring-primary outline-none "
                    placeholder="궁금한 점을 자세히 적어보세요..."
                    value={question}
                    onChange={e => onQuestionChange(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && onAsk()}
                  />
                  <button 
                    onClick={() => onAsk()}
                    disabled={isAsking}
                    className="bg-primary text-primary-foreground px-4 py-2 rounded-lg font-bold hover:opacity-90 disabled:opacity-50 "
                  >
                    {isAsking ? <Loader2 className="animate-spin" size={18} /> : "질문"}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
              <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">AI 답변</p>
              <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 prose prose-sm dark:prose-invert max-w-none ">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>

        {answer && (
          <div className="p-4 border-t border-border bg-muted/30 flex justify-end gap-3">
            <button 
              onClick={onResetAnswer}
              className="px-4 py-2 rounded-lg border border-border bg-background hover:bg-muted font-medium "
            >
              다른 질문하기
            </button>
            <button 
              onClick={onSaveNote}
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-bold hover:opacity-90 flex items-center gap-2 "
            >
              <Save size={18} /> 포스트잇으로 저장
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

interface ViewNoteModalProps {
  note: Note;
  onClose: () => void;
  getProcessedMarkdown: (section: string, text: string) => string;
}

export function ViewNoteModal({ note, onClose, getProcessedMarkdown }: ViewNoteModalProps) {
  return (
    <div 
      className="view-modal-container fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4" 
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div 
        className="bg-surface/95 backdrop-blur-xl border border-border-subtle w-full max-w-lg rounded-[2rem] shadow-2xl overflow-hidden flex flex-col max-h-[80vh] "
        data-section={note.section}
        data-note-context={note.answer}
      >
        <div className="flex items-center justify-between p-4 border-b border-border bg-primary/10">
          <h3 className="font-bold flex items-center gap-2 text-primary">
            <MessageSquare size={18}/> 저장된 포스트잇 노트
          </h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X size={20} />
          </button>
        </div>
        <div className="p-6 overflow-y-auto">
          <div className="mb-4">
            <p className="text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider">질문 내용</p>
            <div className="font-medium text-lg">"{note.question}"</div>
            <div className="text-sm text-muted-foreground mt-1">
              대상: <span className="bg-yellow-200/50 dark:bg-yellow-600/30 px-1 rounded">"{note.selected_text}"</span>
            </div>
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none border-t border-border pt-4 ">
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
              {getProcessedMarkdown(note.section, note.answer)}
            </ReactMarkdown>
          </div>
        </div>
        <div className="p-4 border-t border-border bg-muted/30 flex justify-end">
          <button onClick={onClose} className="px-6 py-2 rounded-lg bg-primary text-primary-foreground font-bold hover:opacity-90">
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}

interface ClusterNoteModalProps {
  cluster: Note[];
  onClose: () => void;
  onSelectNote: (note: Note) => void;
}

export function ClusterNoteModal({ cluster, onClose, onSelectNote }: ClusterNoteModalProps) {
  return (
    <div 
      className="view-modal-container fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4 animate-in fade-in" 
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-surface/95 backdrop-blur-xl border border-border-subtle w-full max-w-lg rounded-[2rem] shadow-2xl overflow-hidden flex flex-col max-h-[80vh] animate-in zoom-in-95">
        <div className="flex items-center justify-between p-4 border-b border-border bg-primary/10">
          <h3 className="font-bold flex items-center gap-2 text-primary">
            <MessageSquare size={18}/> 주변 질문 모음 ({cluster.length})
          </h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X size={20} />
          </button>
        </div>
        <div className="p-4 overflow-y-auto space-y-3">
          {cluster.map((note, idx) => (
            <div 
              key={note.id} 
              className="bg-background/50 backdrop-blur-md border border-primary/20 shadow-sm rounded-xl p-4 cursor-pointer hover:bg-primary/5 hover:border-primary/50 transition-colors" 
              onClick={() => onSelectNote(note)}
            >
              <p className="text-xs font-semibold text-primary mb-2 flex items-center gap-2">
                <Sparkles size={14}/>질문 {idx + 1}
              </p>
              <div className="font-bold text-sm mb-2 text-text-primary">"{note.question}"</div>
              <div className="text-xs text-muted-foreground line-clamp-2 bg-surface-container-low p-2 rounded">
                대상: <span className="text-text-primary">"{note.selected_text}"</span>
              </div>
            </div>
          ))}
        </div>
        <div className="p-4 border-t border-border bg-muted/30 flex justify-end">
          <button onClick={onClose} className="px-6 py-2 rounded-lg bg-primary text-primary-foreground font-bold hover:opacity-90">
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}

interface DeleteConfirmModalProps {
  isDeleting: boolean;
  onClose: () => void;
  onConfirmDelete: () => void;
}

export function DeleteConfirmModal({ isDeleting, onClose, onConfirmDelete }: DeleteConfirmModalProps) {
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[200] flex items-center justify-center p-4 animate-in fade-in">
      <div className="bg-surface border border-border-subtle w-full max-w-md rounded-xl p-8 shadow-2xl animate-in zoom-in-95">
        <div className="flex flex-col items-center text-center">
          <div className="bg-error/10 p-3 rounded-full mb-4">
            <AlertTriangle className="text-error" size={32} />
          </div>
          <h3 className="text-xl font-bold mb-2 text-text-primary">정말 삭제하시겠습니까?</h3>
          <p className="text-muted-foreground mb-6">
            현재 가이드가 영구적으로 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
          </p>
        </div>
        
        <div className="flex gap-3">
          <button 
            onClick={onClose}
            disabled={isDeleting}
            className="flex-1 bg-surface-container text-text-primary font-bold py-3.5 rounded-lg hover:bg-surface-container-high transition-all disabled:opacity-50 border border-border-subtle"
          >
            취소
          </button>
          <button 
            onClick={onConfirmDelete}
            disabled={isDeleting}
            className="flex-1 bg-error text-on-error font-bold py-3.5 rounded-lg hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isDeleting ? <Loader2 className="animate-spin" size={18} /> : <Trash2 size={18} />}
            삭제하기
          </button>
        </div>
      </div>
    </div>
  );
}
