const DEFAULT_RULES = [
  'Blockiere Anleitungen für illegale Aktivitäten',
  'Blockiere Hassrede und Diskriminierung',
  'Blockiere explizite Inhalte für Minderjährige',
  'Blockiere Anleitungen zu Waffenbau',
  'Blockiere Betrugsversuche und Phishing'
];

// Regeln aus dem Speicher laden
async function loadRules() {
  const data = await chrome.storage.local.get({ rules: DEFAULT_RULES });
  renderRules(data.rules);
}

// Regeln rendern
function renderRules(rules) {
  const list = document.getElementById('rules-list');
  list.innerHTML = '';
  rules.forEach((rule, i) => {
    const div = document.createElement('div');
    div.className = 'rule-item';
    div.innerHTML = `<span>${rule}</span> <button data-idx="${i}" class="delete-btn">✕</button>`;
    list.appendChild(div);
  });
  list.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const idx = parseInt(btn.dataset.idx);
      const data = await chrome.storage.local.get({ rules: DEFAULT_RULES });
      data.rules.splice(idx, 1);
      await chrome.storage.local.set({ rules: data.rules });
      renderRules(data.rules);
      syncRulesToServer(data.rules);
    });
  });
}

// Neue Regel hinzufügen
document.getElementById('add-rule-btn').addEventListener('click', async () => {
  const input = document.getElementById('new-rule');
  const rule = input.value.trim();
  if (!rule) return;
  const data = await chrome.storage.local.get({ rules: DEFAULT_RULES });
  data.rules.push(rule);
  await chrome.storage.local.set({ rules: data.rules });
  input.value = '';
  renderRules(data.rules);
  syncRulesToServer(data.rules);
});

// Regeln mit Server synchronisieren
async function syncRulesToServer(rules) {
  try {
    await fetch('http://localhost:8081/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rules })
    });
  } catch (err) {
    console.warn('Konnte Regeln nicht an Server senden:', err);
  }
}

// Server-Status prüfen
async function checkServer() {
  const el = document.getElementById('server-status');
  try {
    const res = await fetch('http://localhost:8081/health');
    if (res.ok) {
      el.textContent = '✅ Server läuft';
      el.className = 'status ok';
    } else {
      el.textContent = '❌ Server Fehler';
      el.className = 'status error';
    }
  } catch {
    el.textContent = '⚠️ Server nicht erreichbar (python server/server.py starten)';
    el.className = 'status warning';
  }
}

// Konfiguration speichern
document.getElementById('save-config-btn').addEventListener('click', async () => {
  const config = {
    modelPath: document.getElementById('model-path').value,
    llamaPort: parseInt(document.getElementById('llama-port').value),
    serverPort: parseInt(document.getElementById('server-port').value)
  };
  await chrome.storage.local.set({ config });
  alert('Konfiguration gespeichert!');
});

// Init
loadRules();
checkServer();
setInterval(checkServer, 5000);
