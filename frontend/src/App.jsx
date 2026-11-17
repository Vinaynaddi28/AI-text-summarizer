import React, { useEffect, useState } from 'react';
import { clearHistory, deleteHistoryItem, extractPdf, getHistory, getHistoryItem, summarizeText } from './services/api.js';

function countWords(value) {
  const trimmed = value.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}

function App() {
  const [text, setText] = useState('');
  const [length, setLength] = useState('Medium');
  const [provider, setProvider] = useState('Google Gemini');
  const [summary, setSummary] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState('');
  const [extracting, setExtracting] = useState(false);
  const [pdfWarnings, setPdfWarnings] = useState([]);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyBusy, setHistoryBusy] = useState(false);
  const [historyMessage, setHistoryMessage] = useState('');

  async function refreshHistory() {
    try {
      setHistory(await getHistory());
      setHistoryMessage('');
    } catch (error) {
      setHistoryMessage(error.message || 'Could not load history.');
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => { refreshHistory(); }, []);

  async function handleRestore(id) {
    setHistoryBusy(true);
    try {
      const item = await getHistoryItem(id);
      setText(item.original_text);
      setSummary(item.summary_text);
      setLength(item.summary_length.charAt(0).toUpperCase() + item.summary_length.slice(1).toLowerCase());
      setProvider(item.provider === 'ollama' ? 'Ollama' : 'Google Gemini');
      setFileName('');
      setPdfWarnings([]);
      setMessage('Previous summary restored.');
      setHistoryMessage('');
      window.location.hash = 'top';
    } catch (error) {
      setHistoryMessage(error.message || 'Could not restore this summary.');
    } finally {
      setHistoryBusy(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Delete this summary from history?')) return;
    setHistoryBusy(true);
    try {
      await deleteHistoryItem(id);
      await refreshHistory();
    } catch (error) {
      setHistoryMessage(error.message || 'Could not delete this summary.');
    } finally {
      setHistoryBusy(false);
    }
  }

  async function handleClear() {
    if (!window.confirm('Clear all summary history? This cannot be undone.')) return;
    setHistoryBusy(true);
    try {
      await clearHistory();
      await refreshHistory();
    } catch (error) {
      setHistoryMessage(error.message || 'Could not clear history.');
    } finally {
      setHistoryBusy(false);
    }
  }

  async function handlePdf(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setExtracting(true);
    setPdfWarnings([]);
    setMessage('Extracting text from PDF…');
    try {
      const result = await extractPdf(file);
      setFileName(file.name);
      setText(result.extracted_text);
      setSummary('');
      const method = { direct: 'direct extraction', text: 'direct extraction', ocr: 'OCR', mixed: 'mixed extraction and OCR' }[result.extraction_method] || result.extraction_method;
      setPdfWarnings(result.warnings || []);
      setMessage(`Extracted ${result.word_count} words from ${result.page_count} pages using ${method} (${result.ocr_page_count} OCR pages). Review the text before summarizing.`);
    } catch (error) {
      setMessage(error.message || 'Could not extract PDF text.');
    } finally {
      setExtracting(false);
      event.target.value = '';
    }
  }

  async function handleGenerate(event) {
    event.preventDefault();
    if (!text.trim()) {
      setMessage('Please enter some text to summarize.');
      return;
    }
    setLoading(true);
    setSummary('');
    setMessage(`Generating summary with ${provider}…`);
    try {
      const result = await summarizeText(text, length, provider === 'Ollama' ? 'ollama' : 'gemini');
      setSummary(result.summary);
      setMessage(`Summary generated with ${provider}.`);
      await refreshHistory();
    } catch (error) {
      setMessage(error.message || 'Could not generate the summary.');
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(summary);
      setMessage('Summary copied to clipboard.');
    } catch {
      setMessage('Could not copy the summary. Please check your browser permissions.');
    }
  }

  function handleDownload() {
    const url = URL.createObjectURL(new Blob([summary], { type: 'text/plain;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    const now = new Date();
    const date = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    link.download = `summary-${date}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function handleShare() {
    if (navigator.share) {
      try {
        await navigator.share({ title: 'AI Text Summarizer', text: summary });
        setMessage('Summary shared.');
        return;
      } catch (error) {
        if (error.name === 'AbortError') return;
      }
    }
    try {
      await navigator.clipboard.writeText(summary);
      setMessage('Sharing is unavailable, so the summary was copied to your clipboard.');
    } catch {
      setMessage('Sharing is unavailable. Please select and copy the summary manually.');
    }
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="header-inner">
          <a className="brand" href="#top" aria-label="AI Text Summarizer home"><span className="brand-mark" aria-hidden="true">✦</span><span>AI Text Summarizer</span></a>
          <a className="nav-link" href="#history">History <span aria-hidden="true">↗</span></a>
        </div>
      </header>

      <main id="top" className="container">
        <section className="intro">
          <div className="eyebrow"><span className="eyebrow-dot" /> YOUR READING COMPANION</div>
          <h1>Make more of <span>what you read.</span></h1>
          <p>Summarize lengthy content using Generative AI</p>
        </section>

        <form onSubmit={handleGenerate}>
          <div className="workspace">
            <section className="card input-card" aria-labelledby="input-title">
              <div className="card-heading"><div><div className="section-kicker">YOUR CONTENT</div><h2 id="input-title">Original text</h2></div><span className="step">01</span></div>
              <p className="card-description">Paste an article, essay, or document to get started.</p>
              <label className="sr-only" htmlFor="source-text">Text to summarize</label>
              <textarea id="source-text" disabled={loading || extracting} value={text} onChange={(event) => { setText(event.target.value); setSummary(''); setMessage(''); }} placeholder="Paste your text here..." />
              <div className="input-meta"><span><strong>{countWords(text)}</strong> words</span><span>Plain text</span></div>
              <div className="upload-row">
                <div className="upload-icon" aria-hidden="true">↑</div>
                <div className="upload-copy"><strong>Have a PDF?</strong><span>{extracting ? 'Extracting text (OCR may take time)…' : fileName || 'Choose a PDF'}</span></div>
                <label className="upload-button" htmlFor="pdf-file">Choose PDF</label>
                <input className="sr-only" id="pdf-file" type="file" accept=".pdf,application/pdf" disabled={extracting || loading} onChange={handlePdf} />
              </div>
              <p className="hint">Scanned pages use local OCR. Review extracted text for accuracy, especially with low-quality scans.</p>
              {pdfWarnings.length > 0 && <div role="status" className="hint"><strong>Some pages may need review:</strong><ul>{pdfWarnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></div>}
            </section>

            <section className="card output-card" aria-labelledby="output-title">
              <div className="card-heading"><div><div className="section-kicker">THE SHORT VERSION</div><h2 id="output-title">Your summary</h2></div><span className="step">02</span></div>
              <p className="card-description">The key ideas, ready when you are.</p>
              <div className={`summary-content ${summary ? 'has-summary' : ''}`} aria-live="polite">
                {loading ? <div className="empty-state"><span className="spinner" />Generating summary...</div> : summary ? <p>{summary}</p> : <div className="empty-state"><div className="empty-icon" aria-hidden="true">✦</div><strong>Your summary will appear here</strong><span>Add your text and choose your preferences to get started.</span></div>}
              </div>
              <div className="output-bottom"><span><strong>{countWords(summary)}</strong> words</span><div className="output-actions"><button type="button" className="text-button" disabled={!summary} onClick={handleCopy}>Copy</button><button type="button" className="text-button" disabled={!summary} onClick={handleDownload}>Download</button><button type="button" className="text-button" disabled={!summary} onClick={handleShare}>Share</button></div></div>
            </section>
          </div>

          <section className="settings card" aria-label="Summary settings">
            <div className="setting"><label htmlFor="length">Summary length</label><select id="length" disabled={loading} value={length} onChange={(event) => setLength(event.target.value)}><option>Short</option><option>Medium</option><option>Long</option></select></div>
            <div className="setting"><label htmlFor="provider">AI provider</label><select id="provider" disabled={loading} value={provider} onChange={(event) => setProvider(event.target.value)}><option>Google Gemini</option><option>Ollama</option></select></div>
            <button className="generate-button" type="submit" disabled={!text.trim() || loading || extracting}>{loading ? 'Generating...' : 'Generate Summary'} <span aria-hidden="true">→</span></button>
          </section>
          <div className="status-line" role="status" aria-live="polite"><span className="status-dot" />{message || (provider === 'Ollama' ? 'Ollama requires a running local server.' : 'Google Gemini requires an API key.')}</div>
        </form>

        <section id="history" className="history" aria-labelledby="history-title">
          <div className="history-heading"><div><div className="section-kicker">PICK UP WHERE YOU LEFT OFF</div><h2 id="history-title">History</h2><p>Revisit your past summaries.</p></div>{history.length > 0 && <button type="button" className="history-clear" disabled={historyBusy} onClick={handleClear}>Clear history</button>}</div>
          {historyMessage && <p className="history-message" role="status">{historyMessage} <button type="button" className="text-button" onClick={refreshHistory}>Retry</button></p>}
          {historyLoading ? <p>Loading history…</p> : history.length === 0 ? <p>No summaries yet. Your generated summaries will appear here.</p> : <div className="history-list">{history.map((item) => <article className="history-item" key={item.id}>
            <div className="history-item-content"><p className="history-preview">{item.summary_text}</p><div className="history-meta"><span>{new Date(item.created_at).toLocaleString()}</span><span>{item.provider === 'ollama' ? 'Ollama' : 'Google Gemini'}</span><span>{item.summary_length}</span><span>{item.summary_word_count} words</span></div></div>
            <div className="history-actions"><button type="button" className="text-button" disabled={historyBusy || loading || extracting} onClick={() => handleRestore(item.id)}>Restore</button><button type="button" className="text-button delete-button" disabled={historyBusy} onClick={() => handleDelete(item.id)}>Delete</button></div>
          </article>)}</div>}
        </section>
      </main>
      <footer><div>AI Text Summarizer | College Internship Project <span>Made for clearer reading.</span></div></footer>
    </div>
  );
}

export default App;
