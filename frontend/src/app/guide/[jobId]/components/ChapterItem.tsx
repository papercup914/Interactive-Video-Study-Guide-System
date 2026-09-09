"use client";

import React, { useState, useRef, useEffect, useMemo } from "react";
import { PlayCircle, MessageSquare } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

import { ErrorBoundary } from "@/components/ErrorBoundary";
import MDXQuiz from "@/components/MDXQuiz";
import MDXDiscussion from "@/components/MDXDiscussion";
import MDXFeynman from "@/components/MDXFeynman";
import MDXStepTracer from "@/components/MDXStepTracer";
import MDXMnemonic from "@/components/MDXMnemonic";
import MDXProcedure from "@/components/MDXProcedure";
import { Highlight, Scribble, MarginNote } from "@/components/markdown/RealStudyElements";
import { Note } from "@/lib/markdownProcessor";

export interface ChapterItemProps {
  section: string;
  idx: number;
  content: string;
  notes: Note[];
  setSelectedNote: (n: Note) => void;
  setSelectedCluster: (notes: Note[]) => void;
  getProcessedMarkdown: (s: string, c: string) => string;
  jobId: string;
  openRSVP: (s: string) => void;
  isInteractiveMode?: boolean;
}

export function ChapterItem({
  section,
  idx,
  content,
  notes,
  setSelectedNote,
  setSelectedCluster,
  getProcessedMarkdown,
  jobId,
  openRSVP,
  isInteractiveMode = true
}: ChapterItemProps) {
  const [clusters, setClusters] = useState<{ id: string, top: number, notes: Note[] }[]>([]);
  const chapterRef = useRef<HTMLElement>(null);
  const chapterNotes = notes.filter(n => n && n.section === section);

  useEffect(() => {
    if (!chapterRef.current || chapterNotes.length === 0) return;
    
    const updateLocalPos = () => {
      if (!chapterRef.current) return;
      const marks = Array.from(chapterRef.current.querySelectorAll('mark'));
      marks.sort((a, b) => a.offsetTop - b.offsetTop);
      
      const newClusters: { id: string, top: number, notes: Note[] }[] = [];
      let currentCluster: { id: string, top: number, notes: Note[] } | null = null;
      
      marks.forEach(mark => {
        const y = mark.offsetTop;
        const note = chapterNotes.find(n => n.id === mark.id);
        if (!note) return;
        
        // 160px 이내에 생성된 질문들은 병합하여 겹침 방지
        if (currentCluster && (y - currentCluster.top < 160)) {
           currentCluster.notes.push(note);
        } else {
           if (currentCluster) {
             newClusters.push(currentCluster);
           }
           currentCluster = { id: note.id, top: y, notes: [note] };
        }
      });
      if (currentCluster) newClusters.push(currentCluster);
      
      setClusters(newClusters);
    };

    const timer = setTimeout(updateLocalPos, 100);
    const resizeObserver = new ResizeObserver(() => {
      updateLocalPos();
    });
    resizeObserver.observe(chapterRef.current);
    
    return () => {
      clearTimeout(timer);
      resizeObserver.disconnect();
    };
  }, [content, chapterNotes]);

  return (
    <div className="relative mb-12 md:mb-16 group/chapter">
      <section ref={chapterRef} id={`chapter-${idx}`} className="scroll-mt-24">
        <div className="flex items-center justify-between mb-4 md:mb-6">
          <h2 className="text-xl md:text-2xl font-bold text-foreground flex items-center gap-3">
            <span className="bg-foreground text-background w-8 h-8 md:w-10 md:h-10 rounded-full flex items-center justify-center text-base md:text-lg shadow-sm shrink-0">
              {idx + 1}
            </span>
            {section}
          </h2>
          <button 
            onClick={() => openRSVP(section)}
            className="flex items-center gap-1 text-xs md:text-sm font-bold bg-muted hover:bg-primary/10 hover:text-primary text-muted-foreground px-3 py-1.5 rounded-full transition-colors opacity-100 xl:opacity-0 xl:group-hover/chapter:opacity-100 "
            title="속독(RSVP) 모드로 이 챕터 읽기"
          >
            <PlayCircle size={16} /> <span>속독 모드</span>
          </button>
        </div>
        
        <div className="prose prose-neutral dark:prose-invert max-w-none break-words w-full overflow-hidden prose-pre:max-w-full prose-pre:overflow-x-auto prose-img:max-w-full prose-headings:font-extrabold prose-a:text-foreground prose-a:underline prose-blockquote:border-l-4 prose-blockquote:border-foreground/40 prose-blockquote:bg-muted/30 prose-blockquote:p-4 md:prose-blockquote:p-5 prose-blockquote:rounded-xl md:prose-blockquote:rounded-2xl prose-blockquote:not-italic prose-li:marker:text-foreground/70 text-base leading-relaxed md:text-lg">
          <ErrorBoundary chapterTitle={section}>
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]} 
              rehypePlugins={[rehypeRaw]}
              components={useMemo(() => ({
                table: (props: any) => (
                  <div className="w-full overflow-hidden mb-8">
                    <table className="w-full text-left border-collapse table-fixed" {...props} />
                  </div>
                ),
                th: (props: any) => <th className="border-b-2 border-border/60 p-2 font-bold bg-surface-container-low break-keep" {...props} />,
                td: (props: any) => <td className="border-b border-border/40 p-2 break-words" {...props} />,
                quiz: (props: any) => isInteractiveMode ? (
                  <ErrorBoundary chapterTitle={`${section} - 퀴즈`}>
                    <MDXQuiz {...props} />
                  </ErrorBoundary>
                ) : null,
                feynman: (props: any) => isInteractiveMode ? (
                  <ErrorBoundary chapterTitle={`${section} - 파인만 모드`}>
                    <MDXFeynman {...props} />
                  </ErrorBoundary>
                ) : null,
                steptracer: (props: any) => isInteractiveMode ? (
                  <ErrorBoundary chapterTitle={`${section} - 논리 트레이서`}>
                    <MDXStepTracer {...props} />
                  </ErrorBoundary>
                ) : null,
                mnemonic: (props: any) => isInteractiveMode ? (
                  <ErrorBoundary chapterTitle={`${section} - 연상기억법`}>
                    <MDXMnemonic {...props} />
                  </ErrorBoundary>
                ) : null,
                procedure: (props: any) => isInteractiveMode ? (
                  <ErrorBoundary chapterTitle={`${section} - 절차 마스터`}>
                    <MDXProcedure {...props} />
                  </ErrorBoundary>
                ) : null,
                highlight: (props: any) => <Highlight {...props} />,
                scribble: (props: any) => <Scribble {...props} />,
                "margin-note": (props: any) => <MarginNote text={props.text} {...props} />,
                discussion: (props: any) => <MDXDiscussion {...props} sectionName={section} sectionContent={content} jobId={jobId} />
              }), [section, content, jobId, isInteractiveMode]) as any}
            >
              {getProcessedMarkdown(section, content)}
            </ReactMarkdown>
          </ErrorBoundary>
        </div>
      </section>

      {clusters.length > 0 && (
        <div className="hidden 2xl:block absolute top-0 -right-[18rem] w-64 h-full pointer-events-none">
          {clusters.map(cluster => {
            const isMulti = cluster.notes.length > 1;
            return (
              <div 
                key={cluster.id}
                className="absolute w-full pointer-events-auto cursor-pointer group"
                style={{ top: cluster.top }}
                onClick={() => {
                  if (isMulti) {
                    setSelectedCluster(cluster.notes);
                  } else {
                    setSelectedNote(cluster.notes[0]);
                  }
                }}
              >
                {/* Stacked background cards for Multi */}
                {isMulti && (
                  <>
                    <div className="absolute w-full h-full bg-surface shadow-sm border border-border/50 rounded-3xl -bottom-2 -right-2 rotate-2 transition-transform group-hover:rotate-6 z-0"></div>
                    <div className="absolute w-full h-full bg-surface shadow-sm border border-border/50 rounded-3xl -bottom-1 -right-1 rotate-1 transition-transform group-hover:rotate-3 z-0"></div>
                  </>
                )}
                
                {/* Main Card */}
                <div className="relative z-10 w-full bg-background shadow-xl shadow-foreground/5 border-2 border-foreground/20 rounded-3xl p-5 hover:border-foreground/50 transition-all duration-300">
                  {isMulti && (
                    <div className="absolute -top-3 -right-3 w-8 h-8 bg-red-500 text-white font-bold text-sm rounded-full flex items-center justify-center shadow-lg ring-4 ring-white z-50">
                      {cluster.notes.length}
                    </div>
                  )}
                  <div className="flex items-center justify-between mb-3 border-b border-border/50 pb-2">
                    <div className="flex items-center gap-2 text-primary font-bold text-sm">
                      <MessageSquare size={16} /> {isMulti ? "저장된 질문 모음" : "저장된 질문"}
                    </div>
                  </div>
                  {isMulti ? (
                     <div className="text-xs font-semibold text-muted-foreground mb-1">
                       이 주변에 {cluster.notes.length}개의 포스트잇이 겹쳐 있습니다. 클릭하여 모두 보기
                     </div>
                  ) : (
                     <div className="text-xs font-semibold text-muted-foreground mb-1 line-clamp-2">"{cluster.notes[0].selected_text}"</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
