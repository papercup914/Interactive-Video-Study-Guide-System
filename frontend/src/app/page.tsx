"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { 
  Search, Sparkles, Loader2, Book, Clock, PlayCircle, Trash2, 
  Link as LinkIcon, Paperclip, FileText, X, HelpCircle, 
  AlertTriangle, Settings, Timer, Layers, ChevronRight, CheckCircle2, Grid, Key
} from "lucide-react";
import { useTask } from "@/app/contexts/TaskContext";

export type HistoryItem = {
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

export type GroupedGuide = {
  groupKey: string;
  url: string;
  title: string;
  provider: string;
  image_url?: string;
  video_duration?: string;
  latestDate: string;
  totalPresets: number;
  items: HistoryItem[];
  presets: Record<string, HistoryItem>;
  defaultItem: HistoryItem;
};

const LENGTH_PRESETS = ["핵심 요약", "적당한 설명", "아주 상세하게"] as const;
const ANALOGY_PRESETS = ["비유 없이 담백하게", "적절한 비유 추가", "풍부한 비유"] as const;

function extractVideoKey(url: string, title: string): string {
  if (!url) return title || "unknown";
  const ytMatch = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^&?]+)/);
  if (ytMatch && ytMatch[1]) {
    return `yt_${ytMatch[1]}`;
  }
  return url.trim().toLowerCase();
}

function groupHistoryItems(items: HistoryItem[]): GroupedGuide[] {
  const map = new Map<string, GroupedGuide>();

  for (const item of items) {
    if (!item) continue;
    const key = extractVideoKey(item.url, item.title);
    const length = item.length_preset || "기본";
    const analogy = item.analogy_preset || "기본";
    const presetKey = `${length}__${analogy}`;

    if (!map.has(key)) {
      map.set(key, {
        groupKey: key,
        url: item.url || "",
        title: item.title || "제목 알 수 없음",
        provider: item.provider || "",
        image_url: item.image_url,
        video_duration: item.video_duration,
        latestDate: item.date || "",
        totalPresets: 1,
        items: [item],
        presets: { [presetKey]: item },
        defaultItem: item,
      });
    } else {
      const g = map.get(key)!;
      g.items.push(item);
      g.presets[presetKey] = item;
      g.totalPresets = Object.keys(g.presets).length;

      // '아주 상세하게 + 풍부한 비유' 프리셋을 최우선 대표로 설정
      if (item.length_preset === "아주 상세하게" && item.analogy_preset === "풍부한 비유") {
        g.defaultItem = item;
      } else if (item.length_preset === "적당한 설명" && item.analogy_preset === "적절한 비유 추가") {
        if (g.defaultItem.length_preset !== "아주 상세하게" || g.defaultItem.analogy_preset !== "풍부한 비유") {
          g.defaultItem = item;
        }
      } else if (new Date(item.date).getTime() > new Date(g.latestDate).getTime()) {
        g.latestDate = item.date;
      }

      if (!g.video_duration && item.video_duration) {
        g.video_duration = item.video_duration;
      }
    }
  }

  return Array.from(map.values()).sort((a, b) => {
    const timeA = a.latestDate ? new Date(a.latestDate).getTime() : 0;
    const timeB = b.latestDate ? new Date(b.latestDate).getTime() : 0;
    return timeB - timeA;
  });
}

/**
 * 9종 프리셋 탐색 모달 컴포넌트
 */
function PresetMatrixModal({ 
  group, 
  onClose, 
  onSelectGuide 
}: { 
  group: GroupedGuide; 
  onClose: () => void; 
  onSelectGuide: (jobId: string) => void;
}) {
  return (
    <div className="fixed inset-0 bg-black/60 z-[110] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-surface w-full max-w-2xl rounded-2xl p-6 shadow-2xl border border-border-subtle" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-start mb-4 pb-3 border-b border-border-subtle">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-primary/10 text-primary text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                <Sparkles size={12} /> 9종 프리셋 탐색기
              </span>
              <span className="text-xs text-muted-foreground">총 {group.totalPresets}개 프리셋 보유</span>
            </div>
            <h3 className="font-bold text-base text-text-primary line-clamp-1">{group.title.replace(/\.pdf$/i, '')}</h3>
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
                  const item = group.presets[key];
                  const isAvailable = Boolean(item);

                  return (
                    <button
                      key={analogy}
                      disabled={!isAvailable}
                      onClick={() => item && onSelectGuide(item.id)}
                      className={`p-2.5 rounded-xl border text-left flex flex-col justify-between min-h-[72px] transition-all ${
                        isAvailable
                          ? "bg-surface border-border-subtle hover:border-primary hover:shadow-md cursor-pointer group/card"
                          : "bg-surface-container-lowest/50 border-dashed border-border-subtle/50 opacity-40 cursor-not-allowed"
                      }`}
                    >
                      <div className="flex items-center justify-between w-full">
                        <span className="font-semibold text-[11px] text-text-primary group-hover/card:text-primary transition-colors">
                          {analogy}
                        </span>
                        {isAvailable ? (
                          <CheckCircle2 size={12} className="text-green-500 shrink-0" />
                        ) : (
                          <span className="text-[9px] text-muted-foreground">미생성</span>
                        )}
                      </div>
                      {isAvailable && (
                        <div className="flex items-center justify-between mt-1 text-[10px] text-muted-foreground">
                          <span>{item.chapter_count}개 챕터</span>
                          <span className="text-primary font-bold flex items-center">
                            보기 <ChevronRight size={10} />
                          </span>
                        </div>
                      )}
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
            onClick={() => onSelectGuide(group.defaultItem.id)}
            className="bg-foreground text-background px-4 py-2 rounded-lg font-bold hover:opacity-90 transition-opacity flex items-center gap-1.5"
          >
            기본 추천 가이드 열기 <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * 대표 영상 그룹 카드 컴포넌트
 */
function GroupedGuideCard({
  group,
  onSelectGuide,
  onDeleteGroup,
}: {
  group: GroupedGuide;
  onSelectGuide: (jobId: string) => void;
  onDeleteGroup: (group: GroupedGuide) => void;
}) {
  const [selectedLength, setSelectedLength] = useState<string>("아주 상세하게");
  const [selectedAnalogy, setSelectedAnalogy] = useState<string>("풍부한 비유");
  const [showMatrix, setShowMatrix] = useState<boolean>(false);

  // 현재 선택된 프리셋 아이템 찾기 (없으면 대표 defaultItem 반환)
  const currentKey = `${selectedLength}__${selectedAnalogy}`;
  const currentPresetItem = group.presets[currentKey];
  const isSelectedPresetAvailable = Boolean(currentPresetItem);

  const isUploadOrDoc = group.provider === "upload" || (!group.url.includes("youtube") && !group.url.includes("youtu.be"));
  const ytVideoId = group.url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^&?]+)/)?.[1];

  return (
    <>
      <div 
        className="group bg-surface border border-border-subtle rounded-2xl overflow-hidden shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300 flex flex-col relative"
      >
        {/* 상단 미디어 영역 (썸네일) */}
        <div 
          className="w-full aspect-video bg-surface-container-low relative border-b border-border-subtle flex items-center justify-center overflow-hidden cursor-pointer"
          onClick={() => onSelectGuide(currentPresetItem ? currentPresetItem.id : group.defaultItem.id)}
        >
          {isUploadOrDoc ? (
            <div className="flex flex-col items-center justify-center text-muted-foreground opacity-70">
              <FileText size={44} className="mb-2 text-primary" />
              <span className="font-label-md text-xs font-semibold">문서 학습 가이드</span>
            </div>
          ) : ytVideoId ? (
            <div className="w-full h-full relative overflow-hidden group-hover:scale-105 transition-transform duration-500">
              <img 
                src={`https://img.youtube.com/vi/${ytVideoId}/hqdefault.jpg`} 
                className="w-full h-full object-cover" 
                alt={group.title} 
              />
              <div className="absolute inset-0 bg-black/25 flex items-center justify-center group-hover:bg-black/10 transition-colors">
                <PlayCircle size={36} className="text-white opacity-90 shadow-md rounded-full" />
              </div>
            </div>
          ) : (
            <div className="w-full h-full bg-surface-variant flex items-center justify-center">
              <PlayCircle size={40} className="text-muted-foreground opacity-50" />
            </div>
          )}

          {/* 영상 길이 뱃지 (좌하단) */}
          {group.video_duration && parseInt(group.video_duration) > 0 && (
            <div className="absolute bottom-2 left-2 bg-black/80 backdrop-blur-sm text-white font-body-sm text-[11px] font-semibold px-2 py-0.5 rounded-md flex items-center gap-1 shadow-sm">
              <Clock size={11} /> {Math.floor(parseInt(group.video_duration) / 60)}:{(parseInt(group.video_duration) % 60).toString().padStart(2, '0')}
            </div>
          )}

          {/* 보유 프리셋 수 뱃지 (우상단) */}
          <div className="absolute top-2 left-2 bg-foreground/90 backdrop-blur-sm text-background font-bold text-[11px] px-2 py-0.5 rounded-md flex items-center gap-1 shadow-sm">
            <Layers size={11} /> {group.totalPresets}종 프리셋
          </div>

          {/* 삭제 버튼 (우상단 호버) */}
          <button 
            onClick={(e) => {
              e.stopPropagation();
              onDeleteGroup(group);
            }}
            aria-label="Delete" 
            className="absolute top-2 right-2 bg-surface/90 text-muted-foreground hover:text-error hover:bg-error-container p-1.5 rounded-lg border border-border-subtle shadow-sm opacity-0 group-hover:opacity-100 transition-all z-10"
            title="이 영상의 모든 프리셋 삭제"
          >
            <Trash2 size={15} />
          </button>
        </div>

        {/* 중단 정보 영역 */}
        <div className="p-4 flex flex-col gap-3 flex-1">
          <div>
            <h3 
              className="font-bold text-[14px] text-text-primary line-clamp-2 leading-snug tracking-tight hover:text-primary transition-colors cursor-pointer"
              onClick={() => onSelectGuide(currentPresetItem ? currentPresetItem.id : group.defaultItem.id)}
              title={group.title}
            >
              {group.title.replace(/\.pdf$/i, '')}
            </h3>

            <div className="flex items-center gap-2 mt-1.5 text-muted-foreground text-[11px]">
              <span className="font-medium">{group.provider === 'upload' ? 'Upload' : 'YouTube'}</span>
              <span>•</span>
              <span>
                {(() => {
                  try {
                    const date = new Date(group.latestDate);
                    if (isNaN(date.getTime())) return group.latestDate;
                    const yy = String(date.getFullYear()).slice(2);
                    const mm = String(date.getMonth() + 1).padStart(2, '0');
                    const dd = String(date.getDate()).padStart(2, '0');
                    return `${yy}.${mm}.${dd}`;
                  } catch {
                    return group.latestDate;
                  }
                })()}
              </span>
            </div>
          </div>

          {/* 하단 9종 프리셋 셀렉터 컨트롤러 */}
          <div className="mt-auto pt-3 border-t border-border-subtle flex flex-col gap-2">
            <div className="flex items-center justify-between text-[11px] text-muted-foreground font-semibold">
              <span className="flex items-center gap-1">
                <Sparkles size={12} className="text-primary" /> 프리셋 맞춤 선택
              </span>
              <button 
                type="button"
                onClick={() => setShowMatrix(true)}
                className="text-primary hover:underline flex items-center gap-0.5 text-[11px] font-bold"
              >
                <Grid size={11} /> 9종 전체보기
              </button>
            </div>

            {/* 프리셋 선택 드롭다운 2종 */}
            <div className="grid grid-cols-2 gap-1.5">
              <select
                value={selectedLength}
                onChange={(e) => setSelectedLength(e.target.value)}
                className="bg-surface-variant/80 border border-border-subtle text-text-primary text-[11px] font-medium rounded-lg px-2 py-1 focus:ring-1 focus:ring-primary outline-none cursor-pointer"
              >
                {LENGTH_PRESETS.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>

              <select
                value={selectedAnalogy}
                onChange={(e) => setSelectedAnalogy(e.target.value)}
                className="bg-surface-variant/80 border border-border-subtle text-text-primary text-[11px] font-medium rounded-lg px-2 py-1 focus:ring-1 focus:ring-primary outline-none cursor-pointer"
              >
                {ANALOGY_PRESETS.map((a) => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>

            {/* 바로 열기 액션 버튼 */}
            <button
              type="button"
              onClick={() => onSelectGuide(currentPresetItem ? currentPresetItem.id : group.defaultItem.id)}
              className={`w-full py-2 px-3 rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 transition-all mt-1 ${
                isSelectedPresetAvailable
                  ? "bg-foreground text-background hover:opacity-90 shadow-sm"
                  : "bg-surface-variant text-text-primary hover:bg-surface-container-high border border-border-subtle"
              }`}
            >
              {isSelectedPresetAvailable ? (
                <>
                  <span>학습 시작 ({currentPresetItem.chapter_count}챕터)</span>
                  <ChevronRight size={13} />
                </>
              ) : (
                <>
                  <span>기본 가이드 열기</span>
                  <ChevronRight size={13} />
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 9종 프리셋 탐색 모달 */}
      {showMatrix && (
        <PresetMatrixModal
          group={group}
          onClose={() => setShowMatrix(false)}
          onSelectGuide={(id) => {
            setShowMatrix(false);
            onSelectGuide(id);
          }}
        />
      )}
    </>
  );
}

export default function Home() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [provider, setProvider] = useState("openrouter/nvidia/nemotron-3.5-lightning:free");
  const [lengthPreset, setLengthPreset] = useState("Auto");
  const [analogyPreset, setAnalogyPreset] = useState("Auto");
  const [pdfParsingMethod, setPdfParsingMethod] = useState("option_b");
  
  // BYOK (Bring Your Own Key) & Multi-Provider Settings
  const [customApiKey, setCustomApiKey] = useState("");
  const [customBaseUrl, setCustomBaseUrl] = useState("");
  const [showByokModal, setShowByokModal] = useState(false);

  useEffect(() => {
    const savedKey = localStorage.getItem("user_byok_api_key") || "";
    const savedBase = localStorage.getItem("user_byok_base_url") || "";
    if (savedKey) setCustomApiKey(savedKey);
    if (savedBase) setCustomBaseUrl(savedBase);
  }, []);
  
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  // Global Job state
  const { isGenerating, startTask, status } = useTask();
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Delete Modal state (Grouped Delete)
  const [deleteTargetGroup, setDeleteTargetGroup] = useState<GroupedGuide | null>(null);
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
        setHistory(Array.isArray(data) ? data : []);
      }
    } catch (e) {
      console.error("Failed to fetch history", e);
    } finally {
      setLoadingHistory(false);
    }
  };

  // 비디오 단위로 그룹핑된 리스트
  const groupedGuides = useMemo(() => {
    return groupHistoryItems(history);
  }, [history]);

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
      } catch (err) {
        console.error("Check API failed", err);
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
      if (customApiKey) formData.append("custom_api_key", customApiKey);
      if (customBaseUrl) formData.append("custom_base_url", customBaseUrl);
      
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
    } catch (err: any) {
      console.error("Guide start failed:", err);
      alert(`서버 연결 오류가 발생했습니다: ${err?.message || "네트워크 상태를 확인해주세요."}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmDeleteGroup = async () => {
    if (!deleteTargetGroup) return;
    setIsDeleting(true);
    
    try {
      const deleteIds = deleteTargetGroup.items.map(item => item.id);
      await Promise.all(
        deleteIds.map(id => fetch(`/api/guide/${id}`, { method: "DELETE" }))
      );
      
      setHistory(prev => prev.filter(item => !deleteIds.includes(item.id)));
      setDeleteTargetGroup(null);
    } catch (err: any) {
      console.error("Failed to delete group", err);
      alert(`삭제 중 오류가 발생했습니다: ${err?.message || "네트워크 상태를 확인해주세요."}`);
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
      <main className="flex-1 w-full max-w-6xl mx-auto px-4 md:px-margin-page py-12 flex flex-col gap-12">
        {/* Hero Section */}
        <section className="flex flex-col items-center text-center max-w-3xl mx-auto w-full">
          <h1 className="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-foreground mb-4 tracking-tight">
            Transform your videos into study guides
          </h1>
          <p className="font-body-lg text-body-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            긴 영상과 복잡한 문서를 9종 맞춤형 스터디 노트로 즉시 변환하세요.
          </p>

          <form onSubmit={handleStart} className="w-full bg-surface border border-border-subtle rounded-2xl shadow-sm p-2 flex flex-col gap-2 relative transition-all focus-within:ring-2 focus-within:ring-foreground" suppressHydrationWarning>
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
                  className="bg-foreground hover:opacity-90 text-background font-label-md text-label-md px-4 sm:px-6 py-2 rounded-xl transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
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
                      <option value="openrouter/nvidia/nemotron-3.5-lightning:free">⚡ [무료 초고속] NVIDIA Nemotron Lightning (추천)</option>
                      <option value="openrouter/nvidia/nemotron-3-ultra-550b-a55b:free">💎 [무료 심층] NVIDIA Nemotron Ultra 550B</option>
                      <option value="OpenAI (GPT-4o)">🔑 [개인키 전용] OpenAI (GPT-4o)</option>
                    </select>
                    <button
                      type="button"
                      onClick={() => setShowByokModal(true)}
                      className="text-[11px] px-2 py-0.5 rounded-full border border-border-subtle hover:bg-surface-variant text-text-secondary flex items-center gap-1 shrink-0 transition-colors ml-1"
                      title="개인 API Key 연결 (BYOK)"
                    >
                      <Key size={11} className={customApiKey ? "text-primary" : "text-muted-foreground"} />
                      <span>{customApiKey ? "개인 Key 사용 중" : "내 API Key 연결"}</span>
                    </button>
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

              {/* AI Architecture Tooltip */}
              <div className="group relative inline-block shrink-0">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-help hover:text-foreground transition-colors">
                  <Sparkles size={14} className="text-foreground" />
                  <strong className="font-semibold font-body-sm">AI 엔진 안내</strong>
                </div>
                <div className="opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 absolute bottom-full right-0 mb-2 w-max max-w-xs bg-surface-inverse text-muted-foreground-foreground text-xs p-3 rounded-lg shadow-lg border border-border-subtle z-50 pointer-events-none text-left" style={{backgroundColor: 'var(--color-inverse-surface)', color: 'white'}}>
                  <p className="leading-relaxed whitespace-nowrap font-body-sm">
                    생성 엔진: <b>Gemini 3.6/3.5 Flash</b><br/>
                    웹/자막 분석: <b>Jina AI / Innertube</b><br/>
                    음성 인식: <b>Whisper STT</b><br/>
                    문서 파싱: <b>PyMuPDF4LLM</b>
                  </p>
                  <div className="absolute -bottom-1.5 right-4 w-3 h-3 border-b border-r border-border-subtle transform rotate-45" style={{backgroundColor: 'var(--color-inverse-surface)'}}></div>
                </div>
              </div>
            </div>
          </form>
        </section>

        {/* Recent Guides Section */}
        <section className="flex flex-col gap-6 w-full">
          <div className="flex justify-between items-center border-b border-border-subtle pb-3">
            <div>
              <h2 className="font-headline-md text-headline-md text-text-primary">내 학습 서재</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                총 <b>{groupedGuides.length}개</b> 영상/문서 (총 {history.length}개 프리셋 보유)
              </p>
            </div>
            <span className="text-muted-foreground font-label-md text-xs bg-surface-variant px-2.5 py-1 rounded-full flex items-center gap-1">
              <Layers size={13} /> 그룹핑 뷰 적용됨
            </span>
          </div>

          {loadingHistory ? (
            <div className="flex justify-center py-16">
              <Loader2 className="animate-spin text-primary-container" size={36} />
            </div>
          ) : groupedGuides.length === 0 ? (
            <div className="text-center py-16 bg-surface border border-border-subtle rounded-2xl shadow-sm">
              <p className="font-body-lg text-muted-foreground">아직 만들어진 가이드가 없습니다.</p>
              <p className="text-sm font-body-sm text-muted-foreground mt-2">위에서 첫 번째 영상을 입력해 보세요!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {groupedGuides.map((group) => (
                <GroupedGuideCard
                  key={group.groupKey}
                  group={group}
                  onSelectGuide={(id) => router.push(`/guide/${id}`)}
                  onDeleteGroup={(g) => setDeleteTargetGroup(g)}
                />
              ))}
            </div>
          )}
        </section>
      </main>

      {/* Delete Confirmation Modal (Grouped) */}
      {deleteTargetGroup && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[120] flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-surface w-full max-w-md rounded-2xl p-8 shadow-2xl animate-in zoom-in-95 border border-border-subtle">
            <div className="flex flex-col items-center text-center">
              <div className="bg-error-container p-3 rounded-full mb-4">
                <AlertTriangle className="text-error" size={32} />
              </div>
              <h3 className="font-headline-md text-headline-md text-text-primary mb-2">정말 삭제하시겠습니까?</h3>
              <p className="font-body-sm text-body-sm text-muted-foreground mb-6 leading-relaxed">
                <span className="font-bold text-text-primary">"{deleteTargetGroup.title}"</span> 영상의 <span className="font-bold text-error">총 {deleteTargetGroup.totalPresets}개 프리셋 가이드</span>가 모두 영구 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
              </p>
            </div>
            
            <div className="flex gap-3">
              <button 
                onClick={() => setDeleteTargetGroup(null)}
                disabled={isDeleting}
                className="flex-1 bg-surface-container-low border border-border-subtle text-text-primary font-label-md py-3 rounded-xl hover:bg-surface-container transition-all disabled:opacity-50"
              >
                취소
              </button>
              <button 
                onClick={confirmDeleteGroup}
                disabled={isDeleting}
                className="flex-1 bg-error text-on-error font-label-md py-3 rounded-xl hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-sm"
              >
                {isDeleting ? <Loader2 className="animate-spin" size={18} /> : <Trash2 size={18} />}
                {deleteTargetGroup.totalPresets}개 전체 삭제
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BYOK (Bring Your Own Key) Settings Modal */}
      {showByokModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[120] flex items-center justify-center p-4 animate-in fade-in" onClick={() => setShowByokModal(false)}>
          <div className="bg-surface w-full max-w-lg rounded-2xl p-6 shadow-2xl animate-in zoom-in-95 border border-border-subtle" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4 pb-3 border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-primary/10 text-primary">
                  <Key size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-base text-text-primary">개인 AI API Key 설정 (BYOK)</h3>
                  <p className="text-xs text-muted-foreground">내 전용 키를 연결하여 할당량 제한 없이 가이드를 생성합니다.</p>
                </div>
              </div>
              <button 
                onClick={() => setShowByokModal(false)}
                className="text-muted-foreground hover:text-text-primary p-1.5 rounded-lg hover:bg-surface-variant transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div className="bg-surface-variant/50 p-3 rounded-xl border border-border-subtle text-xs text-muted-foreground leading-relaxed">
                <span className="font-semibold text-text-primary">🔒 보안 안내: </span>
                입력하신 키는 <b>서버 데이터베이스에 전혀 저장되지 않으며</b>, 오직 본인 브라우저(localStorage)에만 안전하게 보관됩니다.
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-primary mb-1">
                  API Key (OpenAI / Gemini / Groq / OpenRouter 등)
                </label>
                <input
                  type="password"
                  placeholder="sk-..., gsk_..., sk-or-..., AIzaSy..."
                  value={customApiKey}
                  onChange={(e) => setCustomApiKey(e.target.value)}
                  className="w-full bg-surface-container-low border border-border-subtle rounded-xl px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <p className="text-[11px] text-muted-foreground mt-1">
                  Groq(gsk_), OpenRouter(sk-or-), Gemini(AIzaSy), OpenAI(sk-) 키를 입력하면 자동으로 감지합니다.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-primary mb-1">
                  Custom Base URL (선택 사항)
                </label>
                <input
                  type="text"
                  placeholder="예: https://api.groq.com/openai/v1 또는 사내 프록시 URL"
                  value={customBaseUrl}
                  onChange={(e) => setCustomBaseUrl(e.target.value)}
                  className="w-full bg-surface-container-low border border-border-subtle rounded-xl px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            <div className="flex items-center justify-between gap-3 mt-6 pt-3 border-t border-border-subtle">
              <button
                type="button"
                onClick={() => {
                  setCustomApiKey("");
                  setCustomBaseUrl("");
                  localStorage.removeItem("user_byok_api_key");
                  localStorage.removeItem("user_byok_base_url");
                  setShowByokModal(false);
                }}
                className="text-xs text-error hover:underline"
              >
                키 초기화 (기본 무료 AI 사용)
              </button>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowByokModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-medium bg-surface-container-low border border-border-subtle text-text-secondary hover:bg-surface-variant transition-colors"
                >
                  취소
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (customApiKey) {
                      localStorage.setItem("user_byok_api_key", customApiKey.trim());
                    } else {
                      localStorage.removeItem("user_byok_api_key");
                    }
                    if (customBaseUrl) {
                      localStorage.setItem("user_byok_base_url", customBaseUrl.trim());
                    } else {
                      localStorage.removeItem("user_byok_base_url");
                    }
                    setShowByokModal(false);
                  }}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-primary text-on-primary hover:opacity-90 transition-opacity"
                >
                  설정 저장
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
