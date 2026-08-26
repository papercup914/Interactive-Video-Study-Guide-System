export type ThemeInfo = {
  id: string;
  name: string;
  primaryColor: string; // Tailwind bg color class
  lightBgColor: string; // Tailwind bg color class (very light)
  textColor: string; // Tailwind text color class
  gradient: string; // Tailwind gradient class
};

export const THEMES: ThemeInfo[] = [
  { id: "lavender", name: "라벤더", primaryColor: "bg-indigo-300", lightBgColor: "bg-indigo-50", textColor: "text-indigo-900", gradient: "from-indigo-200 to-purple-200" },
  { id: "peach", name: "피치", primaryColor: "bg-rose-300", lightBgColor: "bg-rose-50", textColor: "text-rose-900", gradient: "from-rose-200 to-pink-200" },
  { id: "mint", name: "민트", primaryColor: "bg-teal-300", lightBgColor: "bg-teal-50", textColor: "text-teal-900", gradient: "from-teal-200 to-emerald-200" },
  { id: "sky", name: "스카이", primaryColor: "bg-sky-300", lightBgColor: "bg-sky-50", textColor: "text-sky-900", gradient: "from-sky-200 to-blue-200" },
  { id: "butter", name: "버터", primaryColor: "bg-amber-300", lightBgColor: "bg-amber-50", textColor: "text-amber-900", gradient: "from-amber-200 to-yellow-200" },
];

export const PATTERNS = [
  // CSS patterns using background-image radial-gradient or linear-gradient
  "bg-[radial-gradient(#fff_2px,transparent_2px)] [background-size:16px_16px]", // Polka dots
  "bg-[linear-gradient(45deg,#fff_25%,transparent_25%,transparent_75%,#fff_75%,#fff),linear-gradient(45deg,#fff_25%,transparent_25%,transparent_75%,#fff_75%,#fff)] [background-size:20px_20px] [background-position:0_0,10px_10px]", // Checkered
  "bg-[repeating-linear-gradient(45deg,transparent,transparent_10px,#fff_10px,#fff_12px)]", // Diagonal lines
  "bg-[radial-gradient(circle_at_center,transparent_0%,transparent_50%,#fff_50%,#fff_100%)] [background-size:24px_24px]", // Circles
  "", // Just smooth gradient
];

export function getThemeForId(id: string): { theme: ThemeInfo, pattern: string, emoji: string } {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = ((hash << 5) - hash) + id.charCodeAt(i);
    hash |= 0; 
  }
  
  const absHash = Math.abs(hash);
  const theme = THEMES[absHash % THEMES.length];
  const pattern = PATTERNS[(absHash >> 2) % PATTERNS.length];
  
  // Pick a random study-related cute emoji deterministically
  const emojis = ["🚀", "💡", "🎯", "🧠", "✨", "🌟", "📚", "📝", "🎓", "🎨", "🧩", "🌱"];
  const emoji = emojis[(absHash >> 4) % emojis.length];

  return { theme, pattern, emoji };
}
