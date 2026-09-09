"use client";

import React, { useEffect, useState, use, useRef, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import { 
  ArrowLeft, Loader2, PanelLeftClose, PanelLeftOpen, Trash2, 
  Sparkles, BookOpen, MessageSquare 
} from "lucide-react";
import { Virtuoso } from "react-virtuoso";

import { useRSVP } from "@/hooks/useRSVP";
import { processMarkdownWithNotes, Note } from "@/lib/markdownProcessor";
import { normalizeLength, normalizeAnalogy, extractVideoKey } from "@/lib/presets";

import { ViewerPresetMatrixModal, PresetInfo } from "./components/ViewerPresetMatrixModal";
import { ChapterItem } from "./components/ChapterItem";
import { VideoPanel } from "./components/VideoPanel";
import { FloatingToolbar, SelectionState } from "./components/FloatingToolbar";
import { QAModal, ViewNoteModal, ClusterNoteModal, DeleteConfirmModal } from "./components/NoteModals";
import { RSVPModal } from "./components/RSVPModal";

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
  
  // 파인만 / 인터랙티브 학습 모드 On/Off 상태 (몰입 읽기 모드)
  const [isInteractiveMode, setIsInteractiveMode] = useState<boolean>(true);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("interactive_mode_enabled");
      if (saved !== null) {
        setIsInteractiveMode(saved === "true");
      }
    } catch (e) {
      console.warn("Failed to read interactive mode from localStorage", e);
    }
  }, []);

  const toggleInteractiveMode = () => {
    setIsInteractiveMode((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("interactive_mode_enabled", String(next));
      } catch (e) {}
      return next;
    });
  };
  
  const resolvedParams = use(params);
  const jobId = resolvedParams.jobId;

  const [selection, setSelection] = useState<SelectionState>({ text: "", section: "", contextText: "", x: 0, y: 0, show: false });
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

  // 영상 핵심 내용 함축 요약 및 주제 안내 계산
  const summaryInsight = useMemo(() => {
    if (!document) return null;
    const secKeys = Object.keys(document);
    if (secKeys.length === 0) return null;

    let leadText = profileMessage;

    if (!leadText) {
      const firstSecContent = document[secKeys[0]] || "";
      const cleanText = firstSecContent
        .replace(/<[^>]*>[\s\S]*?<\/[^>]*>/g, '')
        .replace(/<[^>]*>/g, '')
        .replace(/```[\s\S]*?```/g, '')
        .replace(/^#+\s+.*$/gm, '')
        .replace(/>\s*/g, '')
        .replace(/[*_`]/g, '')
        .trim();

      const paragraphs = cleanText.split(/\n\s*\n/).map(p => p.trim()).filter(Boolean);
      leadText = paragraphs[0] ? paragraphs[0].slice(0, 180) + (paragraphs[0].length > 180 ? '...' : '') : "";
    }

    return {
      totalSections: secKeys.length,
      leadText: leadText,
      topics: secKeys.slice(0, 5)
    };
  }, [document, profileMessage]);

  const fetchSiblingPresets = async (currentJobId: string, currentUrl?: string, currentTitle?: string) => {
    let loadedFromApi = false;
    try {
      const query = currentJobId ? `job_id=${encodeURIComponent(currentJobId)}` : `url=${encodeURIComponent(currentUrl || '')}`;
      const res = await fetch(`/api/guide/presets?${query}`);
      if (res.ok) {
        const data = await res.json();
        if (data.presets && typeof data.presets === "object" && Object.keys(data.presets).length > 0) {
          setSiblingPresets(data.presets);
          setTotalSiblingPresets(data.total_presets || Object.keys(data.presets).length);
          loadedFromApi = true;
        }
      }
    } catch (e) {
      console.warn("Direct presets endpoint failed, falling back to history", e);
    }

    if (!loadedFromApi) {
      try {
        const historyRes = await fetch("/api/guide/history");
        if (historyRes.ok) {
          const items = await historyRes.json();
          if (Array.isArray(items)) {
            const targetKey = extractVideoKey(currentUrl || "", currentTitle || "");
            const matchedPresets: Record<string, PresetInfo> = {};
            
            for (const item of items) {
              if (!item) continue;
              const itemKey = extractVideoKey(item.url || "", item.title || "");
              if (itemKey === targetKey) {
                const l = normalizeLength(item.length_preset);
                const a = normalizeAnalogy(item.analogy_preset);
                const presetKey = `${l}__${a}`;
                matchedPresets[presetKey] = {
                  id: item.id,
                  title: item.title,
                  url: item.url,
                  date: item.date,
                  length_preset: l,
                  analogy_preset: a,
                  chapter_count: item.chapter_count || 0,
                  provider: item.provider || "youtube",
                  image_url: item.image_url,
                  video_duration: item.video_duration
                };
              }
            }
            
            if (Object.keys(matchedPresets).length > 0) {
              setSiblingPresets(matchedPresets);
              setTotalSiblingPresets(Object.keys(matchedPresets).length);
            }
          }
        }
      } catch (fallbackErr) {
        console.error("Failed fallback sibling presets fetch", fallbackErr);
      }
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
          fetchSiblingPresets(jobId, data.url || "", data.title || "");
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

        fetchSiblingPresets(jobId, docUrl, data.title || "");
        try {
          localStorage.setItem(`harness_guide_${jobId}`, JSON.stringify(data));
        } catch (storageErr) {
          console.warn("[LocalStorage] 캐시 저장 실패 또는 용량 초과:", storageErr);
        }
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
      }
    } catch (e) {
      if (!localStorage.getItem(`harness_guide_${jobId}`)) {
        setError("서버와 통신할 수 없습니다.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocument();
  }, [jobId]);

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
            if (el.tagName.toLowerCase() === "section") {
              const sectionIndex = parseInt(el.id.replace("chapter-", ""));
              sectionName = Object.keys(document || {})[sectionIndex];
              contextText = document?.[sectionName] || "";
              break;
            }
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
      }, 300);
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
          context: selection.contextText || document?.[selection.section] || "",
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
      if (!note) return;
      tagStart = `<margin-note text="${note}">`;
    }

    const currentContent = document[selection.section];
    if (!currentContent) return;

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

  // useCallback을 통해 자식 컴포넌트(ChapterItem 등)로의 불필요한 함수 재생성 및 리렌더 방지
  const getProcessedMarkdown = useCallback((sectionName: string, text: string) => {
    return processMarkdownWithNotes(sectionName, text, notes);
  }, [notes]);

  const getYoutubeEmbedUrl = (urlStr: string) => {
    if (!urlStr) return null;
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = urlStr.match(regExp);
    return (match && match[2].length === 11) ? `https://www.youtube.com/embed/${match[2]}` : null;
  };
  const embedUrl = getYoutubeEmbedUrl(url);

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

  return (
    <div className="flex flex-col min-h-screen bg-page-bg">
      {/* Floating Toolbar */}
      <FloatingToolbar 
        selection={selection}
        qaModalOpen={qaModalOpen}
        onAnnotate={handleAnnotate}
        onOpenQA={() => setQaModalOpen(true)}
      />

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
        <VideoPanel 
          isLeftPanelOpen={isLeftPanelOpen}
          embedUrl={embedUrl}
          url={url}
          title={title}
          profileMessage={profileMessage}
          sections={sections}
          summaryInsight={summaryInsight}
          lengthPreset={lengthPreset}
          analogyPreset={analogyPreset}
          siblingPresets={siblingPresets}
          jobId={jobId}
          totalSiblingPresets={totalSiblingPresets}
          isInteractiveMode={isInteractiveMode}
          isRegenerating={isRegenerating}
          onLengthPresetChange={handleLengthPresetChange}
          onAnalogyPresetChange={handleAnalogyPresetChange}
          onOpenPresetMatrix={() => setShowPresetMatrix(true)}
          onToggleInteractiveMode={toggleInteractiveMode}
          onRegenerate={handleRegenerate}
          onNavigateToSibling={(sibId) => router.push(`/guide/${sibId}`)}
        />

        {/* Right Pane: Scrollable Content (Tabs) */}
        <div className={`${isLeftPanelOpen ? 'w-full lg:w-[60%]' : 'w-full max-w-5xl mx-auto border-l border-r border-border-subtle'} flex-shrink-0 flex flex-col bg-page-bg min-w-0 transition-all duration-300 ease-in-out`}>
          {/* Tabs Header */}
          <div className="flex items-center border-b border-border-subtle bg-surface px-6 pt-4 sticky top-0 z-10">
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

            {/* 몰입 읽기 / 인터랙티브 모드 스위치 */}
            <div className="ml-auto pb-2 flex items-center">
              <button 
                type="button"
                onClick={toggleInteractiveMode}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold text-xs transition-all border cursor-pointer ${
                  isInteractiveMode 
                    ? "bg-primary/10 text-primary border-primary/20 hover:bg-primary/20" 
                    : "bg-surface-variant text-muted-foreground border-border-subtle hover:text-text-primary"
                }`}
                title={isInteractiveMode ? "파인만/퀴즈 등 인터랙티브 위젯을 숨기고 본문 읽기에 집중합니다." : "파인만/퀴즈 등 인터랙티브 학습 위젯을 다시 표시합니다."}
              >
                {isInteractiveMode ? <Sparkles size={13} className="text-primary" /> : <BookOpen size={13} />}
                <span>{isInteractiveMode ? "인터랙티브 모드" : "몰입 읽기 모드"}</span>
              </button>
            </div>
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
                          isInteractiveMode={isInteractiveMode}
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
                    <div 
                      key={note.id} 
                      onClick={() => setSelectedNote(note)} 
                      className="bg-surface border border-border-subtle rounded-lg p-4 shadow-sm flex gap-4 cursor-pointer hover:border-primary-container transition-colors group"
                    >
                      <div className="text-primary-container font-label-md text-label-md whitespace-nowrap">
                        <MessageSquare size={16} className="inline mr-1" />
                      </div>
                      <div>
                        <p className="font-body-sm text-body-sm text-text-primary font-bold mb-1">"{note.question}"</p>
                        <p className="font-body-sm text-body-sm text-muted-foreground bg-surface-container-low p-2 rounded line-clamp-2">
                          대상: "{note.selected_text}"
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
          </div>
        </div>
      </main>

      {/* Q&A Modal */}
      {qaModalOpen && (
        <QAModal 
          selection={selection}
          question={question}
          answer={answer}
          isAsking={isAsking}
          onClose={() => { setQaModalOpen(false); setSelection(s => ({ ...s, show: false })); }}
          onQuestionChange={setQuestion}
          onAsk={handleAsk}
          onResetAnswer={() => { setAnswer(""); setQuestion(""); }}
          onSaveNote={handleSaveNote}
        />
      )}

      {/* View Note Modal */}
      {selectedNote && (
        <ViewNoteModal 
          note={selectedNote}
          onClose={() => setSelectedNote(null)}
          getProcessedMarkdown={getProcessedMarkdown}
        />
      )}

      {/* Cluster Note Modal */}
      {selectedCluster && (
        <ClusterNoteModal 
          cluster={selectedCluster}
          onClose={() => setSelectedCluster(null)}
          onSelectNote={(note) => {
            setSelectedCluster(null);
            setSelectedNote(note);
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && (
        <DeleteConfirmModal 
          isDeleting={isDeleting}
          onClose={() => setDeleteModalOpen(false)}
          onConfirmDelete={handleDelete}
        />
      )}

      {/* RSVP Modal */}
      {rsvpOpen && (
        <RSVPModal 
          section={rsvpSection}
          rsvp={rsvp}
          onClose={closeRSVP}
        />
      )}

      {/* 9종 프리셋 탐색기 모달 */}
      {showPresetMatrix && (
        <ViewerPresetMatrixModal
          title={title}
          currentJobId={jobId}
          presets={siblingPresets}
          totalPresets={totalSiblingPresets}
          currentLengthPreset={lengthPreset}
          currentAnalogyPreset={analogyPreset}
          onClose={() => setShowPresetMatrix(false)}
          onSelectGuide={handleSelectPresetGuide}
          onCreatePreset={handleCreatePresetFromModal}
        />
      )}

    </div>
  );
}
