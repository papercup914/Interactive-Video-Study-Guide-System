export type Note = {
  id: string;
  section: string;
  selected_text: string;
  question: string;
  answer: string;
};

// 정규식 상수 사전 컴파일
const GREETING_REGEX_1 = /^\s*(?:\*\*)?(?:안녕하세요|반갑습니다|환영합니다)[\s\S]*?(?:입니다|멘토입니다|튜터입니다|가이드입니다|파트너입니다)[.!\n]+(?:\*\*)?\s*/i;
const GREETING_REGEX_2 = /^\s*(?:\*\*)?(?:이번\s*(?:챕터|시간|강의|가이드)에서는?|오늘(?:\s*우리가)?\s*(?:함께)?\s*(?:살펴볼|알아볼|파헤쳐\s*볼|배워볼))[\s\S]*?(?:알아보겠습니다|살펴보겠습니다|배워보겠습니다|시작하겠습니다|파헤쳐\s*보겠습니다|짚어보겠습니다|함께\s*가보시죠|하겠습니다|합니다|입니다)[.!\n]+(?:\*\*)?\s*/i;
const GREETING_REGEX_3 = /^\s*(?:\*\*)?(?:안녕하세요|반갑습니다|환영합니다)[^\n]*?(?:\*\*)?\n+/i;

const TAGS_TO_PROCESS = ['quiz', 'feynman', 'steptracer', 'mnemonic', 'procedure'] as const;

/**
 * 마크다운 텍스트에서 불필요한 메타 태그, 인사말을 정제하고 인터랙티브 위젯 태그를 정규화합니다.
 */
export function cleanAndNormalizeMarkdown(sectionName: string, text: string): string {
  if (!text) return "";
  let processed = text;

  // 0-1. 파트 1/2 메타 텍스트 전역 제거
  processed = processed.replace(/#{0,4}\s*\[?\s*파트\s*[12]\s*:[^\]\n]*\]?\s*\n*/gi, '');

  // 0-2. 본문 서두 챕터 제목 중복 줄 제거
  if (sectionName) {
    const escaped = sectionName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    processed = processed.trim().replace(new RegExp(`^\\s*(?:#{1,4}\\s*)?(?:\\d+\\.\\s*)?${escaped}\\s*\\n+`, 'i'), '');
  }

  // 첫 줄이 제목 형태인 경우 보존하며 두 번째 줄 이하의 인사말 블록 제거
  const lines = processed.trim().split('\n');
  if (lines.length > 1 && (lines[0].startsWith('#') || (lines[0].trim().length < 80 && !lines[0].trim().endsWith('.')))) {
    const firstLine = lines[0];
    let rest = lines.slice(1).join('\n').trim();
    rest = rest.replace(GREETING_REGEX_1, '');
    rest = rest.replace(GREETING_REGEX_2, '');
    rest = rest.replace(GREETING_REGEX_3, '');
    processed = `${firstLine}\n\n${rest}`;
  }

  // 최상단 직격 인사말 제거
  processed = processed.trim().replace(GREETING_REGEX_1, '');
  processed = processed.trim().replace(GREETING_REGEX_2, '');
  processed = processed.trim().replace(GREETING_REGEX_3, '');

  // Fix CommonMark parsing bug with Korean particles attached to markdown markers.
  processed = processed.replace(/(\*\*|__|\*|_)(?=[가-힣])/g, '$1<!-- -->');
  
  // Normalize hyphenated/underscored custom tag names (e.g. <step_tracer>, <step-tracer> -> <steptracer>)
  processed = processed.replace(/<\s*(\/?)\s*(?:step[-_]tracer|steptracer)\b([^>]*)>/gi, '<$1steptracer$2>');
  
  // Unwrap markdown code fences wrapping custom tags
  processed = processed.replace(/```[\w-]*\s*\n?\s*(<(?:quiz|feynman|steptracer|mnemonic|procedure|discussion)[\s\S]*?<\/(?:quiz|feynman|steptracer|mnemonic|procedure|discussion)>)\s*(?:```)?/gi, '$1');
  
  TAGS_TO_PROCESS.forEach(tag => {
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

  // AI나 파서가 임의로 생성한 <mark> 태그 제거
  processed = processed.replace(/<\/?mark[^>]*>/gi, '');

  return processed;
}

/**
 * 정제된 마크다운 텍스트에 사용자 하이라이트 및 노트 태그를 주입합니다.
 */
export function injectNotes(cleanedMarkdown: string, sectionName: string, notes: Note[]): string {
  if (!cleanedMarkdown) return "";
  let processed = cleanedMarkdown;
  const sectionNotes = (notes || []).filter(n => n && n.section === sectionName);
  
  sectionNotes.forEach(note => {
    if (!note.selected_text) return;
    const escaped = note.selected_text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(\\*\\*|__|\\*|_)?(${escaped})(\\*\\*|__|\\*|_)?`, 'g');
    
    processed = processed.replace(regex, (match, p1, p2, p3) => {
      if (p1 && p3 && p1 === p3) {
        return `<mark id="${note.id}" class="bg-foreground text-background rounded px-1 cursor-pointer transition-colors shadow-sm " title="노트 보기">${p1}${p2}${p3}</mark>`;
      }
      return `${p1 || ''}<mark id="${note.id}" class="bg-foreground text-background rounded px-1 cursor-pointer transition-colors shadow-sm " title="노트 보기">${p2}</mark>${p3 || ''}`;
    });
  });

  return processed;
}

// 마크다운 정제 결과 메모이제이션 캐시 (최대 200개 챕터 보존)
const markdownCleanCache = new Map<string, string>();
const MAX_CACHE_SIZE = 200;

/**
 * 정규화 캐시를 활용하여 마크다운을 정제하고 노트를 주입합니다.
 */
export function processMarkdownWithNotes(sectionName: string, text: string, notes: Note[]): string {
  if (!text) return "";
  const cacheKey = `${sectionName}::${text.length}::${text.slice(0, 40)}::${text.slice(-40)}`;
  let cleaned = markdownCleanCache.get(cacheKey);
  if (!cleaned) {
    cleaned = cleanAndNormalizeMarkdown(sectionName, text);
    if (markdownCleanCache.size >= MAX_CACHE_SIZE) {
      const firstKey = markdownCleanCache.keys().next().value;
      if (firstKey) markdownCleanCache.delete(firstKey);
    }
    markdownCleanCache.set(cacheKey, cleaned);
  }
  return injectNotes(cleaned, sectionName, notes);
}

