"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
  chapterTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`[ErrorBoundary] Caught error in chapter: ${this.props.chapterTitle}`, error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-xl my-4">
          <h3 className="text-red-400 font-bold mb-2">
            ⚠️ 해당 챕터({this.props.chapterTitle || '내용'})를 렌더링하는 중 문제가 발생했습니다.
          </h3>
          <p className="text-sm text-red-300/80">
            문맥 데이터가 손상되었거나 예상치 못한 형식입니다. 다른 챕터는 정상적으로 이용 가능합니다.
          </p>
          <button 
            onClick={() => this.setState({ hasError: false })}
            className="mt-3 px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded text-sm transition-colors"
          >
            다시 시도
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
