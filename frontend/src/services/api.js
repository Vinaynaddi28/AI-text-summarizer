const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) throw new Error('Unable to reach the backend.');
  return response.json();
}

export async function summarizeText(text, length, provider = 'gemini') {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, length: length.toLowerCase(), provider }),
    });
  } catch {
    throw new Error('Could not reach the backend. Make sure FastAPI is running on port 8000.');
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'The summary request failed.');
  return data;
}

export async function extractPdf(file) {
  const form = new FormData();
  form.append('file', file);
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/extract-pdf`, { method: 'POST', body: form });
  } catch {
    throw new Error('Could not reach the backend. Make sure FastAPI is running on port 8000.');
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'PDF extraction failed.');
  return data;
}

async function historyRequest(path = '', options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/history${path}`, options);
  } catch {
    throw new Error('Could not reach the backend. Make sure FastAPI is running on port 8000.');
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(typeof data.detail === 'string' ? data.detail : 'History request failed.');
  }
  return response.status === 204 ? null : response.json();
}

export const getHistory = () => historyRequest();
export const getHistoryItem = (id) => historyRequest(`/${encodeURIComponent(id)}`);
export const deleteHistoryItem = (id) => historyRequest(`/${encodeURIComponent(id)}`, { method: 'DELETE' });
export const clearHistory = () => historyRequest('', { method: 'DELETE' });
