const LOCAL_SERVER = 'http://localhost:8081';

// Query aus Search-URLs extrahieren
function extractQuery(url) {
  try {
    const u = new URL(url);
    const h = u.hostname;
    if (h.includes('google.')) return u.searchParams.get('q');
    if (h.includes('bing.com')) return u.searchParams.get('q');
    if (h.includes('duckduckgo.com')) return u.searchParams.get('q');
    if (h.includes('search.brave.com')) return u.searchParams.get('q');
    if (h.includes('yahoo.com')) return u.searchParams.get('p');
    if (h.includes('baidu.com')) return u.searchParams.get('wd');
    return null;
  } catch { return null; }
}

// Query gegen lokalen Server prüfen
async function checkQuery(query, tabId) {
  try {
    const res = await fetch(`${LOCAL_SERVER}/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    if (data.blocked) {
      const reason = encodeURIComponent(data.reason || 'Regelverstoß');
      const q = encodeURIComponent(query);
      chrome.tabs.update(tabId, {
        url: `${LOCAL_SERVER}/blocked?query=${q}&reason=${reason}`
      });
    }
  } catch (err) {
    console.warn('[AI Search Guard] Server nicht erreichbar:', err);
  }
}

// Tab-Updates überwachen (fängt auch Adressleiste-Suchen ab)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'loading' && tab.url) {
    const query = extractQuery(tab.url);
    if (query && query.length > 0) {
      checkQuery(query, tabId);
    }
  }
});

// Nachrichten von Content Scripts entgegennehmen
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'CHECK_QUERY' && sender.tab) {
    checkQuery(msg.query, sender.tab.id);
    sendResponse({ status: 'checking' });
  }
});
