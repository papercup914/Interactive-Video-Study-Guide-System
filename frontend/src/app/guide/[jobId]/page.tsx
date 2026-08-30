"use client";

import { useEffect, useState, use, useRef, useMemo } from "react";
import { useRouter } from "next/navigation";
import { 
  ArrowLeft, Loader2, List, FileText, Sparkles, X, Save, 
  MessageSquare, Trash2, AlertTriangle, Link as LinkIcon, 
  PlayCircle, Play, Pause, FastForward, Rewind, PanelLeftClose, 
  PanelLeftOpen, CheckCircle2, ChevronRight, Grid 
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

import MDXQuiz from "@/components/MDXQuiz";
import MDXDiscussion from "@/components/MDXDiscussion";
import MDXFeynman from "@/components/MDXFeynman";
import MDXStepTracer from "@/components/MDXStepTracer";
import MDXMnemonic from "@/components/MDXMnemonic";
import MDXProcedure from "@/components/MDXProcedure";
import { Highlight, Scribble, MarginNote } from "@/components/markdown/RealStudyElements";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Virtuoso } from "react-virtuoso";

import { getThemeForId } from "@/lib/theme";
import { useRSVP } from "@/hooks/useRSVP";

type SelectionState = {
  text: string;
  section: string;
  contextText?: string;
  x: number;
  y: number;
  show: boolean;
};

type Note = {
  id: string;
  section: string;
  selected_text: string;
  question: string;
  answer: string;
};

const LENGTH_PRESETS = ["핵심 요약", "적당한 설명", "아주 상세하게"] as const;
const ANALOGY_PRESETS = ["비유 없이 담백하게", "적절한 비유 추가", "풍부한 비유"] as const;

export type PresetInfo = {
  id: string;
  title: string;
  url: string;
  date: string;
  length_preset: string;
  analogy_preset: string;
  chapter_count: number;
  provider: string;
  image_url?: string;
  video_duration?: string;
};

/**
 * 가이드 상세 뷰어 전용 9종 프리셋 매트릭스 탐색 모달
 */
function ViewerPresetMatrixModal({
  title,
  currentJobId,
  presets,
  totalPresets,
  onClose,
  onSelectGuide,
  onCreatePreset
}: {
  title: string;
  currentJobId: string;
  presets: Record<string, PresetInfo>;
  totalPresets: number;
  onClose: () => void;
  onSelectGuide: (jobId: string) => void;
  onCreatePreset: (length: string, analogy: string) => void;
}) {
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[110] flex items-center justify-center p-4 animate-in fade-in" onClick={onClose}>
      <div className="bg-surface w-full max-w-2xl rounded-2xl p-6 shadow-2xl border border-border-subtle animate-in zoom-in-95" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="flex justify-between items-start mb-4 pb-3 border-b border-border-subtle">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-primary/10 text-primary text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                <Sparkles size={12} /> 9종 프리셋 탐색기
              </span>
              <span className="text-xs text-muted-foreground">총 {totalPresets}개 프리셋 보유</span>
            </div>
            <h3 className="font-bold text-base text-text-primary line-clamp-1">{title.replace(/\.pdf$/i, '')}</h3>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-text-primary p-1.5 rounded-lg hover:bg-surface-variant transition-colors">
            <X size={20} />
          </button>
        </div>

        <p className="text-xs text-muted-foreground mb-4">
          원하는 <b>요약 분량</b>과 <b>설명 방식</b>의 조합을 클릭하면 해당 맞춤형 학습 가이드로 즉시 이동합니다.
        </p>

        {/* 3x3 Preset Grid */}
        <div className="grid grid-cols-3 gap-3">
          {LENGTH_PRESETS.map((length) => (
            <div key={length} className="flex flex-col gap-2">
              <div className="bg-surface-variant text-center font-bold text-xs py-1.5 rounded-lg text-text-primary">
                {length}
              </div>
              <div className="flex flex-col gap-2">
                {ANALOGY_PRESETS.map((analogy) => {
                  const key = `${length}__${analogy}`;
                  const item = presets[key];
                  const isAvailable = Boolean(item);
                  const isCurrent = item?.id === currentJobId;

                  return (
                    <button
                      key={analogy}
                      onClick={() => {
                        if (isAvailable && item) {
                          onSelectGuide(item.id);
                        } else {
                          onCreatePreset(length, analogy);
                        }
                      }}
                      className={`p-2.5 rounded-xl border text-left flex flex-col justify-between min-h-[76px] transition-all relative ${
                        isCurrent
                          ? "bg-primary/10 border-primary shadow-sm ring-2 ring-primary/20 cursor-default"
                          : isAvailable
                          ? "bg-surface border-border-subtle hover:border-primary hover:shadow-md cursor-pointer group/card"
                          : "bg-surface-container-lowest/50 border-dashed border-border-subtle/50 opacity-50 hover:opacity-80 hover:border-primary/40 cursor-pointer"
                      }`}
                    >
                      <div className="flex items-center justify-between w-full">
                        <span className={`font-semibold text-[11px] ${isCurrent ? "text-primary font-bold" : "text-text-primary group-hover/card:text-primary"} transition-colors`}>
                          {analogy}
                        </span>
                        {isCurrent ? (
                          <span className="text-[9px] font-bold bg-primary text-white px-1.5 py-0.2 rounded-full shrink-0">
                            현재 열람 중
                          </span>
                        ) : isAvailable ? (
                          <CheckCircle2 size={13} className="text-green-500 shrink-0" />
                        ) : (
                          <span className="text-[9px] text-muted-foreground">미생성</span>
                        )}
                      </div>
                      <div className="flex items-center justify-between mt-1 text-[10px]">
                        {isCurrent ? (
                          <span className="text-primary font-bold">{item.chapter_count}개 챕터</span>
                        ) : isAvailable ? (
                          <>
                            <span className="text-muted-foreground">{item.chapter_count}개 챕터</span>
                            <span className="text-primary font-bold flex items-center">
                              보기 <ChevronRight size={10} />
                            </span>
                          </>
                        ) : (
                          <span className="text-muted-foreground text-[9px] hover:text-primary">클릭하여 생성</span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-3 border-t border-border-subtle flex justify-between items-center text-xs text-muted-foreground">
          <span>* 비유/분량에 따라 AI 설명 톤과 깊이가 최적화되어 있습니다.</span>
          <button
            onClick={onClose}
            className="bg-foreground text-background px-4 py-2 rounded-lg font-bold hover:opacity-90 transition-opacity"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}

const SidebarNav = ({ sections, router, isFloating = false }: { sections: string[], router: any, isFloating?: boolean }) => (
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

const ChapterItem = ({ 
  section, idx, content, notes, setSelectedNote, setSelectedCluster, getProcessedMarkdown, jobId, openRSVP
}: { 
  section: string; idx: number; content: string; notes: Note[]; 
  setSelectedNote: (n: Note) => void;
  setSelectedCluster: (notes: Note[]) => void;
  getProcessedMarkdown: (s: string, c: string) => string;
  jobId: string;
  openRSVP: (s: string) => void;
}) => {
  const [clusters, setClusters] = useState<{ id: string, top: number, notes: Note[] }[]>([]);
  const chapterRef = useRef<HTMLElement>(null);
  const chapterNotes = notes.filter(n => n.section === section);

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
        
        // 카드의 실제 높이(약 140~150px)를 고려하여, 160px 이내에 생성된 질문들은 무조건 병합하여 겹침을 방지합니다.
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
                quiz: (props: any) => (
                  <ErrorBoundary chapterTitle={`${section} - 퀴즈`}>
                    <MDXQuiz {...props} />
                  </ErrorBoundary>
                ),
                feynman: (props: any) => (
                  <ErrorBoundary chapterTitle={`${section} - 파인만 모드`}>
                    <MDXFeynman {...props} />
                  </ErrorBoundary>
                ),
                steptracer: (props: any) => (
                  <ErrorBoundary chapterTitle={`${section} - 논리 트레이서`}>
                    <MDXStepTracer {...props} />
                  </ErrorBoundary>
                ),
                mnemonic: (props: any) => (
                  <ErrorBoundary chapterTitle={`${section} - 연상기억법`}>
                    <MDXMnemonic {...props} />
                  </ErrorBoundary>
                ),
                procedure: (props: any) => (
                  <ErrorBoundary chapterTitle={`${section} - 절차 마스터`}>
                    <MDXProcedure {...props} />
                  </ErrorBoundary>
                ),
                highlight: (props: any) => <Highlight {...props} />,
                scribble: (props: any) => <Scribble {...props} />,
                "margin-note": (props: any) => <MarginNote text={props.text} {...props} />,
                discussion: (props: any) => <MDXDiscussion {...props} sectionName={section} sectionContent={content} jobId={jobId} />
              }), [section, content, jobId]) as any}
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
};

export default function GuideViewer({ params }: { params: Promise<{ jobId: string }> }) {
  const router = useRouter();
  const [document, setDocument] = useState<Record<string, string> | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);
  const [title, setTitle] = useState("AI 맞춤형 학습 가이드");
  const [url, setUrl] = useState("");
  const [imageUrl, setImageUrl] = useState("https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=800&auto=format&fit=crop");
  const [profileMessage, setProfileMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // Settings / Regenerate State
  const [provider, setProvider] = useState("");
  const [lengthPreset, setLengthPreset] = useState("적당한 설명");
  const [analogyPreset, setAnalogyPreset] = useState("적절한 비유 추가");
  const [originalLengthPreset, setOriginalLengthPreset] = useState("적당한 설명");
  const [originalAnalogyPreset, setOriginalAnalogyPreset] = useState("적절한 비유 추가");
  const [isRegenerating, setIsRegenerating] = useState(false);
  
  // 9종 프리셋 상태
  const [siblingPresets, setSiblingPresets] = useState<Record<string, PresetInfo>>({});
  const [totalSiblingPresets, setTotalSiblingPresets] = useState<number>(1);
  const [showPresetMatrix, setShowPresetMatrix] = useState<boolean>(false);
  
  const resolvedParams = use(params);
  const jobId = resolvedParams.jobId;

  const [selection, setSelection] = useState<SelectionState>({ text: "", section: "", x: 0, y: 0, show: false });
  const [qaModalOpen, setQaModalOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  
  // View Existing Note Modal
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<Note[] | null>(null);

  // Delete State
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Tab State
  const [activeTab, setActiveTab] = useState<"guide" | "notes">("guide");
  
  // Layout State
  const [isLeftPanelOpen, setIsLeftPanelOpen] = useState(true);

  // RSVP State
  const [rsvpOpen, setRsvpOpen] = useState(false);
  const [rsvpSection, setRsvpSection] = useState("");
  const rsvpText = rsvpSection && document ? document[rsvpSection] : "";
  const rsvp = useRSVP(rsvpText, 350);

  const handleOpenRSVP = (section: string) => {
    setRsvpSection(section);
    setRsvpOpen(true);
    rsvp.reset();
  };
  
  const closeRSVP = () => {
    rsvp.reset();
    setRsvpOpen(false);
  };

  const articleRef = useRef<HTMLElement>(null);

  const fetchSiblingPresets = async (currentJobId: string, currentUrl?: string) => {
    try {
      const query = currentJobId ? `job_id=${encodeURIComponent(currentJobId)}` : `url=${encodeURIComponent(currentUrl || '')}`;
      const res = await fetch(`/api/guide/presets?${query}`);
      if (res.ok) {
        const data = await res.json();
        if (data.presets && typeof data.presets === "object") {
          setSiblingPresets(data.presets);
          setTotalSiblingPresets(data.total_presets || Object.keys(data.presets).length);
        }
      }
    } catch (e) {
      console.error("Failed to fetch sibling presets", e);
    }
  };

  const handleLengthPresetChange = (newLength: string) => {
    setLengthPreset(newLength);
    const targetKey = `${newLength}__${analogyPreset}`;
    const targetItem = siblingPresets[targetKey];
    if (targetItem && targetItem.id && targetItem.id !== jobId) {
      router.push(`/guide/${targetItem.id}`);
    }
  };

  const handleAnalogyPresetChange = (newAnalogy: string) => {
    setAnalogyPreset(newAnalogy);
    const targetKey = `${lengthPreset}__${newAnalogy}`;
    const targetItem = siblingPresets[targetKey];
    if (targetItem && targetItem.id && targetItem.id !== jobId) {
      router.push(`/guide/${targetItem.id}`);
    }
  };

  const handleSelectPresetGuide = (targetJobId: string) => {
    setShowPresetMatrix(false);
    if (targetJobId && targetJobId !== jobId) {
      router.push(`/guide/${targetJobId}`);
    }
  };

  const handleCreatePresetFromModal = (length: string, analogy: string) => {
    setShowPresetMatrix(false);
    setLengthPreset(length);
    setAnalogyPreset(analogy);
  };

  useEffect(() => {
    fetchDocument();
  }, [jobId]);

  const fetchDocument = async () => {
    try {
      const cached = localStorage.getItem(`harness_guide_${jobId}`);
      if (cached) {
        try {
          const data = JSON.parse(cached);
          setDocument(data.document);
          setNotes(data.notes || []);
          setTitle(data.title || "AI 맞춤형 학습 가이드");
          setUrl(data.url || "");
          setImageUrl(data.image_url || "https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=800&auto=format&fit=crop");
          if (data.profile_message) {
            setProfileMessage(data.profile_message);
          }
          setLoading(false);
        } catch(e) {}
      }

      const res = await fetch(`/api/guide/result/${jobId}`);
      if (res.ok) {
        const data = await res.json();
        


        setDocument(data.document);
        setNotes(data.notes || []);
        setTitle(data.title || "AI 맞춤형 학습 가이드");
        setUrl(data.url || "");
        setImageUrl(data.image_url || "https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=800&auto=format&fit=crop");
        setProvider(data.provider || "youtube");
        if (data.length_preset) {
            setLengthPreset(data.length_preset);
            setOriginalLengthPreset(data.length_preset);
        }
        if (data.analogy_preset) {
            setAnalogyPreset(data.analogy_preset);
            setOriginalAnalogyPreset(data.analogy_preset);
        }
        if (data.profile_message) {
          setProfileMessage(data.profile_message);
        }
        
        const docUrl = data.url || "";
        const docProvider = data.provider || "youtube";
        if (docProvider === "upload" || (!docUrl.includes("youtube.com") && !docUrl.includes("youtu.be") && docUrl !== "")) {
          setIsLeftPanelOpen(false);
        }

        fetchSiblingPresets(jobId, docUrl);
        localStorage.setItem(`harness_guide_${jobId}`, JSON.stringify(data));
      } else {
        if (!cached) {
          let errStr = "문서를 불러오는 데 실패했습니다.";
          try {
            const err = await res.json();
            errStr = err.detail || errStr;
          } catch(e) {
            errStr = "서버 통신 오류가 발생했습니다. (백엔드 재시작 중일 수 있습니다.)";
          }
          setError(errStr);
        }
        setLoading(false);
      }
    } catch (e) {
      if (!localStorage.getItem(`harness_guide_${jobId}`)) {
        setError("서버와 통신할 수 없습니다.");
      }
    } finally {
      setLoading(false);
    }
  };

  // 1. Text Selection tracking
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    
    const handleSelectionChange = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        const sel = window.getSelection();
        if (!sel || sel.isCollapsed) {
          if (!qaModalOpen) setSelection(s => s.show ? { ...s, show: false } : s);
          return;
        }

        // Check if selection is inside modal or toolbar using anchorNode
        let isIgnored = false;
        let curr = sel.anchorNode;
        while (curr && curr !== window.document.body) {
          if (curr.nodeType === 1) {
            const el = curr as Element;
            if (el.classList.contains('ask-modal-container') || el.classList.contains('floating-toolbar') || el.tagName.toLowerCase() === 'mark') {
              isIgnored = true;
              break;
            }
          }
          curr = curr.parentNode;
        }
        
        if (isIgnored) return;

        const text = sel.toString().trim();
        if (text.length < 2) return;

        let node = sel.anchorNode;
        let sectionName = "";
        let contextText = "";
        
        while (node && node !== window.document.body) {
          if (node.nodeType === 1) {
            const el = node as Element;
            // Standard document section
            if (el.tagName.toLowerCase() === "section") {
              const sectionIndex = parseInt(el.id.replace("chapter-", ""));
              sectionName = Object.keys(document || {})[sectionIndex];
              contextText = document?.[sectionName] || "";
              break;
            }
            // Inside a Note (Desktop or Modal)
            if (el.hasAttribute('data-section')) {
              sectionName = el.getAttribute('data-section') || "";
              if (el.hasAttribute('data-note-context')) {
                 contextText = el.getAttribute('data-note-context') || "";
              }
              break;
            }
          }
          node = node.parentNode;
        }

        if (!sectionName) return;

        const range = sel.getRangeAt(0);
        const rect = range.getBoundingClientRect();

        setSelection({
          text,
          section: sectionName,
          contextText,
          x: rect.left + rect.width / 2,
          y: rect.top + window.scrollY - 10,
          show: true
        });
      }, 300); // 300ms debounce for mobile selection rendering
    };

    window.document.addEventListener("selectionchange", handleSelectionChange);
    return () => {
      clearTimeout(timeoutId);
      window.document.removeEventListener("selectionchange", handleSelectionChange);
    };
  }, [document, qaModalOpen]);

  // 2. Existing Note Click tracking
  useEffect(() => {
    const handleMarkClick = (e: Event) => {
      const target = e.target as HTMLElement;
      if (target.tagName.toLowerCase() === 'mark' && target.id.startsWith('note_')) {
        const noteId = target.id;
        const note = notes.find(n => n.id === noteId);
        if (note) {
          setSelectedNote(note);
        }
      }
    };

    window.document.addEventListener("pointerup", handleMarkClick);
    return () => window.document.removeEventListener("pointerup", handleMarkClick);
  }, [notes]);

  // Sidenote positioning is now handled locally by ChapterItem

  const handleAsk = async (presetQ?: string) => {
    const q = presetQ || question;
    if (!q) return;
    
    setIsAsking(true);
    setAnswer("");
    
    try {
      const res = await fetch("/api/guide/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          selected_text: selection.text,
          context: (selection as any).contextText || document?.[selection.section] || "",
          question: q,
          provider: "Google Gemini",
          learner_profile: localStorage.getItem("learnerProfile_v2") || ""
        })
      });
      const data = await res.json();
      setAnswer(data.answer);
    } catch (e) {
      setAnswer("답변을 불러오는 중 오류가 발생했습니다.");
    } finally {
      setIsAsking(false);
    }
  };

  const handleSaveNote = async () => {
    if (!document) return;

    const newNote: Note = {
      id: `note_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      section: selection.section,
      selected_text: selection.text,
      question: question || "궁금한 점",
      answer: answer
    };

    const updatedNotes = [...notes, newNote];
    setNotes(updatedNotes);
    
    setQaModalOpen(false);
    setSelection(s => ({ ...s, show: false }));
    setAnswer("");
    setQuestion("");

    try {
      await fetch(`/api/guide/update/${jobId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document, notes: updatedNotes })
      });
    } catch (e) {
      console.error("Failed to sync note with server");
    }
  };

  const handleAnnotate = async (type: 'highlight' | 'scribble' | 'margin-note') => {
    if (!document || !selection.section || !selection.text) return;
    
    let tagStart = `<${type}>`;
    let tagEnd = `</${type}>`;
    
    if (type === 'margin-note') {
      const note = window.prompt("포스트잇에 남길 메모를 입력하세요 (10~20자 내외):");
      if (!note) return; // User cancelled
      tagStart = `<margin-note text="${note}">`;
    }

    const currentContent = document[selection.section];
    if (!currentContent) return;

    // Replace the first occurrence of the selected text
    const newContent = currentContent.replace(selection.text, `${tagStart}${selection.text}${tagEnd}`);
    
    if (newContent === currentContent) {
      console.warn("Could not find selected text in document section.");
      return;
    }

    const newDocument = { ...document, [selection.section]: newContent };
    setDocument(newDocument);
    setSelection(s => ({ ...s, show: false }));

    try {
      await fetch(`/api/guide/update/${jobId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document: newDocument, notes })
      });
    } catch (e) {
      console.error("Failed to sync document with server");
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      const res = await fetch(`/api/guide/${jobId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        router.push("/");
      } else {
        alert("가이드 삭제에 실패했습니다.");
      }
    } catch (e) {
      console.error("Failed to delete", e);
      alert("서버 오류가 발생했습니다.");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    try {
      const learnerProfile = localStorage.getItem("learnerProfile_v2") || "";
      const formData = new FormData();
      formData.append("url", url);
      formData.append("provider", provider);
      formData.append("length_preset", lengthPreset);
      formData.append("analogy_preset", analogyPreset);
      formData.append("pdf_parsing_method", "basic");
      formData.append("learner_profile", learnerProfile);
      formData.append("force_refresh", "true");
      
      const res = await fetch("/api/guide/start", {
        method: "POST",
        body: formData
      });
      
      const data = await res.json();
      if (data.job_id) {
        // Rediect to home to see the processing or wait there
        router.push("/");
      } else {
        alert("재생성 시작에 실패했습니다.");
        setIsRegenerating(false);
      }
    } catch(e) {
      alert("서버 오류가 발생했습니다.");
      setIsRegenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="animate-spin text-primary mb-4" size={48} />
        <p className="text-muted-foreground text-lg">문서를 불러오는 중입니다...</p>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="text-center py-20">
        <p className="text-red-500 text-xl font-bold mb-4">{error}</p>
        <button onClick={() => router.push("/")} className="bg-primary text-primary-foreground px-6 py-2 rounded-lg ">
          홈으로 돌아가기
        </button>
      </div>
    );
  }

  const sections = Object.keys(document);

  // Helper to inject <mark> tags into Markdown
  const getProcessedMarkdown = (sectionName: string, text: string) => {
    if (!text) return "";
    let processed = text;
    
    // HTML5 parsers (rehype-raw) don't support self-closing custom tags like <quiz />
    // Also, custom tags are treated as inline by react-markdown and wrapped in <p>.
    // A <button> (inside our custom components) inside a <p> causes a React hydration mismatch!
    // Wrapping them in a <div> prevents the <p> wrapper.
    
    // Fix CommonMark parsing bug with Korean particles attached to markdown markers.
    processed = processed.replace(/(\*\*|__|\*|_)(?=[가-힣])/g, '$1<!-- -->');
    
    // Normalize hyphenated/underscored custom tag names (e.g. <step_tracer>, <step-tracer> -> <steptracer>)
    processed = processed.replace(/<\s*(\/?)\s*(?:step[-_]tracer|steptracer)\b([^>]*)>/gi, '<$1steptracer$2>');
    
    // Unwrap markdown code fences (```xml ... ``` or ```json ... ``` or ```feynman ... ```) wrapping custom tags so they render as interactive components
    processed = processed.replace(/```[\w-]*\s*\n?\s*(<(?:quiz|feynman|steptracer|mnemonic|procedure|discussion)[\s\S]*?<\/(?:quiz|feynman|steptracer|mnemonic|procedure|discussion)>)\s*(?:```)?/gi, '$1');
    
    const tagsToProcess = ['quiz', 'feynman', 'steptracer', 'mnemonic', 'procedure'];
    tagsToProcess.forEach(tag => {
      // Normalize tag spaces (e.g. < feynman > -> <feynman>)
      processed = processed.replace(new RegExp(`<\\s*${tag}\\s*>`, 'gi'), `<${tag}>`);
      processed = processed.replace(new RegExp(`<\\/\\s*${tag}\\s*>`, 'gi'), `</${tag}>`);
      
      // Auto-wrap leaked raw JSON payloads (Defensive Fallback)
      if (tag === 'feynman') {
        const rawJsonFeynmanRegex = /{\s*"tag_team_scenario"[\s\S]*?}/gi;
        processed = processed.replace(rawJsonFeynmanRegex, (match) => {
          if (processed.indexOf(`<${tag}>`) !== -1) return match;
          return `\n<${tag}>\n${match}\n</${tag}>\n`;
        });
      } else if (tag === 'steptracer') {
        const rawJsonStepRegex = /{\s*"(?:scenario|steps)"[\s\S]*?}/gi;
        processed = processed.replace(rawJsonStepRegex, (match) => {
          if (processed.indexOf(`<${tag}>`) !== -1) return match;
          return `\n<${tag}>\n${match}\n</${tag}>\n`;
        });
      } else if (tag === 'mnemonic') {
        const rawJsonMnemRegex = /{\s*"(?:story|flashcards)"[\s\S]*?}/gi;
        processed = processed.replace(rawJsonMnemRegex, (match) => {
          if (processed.indexOf(`<${tag}>`) !== -1) return match;
          return `\n<${tag}>\n${match}\n</${tag}>\n`;
        });
      } else if (tag === 'procedure') {
        const rawJsonProcRegex = /{\s*"(?:checklists|overall_goal)"[\s\S]*?}/gi;
        processed = processed.replace(rawJsonProcRegex, (match) => {
          if (processed.indexOf(`<${tag}>`) !== -1) return match;
          return `\n<${tag}>\n${match}\n</${tag}>\n`;
        });
      }
      
      // Fix missing closing tags
      if (processed.includes(`<${tag}>`) && !processed.includes(`</${tag}>`)) {
        processed += `\n</${tag}>`;
      }
      
      // Fix broken JSON formatting and internal code fences inside tags
      const tagRegex = new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`, 'gi');
      processed = processed.replace(tagRegex, (_fullMatch, rawInner) => {
        let jsonContent = rawInner.trim();
        jsonContent = jsonContent.replace(/```[\w-]*\n?/g, '').replace(/```/g, '').replace(/`/g, '').trim();
        jsonContent = jsonContent.replace(/,\s*([\]}])/g, '$1'); // Remove trailing commas
        if (tag === 'quiz' && !jsonContent.startsWith("[") && jsonContent.includes("{")) {
          jsonContent = `[${jsonContent}]`;
        }
        return `<${tag}>\n${jsonContent}\n</${tag}>`;
      });
      
      // Wrap properly closed tags in div
      const wrapRegex = new RegExp(`<${tag}([^>]*?)>([\\s\\S]*?)<\\/${tag}>`, 'gi');
      processed = processed.replace(wrapRegex, (match, p1, p2) => {
        return `\n\n<div className="custom-${tag}-wrapper"><${tag}${p1}>${p2}</${tag}></div>\n\n`;
      });
      
      // Convert self-closing tags and wrap in div
      const selfCloseRegex = new RegExp(`<${tag}([^>]*?)\\/>`, 'gi');
      processed = processed.replace(selfCloseRegex, (match, p1) => {
        return `\n\n<div className="custom-${tag}-wrapper"><${tag}${p1}></${tag}></div>\n\n`;
      });
    });
    
    // Convert <discussion /> to <discussion></discussion> and wrap in div
    processed = processed.replace(/<discussion([^>]*?)\/>/gi, (match, p1) => {
      return `\n\n<div className="custom-discussion-wrapper"><discussion${p1}></discussion></div>\n\n`;
    });

    // AI나 파서가 임의로 생성한 <mark> 태그 제거 (사용자 노트와 충돌 방지 및 원치 않는 형광펜 효과 제거)
    processed = processed.replace(/<\/?mark[^>]*>/gi, '');

    const sectionNotes = notes.filter(n => n.section === sectionName);
    
    sectionNotes.forEach(note => {
      const escaped = note.selected_text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`(\\*\\*|__|\\*|_)?(${escaped})(\\*\\*|__|\\*|_)?`);
      
      processed = processed.replace(regex, (match, p1, p2, p3) => {
        if (p1 && p3 && p1 === p3) {
          return `<mark id="${note.id}" class="bg-foreground text-background rounded px-1 cursor-pointer transition-colors shadow-sm " title="노트 보기">${p1}${p2}${p3}</mark>`;
        }
        return `${p1 || ''}<mark id="${note.id}" class="bg-foreground text-background rounded px-1 cursor-pointer transition-colors shadow-sm " title="노트 보기">${p2}</mark>${p3 || ''}`;
      });
    });
    return processed;
  };

  const getYoutubeEmbedUrl = (urlStr: string) => {
    if (!urlStr) return null;
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = urlStr.match(regExp);
    return (match && match[2].length === 11) ? `https://www.youtube.com/embed/${match[2]}` : null;
  };
  const embedUrl = getYoutubeEmbedUrl(url);

  return (
    <div className="flex flex-col min-h-screen bg-page-bg">
      {/* Floating Toolbar (Remains unchanged but positioned absolute to body) */}
      {selection.show && !qaModalOpen && (
        <div
          className="floating-toolbar absolute z-[200] bg-primary-container text-on-primary shadow-xl rounded-full px-2 py-1.5 font-bold flex items-center gap-1 hover:scale-105 transition-transform transform -translate-x-1/2 -translate-y-full"
          style={{ left: selection.x, top: selection.y - 10 }}
        >
          <button onClick={() => handleAnnotate('highlight')} className="p-2 hover:bg-white/20 rounded-full transition-colors flex items-center gap-1 text-sm whitespace-nowrap" title="형광펜 칠하기">
            🟨 형광펜
          </button>
          <div className="w-[1px] h-4 bg-white/30 mx-1"></div>
          <button onClick={() => handleAnnotate('scribble')} className="p-2 hover:bg-white/20 rounded-full transition-colors flex items-center gap-1 text-sm whitespace-nowrap" title="동그라미 치기">
            🔴 동그라미
          </button>
          <div className="w-[1px] h-4 bg-white/30 mx-1"></div>
          <button onClick={() => handleAnnotate('margin-note')} className="p-2 hover:bg-white/20 rounded-full transition-colors flex items-center gap-1 text-sm whitespace-nowrap" title="포스트잇 남기기">
            📝 포스트잇
          </button>
          <div className="w-[1px] h-4 bg-white/30 mx-1"></div>
          <button onClick={() => setQaModalOpen(true)} className="p-2 hover:bg-white/20 rounded-full transition-colors flex items-center gap-1 text-sm whitespace-nowrap" title="AI에게 질문하기">
            <Sparkles size={16} /> Q&A
          </button>
        </div>
      )}

      {/* TopNavBar */}
      <nav className="flex justify-between items-center w-full px-margin-page h-16 sticky top-0 z-50 bg-surface border-b border-border-subtle shadow-sm">
        <div className="flex items-center gap-6">
          <button 
            onClick={() => setIsLeftPanelOpen(!isLeftPanelOpen)} 
            className="text-muted-foreground hover:text-primary-container hover:bg-surface-variant p-2 rounded-lg transition-colors cursor-pointer hidden lg:flex"
            title={isLeftPanelOpen ? "비디오 패널 숨기기" : "비디오 패널 열기"}
          >
            {isLeftPanelOpen ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
          </button>
          <div className="font-headline-md text-headline-md text-primary-container truncate max-w-[200px] md:max-w-md">{title || "Loading..."}</div>
          <div className="hidden md:flex gap-4">
            <button onClick={() => router.push("/")} className="font-label-md text-label-md text-muted-foreground hover:text-primary-container transition-colors cursor-pointer active:opacity-80">Dashboard</button>
            <button className="font-label-md text-label-md text-primary-container border-b-2 border-primary-container pb-1 transition-colors cursor-pointer">Learning Guide</button>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={() => router.push("/")} className="bg-primary-container text-on-primary hover:bg-hover-indigo px-4 py-2 rounded font-label-md text-label-md transition-colors hidden md:block">서재로 돌아가기</button>
          <button onClick={() => router.push("/")} className="md:hidden text-muted-foreground"><ArrowLeft size={20}/></button>
          <div className="flex gap-2 text-muted-foreground">
            <button onClick={() => setDeleteModalOpen(true)} className="cursor-pointer active:opacity-80 hover:text-error transition-colors" title="가이드 삭제"><Trash2 size={20}/></button>
          </div>
        </div>
      </nav>

      {/* Main Content Split Pane */}
      <main className="flex-1 flex flex-col lg:flex-row w-full h-[calc(100vh-4rem)] overflow-hidden">
        
        {/* Left Pane: Video Player */}
        <div className={`flex-shrink-0 bg-surface border-r border-border-subtle flex flex-col p-6 overflow-y-auto transition-all duration-300 ease-in-out ${isLeftPanelOpen ? 'w-full lg:w-[40%] opacity-100' : 'w-0 opacity-0 px-0 border-r-0 hidden lg:flex'}`}>
          {(embedUrl || url) && (
            <div className="aspect-video w-full bg-black rounded-lg relative overflow-hidden mb-6 shadow-sm border border-border-subtle group">
               {embedUrl ? (
                 <iframe 
                   src={embedUrl} 
                   className="w-full h-full border-none"
                   allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                   allowFullScreen
                 />
               ) : (
                 <div className="flex items-center justify-center p-8 w-full h-full">
                   <a href={url} target="_blank" rel="noopener noreferrer" className="bg-primary-container text-on-primary px-6 py-3 rounded-full font-bold shadow-md hover:scale-105 transition-transform flex items-center gap-2">원본 문서 보기 <LinkIcon size={18}/></a>
                 </div>
               )}
            </div>
          )}

          <div className="flex-1">
            <h1 className="font-headline-lg text-headline-lg text-text-primary mb-2 leading-tight">{title}</h1>
            {profileMessage && (
              <p className="font-body-lg text-body-lg text-muted-foreground mb-6 flex items-center gap-2">
                 <Sparkles className="text-primary-container" size={16} /> {profileMessage}
              </p>
            )}
            
            {/* Options Toolbar */}
            {(() => {
              const currentKey = `${lengthPreset}__${analogyPreset}`;
              const matchedSibling = siblingPresets[currentKey];
              const isMatchedAvailable = Boolean(matchedSibling);
              const isOtherExisting = isMatchedAvailable && matchedSibling.id !== jobId;
              const isUncreated = !isMatchedAvailable;

              return (
                <div className="bg-surface-container border border-border-subtle rounded-2xl p-3.5 mb-6 flex flex-wrap items-center gap-3 md:gap-4 shadow-sm">
                  {/* 요약 분량 드롭다운 */}
                  <div className="flex items-center gap-2 bg-surface px-3 py-1.5 rounded-xl border border-border-subtle/80 shadow-xs">
                    <span className="font-body-sm text-xs font-semibold text-muted-foreground whitespace-nowrap">요약 분량</span>
                    <select 
                      className="bg-transparent border-none font-body-sm text-xs md:text-sm font-bold text-text-primary cursor-pointer focus:ring-0 py-0 pl-1 pr-6"
                      value={lengthPreset}
                      onChange={(e) => handleLengthPresetChange(e.target.value)}
                    >
                      {LENGTH_PRESETS.map((lp) => (
                        <option key={lp} value={lp}>{lp}</option>
                      ))}
                    </select>
                  </div>

                  {/* 설명 방식 드롭다운 */}
                  <div className="flex items-center gap-2 bg-surface px-3 py-1.5 rounded-xl border border-border-subtle/80 shadow-xs">
                    <span className="font-body-sm text-xs font-semibold text-muted-foreground whitespace-nowrap">설명 방식</span>
                    <select 
                      className="bg-transparent border-none font-body-sm text-xs md:text-sm font-bold text-text-primary cursor-pointer focus:ring-0 py-0 pl-1 pr-6"
                      value={analogyPreset}
                      onChange={(e) => handleAnalogyPresetChange(e.target.value)}
                    >
                      {ANALOGY_PRESETS.map((ap) => (
                        <option key={ap} value={ap}>{ap}</option>
                      ))}
                    </select>
                  </div>

                  {/* 9종 프리셋 탐색기 모달 트리거 버튼 */}
                  <button 
                    type="button"
                    onClick={() => setShowPresetMatrix(true)}
                    className="flex items-center gap-1.5 px-3 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-xl font-bold text-xs transition-colors border border-primary/20 cursor-pointer shadow-xs"
                    title="9종 맞춤형 프리셋 전체보기"
                  >
                    <Sparkles size={14} className="text-primary animate-pulse" />
                    <span className="hidden sm:inline">9종 프리셋 탐색기</span>
                    <span className="sm:hidden">9종 탐색기</span>
                    <span className="bg-primary text-white text-[10px] px-1.5 py-0.2 rounded-full font-extrabold ml-0.5">
                      {totalSiblingPresets}/9
                    </span>
                  </button>

                  {/* 다른 생성된 프리셋이 선택되었을 때의 바로 이동 버튼 */}
                  {isOtherExisting && (
                    <button 
                      onClick={() => router.push(`/guide/${matchedSibling.id}`)}
                      className="ml-auto bg-primary text-white px-4 py-2 rounded-xl font-bold text-xs hover:bg-primary/90 transition-all flex items-center gap-1.5 shadow-sm hover:shadow"
                    >
                      <CheckCircle2 size={14} className="text-green-300" />
                      <span>해당 버전으로 즉시 이동</span>
                      <ChevronRight size={12} />
                    </button>
                  )}

                  {/* 미생성 프리셋이 선택되었을 때의 재생성/새로 생성 버튼 */}
                  {isUncreated && (
                    <button 
                      onClick={handleRegenerate}
                      disabled={isRegenerating}
                      className="ml-auto bg-primary-container text-on-primary px-4 py-2 rounded-xl font-bold text-xs hover:bg-hover-indigo transition-colors flex items-center gap-2 disabled:opacity-50 shadow-sm"
                    >
                      {isRegenerating ? <Loader2 className="animate-spin" size={14}/> : <Sparkles size={14}/>}
                      <span>새 버전으로 생성하기</span>
                    </button>
                  )}
                </div>
              );
            })()}
            
            <div className="bg-surface-container-low p-4 rounded-lg border border-border-subtle mb-6 lg:mb-0">
              <h3 className="font-label-md text-label-md text-text-primary mb-2">Guide Overview</h3>
              <p className="font-body-sm text-body-sm text-muted-foreground">이 가이드는 사용자가 선택한 영상/문서에서 추출된 학습 자료입니다. 오른쪽 탭에서 상세 내용을 확인하고 드래그하여 노트를 추가해보세요.</p>
            </div>
          </div>
        </div>

        {/* Right Pane: Scrollable Content (Tabs) */}
        <div className={`${isLeftPanelOpen ? 'w-full lg:w-[60%]' : 'w-full max-w-5xl mx-auto border-l border-r border-border-subtle'} flex-shrink-0 flex flex-col bg-page-bg min-w-0 transition-all duration-300 ease-in-out`}>
          {/* Tabs Header */}
          <div className="flex border-b border-border-subtle bg-surface px-6 pt-4 sticky top-0 z-10">
            <button 
              onClick={() => setActiveTab("guide")}
              className={`pb-3 px-4 font-label-md text-label-md ${activeTab === "guide" ? "text-text-primary border-b-2 border-primary-container" : "text-muted-foreground border-b-2 border-transparent hover:text-text-primary transition-colors"}`}
            >
              학습 가이드
            </button>
            <button 
              onClick={() => setActiveTab("notes")}
              className={`pb-3 px-4 font-label-md text-label-md flex items-center gap-2 ${activeTab === "notes" ? "text-text-primary border-b-2 border-primary-container" : "text-muted-foreground border-b-2 border-transparent hover:text-text-primary transition-colors"}`}
            >
              내 노트 <span className="bg-primary-container/10 text-primary-container text-xs py-0.5 px-2 rounded-full">{notes.length}</span>
            </button>
          </div>
          
          {/* Tab Contents Container */}
          <div className="flex-1 h-full overflow-hidden min-w-0">
            
            {/* Tab: Guide */}
            <div className={activeTab === "guide" ? "h-full w-full overflow-x-hidden" : "hidden"}>
              <Virtuoso
                className="h-full w-full scrollbar-hide"
                style={{ overflowX: 'hidden' }}
                data={sections}
                itemContent={(idx, section) => (
                  <div className="px-4 md:px-6 py-4 md:py-6 w-full max-w-full">
                    <div className="bg-surface border border-border-subtle rounded-xl p-inner-padding shadow-sm mb-6 w-full">
                    <h2 className="font-headline-md text-headline-md text-text-primary mb-4 flex items-center gap-2">
                      <span className="text-primary-container">{idx + 1}.</span> {section}
                    </h2>
                    <div className="font-body-sm text-body-sm text-muted-foreground">
                      <ChapterItem 
                        key={section}
                        idx={idx}
                        section={section}
                        content={document[section]}
                        notes={notes}
                        setSelectedNote={setSelectedNote}
                        setSelectedCluster={setSelectedCluster}
                        getProcessedMarkdown={getProcessedMarkdown}
                        jobId={jobId}
                        openRSVP={handleOpenRSVP}
                      />
                    </div>
                  </div>
                  </div>
                )}
              />
            </div>
            
            {/* Tab: Notes */}
            <div className={activeTab === "notes" ? "h-full w-full overflow-y-auto scrollbar-hide px-4 md:px-6 py-6 flex flex-col gap-6" : "hidden"}>
              {notes.length === 0 ? (
                <div className="bg-surface border border-border-subtle rounded-xl p-8 text-center text-muted-foreground font-medium shadow-sm">
                  아직 저장된 노트가 없습니다. 학습 가이드의 텍스트를 드래그하여 질문하고 노트로 저장해보세요.
                </div>
              ) : (
                <div className="flex flex-col gap-4">
                  <h3 className="font-label-md text-label-md text-text-primary border-b border-border-subtle pb-2">Saved Notes</h3>
                  {notes.map(note => (
                    <div key={note.id} onClick={() => setSelectedNote(note)} className="bg-surface border border-border-subtle rounded-lg p-4 shadow-sm flex gap-4 cursor-pointer hover:border-primary-container transition-colors group">
                      <div className="text-primary-container font-label-md text-label-md whitespace-nowrap"><MessageSquare size={16} className="inline mr-1" /></div>
                      <div>
                        <p className="font-body-sm text-body-sm text-text-primary font-bold mb-1">"{note.question}"</p>
                        <p className="font-body-sm text-body-sm text-muted-foreground bg-surface-container-low p-2 rounded line-clamp-2">대상: "{note.selected_text}"</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
          </div>
        </div>
      </main>

      {/* Q&A Modal (Ask) */}
      {qaModalOpen && (
        <div className="ask-modal-container fixed inset-0 bg-black/40 backdrop-blur-sm z-[150] flex items-center justify-center p-4">
          <div className="bg-surface border border-border-subtle w-full max-w-2xl rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] ">
            <div className="flex items-center justify-between p-4 border-b border-border-subtle bg-surface-container-low">
              <h3 className="font-bold flex items-center gap-2 text-text-primary"><Sparkles className="text-primary-container" size={18}/> 궁금한 점 해결하기</h3>
              <button onClick={() => {setQaModalOpen(false); setSelection(s => ({...s, show: false}));}} className="text-muted-foreground hover:text-text-primary transition-colors">
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
                      {["이 단어의 정확한 뜻이 무엇인가요?", "이 부분을 자동차에 비유해서 설명해줄 수 있나요?", "이 개념의 핵심 요약이 무엇인가요?", "초등학생도 이해할 수 있게 다시 설명해주세요."].map(q => (
                        <button 
                          key={q}
                          onClick={() => { setQuestion(q); handleAsk(q); }}
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
                        onChange={e => setQuestion(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleAsk()}
                      />
                      <button 
                        onClick={() => handleAsk()}
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
                  onClick={() => {setAnswer(""); setQuestion("");}}
                  className="px-4 py-2 rounded-lg border border-border bg-background hover:bg-muted font-medium "
                >
                  다른 질문하기
                </button>
                <button 
                  onClick={handleSaveNote}
                  className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-bold hover:opacity-90 flex items-center gap-2 "
                >
                  <Save size={18} /> 포스트잇으로 저장
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* View Note Modal (For Mobile or explicit click) */}
      {selectedNote && (
        <div className="view-modal-container fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4" onClick={(e) => {if(e.target === e.currentTarget) setSelectedNote(null)}}>
          <div 
            className="bg-surface/95 backdrop-blur-xl border border-border-subtle w-full max-w-lg rounded-[2rem] shadow-2xl overflow-hidden flex flex-col max-h-[80vh] "
            data-section={selectedNote.section}
            data-note-context={selectedNote.answer}
          >
            <div className="flex items-center justify-between p-4 border-b border-border bg-primary/10">
              <h3 className="font-bold flex items-center gap-2 text-primary"><MessageSquare size={18}/> 저장된 포스트잇 노트</h3>
              <button onClick={() => setSelectedNote(null)} className="text-muted-foreground hover:text-foreground">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 overflow-y-auto">
              <div className="mb-4">
                <p className="text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider">질문 내용</p>
                <div className="font-medium text-lg">"{selectedNote.question}"</div>
                <div className="text-sm text-muted-foreground mt-1">대상: <span className="bg-yellow-200/50 dark:bg-yellow-600/30 px-1 rounded">"{selectedNote.selected_text}"</span></div>
              </div>
              <div className="prose prose-sm dark:prose-invert max-w-none border-t border-border pt-4 ">
                <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                  {getProcessedMarkdown(selectedNote.section, selectedNote.answer)}
                </ReactMarkdown>
              </div>
            </div>
            <div className="p-4 border-t border-border bg-muted/30 flex justify-end">
              <button onClick={() => setSelectedNote(null)} className="px-6 py-2 rounded-lg bg-primary text-primary-foreground font-bold hover:opacity-90">닫기</button>
            </div>
          </div>
        </div>
      )}

      {/* Cluster Note Modal */}
      {selectedCluster && (
        <div className="view-modal-container fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4 animate-in fade-in" onClick={(e) => {if(e.target === e.currentTarget) setSelectedCluster(null)}}>
          <div className="bg-surface/95 backdrop-blur-xl border border-border-subtle w-full max-w-lg rounded-[2rem] shadow-2xl overflow-hidden flex flex-col max-h-[80vh] animate-in zoom-in-95">
            <div className="flex items-center justify-between p-4 border-b border-border bg-primary/10">
              <h3 className="font-bold flex items-center gap-2 text-primary"><MessageSquare size={18}/> 주변 질문 모음 ({selectedCluster.length})</h3>
              <button onClick={() => setSelectedCluster(null)} className="text-muted-foreground hover:text-foreground">
                <X size={20} />
              </button>
            </div>
            <div className="p-4 overflow-y-auto space-y-3">
              {selectedCluster.map((note, idx) => (
                <div key={note.id} className="bg-background/50 backdrop-blur-md border border-primary/20 shadow-sm rounded-xl p-4 cursor-pointer hover:bg-primary/5 hover:border-primary/50 transition-colors" onClick={() => {
                   setSelectedCluster(null);
                   setSelectedNote(note);
                }}>
                  <p className="text-xs font-semibold text-primary mb-2 flex items-center gap-2"><Sparkles size={14}/>질문 {idx + 1}</p>
                  <div className="font-bold text-sm mb-2 text-text-primary">"{note.question}"</div>
                  <div className="text-xs text-muted-foreground line-clamp-2 bg-surface-container-low p-2 rounded">대상: <span className="text-text-primary">"{note.selected_text}"</span></div>
                </div>
              ))}
            </div>
            <div className="p-4 border-t border-border bg-muted/30 flex justify-end">
              <button onClick={() => setSelectedCluster(null)} className="px-6 py-2 rounded-lg bg-primary text-primary-foreground font-bold hover:opacity-90">닫기</button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && (
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
                onClick={() => setDeleteModalOpen(false)}
                disabled={isDeleting}
                className="flex-1 bg-surface-container text-text-primary font-bold py-3.5 rounded-lg hover:bg-surface-container-high transition-all disabled:opacity-50 border border-border-subtle"
              >
                취소
              </button>
              <button 
                onClick={handleDelete}
                disabled={isDeleting}
                className="flex-1 bg-error text-on-error font-bold py-3.5 rounded-lg hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isDeleting ? <Loader2 className="animate-spin" size={18} /> : <Trash2 size={18} />}
                삭제하기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* RSVP Modal */}
      {rsvpOpen && (
        <div className="fixed inset-0 bg-surface/95 backdrop-blur-md z-[300] flex flex-col ">
          {/* Header */}
          <div className="p-4 md:p-6 flex items-center justify-between border-b border-border-subtle">
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2 text-text-primary">
                <Sparkles className="text-primary-container"/> 속독 모드 (RSVP)
              </h2>
              <p className="text-sm text-muted-foreground">{rsvpSection}</p>
            </div>
            <button onClick={closeRSVP} className="p-2 bg-surface-container-low rounded-full hover:bg-error/10 hover:text-error transition-colors">
              <X size={24} />
            </button>
          </div>

          {/* Main Area */}
          <div className="flex-1 flex flex-col items-center justify-center p-4 relative cursor-pointer" onClick={rsvp.toggle}>
             <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl px-4 flex justify-center items-center pointer-events-none">
                <div className="w-full flex items-baseline">
                   {/* Left Pad */}
                   <div className="flex-1 text-right text-5xl md:text-7xl font-bold text-text-primary opacity-80">
                      {rsvp.aligned.left}
                   </div>
                   {/* Pivot */}
                   <div className="text-5xl md:text-7xl font-bold text-primary-container">
                      {rsvp.aligned.pivot}
                   </div>
                   {/* Right Pad */}
                   <div className="flex-1 text-left text-5xl md:text-7xl font-bold text-text-primary opacity-80">
                      {rsvp.aligned.right}
                   </div>
                </div>
             </div>
             {!rsvp.isPlaying && (
                <div className="absolute top-2/3 mt-12 flex items-center gap-2 text-muted-foreground font-semibold animate-pulse pointer-events-none">
                  화면을 탭하여 시작/일시정지
                </div>
             )}
          </div>

          {/* Controls */}
          <div className="p-6 md:p-8 bg-surface border-t border-border-subtle flex flex-col gap-6 max-w-3xl w-full mx-auto rounded-t-2xl shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.1)]">
             <div className="flex items-center justify-between gap-4">
                <button onClick={rsvp.reset} className="text-muted-foreground hover:text-text-primary">
                  <Rewind size={24} />
                </button>
                <button onClick={rsvp.toggle} className="w-16 h-16 rounded-full bg-primary-container text-on-primary flex items-center justify-center shadow-md shadow-primary-container/20 hover:scale-105 active:scale-95 transition-all">
                  {rsvp.isPlaying ? <Pause size={32} /> : <Play size={32} className="ml-1" />}
                </button>
                <div className="flex flex-col items-center gap-1 w-32">
                  <span className="text-xs font-bold text-muted-foreground">속도: {rsvp.wpm} WPM</span>
                  <input type="range" min="150" max="800" step="10" value={rsvp.wpm} onChange={(e) => rsvp.setWpm(Number(e.target.value))} className="w-full accent-primary-container" />
                </div>
             </div>
             
             {/* Progress Bar */}
             <div className="flex items-center gap-3">
               <span className="text-xs font-bold text-muted-foreground w-12 text-right">{(rsvp.progress * 100).toFixed(0)}%</span>
               <div className="flex-1 h-3 bg-surface-container-highest rounded-full overflow-hidden relative cursor-pointer group" onClick={(e) => {
                 const rect = e.currentTarget.getBoundingClientRect();
                 const x = e.clientX - rect.left;
                 rsvp.seek(x / rect.width);
               }}>
                 <div className="absolute inset-0 bg-primary-container/10 group-hover:bg-primary-container/20 transition-colors"></div>
                 <div className="h-full bg-primary-container transition-all duration-150 ease-out" style={{ width: `${rsvp.progress * 100}%` }}></div>
               </div>
             </div>
          </div>
        </div>
      )}

      {/* 9종 프리셋 탐색기 모달 */}
      {showPresetMatrix && (
        <ViewerPresetMatrixModal
          title={title}
          currentJobId={jobId}
          presets={siblingPresets}
          totalPresets={totalSiblingPresets}
          onClose={() => setShowPresetMatrix(false)}
          onSelectGuide={handleSelectPresetGuide}
          onCreatePreset={handleCreatePresetFromModal}
        />
      )}

    </div>
  );
}
