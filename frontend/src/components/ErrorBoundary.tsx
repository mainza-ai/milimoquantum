import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center h-full p-8 text-center">
          <div className="w-16 h-16 mb-4 rounded-full bg-red-500/10 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-white mb-2">Something went wrong</h3>
          <p className="text-sm text-gray-400 mb-4 max-w-md">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm text-white transition-colors"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export class ExtensionErrorBoundary extends Component<{
  children: ReactNode;
  extensionName: string;
  extensionId: string;
}> {
  render() {
    return (
      <ErrorBoundary
        fallback={
          <div className="flex flex-col items-center justify-center h-full p-8">
            <div className="w-12 h-12 mb-3 rounded-full bg-red-500/10 flex items-center justify-center">
              <span className="text-2xl">⚠️</span>
            </div>
            <h3 className="text-sm font-medium text-white mb-1">
              {this.props.extensionName} Error
            </h3>
            <p className="text-xs text-gray-500 mb-3">
              This extension encountered an error and couldn't load.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded text-xs text-gray-400 transition-colors"
            >
              Reload Page
            </button>
          </div>
        }
      >
        {this.props.children}
      </ErrorBoundary>
    );
  }
}

export class QuantumExecutionErrorBoundary extends Component<{
  children: ReactNode;
}> {
  render() {
    return (
      <ErrorBoundary
        fallback={
          <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-red-400">⚛️</span>
              <span className="text-sm font-medium text-red-400">
                Quantum Execution Error
              </span>
            </div>
            <p className="text-xs text-gray-400">
              The quantum circuit execution failed. This could be due to invalid
              circuit parameters or backend unavailability.
            </p>
          </div>
        }
      >
        {this.props.children}
      </ErrorBoundary>
    );
  }
}
