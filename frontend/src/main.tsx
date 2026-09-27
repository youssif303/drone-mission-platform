import React, { Component, ErrorInfo, ReactNode } from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './styles/globals.css';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '30px', color: '#f87171', backgroundColor: '#0a0f1a', minHeight: '100vh', fontFamily: 'monospace' }}>
          <h2 style={{ fontSize: '20px', color: '#ef4444' }}>⚠️ Application Render Error Caught</h2>
          <p style={{ color: '#cbd5e1' }}>{this.state.error?.message}</p>
          <pre style={{ backgroundColor: '#1e293b', padding: '15px', borderRadius: '6px', overflow: 'auto', color: '#94a3b8' }}>
            {this.state.error?.stack}
          </pre>
          <button 
            onClick={() => window.location.reload()} 
            style={{ marginTop: '20px', padding: '8px 16px', backgroundColor: '#10b981', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            Reload Dashboard
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
