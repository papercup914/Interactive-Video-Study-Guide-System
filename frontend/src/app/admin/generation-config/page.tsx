"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Sliders,
  Sparkles,
  Save,
  RotateCcw,
  Zap,
  CheckCircle2,
  AlertCircle,
  Cpu,
  FileText,
  HelpCircle,
  Layers,
  ShieldCheck,
  Play,
  Copy,
  ChevronRight,
  Info,
  Clock,
  ArrowLeft,
  AlertTriangle,
  FileCode,
  ToggleLeft,
  ToggleRight,
  Settings,
  Database,
  RefreshCw,
  Eye
} from "lucide-react";
import { useAdminAuth } from "../layout";

// Config Data Types matching backend pipeline_config.py
interface LLMConfig {
  primary_model: string;
  fallback_models: string[];
  temperature: number;
  max_tokens: number;
  concurrency: number;
  timeout_seconds: number;
  max_retries: number;
  retry_multiplier: number;
}

interface OutlineConfig {
  use_official_chapters: boolean;
  official_adaptation_style: string;
  min_chapters: number;
  max_chapters: number;
  target_chunk_size: number;
  strict_time_sequence: boolean;
  smart_slicing_window: number;
  clean_noise_tags: boolean;
  fallback_templates: {
    business: string[];
    technical: string[];
    general: string[];
  };
}

interface ChapterConfig {
  zero_greeting_policy: boolean;
  strict_korean_policy: boolean;
  default_persona_role: string;
  default_persona_tone: string;
  default_focus_areas: string;
  forbidden_greeting_words: string[];
  narrative_sections: string[];
}

interface WidgetsConfig {
  feynman_enabled: boolean;
  steptracer_enabled: boolean;
  mnemonic_enabled: boolean;
  procedure_enabled: boolean;
  attachment_mode: string;
  require_strict_json: boolean;
}

interface GuardrailsConfig {
  min_total_chars_summary: number;
  min_total_chars_detailed: number;
  min_narrative_chars_summary: number;
  min_narrative_chars_detailed: number;
  min_korean_chars: number;
  min_korean_ratio_percent: number;
  english_char_threshold_for_ratio_check: number;
  enable_auto_escalation_retry: boolean;
  escalation_prompt: string;
}

interface SourcesConfig {
  transcript_priority: string[];
  whisper_model_size: string;
  clean_jina_scraped_noise: boolean;
  enable_gemini_context_caching: boolean;
  max_script_chars_for_caching: number;
}

interface PipelineConfig {
  llm: LLMConfig;
  outline: OutlineConfig;
  chapter: ChapterConfig;
  widgets: WidgetsConfig;
  guardrails: GuardrailsConfig;
  sources: SourcesConfig;
}

interface PresetMeta {
  name: string;
  description: string;
}

export default function GenerationConfigPage() {
  const { isAuthorized, getAdminHeaders } = useAdminAuth();

  // Active Main Tab
  const [activeTab, setActiveTab] = useState<
    "llm" | "outline" | "chapter" | "widgets" | "guardrails" | "sources" | "playground"
  >("llm");

  // Config State
  const [config, setConfig] = useState<PipelineConfig | null>(null);
  const [initialConfig, setInitialConfig] = useState<PipelineConfig | null>(null);
  const [presets, setPresets] = useState<Record<string, PresetMeta>>({});
  const [hasChanges, setHasChanges] = useState<boolean>(false);

  // Status & Feedback
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [resetting, setResetting] = useState<boolean>(false);
  const [applyingPreset, setApplyingPreset] = useState<string | null>(null);
  const [toast, setToast] = useState<{ msg: string; type: "success" | "error" } | null>(null);

  // Playground Simulation State
  const [simType, setSimType] = useState<"outline" | "chapter">("outline");
  const [simText, setSimText] = useState<string>(
    "인공지능과 대규모 언어 모델(LLM)은 현대 소프트웨어 개발의 패러다임을 급격히 변화시키고 있습니다. 전통적인 규칙 기반 프로그래밍과 달리, 방대한 데이터로부터 문맥을 스스로 학습하여 복잡한 추론과 코드 생성, 문서 요약을 수행합니다. 특히 에이전트 아키텍처는 목표 지향적 계획 수립과 도구 호출(Tool Calling)을 통해 스스로 오류를 감지하고 수정하는 자율성을 제공합니다."
  );
  const [simTitle, setSimTitle] = useState<string>("인공지능 에이전트 시스템 아키텍처");
  const [simRunning, setSimRunning] = useState<boolean>(false);
  const [simResult, setSimResult] = useState<any>(null);

  const showToast = (msg: string, type: "success" | "error" = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  // 1. Fetch Configuration from Backend
  const fetchConfig = useCallback(async () => {
    if (!isAuthorized) return;
    setLoading(true);
    try {
      const res = await fetch("/api/admin/pipeline/config", {
        headers: getAdminHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        if (data.config) {
          setConfig(data.config);
          setInitialConfig(JSON.parse(JSON.stringify(data.config)));
          setHasChanges(false);
        }
        if (data.presets) {
          setPresets(data.presets);
        }
      } else {
        showToast("설정 데이터를 불러오는 중 오류가 발생했습니다.", "error");
      }
    } catch (e: any) {
      console.error("Config fetch error:", e);
      showToast("서버 통신 실패: " + e.message, "error");
    } finally {
      setLoading(false);
    }
  }, [isAuthorized, getAdminHeaders]);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  // Check dirty state
  const handleConfigChange = (newConfig: PipelineConfig) => {
    setConfig(newConfig);
    if (initialConfig) {
      const changed = JSON.stringify(newConfig) !== JSON.stringify(initialConfig);
      setHasChanges(changed);
    }
  };

  // 2. Save Configuration
  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    try {
      const res = await fetch("/api/admin/pipeline/config", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...getAdminHeaders()
        },
        body: JSON.stringify({ config })
      });
      if (res.ok) {
        const data = await res.json();
        setConfig(data.config);
        setInitialConfig(JSON.parse(JSON.stringify(data.config)));
        setHasChanges(false);
        showToast("생성 매커니즘 설정이 DB에 영속화되어 즉시 반영되었습니다.", "success");
      } else {
        const err = await res.json();
        showToast(`저장 실패: ${err.detail || "알 수 없는 오류"}`, "error");
      }
    } catch (e: any) {
      showToast("설정 저장 실패: " + e.message, "error");
    } finally {
      setSaving(false);
    }
  };

  // 3. Reset to Defaults
  const handleReset = async () => {
    if (!confirm("모든 파이프라인 매커니즘 설정을 시스템 표준 기본값(Factory Default)으로 리셋하시겠습니까?")) {
      return;
    }
    setResetting(true);
    try {
      const res = await fetch("/api/admin/pipeline/reset", {
        method: "POST",
        headers: getAdminHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setConfig(data.config);
        setInitialConfig(JSON.parse(JSON.stringify(data.config)));
        setHasChanges(false);
        showToast("모든 설정이 초기 표준값으로 성공적으로 리셋되었습니다.", "success");
      } else {
        showToast("초기화 실패", "error");
      }
    } catch (e: any) {
      showToast("초기화 중 오류 발생: " + e.message, "error");
    } finally {
      setResetting(false);
    }
  };

  // 4. Apply Preset
  const handleApplyPreset = async (presetKey: string) => {
    setApplyingPreset(presetKey);
    try {
      const res = await fetch("/api/admin/pipeline/apply-preset", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAdminHeaders()
        },
        body: JSON.stringify({ preset_key: presetKey })
      });
      if (res.ok) {
        const data = await res.json();
        setConfig(data.config);
        setInitialConfig(JSON.parse(JSON.stringify(data.config)));
        setHasChanges(false);
        showToast(`'${presets[presetKey]?.name || presetKey}' 프리셋이 성공적으로 적용되었습니다.`, "success");
      } else {
        showToast("프리셋 적용 실패", "error");
      }
    } catch (e: any) {
      showToast("프리셋 적용 오류: " + e.message, "error");
    } finally {
      setApplyingPreset(null);
    }
  };

  // 5. Run Simulation Playground
  const handleRunSimulation = async () => {
    setSimRunning(true);
    setSimResult(null);
    try {
      const res = await fetch("/api/admin/pipeline/test-simulate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAdminHeaders()
        },
        body: JSON.stringify({
          test_type: simType,
          sample_text: simText,
          section_title: simTitle,
          raw_title: simTitle,
          config_override: config // 관리자가 수정한 현재 상태 임시 반영
        })
      });
      const data = await res.json();
      setSimResult(data);
      if (data.status === "success") {
        showToast("시뮬레이션이 성공적으로 완료되었습니다!", "success");
      } else {
        showToast("시뮬레이션 실패: " + data.message, "error");
      }
    } catch (e: any) {
      showToast("시뮬레이션 통신 에러: " + e.message, "error");
    } finally {
      setSimRunning(false);
    }
  };

  const tabs = [
    { id: "llm", label: "AI 모델 & 엔진", icon: Cpu },
    { id: "outline", label: "목차 설계 규칙", icon: Layers },
    { id: "chapter", label: "본문 서술 & 프롬프트", icon: FileText },
    { id: "widgets", label: "인터랙티브 위젯", icon: Sparkles },
    { id: "guardrails", label: "품질 검증 가드레일", icon: ShieldCheck },
    { id: "sources", label: "데이터 소스 & 자막", icon: Database },
    { id: "playground", label: "실시간 테스트 랩", icon: Play },
  ];

  return (
    <div className="space-y-6 pb-20">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-2xl border transition-all animate-in fade-in slide-in-from-bottom-5 ${
            toast.type === "success"
              ? "bg-slate-900 border-emerald-500/50 text-emerald-300"
              : "bg-slate-900 border-rose-500/50 text-rose-300"
          }`}
        >
          {toast.type === "success" ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : (
            <AlertCircle className="w-5 h-5 text-rose-400" />
          )}
          <span className="text-xs sm:text-sm font-semibold">{toast.msg}</span>
        </div>
      )}

      {/* Top Header & Floating Action Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2.5">
            <Link
              href="/admin"
              className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
              title="관리자 허브로 돌아가기"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-2">
              학습 가이드 생성 매커니즘 제어 포털
            </h1>
            {hasChanges && (
              <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 text-xs font-bold animate-pulse">
                수정 사항 미저장
              </span>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            AI 모델, 목차 생성 알고리즘, 서술형 본문 프롬프트, 4대 인터랙티브 위젯 규칙, 품질 검증 가드레일을 실시간으로 수정·저장합니다.
          </p>
        </div>

        {/* Action Buttons: Presets, Reset, Save */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Preset Selector */}
          <div className="relative inline-block">
            <select
              value=""
              onChange={(e) => {
                if (e.target.value) handleApplyPreset(e.target.value);
              }}
              disabled={applyingPreset !== null}
              className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs font-semibold text-slate-200 hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all cursor-pointer"
            >
              <option value="" disabled>
                {applyingPreset ? "프리셋 적용 중..." : "⚡ 추천 프리셋 선택..."}
              </option>
              {Object.entries(presets).map(([key, meta]) => (
                <option key={key} value={key}>
                  {meta.name}
                </option>
              ))}
            </select>
          </div>

          {/* Reset Button */}
          <button
            onClick={handleReset}
            disabled={resetting || loading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 hover:bg-rose-950/40 text-slate-300 hover:text-rose-300 border border-slate-700/80 hover:border-rose-800/50 text-xs font-bold transition-all disabled:opacity-50"
            title="시스템 초기 기본값으로 복원"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${resetting ? "animate-spin text-rose-400" : ""}`} />
            <span>기본값 복원</span>
          </button>

          {/* Save Button */}
          <button
            onClick={handleSave}
            disabled={saving || loading || !hasChanges}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold shadow-lg transition-all ${
              hasChanges
                ? "bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white shadow-indigo-600/30 animate-bounce"
                : "bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed"
            }`}
          >
            {saving ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>저장 중...</span>
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5" />
                <span>설정 변경사항 저장</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center space-x-1 sm:space-x-2 border-b border-slate-800 overflow-x-auto pb-2 scrollbar-none">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
                isActive
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-slate-400"}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {loading || !config ? (
        <div className="flex flex-col items-center justify-center py-32 space-y-4">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-400 font-medium">파이프라인 매커니즘 설정 로드 중...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* TAB 1: LLM & Runtime Engine */}
          {activeTab === "llm" && (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-5">
                <div className="border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-indigo-400" />
                    AI 주 모델 및 보조 모델(Fallback) 설정
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    학습 가이드 및 목차 생성에 사용할 기본 AI 엔진과, 장애 발생 시 자동 전환될 대체 모델을 지정합니다.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {/* Primary Model */}
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">
                      주 생성 모델 (Primary LLM)
                    </label>
                    <select
                      value={config.llm.primary_model}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          llm: { ...config.llm, primary_model: e.target.value }
                        })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
                    >
                      <option value="gemini-2.5-flash">Google Gemini 2.5 Flash (추천 - 속도/품질 최적)</option>
                      <option value="gemini-2.5-flash-lite">Google Gemini 2.5 Flash Lite (초경량 초고속)</option>
                      <option value="gemini-1.5-pro">Google Gemini 1.5 Pro (초고도 정밀 추론)</option>
                      <option value="openai/gpt-4o">OpenAI GPT-4o (고성능 표준)</option>
                      <option value="llama-3.3-70b-versatile">Groq Llama 3.3 70B (초고속 오픈소스)</option>
                      <option value="cerebras/gpt-oss-120b">Cerebras OSS 120B (초고속 웨이퍼 스케일)</option>
                    </select>
                    <p className="text-[11px] text-slate-500 mt-1">
                      💡 기본 파이프라인에서 목차 및 본문 생성에 우선 호출되는 최우선 모델입니다.
                    </p>
                  </div>

                  {/* Concurrency Semaphore */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-bold text-slate-300">
                        챕터 비동기 동시 생성 수 (Concurrency)
                      </label>
                      <span className="text-xs font-extrabold text-indigo-400">
                        {config.llm.concurrency}개 동시 생성
                      </span>
                    </div>
                    <input
                      type="range"
                      min={1}
                      max={8}
                      step={1}
                      value={config.llm.concurrency}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          llm: { ...config.llm, concurrency: parseInt(e.target.value, 10) }
                        })
                      }
                      className="w-full accent-indigo-500 cursor-pointer"
                    />
                    <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                      <span>1개 (순차/안정적)</span>
                      <span>3개 (권장 기본값)</span>
                      <span>8개 (최대 병렬)</span>
                    </div>
                  </div>

                  {/* Temperature */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-bold text-slate-300">
                        생성 온도 (Temperature: 창의성 vs 정확도)
                      </label>
                      <span className="text-xs font-extrabold text-indigo-400">
                        {config.llm.temperature}
                      </span>
                    </div>
                    <input
                      type="range"
                      min={0.0}
                      max={1.0}
                      step={0.05}
                      value={config.llm.temperature}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          llm: { ...config.llm, temperature: parseFloat(e.target.value) }
                        })
                      }
                      className="w-full accent-indigo-500 cursor-pointer"
                    />
                    <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                      <span>0.0 (완벽한 사실 기반)</span>
                      <span>0.2 (학습 가이드 권장)</span>
                      <span>1.0 (자유로운 창작)</span>
                    </div>
                  </div>

                  {/* Max Tokens */}
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">
                      최대 출력 토큰 (Max Tokens)
                    </label>
                    <input
                      type="number"
                      value={config.llm.max_tokens}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          llm: { ...config.llm, max_tokens: parseInt(e.target.value, 10) || 8192 }
                        })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                    />
                    <p className="text-[11px] text-slate-500 mt-1">
                      챕터 1개당 생성할 수 있는 최대 출력 길이입니다 (보통 8,192 토큰).
                    </p>
                  </div>

                  {/* Timeout */}
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">
                      요청 제한 시간 (Timeout Seconds)
                    </label>
                    <input
                      type="number"
                      value={config.llm.timeout_seconds}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          llm: { ...config.llm, timeout_seconds: parseInt(e.target.value, 10) || 60 }
                        })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                    />
                  </div>

                  {/* Max Retries */}
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">
                      최대 재시도 횟수 (Max Retries)
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={5}
                      value={config.llm.max_retries}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          llm: { ...config.llm, max_retries: parseInt(e.target.value, 10) || 3 }
                        })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                    />
                    <p className="text-[11px] text-slate-500 mt-1">
                      API 일시 장애나 Rate Limit 발생 시 지수 백오프로 재시도하는 횟수입니다.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Outline Mechanics */}
          {activeTab === "outline" && (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-5">
                <div className="border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Layers className="w-5 h-5 text-indigo-400" />
                    목차(Outline) 설계 및 시간 순서 제어 규칙
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    공식 유튜브 챕터 파싱 우선순위, 질문형 각색 스타일, 그리고 역순 생성 방지 가드레일을 제어합니다.
                  </p>
                </div>

                <div className="space-y-4">
                  {/* Official Chapters Toggle */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div>
                      <h4 className="text-sm font-bold text-white">
                        유튜브 공식 타임스탬프 챕터 우선 파싱
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        영상 설명란이나 메타데이터에 공식 챕터가 3개 이상 등록되어 있는 경우, 이를 최우선으로 수집하여 학습 목차로 각색합니다.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        handleConfigChange({
                          ...config,
                          outline: {
                            ...config.outline,
                            use_official_chapters: !config.outline.use_official_chapters
                          }
                        })
                      }
                      className="text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      {config.outline.use_official_chapters ? (
                        <ToggleRight className="w-8 h-8 text-indigo-500" />
                      ) : (
                        <ToggleLeft className="w-8 h-8 text-slate-600" />
                      )}
                    </button>
                  </div>

                  {/* Strict Time Sequence Toggle */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div>
                      <h4 className="text-sm font-bold text-white flex items-center gap-1.5">
                        <Clock className="w-4 h-4 text-emerald-400" />
                        시간 순서(Time Sequence) 엄격 강제
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        목차가 영상의 시작(도입)부터 끝(결론)까지 시간 흐름을 엄격하게 지키도록 강제하고, '결론'이 앞에 오거나 '도입'이 뒤로 밀리는 역순 왜곡을 원천 차단합니다.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        handleConfigChange({
                          ...config,
                          outline: {
                            ...config.outline,
                            strict_time_sequence: !config.outline.strict_time_sequence
                          }
                        })
                      }
                      className="text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      {config.outline.strict_time_sequence ? (
                        <ToggleRight className="w-8 h-8 text-indigo-500" />
                      ) : (
                        <ToggleLeft className="w-8 h-8 text-slate-600" />
                      )}
                    </button>
                  </div>

                  {/* Adaptation Style */}
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">
                      공식 챕터 각색 스타일 (Adaptation Style)
                    </label>
                    <select
                      value={config.outline.official_adaptation_style}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          outline: { ...config.outline, official_adaptation_style: e.target.value }
                        })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="curiosity_hook">지적 호기심 자극형 질문 (예: "왜 지금 세대의 스타트업은 더 거대해졌는가?")</option>
                      <option value="direct_insight">실전 인사이트 및 법칙형 (예: "비즈니스 모델의 3대 성공 공식")</option>
                      <option value="literal_korean">단백한 직역 및 핵심어 요약형 (예: "스타트업 창업자의 핵심 동기")</option>
                    </select>
                  </div>

                  {/* Min / Max Chapters */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">
                        목차 목표 최소 챕터 수
                      </label>
                      <input
                        type="number"
                        min={2}
                        max={10}
                        value={config.outline.min_chapters}
                        onChange={(e) =>
                          handleConfigChange({
                            ...config,
                            outline: { ...config.outline, min_chapters: parseInt(e.target.value, 10) || 4 }
                          })
                        }
                        className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">
                        목차 목표 최대 챕터 수
                      </label>
                      <input
                        type="number"
                        min={5}
                        max={25}
                        value={config.outline.max_chapters}
                        onChange={(e) =>
                          handleConfigChange({
                            ...config,
                            outline: { ...config.outline, max_chapters: parseInt(e.target.value, 10) || 15 }
                          })
                        }
                        className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white font-mono"
                      />
                    </div>
                  </div>

                  {/* Smart Slicing Window */}
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">
                      대용량 스크립트 스마트 슬라이싱 윈도우 (글자 수)
                    </label>
                    <input
                      type="number"
                      step={500}
                      value={config.outline.smart_slicing_window}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          outline: { ...config.outline, smart_slicing_window: parseInt(e.target.value, 10) || 4500 }
                        })
                      }
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white font-mono"
                    />
                    <p className="text-[11px] text-slate-500 mt-1">
                      12,000자 초과 긴 영상에서 각 챕터가 다루는 위치를 중심으로 앞뒤로 추출할 컨텍스트 글자 수 (기본 4,500자).
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: Narrative & Prompts */}
          {activeTab === "chapter" && (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-5">
                <div className="border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <FileText className="w-5 h-5 text-indigo-400" />
                    본문 서술 원칙 & 시스템 가드레일 정책
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    인사말 완전 배제(Zero-Greeting), 100% 한국어 번역 서술(Strict Korean Policy) 및 페르소나를 제어합니다.
                  </p>
                </div>

                <div className="space-y-4">
                  {/* Zero-Greeting Policy Toggle */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div>
                      <h4 className="text-sm font-bold text-white flex items-center gap-1.5">
                        <AlertTriangle className="w-4 h-4 text-amber-400" />
                        인사말/자기소개 영구 완전 금지 (Zero-Greeting Policy)
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        "안녕하세요", "여러분의 튜터입니다", "이번 시간에는" 등의 메타 인사말을 출력하지 못하도록 본문 서두를 즉각적인 본론 훅(Hook)으로 강제합니다.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        handleConfigChange({
                          ...config,
                          chapter: {
                            ...config.chapter,
                            zero_greeting_policy: !config.chapter.zero_greeting_policy
                          }
                        })
                      }
                      className="text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      {config.chapter.zero_greeting_policy ? (
                        <ToggleRight className="w-8 h-8 text-indigo-500" />
                      ) : (
                        <ToggleLeft className="w-8 h-8 text-slate-600" />
                      )}
                    </button>
                  </div>

                  {/* Strict Korean Policy Toggle */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div>
                      <h4 className="text-sm font-bold text-white flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        100% 자연스러운 한국어 번역 및 서술 강제 (Strict Korean Policy)
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        외국어 원본 영상이더라도 필수 기술 고유명사(Docker, API 등)를 제외한 모든 설명을 100% 유창한 한국어로 번역 및 해설하여 작성하도록 강제합니다.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        handleConfigChange({
                          ...config,
                          chapter: {
                            ...config.chapter,
                            strict_korean_policy: !config.chapter.strict_korean_policy
                          }
                        })
                      }
                      className="text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      {config.chapter.strict_korean_policy ? (
                        <ToggleRight className="w-8 h-8 text-indigo-500" />
                      ) : (
                        <ToggleLeft className="w-8 h-8 text-slate-600" />
                      )}
                    </button>
                  </div>

                  {/* Persona Role */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">
                        기본 튜터 페르소나 역할 (Role)
                      </label>
                      <input
                        type="text"
                        value={config.chapter.default_persona_role}
                        onChange={(e) =>
                          handleConfigChange({
                            ...config,
                            chapter: { ...config.chapter, default_persona_role: e.target.value }
                          })
                        }
                        className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">
                        기본 튜터 어조 (Tone)
                      </label>
                      <input
                        type="text"
                        value={config.chapter.default_persona_tone}
                        onChange={(e) =>
                          handleConfigChange({
                            ...config,
                            chapter: { ...config.chapter, default_persona_tone: e.target.value }
                          })
                        }
                        className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white"
                      />
                    </div>
                  </div>

                  {/* Focus Areas */}
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">
                      핵심 집중 영역 (Focus Areas)
                    </label>
                    <input
                      type="text"
                      value={config.chapter.default_focus_areas}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          chapter: { ...config.chapter, default_focus_areas: e.target.value }
                        })
                      }
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white"
                    />
                  </div>

                  {/* Forbidden Greeting Words list */}
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">
                      원천 차단 금지어 목록 (쉼표 구분)
                    </label>
                    <input
                      type="text"
                      value={config.chapter.forbidden_greeting_words.join(", ")}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          chapter: {
                            ...config.chapter,
                            forbidden_greeting_words: e.target.value.split(",").map((s) => s.trim()).filter(Boolean)
                          }
                        })
                      }
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white font-mono"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: Interactive Widgets */}
          {activeTab === "widgets" && (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-5">
                <div className="border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-indigo-400" />
                    4대 인터랙티브 학습 위젯 활성화 및 부착 규칙
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    본문 서술 하단에 동적으로 부착되는 학습 장치(파인만 기법, 논리 트레이서, 연상기억법, 실습 절차)를 제어합니다.
                  </p>
                </div>

                <div className="space-y-4">
                  {/* Attachment Mode */}
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">
                      챕터당 위젯 부착 방식 (Attachment Mode)
                    </label>
                    <select
                      value={config.widgets.attachment_mode}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          widgets: { ...config.widgets, attachment_mode: e.target.value }
                        })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="auto_one">AI 자동 판단: 챕터 성격에 가장 적합한 1개만 부착 (권장 기본값)</option>
                      <option value="all">모든 허용된 위젯 동시 부착</option>
                      <option value="disabled">위젯 완전 비활성화 (순수 텍스트 서술문만 생성)</option>
                    </select>
                  </div>

                  {/* 4 Widgets Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Feynman */}
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-start justify-between">
                      <div>
                        <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold">
                          CONCEPT
                        </span>
                        <h4 className="text-sm font-bold text-white mt-1.5">
                          파인만 기법 태그팀 (<code className="text-xs text-indigo-300 font-mono">&lt;feynman&gt;</code>)
                        </h4>
                        <p className="text-xs text-slate-400 mt-0.5">
                          초보자 맞춤형 비유 설명 유도 및 SOS 치트키를 제공합니다.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          handleConfigChange({
                            ...config,
                            widgets: {
                              ...config.widgets,
                              feynman_enabled: !config.widgets.feynman_enabled
                            }
                          })
                        }
                      >
                        {config.widgets.feynman_enabled ? (
                          <ToggleRight className="w-7 h-7 text-indigo-500" />
                        ) : (
                          <ToggleLeft className="w-7 h-7 text-slate-600" />
                        )}
                      </button>
                    </div>

                    {/* StepTracer */}
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-start justify-between">
                      <div>
                        <span className="px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 text-[10px] font-bold">
                          LOGIC
                        </span>
                        <h4 className="text-sm font-bold text-white mt-1.5">
                          논리 트레이서 (<code className="text-xs text-indigo-300 font-mono">&lt;steptracer&gt;</code>)
                        </h4>
                        <p className="text-xs text-slate-400 mt-0.5">
                          코드의 실행 흐름, 수학적 증명, 단계별 추론 스텝을 학습합니다.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          handleConfigChange({
                            ...config,
                            widgets: {
                              ...config.widgets,
                              steptracer_enabled: !config.widgets.steptracer_enabled
                            }
                          })
                        }
                      >
                        {config.widgets.steptracer_enabled ? (
                          <ToggleRight className="w-7 h-7 text-indigo-500" />
                        ) : (
                          <ToggleLeft className="w-7 h-7 text-slate-600" />
                        )}
                      </button>
                    </div>

                    {/* Mnemonic */}
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-start justify-between">
                      <div>
                        <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 text-[10px] font-bold">
                          MEMORY
                        </span>
                        <h4 className="text-sm font-bold text-white mt-1.5">
                          연상기억법 & 플래시카드 (<code className="text-xs text-indigo-300 font-mono">&lt;mnemonic&gt;</code>)
                        </h4>
                        <p className="text-xs text-slate-400 mt-0.5">
                          강렬한 연상 스토리와 앞/뒷면 문답 카드로 암기를 돕습니다.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          handleConfigChange({
                            ...config,
                            widgets: {
                              ...config.widgets,
                              mnemonic_enabled: !config.widgets.mnemonic_enabled
                            }
                          })
                        }
                      >
                        {config.widgets.mnemonic_enabled ? (
                          <ToggleRight className="w-7 h-7 text-indigo-500" />
                        ) : (
                          <ToggleLeft className="w-7 h-7 text-slate-600" />
                        )}
                      </button>
                    </div>

                    {/* Procedure */}
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-start justify-between">
                      <div>
                        <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] font-bold">
                          PROCEDURE
                        </span>
                        <h4 className="text-sm font-bold text-white mt-1.5">
                          절차적 체크리스트 (<code className="text-xs text-indigo-300 font-mono">&lt;procedure&gt;</code>)
                        </h4>
                        <p className="text-xs text-slate-400 mt-0.5">
                          실습 단계, 환경 구축 순서, 팁을 체크리스트로 제공합니다.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          handleConfigChange({
                            ...config,
                            widgets: {
                              ...config.widgets,
                              procedure_enabled: !config.widgets.procedure_enabled
                            }
                          })
                        }
                      >
                        {config.widgets.procedure_enabled ? (
                          <ToggleRight className="w-7 h-7 text-indigo-500" />
                        ) : (
                          <ToggleLeft className="w-7 h-7 text-slate-600" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: Quality Guardrails */}
          {activeTab === "guardrails" && (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-5">
                <div className="border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-indigo-400" />
                    품질 검증 가드레일 및 재시도 에스컬레이션 임계치
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    생성된 챕터가 통과해야 하는 최소 글자 수, 한국어 알파벳 비율 및 불합격 시 에스컬레이션 명령을 제어합니다.
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">
                        한글 절대 최소 글자 수 (기준: 250자)
                      </label>
                      <input
                        type="number"
                        min={50}
                        max={1000}
                        value={config.guardrails.min_korean_chars}
                        onChange={(e) =>
                          handleConfigChange({
                            ...config,
                            guardrails: {
                              ...config.guardrails,
                              min_korean_chars: parseInt(e.target.value, 10) || 250
                            }
                          })
                        }
                        className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white font-mono"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">
                        한글 / 영문 알파벳 비율 최소 임계치 (%)
                      </label>
                      <input
                        type="number"
                        min={10}
                        max={90}
                        value={config.guardrails.min_korean_ratio_percent}
                        onChange={(e) =>
                          handleConfigChange({
                            ...config,
                            guardrails: {
                              ...config.guardrails,
                              min_korean_ratio_percent: parseFloat(e.target.value) || 40.0
                            }
                          })
                        }
                        className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white font-mono"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">
                        상세형 최소 전체 글자 수
                      </label>
                      <input
                        type="number"
                        value={config.guardrails.min_total_chars_detailed}
                        onChange={(e) =>
                          handleConfigChange({
                            ...config,
                            guardrails: {
                              ...config.guardrails,
                              min_total_chars_detailed: parseInt(e.target.value, 10) || 1500
                            }
                          })
                        }
                        className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white font-mono"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">
                        상세형 최소 순수 서술문 글자 수
                      </label>
                      <input
                        type="number"
                        value={config.guardrails.min_narrative_chars_detailed}
                        onChange={(e) =>
                          handleConfigChange({
                            ...config,
                            guardrails: {
                              ...config.guardrails,
                              min_narrative_chars_detailed: parseInt(e.target.value, 10) || 1200
                            }
                          })
                        }
                        className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white font-mono"
                      />
                    </div>
                  </div>

                  {/* Auto Escalation Toggle */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div>
                      <h4 className="text-sm font-bold text-white">
                        품질 미달 시 자동 에스컬레이션 재시도 (Auto Escalation)
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        1회차 생성이 분량 미달이거나 태그만 누락된 경우, 긴급 시정 프롬프트를 주입하여 즉시 2회차 재시도를 트리거합니다.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        handleConfigChange({
                          ...config,
                          guardrails: {
                            ...config.guardrails,
                            enable_auto_escalation_retry: !config.guardrails.enable_auto_escalation_retry
                          }
                        })
                      }
                    >
                      {config.guardrails.enable_auto_escalation_retry ? (
                        <ToggleRight className="w-8 h-8 text-indigo-500" />
                      ) : (
                        <ToggleLeft className="w-8 h-8 text-slate-600" />
                      )}
                    </button>
                  </div>

                  {/* Escalation Prompt Editor */}
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">
                      에스컬레이션 재시도 시정 명령 프롬프트 (Escalation Prompt)
                    </label>
                    <textarea
                      rows={3}
                      value={config.guardrails.escalation_prompt}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          guardrails: { ...config.guardrails, escalation_prompt: e.target.value }
                        })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: Data Sources & Transcripts */}
          {activeTab === "sources" && (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-5">
                <div className="border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Database className="w-5 h-5 text-indigo-400" />
                    자막 수집 및 오디오 전사 파이프라인 제어
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    공식 자막, yt-dlp, Whisper ASR 우선순위 및 웹 스크랩 정제 필터를 제어합니다.
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">
                      Whisper 음성 전사 모델 사이즈 (Fallback ASR)
                    </label>
                    <select
                      value={config.sources.whisper_model_size}
                      onChange={(e) =>
                        handleConfigChange({
                          ...config,
                          sources: { ...config.sources, whisper_model_size: e.target.value }
                        })
                      }
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="tiny">tiny (초고속 저용량 - 약 75MB)</option>
                      <option value="base">base (표준 권장 - 약 145MB)</option>
                      <option value="small">small (정밀 음성 인식 - 약 480MB)</option>
                      <option value="medium">medium (고성능 학술 전사 - 약 1.5GB)</option>
                    </select>
                  </div>

                  {/* Clean Jina noise */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div>
                      <h4 className="text-sm font-bold text-white">
                        Jina Reader 웹 스크랩 UI 잡음 정제 필터
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        웹페이지 텍스트에서 'NaN/NaN', '조회수', 추천 영상 UI 잡음을 정규식으로 자동 제거합니다.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        handleConfigChange({
                          ...config,
                          sources: {
                            ...config.sources,
                            clean_jina_scraped_noise: !config.sources.clean_jina_scraped_noise
                          }
                        })
                      }
                    >
                      {config.sources.clean_jina_scraped_noise ? (
                        <ToggleRight className="w-8 h-8 text-indigo-500" />
                      ) : (
                        <ToggleLeft className="w-8 h-8 text-slate-600" />
                      )}
                    </button>
                  </div>

                  {/* Gemini Context Caching */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div>
                      <h4 className="text-sm font-bold text-white">
                        Gemini Context Caching 토큰 절감 기술
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        대용량 스크립트를 Gemini File API에 업로드하여 캐싱함으로써 토큰 비용을 최대 75% 절감합니다.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        handleConfigChange({
                          ...config,
                          sources: {
                            ...config.sources,
                            enable_gemini_context_caching: !config.sources.enable_gemini_context_caching
                          }
                        })
                      }
                    >
                      {config.sources.enable_gemini_context_caching ? (
                        <ToggleRight className="w-8 h-8 text-indigo-500" />
                      ) : (
                        <ToggleLeft className="w-8 h-8 text-slate-600" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: Live Simulation Playground */}
          {activeTab === "playground" && (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-5">
                <div className="border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Play className="w-5 h-5 text-indigo-400" />
                    실시간 생성 매커니즘 샌드박스 (Simulation Playground)
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    현재 화면에 설정된 파라미터(또는 임시 수정치)를 바탕으로 실제 목차 추출 또는 단일 챕터 생성을 즉석에서 실행하고 품질을 검증합니다.
                  </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                  {/* Left: Input Sandbox Form */}
                  <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={() => setSimType("outline")}
                        className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all ${
                          simType === "outline"
                            ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                            : "bg-slate-950 text-slate-400 border border-slate-800 hover:text-white"
                        }`}
                      >
                        1. 목차 추출 시뮬레이션
                      </button>
                      <button
                        type="button"
                        onClick={() => setSimType("chapter")}
                        className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all ${
                          simType === "chapter"
                            ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                            : "bg-slate-950 text-slate-400 border border-slate-800 hover:text-white"
                        }`}
                      >
                        2. 챕터 1개 생성 시뮬레이션
                      </button>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1.5">
                        시뮬레이션 대상 주제 / 영상 제목
                      </label>
                      <input
                        type="text"
                        value={simTitle}
                        onChange={(e) => setSimTitle(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white"
                      />
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-bold text-slate-300">
                          테스트 입력 스크립트 샘플
                        </label>
                        <span className="text-[11px] text-slate-500">
                          {simText.length}자
                        </span>
                      </div>
                      <textarea
                        rows={6}
                        value={simText}
                        onChange={(e) => setSimText(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="테스트할 스크립트 텍스트를 입력하세요..."
                      />
                    </div>

                    <button
                      type="button"
                      onClick={handleRunSimulation}
                      disabled={simRunning || !simText.trim()}
                      className="w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {simRunning ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>파이프라인 시뮬레이션 실행 중...</span>
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4" />
                          <span>시뮬레이션 실행하기</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Right: Output Result Preview */}
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col h-full min-h-[350px]">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white">시뮬레이션 결과 리포트</span>
                        {simResult?.status === "success" && (
                          <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold">
                            완료 ({simResult.elapsed_seconds}초)
                          </span>
                        )}
                      </div>
                      {simResult?.used_provider && (
                        <span className="text-[11px] text-slate-400 font-mono">
                          {simResult.used_provider}
                        </span>
                      )}
                    </div>

                    <div className="flex-1 overflow-y-auto max-h-[420px] pr-1 scrollbar-thin">
                      {!simResult ? (
                        <div className="flex flex-col items-center justify-center h-full text-center py-16 text-slate-500">
                          <Play className="w-8 h-8 mb-2 opacity-30" />
                          <p className="text-xs">
                            좌측에서 스크립트를 입력하고 [시뮬레이션 실행하기]를 누르면 실시간 결과가 이곳에 표시됩니다.
                          </p>
                        </div>
                      ) : simResult.status === "error" ? (
                        <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-900/50 text-rose-300 text-xs">
                          <p className="font-bold flex items-center gap-1.5">
                            <AlertCircle className="w-4 h-4 text-rose-400" />
                            시뮬레이션 에러
                          </p>
                          <p className="mt-1 font-mono text-[11px]">{simResult.message}</p>
                        </div>
                      ) : simResult.test_type === "outline" ? (
                        <div className="space-y-3">
                          <p className="text-xs font-semibold text-slate-300">
                            추출된 목차 ({simResult.sections_count}개):
                          </p>
                          <div className="space-y-1.5">
                            {simResult.sections?.map((sec: string, idx: number) => (
                              <div
                                key={idx}
                                className="flex items-center gap-2.5 p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white"
                              >
                                <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-300 flex items-center justify-center text-[10px] font-bold">
                                  {idx + 1}
                                </span>
                                <span className="font-medium">{sec}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {/* Guardrails Check */}
                          <div
                            className={`p-3 rounded-xl border flex items-center justify-between text-xs ${
                              simResult.is_valid
                                ? "bg-emerald-950/20 border-emerald-500/30 text-emerald-300"
                                : "bg-amber-950/20 border-amber-500/30 text-amber-300"
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              {simResult.is_valid ? (
                                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                              ) : (
                                <AlertTriangle className="w-4 h-4 text-amber-400" />
                              )}
                              <span className="font-bold">
                                {simResult.is_valid ? "가드레일 통과" : "가드레일 미달 (재시도 대상)"}
                              </span>
                            </div>
                            <span className="font-mono text-[11px]">
                              {simResult.total_chars}자 생성됨
                            </span>
                          </div>

                          {/* Markdown Preview */}
                          <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed">
                            {simResult.content}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
