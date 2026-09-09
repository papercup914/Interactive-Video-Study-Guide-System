export const LENGTH_PRESETS = ["핵심 요약", "적당한 설명", "아주 상세하게"] as const;
export type LengthPreset = typeof LENGTH_PRESETS[number];

export const ANALOGY_PRESETS = ["비유 없이 담백하게", "적절한 비유 추가", "풍부한 비유"] as const;
export type AnalogyPreset = typeof ANALOGY_PRESETS[number];

export function normalizeLength(val?: string): LengthPreset {
  if (!val) return "적당한 설명";
  const v = val.trim().toLowerCase();
  if (v.includes("핵심") || v.includes("basic") || v.includes("short") || v.includes("summary") || v.includes("quick")) {
    return "핵심 요약";
  }
  if (v.includes("상세") || v.includes("deep") || v.includes("detailed") || v.includes("long")) {
    return "아주 상세하게";
  }
  return "적당한 설명";
}

export function normalizeAnalogy(val?: string): AnalogyPreset {
  if (!val) return "적절한 비유 추가";
  const v = val.trim().toLowerCase();
  if (v.includes("담백") || v.includes("academic") || v.includes("none") || v.includes("plain")) {
    return "비유 없이 담백하게";
  }
  if (v.includes("풍부") || v.includes("story") || v.includes("rich") || v.includes("feynman")) {
    return "풍부한 비유";
  }
  return "적절한 비유 추가";
}

export function extractVideoKey(url?: string, title?: string): string {
  if (!url) return (title || "unknown").trim().toLowerCase();
  const ytMatch = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^&?]+)/);
  if (ytMatch && ytMatch[1]) {
    return `yt_${ytMatch[1]}`;
  }
  return url.trim().toLowerCase();
}
