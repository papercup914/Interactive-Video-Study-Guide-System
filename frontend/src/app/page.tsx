"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, Sparkles, Loader2, Book, Clock, PlayCircle, Trash2, Link as LinkIcon, Paperclip, FileText, X, HelpCircle, AlertTriangle, Settings, Timer } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useTask } from "@/app/contexts/TaskContext";
type HistoryItem = {
  id: string;
  url: string;
  title: string;
  date: string;
  provider: string;
  chapter_count: number;
  generation_time_sec?: number;
  image_url?: string;
  video_duration?: string;
  length_preset?: string;
  analogy_preset?: string;
  learning_profile?: {
    average_score: number;
    total_questions: number;
    recent_advice: string;
    type_counts: Record<string, number>;
  };
};

export default function Home() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [provider, setProvider] = useState("nvidia/nemotron-3-ultra-550b-a55b");
  const [lengthPreset, setLengthPreset] = useState("Auto");
  const [analogyPreset, setAnalogyPreset] = useState("Auto");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [pdfParsingMethod, setPdfParsingMethod] = useState("option_b");
  
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  // Global Job state
  const { isGenerating, startTask, status } = useTask();
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Delete Modal state
  const [deleteTarget, setDeleteTarget] = useState<{id: string, title: string} | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [files, setFiles] = useState<File[]>([]);

  useEffect(() => {
    if (status === "idle" || status === "completed") {
      fetchHistory();
    }
  }, [status]);

  const fetchHistory = async () => {
    try {
      const res = await fetch("/api/guide/history");
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.error("Failed to fetch history", e);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url && files.length === 0) return;

    setIsSubmitting(true);
    let isForce = false;
    
    if (url && files.length === 0) {
      try {
        const checkRes = await fetch(`/api/guide/check?url=${encodeURIComponent(url)}`);
        if (checkRes.ok) {
          const checkData = await checkRes.json();
          if (checkData.exists) {
            const goToExisting = window.confirm("✨ 이미 이 영상으로 만든 학습서가 있어요! 보러 가시겠습니까?\n(취소를 누르면 옵션을 적용하여 새 버전으로 생성합니다.)");
            if (goToExisting) {
              router.push(`/guide/${checkData.job_id}`);
              setIsSubmitting(false);
              return;
            } else {
              isForce = true;
            }
          }
        }
      } catch(e) {
        console.error("Check API failed", e);
      }
    }
    
    try {
      const learnerProfile = localStorage.getItem("learnerProfile_v2") || "";
      
      const formData = new FormData();
      formData.append("url", url);
      formData.append("provider", provider);
      formData.append("length_preset", lengthPreset);
      formData.append("analogy_preset", analogyPreset);
      formData.append("pdf_parsing_method", pdfParsingMethod);
      formData.append("learner_profile", learnerProfile);
      formData.append("force_refresh", String(isForce));
      
      if (files.length > 0) {
        files.forEach(f => formData.append("files", f));
      }
      
      const res = await fetch("/api/guide/start", {
        method: "POST",
        body: formData
      });
      
      if (!res.ok) {
        let errorDetail = `서버 응답 오류 (상태 코드: ${res.status})`;
        try {
          const errData = await res.json();
          if (errData?.detail) {
            errorDetail = errData.detail;
          } else if (errData?.message) {
            errorDetail = errData.message;
          }
        } catch {
          const text = await res.text().catch(() => "");
          if (text) errorDetail = text.slice(0, 100);
        }

        if (res.status === 401) {
          alert("로그인 세션이 만료되었습니다. 다시 로그인해 주세요.");
          router.push("/login");
          return;
        }

        alert(`생성 요청 실패: ${errorDetail}`);
        return;
      }

      const data = await res.json();
      if (data?.job_id) {
        startTask(data.job_id);
      } else {
        alert("생성 시작에 실패했습니다. (Job ID가 생성되지 않음)");
      }
    } catch (e: any) {
      console.error("Guide start failed:", e);
      alert(`서버 연결 오류가 발생했습니다: ${e?.message || "네트워크 상태를 확인해주세요."}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    
    try {
      const res = await fetch(`/api/guide/${deleteTarget.id}`, {
        method: "DELETE",
      });
      
      if (res.ok) {
        setHistory(prev => prev.filter(item => item?.id !== deleteTarget.id));
        setDeleteTarget(null);
      } else {
        const err = await res.json().catch(() => ({}));
        alert(`가이드 삭제에 실패했습니다: ${err?.detail || err?.message || res.statusText}`);
      }
    } catch (e: any) {
      console.error("Failed to delete", e);
      alert(`삭제 중 오류가 발생했습니다: ${e?.message || "네트워크 상태를 확인해주세요."}`);
    } finally {
      setIsDeleting(false);
    }
  };

  const isDocumentOrUrl = (files.length > 0) || (url.length > 0 && !url.includes("youtube.com") && !url.includes("youtu.be"));

  return (
    <div className="bg-page-bg text-text-primary min-h-screen font-body-lg flex flex-col">
      {/* Top Navigation Bar */}
      <header className="bg-surface border-b border-border-subtle sticky top-0 z-50 h-16 flex justify-between items-center px-margin-page shadow-sm">
        <div className="flex items-center gap-2">
          <Book className="text-foreground" size={24} />
          <span className="font-headline-md text-headline-md text-foreground">StudyGuide.AI</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 rounded-full overflow-hidden border border-border-subtle cursor-pointer hover:ring-2 ring-primary-container transition-all">
            <img alt="User Profile" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAQRItX-_I6iDIBk9e3eqsrihz7X4tI_UxiYWYbxANkMnf6m4mIsjRKHojkc78fzI7maw-D93LcjEiahnNRi91p_myN6Y96qvttHWJcioQWT4RKAuXqldhxIZAwpHTApOlCirsTkDdR9N9DJXPr2ut_7Kdhfnt3SK9k1Cm9dAmOJ9qGHqAdfG8SYx-AweYKzZWrdwyIygreOfus7qfVF3McX6brAhKznJTYepNxK62iFiDxIjsVBoP-OoZ6Cl01cAwgwmb2qdX_gWc"/>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-5xl mx-auto px-4 md:px-margin-page py-12 flex flex-col gap-12">
        {/* Hero Section */}
        <section className="flex flex-col items-center text-center max-w-3xl mx-auto w-full">
          <h1 className="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-foreground mb-4 tracking-tight">
            Transform your videos into study guides
          </h1>
          <p className="font-body-lg text-body-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            긴 영상과 복잡한 문서를 내게 꼭 맞는 스터디 노트로.
          </p>

          <form onSubmit={handleStart} className="w-full bg-surface border border-border-subtle rounded-xl shadow-sm p-2 flex flex-col gap-2 relative transition-all focus-within:ring-2 focus-within:ring-foreground" suppressHydrationWarning>
            <div className="flex items-center gap-2 p-2">
              <LinkIcon className="text-muted-foreground ml-2 shrink-0" size={20} />
              
              {files.length > 0 ? (
                <div className="flex-1 bg-transparent px-2 font-body-lg text-body-lg text-primary flex items-center gap-2 overflow-x-auto scrollbar-hide">
                  {files.map((f, idx) => (
                    <div key={idx} className="flex items-center bg-primary-container/10 px-2 py-1 rounded-md shrink-0 border border-primary-container/20">
                      <span className="truncate max-w-[150px] text-sm">{f.name}</span>
                      <button type="button" onClick={() => setFiles(files.filter((_, i) => i !== idx))} className="ml-1 text-muted-foreground hover:text-error transition-colors">
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                  <button type="button" onClick={() => setFiles([])} className="text-muted-foreground hover:text-error transition-colors ml-auto shrink-0" title="모두 지우기">
                    <X size={18} />
                  </button>
                </div>
              ) : (
                <input 
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="유튜브 링크를 붙여넣거나 문서를 업로드하세요..." 
                  className="flex-1 bg-transparent border-none focus:ring-0 font-body-lg text-body-lg text-text-primary placeholder-muted-foreground outline-none w-full"
                  required={files.length === 0}
                />
              )}

              <div className="flex gap-2 shrink-0">
                <label className="p-2 text-muted-foreground hover:text-text-primary hover:bg-surface-container-lowest rounded-lg transition-colors border border-transparent hover:border-border-subtle flex items-center justify-center cursor-pointer">
                  <Paperclip size={20} />
                  <input 
                    type="file" 
                    accept=".pdf,.txt,.md" 
                    multiple
                    className="hidden" 
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        setFiles(Array.from(e.target.files));
                        setUrl("");
                      }
                    }}
                  />
                </label>
                <button 
                  type="submit"
                  disabled={isGenerating || isSubmitting}
                  className="bg-foreground hover:opacity-90 text-background font-label-md text-label-md px-4 sm:px-6 py-2 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? <Loader2 className="animate-spin" size={18} /> : <Sparkles size={18} />}
                  <span className="hidden sm:inline">Generate Guide</span>
                  <span className="sm:hidden">생성</span>
                </button>
              </div>
            </div>

            {/* Advanced Settings */}
            <div className="flex flex-wrap items-center justify-between gap-4 px-4 pb-2 border-t border-border-subtle pt-3 text-muted-foreground w-full">
              
              <div className="flex items-center gap-4 overflow-x-auto scrollbar-hide">
                <div className="flex items-center gap-2 shrink-0">
                  <Sparkles size={16} className="text-muted-foreground" />
                  <div className="flex items-center gap-1">
                    <span className="font-body-sm text-xs font-semibold text-text-primary">생성 모델</span>
                    <select 
                      className="bg-transparent border-none font-body-sm text-body-sm cursor-pointer hover:text-text-primary focus:ring-0 py-0 pl-1 pr-6"
                      value={provider}
                      onChange={(e) => setProvider(e.target.value)}
                    >
                      <option value="cerebras/gpt-oss-120b">Cerebras (Llama3)</option>
                      <option value="Google Gemini">Google Gemini</option>
                      <option value="OpenAI (GPT-4o)">OpenAI (GPT-4o)</option>
                      <option value="glm-5.2">Zhipu GLM-5.2</option>
                      <option value="nvidia/nemotron-3-ultra-550b-a55b">Nvidia Nemotron-3 Ultra 550B</option>
                    </select>
                  </div>
                </div>
                <div className="w-px h-4 bg-border-subtle hidden sm:block"></div>
                
                {!isDocumentOrUrl ? (
                  <>
                    <div className="flex items-center gap-2 shrink-0">
                      <FileText size={16} className="text-muted-foreground" />
                      <div className="flex items-center gap-1">
                        <span className="font-body-sm text-xs font-semibold text-text-primary">요약 분량</span>
                        <select 
                          className="bg-transparent border-none font-body-sm text-body-sm cursor-pointer hover:text-text-primary focus:ring-0 py-0 pl-1 pr-6"
                          value={lengthPreset}
                          onChange={(e) => setLengthPreset(e.target.value)}
                        >
                          <option value="Auto">자동 지정</option>
                          <option value="핵심 요약">핵심 요약</option>
                          <option value="적당한 설명">적당한 설명</option>
                          <option value="아주 상세하게">아주 상세하게</option>
                        </select>
                      </div>
                    </div>
                    <div className="w-px h-4 bg-border-subtle hidden sm:block"></div>
                    <div className="flex items-center gap-2 shrink-0">
                      <HelpCircle size={16} className="text-muted-foreground" />
                      <div className="flex items-center gap-1">
                        <span className="font-body-sm text-xs font-semibold text-text-primary">설명 방식</span>
                        <select 
                          className="bg-transparent border-none font-body-sm text-body-sm cursor-pointer hover:text-text-primary focus:ring-0 py-0 pl-1 pr-6"
                          value={analogyPreset}
                          onChange={(e) => setAnalogyPreset(e.target.value)}
                        >
                          <option value="Auto">자동 지정</option>
                          <option value="비유 없이 담백하게">비유 없이</option>
                          <option value="적절한 비유 추가">적절한 비유</option>
                          <option value="풍부한 비유">풍부한 비유</option>
                        </select>
                      </div>
                    </div>
                  </>
                ) : (
                  <span className="font-body-sm text-body-sm text-muted-foreground flex items-center gap-1 shrink-0">
                    <AlertTriangle size={14} className="text-yellow-500"/> 문서는 상세 설정이 비활성화됩니다.
                  </span>
                )}
              </div>

              {/* AI Architecture Tooltip Restored */}
              <div className="group relative inline-block shrink-0">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-help hover:text-foreground transition-colors">
                  <Sparkles size={14} className="text-foreground" />
                  <strong className="font-semibold font-body-sm">AI 아키텍처 안내</strong>
                </div>
                <div className="opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 absolute bottom-full right-0 mb-2 w-max max-w-xs bg-surface-inverse text-muted-foreground-foreground text-xs p-3 rounded-lg shadow-lg border border-border-subtle z-50 pointer-events-none text-left" style={{backgroundColor: 'var(--color-inverse-surface)', color: 'white'}}>
                  <p className="leading-relaxed whitespace-nowrap font-body-sm">
                    텍스트 생성: <b>Nvidia Nemotron 550B</b><br/>
                    시각 분석: <b>Gemini 3.6 Flash</b><br/>
                    음성 프로파일링: <b>Gemini 3.5 Flash-Lite</b><br/>
                    음성 추출: <b>Whisper</b><br/>
                    PDF 파싱: <b>pymupdf4llm</b>
                  </p>
                  <div className="absolute -bottom-1.5 right-4 w-3 h-3 border-b border-r border-border-subtle transform rotate-45" style={{backgroundColor: 'var(--color-inverse-surface)'}}></div>
                </div>
              </div>

            </div>
          </form>
        </section>

        {/* Recent Guides Section */}
        <section className="flex flex-col gap-6 w-full">
          <div className="flex justify-between items-center border-b border-border-subtle pb-2">
            <h2 className="font-headline-md text-headline-md text-text-primary">내 학습 서재</h2>
            <span className="text-muted-foreground font-label-md text-label-md flex items-center gap-1">
              최근 항목
            </span>
          </div>

          {loadingHistory ? (
            <div className="flex justify-center py-12">
              <Loader2 className="animate-spin text-primary-container" size={32} />
            </div>
          ) : history.length === 0 ? (
            <div className="text-center py-16 bg-surface border border-border-subtle rounded-xl shadow-sm">
              <p className="font-body-lg text-muted-foreground">아직 만들어진 가이드가 없습니다.</p>
              <p className="text-sm font-body-sm text-muted-foreground mt-2">위에서 첫 번째 영상을 입력해 보세요!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {history.map((item) => (
                <div 
                  key={item.id} 
                  className="group bg-surface border border-border-subtle rounded-xl overflow-hidden shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-200 cursor-pointer flex flex-col relative"
                  onClick={() => router.push(`/guide/${item.id}`)}
                >
                  <div className="w-full aspect-video bg-surface-container-low relative border-b border-border-subtle flex items-center justify-center overflow-hidden">
                    {item.provider === "upload" || (!item.url.includes("youtube") && !item.url.includes("youtu.be")) ? (
                      <div className="flex flex-col items-center justify-center text-muted-foreground opacity-70">
                        <FileText size={40} className="mb-2" />
                        <span className="font-label-md text-xs">문서 가이드</span>
                      </div>
                    ) : (
                      <div className="w-full h-full relative overflow-hidden group-hover:scale-105 transition-transform duration-500">
                         {item.url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^&?]+)/) ? (
                            <>
                              <img src={`https://img.youtube.com/vi/${item.url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^&?]+)/)?.[1]}/hqdefault.jpg`} className="w-full h-full object-cover" alt="Thumbnail" />
                              <div className="absolute inset-0 bg-black/20 flex items-center justify-center group-hover:bg-black/10 transition-colors">
                                <PlayCircle size={32} className="text-white opacity-80 shadow-sm rounded-full" />
                              </div>
                            </>
                         ) : (
                           <div className="w-full h-full bg-surface-variant flex items-center justify-center">
                              <PlayCircle size={40} className="text-muted-foreground opacity-50" />
                           </div>
                         )}
                      </div>
                    )}
                    {item.generation_time_sec && (
                      <div className="absolute bottom-2 right-2 bg-on-surface/80 backdrop-blur-none text-on-primary font-body-sm text-[11px] px-2 py-0.5 rounded flex items-center gap-1">
                        <Timer size={10} /> {item.generation_time_sec}s
                      </div>
                    )}
                    {item.video_duration && parseInt(item.video_duration) > 0 && (
                      <div className="absolute bottom-2 left-2 bg-black/80 backdrop-blur-none text-white font-body-sm text-[11px] px-2 py-0.5 rounded flex items-center gap-1">
                        <Clock size={10} /> {Math.floor(parseInt(item.video_duration) / 60)}:{(parseInt(item.video_duration) % 60).toString().padStart(2, '0')}
                      </div>
                    )}
                  </div>
                  <div className="p-4 flex flex-col gap-2 flex-1">
                    <h3 className="font-bold text-[13px] text-text-primary line-clamp-2 leading-snug tracking-tight">
                      {item.title.replace(/\.pdf$/i, '')}
                    </h3>
                    <div className="flex gap-1 flex-wrap mt-1">
                        <span className="bg-surface-variant text-muted-foreground px-1.5 py-0.5 rounded text-[10px] whitespace-nowrap">{item.length_preset || '기본'}</span>
                        <span className="bg-surface-variant text-muted-foreground px-1.5 py-0.5 rounded text-[10px] whitespace-nowrap">{item.analogy_preset || '기본'}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-auto text-muted-foreground text-[11px] tracking-tight">
                      <span className="truncate max-w-[100px]">{item.provider === 'upload' ? 'Upload' : 'YouTube'}</span>
                      <span>•</span>
                      <span>
                        {(() => {
                          try {
                            const date = new Date(item.date);
                            if (isNaN(date.getTime())) return item.date;
                            const yy = String(date.getFullYear()).slice(2);
                            const mm = String(date.getMonth() + 1).padStart(2, '0');
                            return `${yy}/${mm}`;
                          } catch (e) {
                            return item.date;
                          }
                        })()}
                      </span>
                    </div>
                  </div>
                  
                  {/* Hover Action */}
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteTarget({id: item.id, title: item.title});
                    }}
                    aria-label="Delete" 
                    className="absolute top-2 right-2 bg-surface text-muted-foreground hover:text-error hover:bg-error-container p-1.5 rounded border border-border-subtle shadow-sm hidden group-hover:flex transition-colors z-10"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-surface w-full max-w-md rounded-xl p-8 shadow-2xl animate-in zoom-in-95 border border-border-subtle">
            <div className="flex flex-col items-center text-center">
              <div className="bg-error-container p-3 rounded-full mb-4">
                <AlertTriangle className="text-error" size={32} />
              </div>
              <h3 className="font-headline-md text-headline-md text-text-primary mb-2">정말 삭제하시겠습니까?</h3>
              <p className="font-body-sm text-body-sm text-muted-foreground mb-6">
                <span className="font-bold text-text-primary">"{deleteTarget.title}"</span> 가이드가 영구적으로 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
              </p>
            </div>
            
            <div className="flex gap-3">
              <button 
                onClick={() => setDeleteTarget(null)}
                disabled={isDeleting}
                className="flex-1 bg-surface-container-low border border-border-subtle text-text-primary font-label-md py-3 rounded-lg hover:bg-surface-container transition-all disabled:opacity-50"
              >
                취소
              </button>
              <button 
                onClick={confirmDelete}
                disabled={isDeleting}
                className="flex-1 bg-error text-on-error font-label-md py-3 rounded-lg hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-sm"
              >
                {isDeleting ? <Loader2 className="animate-spin" size={18} /> : <Trash2 size={18} />}
                삭제하기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
