import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

class StartupErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('Frontend render error:', error, info);
  }

  render() {
    if (this.state.error) {
      return <div style={{ maxWidth: 720, margin: '80px auto', padding: 32, fontFamily: 'Arial, sans-serif', color: '#17233d' }}>
        <h1>AI Text Summarizer</h1>
        <p>The interface could not render. Restart Vite and reload the page.</p>
        <pre style={{ whiteSpace: 'pre-wrap', color: '#a33' }}>{String(this.state.error)}</pre>
      </div>;
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><StartupErrorBoundary><App /></StartupErrorBoundary></React.StrictMode>,
);
