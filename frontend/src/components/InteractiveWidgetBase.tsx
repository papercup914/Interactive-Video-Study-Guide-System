import React from 'react';

/**
 * React 노드 트리에서 순수 텍스트를 재귀적으로 추출합니다.
 */
export function extractTextFromReactNode(node: React.ReactNode): string {
  if (!node) return '';
  if (typeof node === 'string') return node;
  if (typeof node === 'number') return String(node);
  if (Array.isArray(node)) return node.map(extractTextFromReactNode).join('');
  if (React.isValidElement(node)) {
    const props = node.props as { children?: React.ReactNode };
    if (props && props.children) {
      return extractTextFromReactNode(props.children);
    }
  }
  return '';
}

/**
 * 마크다운 코드블록 등으로 감싸진 raw JSON 문자열을 정제하고 파싱합니다.
 */
export function parseInteractiveWidgetJson<T>(rawChildren: React.ReactNode): { data: T | null; error: string | null } {
  const rawText = extractTextFromReactNode(rawChildren).trim();
  if (!rawText) {
    return { data: null, error: "빈 데이터입니다." };
  }
  const cleanJson = rawText
    .replace(/```[\w-]*\n?/g, '')
    .replace(/```/g, '')
    .replace(/`/g, '')
    .replace(/,\s*([\]}])/g, '$1')
    .trim();

  try {
    const parsed = JSON.parse(cleanJson);
    return { data: parsed as T, error: null };
  } catch (e) {
    return { data: null, error: e instanceof Error ? e.message : String(e) };
  }
}

interface InteractiveWidgetBaseProps<T> {
  children?: React.ReactNode;
  fallbackName?: string;
  render: (data: T) => React.ReactNode;
  validate?: (data: T) => boolean;
}

/**
 * 인터랙티브 위젯들의 공통 JSON 파싱, 정규화, 에러 바운더리 폴백을 처리하는 공통 베이스 컴포넌트입니다.
 */
export function InteractiveWidgetBase<T>({
  children,
  fallbackName = "인터랙티브 학습 요소",
  render,
  validate
}: InteractiveWidgetBaseProps<T>) {
  const { data, error } = parseInteractiveWidgetJson<T>(children);

  if (error || !data || (validate && !validate(data))) {
    return (
      <div className="p-4 bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-xl my-4 text-sm font-bold border border-amber-500/20 flex items-center gap-2">
        <span>⚠️</span>
        <span>AI가 생성한 {fallbackName}을(를) 불러올 수 없습니다. (형식 오류)</span>
      </div>
    );
  }

  return <>{render(data)}</>;
}
