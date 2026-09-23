import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
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
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-slate-950 p-4 text-slate-100">
          <div className="w-full max-w-md rounded-2xl border border-rose-500/30 bg-slate-900/90 p-8 shadow-2xl">
            <h1 className="mb-4 text-2xl font-bold text-rose-500">Something went wrong.</h1>
            <p className="mb-6 text-sm text-slate-400">
              An unexpected error occurred in the application. Please refresh the page or try again later.
            </p>
            {this.state.error && (
              <pre className="mb-6 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-rose-400">
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={() => window.location.reload()}
              className="w-full rounded-xl bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-rose-500"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
