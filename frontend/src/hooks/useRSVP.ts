import { useState, useEffect, useCallback, useMemo } from 'react';

export function useRSVP(text: string, initialWpm: number = 350) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [wpm, setWpm] = useState(initialWpm);
  
  // Basic tokenization: split by spaces, but also handle some punctuation
  const words = useMemo(() => {
    if (!text) return [];
    return text
      // Remove markdown formatting characters
      .replace(/[#*`_~]/g, '')
      .split(/\s+/)
      .filter(w => w.length > 0);
  }, [text]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying && currentWordIndex < words.length) {
      // Calculate delay with slight pause for punctuation
      let delay = 60000 / wpm;
      const currentWord = words[currentWordIndex];
      if (currentWord && /[.!?]$/.test(currentWord)) {
        delay *= 1.5; // Pause slightly longer at end of sentences
      } else if (currentWord && /[,;]$/.test(currentWord)) {
        delay *= 1.2; // Pause slightly longer at commas
      }

      interval = setTimeout(() => {
        setCurrentWordIndex(prev => {
          if (prev >= words.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, delay);
    }
    return () => clearTimeout(interval);
  }, [isPlaying, currentWordIndex, words, wpm]);

  const toggle = useCallback(() => {
    if (currentWordIndex >= words.length - 1) {
      setCurrentWordIndex(0);
    }
    setIsPlaying(p => !p);
  }, [currentWordIndex, words.length]);
  
  const reset = useCallback(() => { 
    setIsPlaying(false); 
    setCurrentWordIndex(0); 
  }, []);

  const seek = useCallback((progress: number) => {
    const newIdx = Math.floor(progress * (words.length - 1));
    setCurrentWordIndex(Math.max(0, Math.min(newIdx, words.length - 1)));
  }, [words.length]);

  // Center alignment logic for RSVP
  const getAlignedWord = (word: string) => {
    if (!word) return { left: '', pivot: '', right: '' };
    // Usually pivot is slightly left of center
    const pivotIndex = Math.floor((word.length - 1) / 2);
    return {
      left: word.substring(0, pivotIndex),
      pivot: word[pivotIndex],
      right: word.substring(pivotIndex + 1)
    };
  };

  const currentWord = words[currentWordIndex] || "";
  const aligned = getAlignedWord(currentWord);

  return { 
    isPlaying, 
    toggle, 
    reset, 
    seek,
    currentWord, 
    aligned,
    wpm,
    setWpm,
    progress: words.length > 0 ? currentWordIndex / (words.length - 1) : 0,
    totalWords: words.length
  };
}
