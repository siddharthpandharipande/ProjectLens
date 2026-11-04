import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackTitle?: string;
  sectionName?: string;
  onReset?: () => void;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error(
        `[ProjectLens ErrorBoundary] Caught error in ${this.props.sectionName || 'component'}:`,
        error,
        errorInfo
      );
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.handleReset);
      }

      const section = this.props.sectionName || 'This section';
      const title = this.props.fallbackTitle || `${section} encountered a rendering issue`;
      const rawMessage = this.state.error.message || 'An unexpected error occurred during rendering.';
      // Sanitize: ensure no potential API keys or tokens are leaked in UI
      const sanitizedMessage = rawMessage.replace(/sk-[a-zA-Z0-9_-]{20,}/g, '[REDACTED_KEY]');

      return (
        <div
          className="bg-white border-[2.5px] border-[#121212] p-6 flex flex-col gap-4 my-4"
          style={{ boxShadow: '4px 4px 0px #121212' }}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div
                className="w-10 h-10 bg-[#FF5C8D] border-2 border-[#121212] flex items-center justify-center shrink-0 mt-0.5"
                style={{ boxShadow: '2px 2px 0px #121212' }}
              >
                <AlertTriangle size={20} className="text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-[10px] font-bold bg-[#FFE600] border border-[#121212] px-2 py-0.5 uppercase">
                    Error Caught
                  </span>
                  <span className="font-mono text-[10px] text-[#4b4731]">
                    {this.props.sectionName || 'Component'}
                  </span>
                </div>
                <h3 className="font-display font-bold text-lg text-[#1c1b1b] mt-1">
                  {title}
                </h3>
                <p className="font-sans text-xs text-[#4b4731] mt-0.5">
                  A component error occurred while rendering this view. Your other tabs and project data remain unaffected.
                </p>
              </div>
            </div>

            <button
              onClick={this.handleReset}
              className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5 cursor-pointer shrink-0"
            >
              <RefreshCw size={13} />
              Retry View
            </button>
          </div>

          <div className="bg-[#FAF6EE] border border-[#121212] p-3 text-xs font-mono text-[#1c1b1b] overflow-x-auto">
            <span className="text-[10px] uppercase font-bold text-[#b43b5b] block mb-1">
              Error Details:
            </span>
            {sanitizedMessage}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

