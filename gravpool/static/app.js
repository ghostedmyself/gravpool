const UI = {
  proxyStatus: document.getElementById('proxy-status'),
  proxyEndpoint: document.getElementById('proxy-endpoint'),
  copyBtn: document.getElementById('copy-key-btn'),
  statTotal: document.getElementById('stat-total'),
  statOk: document.getElementById('stat-ok'),
  statExpired: document.getElementById('stat-expired'),
  statDisabled: document.getElementById('stat-disabled'),
  refreshAllBtn: document.getElementById('refresh-all-btn'),
  reloadQuotaBtn: document.getElementById('reload-quota-btn'),
  accountsContainer: document.getElementById('accounts-container'),
  combosContainer: document.getElementById('combos-container'),
  comboForm: document.getElementById('combo-form'),
  addAccountBtn: document.getElementById('add-account-btn'),
  addAccountDialog: document.getElementById('add-account-dialog'),
  closeAddAccountBtn: document.getElementById('close-add-account'),
  addAccountState: document.getElementById('add-account-state'),
  modelsGrid: document.getElementById('models-grid'),
  modelsCount: document.getElementById('models-count'),
  providersContainer: document.getElementById('providers-container'),
  addProviderBtn: document.getElementById('add-provider-btn'),
  addProviderDialog: document.getElementById('add-provider-dialog'),
  closeAddProviderBtn: document.getElementById('close-add-provider'),
  providerForm: document.getElementById('provider-form'),
  testProviderBtn: document.getElementById('test-provider-btn'),
  providerTestResult: document.getElementById('provider-test-result'),
  toastContainer: document.getElementById('toast-container')
};

let state = {
  apiKey: '',
  pollingAuth: false
};

const escapeHTML = str => {
  if (typeof str !== 'string') return '';
  return str.replace(/[&<>'"]/g, tag => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[tag]));
};

const showToast = (msg, type = 'info') => {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  UI.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.2s';
    setTimeout(() => toast.remove(), 200);
  }, 3000);
};

const apiCall = async (url, options = {}) => {
  try {
    const res = await fetch(url, options);
    let data = null;
    try { data = await res.json(); } catch { /* non-JSON */ }
    if (!res.ok) {
      const backendErr = (data && data.error) ? String(data.error) : `HTTP ${res.status}`;
      const e = new Error(backendErr);
      e.status = res.status;
      e.data = data;
      throw e;
    }
    return data;
  } catch (err) {
    console.error(`API Error (${url}):`, err);
    throw err;
  }
};

/* Proxy status */
const loadProxy = async () => {
  try {
    const data = await apiCall('/api/proxy');
    UI.proxyStatus.classList.remove('skeleton');
    UI.proxyEndpoint.classList.remove('skeleton-text');
    if (data.running && data.healthy) {
      UI.proxyStatus.dataset.state = 'running';
      UI.proxyStatus.innerHTML = `<span class="status-dot"></span> <span class="status-text">Live</span>`;
    } else {
      UI.proxyStatus.dataset.state = 'down';
      UI.proxyStatus.innerHTML = `<span class="status-dot"></span> <span class="status-text">Down</span>`;
    }
    UI.proxyEndpoint.textContent = data.endpoint;
    state.apiKey = data.api_key;
    UI.copyBtn.disabled = false;
  } catch (err) {
    UI.proxyStatus.classList.remove('skeleton');
    UI.proxyStatus.dataset.state = 'down';
    UI.proxyStatus.innerHTML = `<span class="status-dot"></span> <span class="status-text">Offline</span>`;
    UI.proxyEndpoint.textContent = '—';
  }
};

/* Accounts */
const fmtExpiry = (isoStr) => {
  if (!isoStr) return '';
  try {
    const d = new Date(isoStr);
    const now = new Date();
    const diffMs = d - now;
    const absMin = Math.abs(diffMs / 60000);
    let str;
    if (absMin < 60) str = `${Math.round(absMin)}m`;
    else if (absMin < 1440) str = `${(absMin / 60).toFixed(1)}h`;
    else str = `${(absMin / 1440).toFixed(1)}d`;
    if (diffMs < 0) return `${str} ago`;
    return `in ${str}`;
  } catch { return ''; }
};

const fmtReset = (isoStr, verb = 'resets') => {
  if (!isoStr) return '';
  const rel = fmtExpiry(isoStr);
  if (!rel) return '';
  return rel.startsWith('in ') ? `${verb} ${rel}` : rel;
};

const renderAccounts = (statusData, quotaData) => {
  UI.statTotal.textContent = statusData.length;
  UI.statOk.textContent = statusData.filter(a => a.state === 'ok').length;
  UI.statExpired.textContent = statusData.filter(a => a.state === 'expired').length;
  UI.statDisabled.textContent = statusData.filter(a => a.state === 'disabled').length;

  if (statusData.length === 0) {
    UI.accountsContainer.innerHTML = `<div class="empty-state">No accounts configured.</div>`;
    return;
  }

  const order = { ok: 1, expired: 2, disabled: 3 };
  statusData.sort((a, b) => order[a.state] - order[b.state]);

  UI.accountsContainer.innerHTML = statusData.map(acc => {
    const qData = quotaData.accounts?.[acc.email];
    let quotaHtml = '';

    // — estilo fleet-control (mirip panel antigravity): satu bar per akun —
    if (qData && qData.error) {
      quotaHtml = `<div class="inline-err">Quota error: ${escapeHTML(qData.error)}</div>`;
    } else if (qData && qData.models) {
      const models = Object.values(qData.models);
      const pcts = models.map(m => (m.remaining * 100));
      const avg = pcts.reduce((a, b) => a + b, 0) / (pcts.length || 1);
      const worst = Math.min(...pcts);
      const colorClass = worst < 20 ? 'low' : worst < 50 ? 'mid' : 'high';
      const resets = models.map(m => m.reset).filter(Boolean);
      const resetStr = resets.length
        ? ` · <span class="acc-sub">${escapeHTML(fmtReset(new Date(Math.min(...resets.map(r => new Date(r)))), 'reset'))}</span>`
        : '';
      const modelStr = models.length === 1 ? '1 model' : `${models.length} models`;
      quotaHtml = `
        <div class="acc-quota">
          <div class="acc-bar-row">
            <span class="acc-bar">
              <span class="quota-fill ${colorClass}" style="width: ${avg}%"></span>
            </span>
            <span class="acc-pct">${avg.toFixed(1)}%</span>
          </div>
          <div class="acc-meta">
            <span class="acc-sub">${modelStr}${resetStr}</span>
          </div>
        </div>`;
    } else {
      quotaHtml = `<div class="quota-label"><span>No quota data</span></div>`;
    }

    const toggleAction = acc.state === 'disabled' ? 'Enable' : 'Disable';
    const isDisabling = acc.state !== 'disabled';
    const expiryInfo = fmtExpiry(acc.expired);
    const expiryHtml = expiryInfo
      ? `<span class="acc-sub">· token ${escapeHTML(expiryInfo)}</span>`
      : '';

    return `
      <div class="card">
        <div class="card-row">
          <div class="acc-id">
            <span class="acc-dot" style="background:${qData && qData.models ? (Math.min(...Object.values(qData.models).map(m => m.remaining * 100)) > 50 ? '#10b981' : Math.min(...Object.values(qData.models).map(m => m.remaining * 100)) > 20 ? '#f59e0b' : '#ef4444') : '#71717a'}"></span>
            <span class="card-email">${escapeHTML(acc.email)}</span>
            <span class="badge ${acc.state}">${acc.state}</span>
          </div>
          <div class="card-actions">
            <button class="btn-icon toggle-acc-btn" data-email="${escapeHTML(acc.email)}" data-disable="${isDisabling}" title="${toggleAction}" aria-label="${toggleAction} account">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                ${isDisabling ? '<path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line>' : '<polygon points="5 3 19 12 5 21 5 3"></polygon>'}
              </svg>
            </button>
          </div>
        </div>
        <div class="acc-meta">${expiryHtml}</div>
        ${quotaHtml}
      </div>
    `;
  }).join('');

  document.querySelectorAll('.toggle-acc-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const email = e.currentTarget.dataset.email;
      const disable = e.currentTarget.dataset.disable === 'true';
      e.currentTarget.disabled = true;
      try {
        await apiCall('/api/accounts/toggle', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ email, disabled: disable })
        });
        showToast(`${disable ? 'Disabled' : 'Enabled'} ${email}`);
        await loadData();
      } catch (err) {
        showToast('Failed to toggle account', 'error');
        e.currentTarget.disabled = false;
      }
    });
  });
};

/* Models */
const loadModels = async () => {
  try {
    const [proxyRes, extRes] = await Promise.all([
      apiCall('/api/models').catch(() => ({ data: [] })),
      apiCall('/api/providers/models').catch(() => ({ data: [] }))
    ]);
    const proxyModels = (proxyRes.data || []).filter(m => m && m.id)
      .map(m => ({ id: m.id, source: 'antigravity' }));
    const extModels = (extRes.data || []).filter(m => m && m.id)
      .map(m => ({ id: m.id, source: m.provider || 'external' }));
    const all = [...proxyModels, ...extModels];
    if (!all.length) {
      UI.modelsGrid.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;">No models found.</div>`;
      UI.modelsCount.textContent = '0';
      return;
    }
    UI.modelsCount.textContent = `${all.length}`;
    
    const bySource = {};
    for (const m of all) {
      (bySource[m.source] = bySource[m.source] || []).push(m.id);
    }
    const order = ['antigravity', ...Object.keys(bySource).filter(s => s !== 'antigravity').sort()];
    UI.modelsGrid.innerHTML = order.map(src => {
      const ids = bySource[src];
      const label = src === 'antigravity' ? 'Antigravity Pool' : src;
      return `
        <div class="model-group" data-source="${escapeHTML(src)}">
          <div class="model-group-head">
            <span class="model-group-name">${escapeHTML(label)}</span>
            <span class="model-group-count">${ids.length}</span>
          </div>
          <div class="model-group-chips">
            ${ids.map(id => `<span class="model-chip" title="${escapeHTML(id)}">${escapeHTML(id)}</span>`).join('')}
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    UI.modelsGrid.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;">Failed to load models.</div>`;
    UI.modelsCount.textContent = '—';
  }
};

/* External Providers */
const loadProviders = async () => {
  UI.providersContainer.innerHTML = `<div class="empty-state skeleton">Loading...</div>`;
  try {
    const providers = await apiCall('/api/providers');
    if (providers.length === 0) {
      UI.providersContainer.innerHTML = `<div class="empty-state">No external providers configured.</div>`;
      return;
    }
    UI.providersContainer.innerHTML = providers.map(p => `
      <div class="provider-card ${p.enabled ? '' : 'disabled'}" data-name="${escapeHTML(p.name)}">
        <div class="provider-header">
          <div>
            <span class="provider-name">${escapeHTML(p.name)}</span>
            ${p.enabled ? '' : '<span class="badge disabled" style="margin-left:6px">disabled</span>'}
          </div>
          <div style="display:flex; gap:4px;">
            <button class="btn-icon toggle-provider-btn" data-name="${escapeHTML(p.name)}" data-enabled="${p.enabled}" title="${p.enabled ? 'Disable' : 'Enable'}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                ${p.enabled ? '<path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line>' : '<polygon points="5 3 19 12 5 21 5 3"></polygon>'}
              </svg>
            </button>
            <button class="btn-icon delete-provider-btn" data-name="${escapeHTML(p.name)}" title="Delete">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
        </div>
        <div class="provider-url">${escapeHTML(p.base_url)}</div>
        ${p.models && p.models.length ? `<div class="provider-models">${p.models.map(escapeHTML).join(', ')}</div>` : ''}
      </div>
    `).join('');

    document.querySelectorAll('.toggle-provider-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const name = e.currentTarget.dataset.name;
        const newEnabled = e.currentTarget.dataset.enabled !== 'true';
        try {
          await apiCall('/api/providers/update', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, enabled: newEnabled })
          });
          showToast(`${newEnabled ? 'Enabled' : 'Disabled'} ${name}`);
          await Promise.all([loadProviders(), loadModels()]);
        } catch (err) {
          showToast('Failed to toggle provider', 'error');
        }
      });
    });

    document.querySelectorAll('.delete-provider-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        if (!confirm('Delete provider?')) return;
        const name = e.currentTarget.dataset.name;
        try {
          await apiCall(`/api/providers/${encodeURIComponent(name)}`, { method: 'DELETE' });
          showToast(`Deleted ${name}`);
          await Promise.all([loadProviders(), loadModels()]);
        } catch (err) {
          showToast('Failed to delete provider', 'error');
        }
      });
    });
  } catch (err) {
    UI.providersContainer.innerHTML = `<div class="empty-state text-err">Failed to load providers</div>`;
  }
};

/* Provider Form */
UI.addProviderBtn.addEventListener('click', () => {
  UI.providerForm.reset();
  UI.providerTestResult.innerHTML = '';
  UI.addProviderDialog.showModal();
});

UI.closeAddProviderBtn.addEventListener('click', () => {
  UI.addProviderDialog.close();
});

UI.testProviderBtn.addEventListener('click', async () => {
  const name = document.getElementById('provider-name').value.trim();
  const baseUrl = document.getElementById('provider-base-url').value.trim();
  const apiKey = document.getElementById('provider-api-key').value.trim();
  if (!baseUrl || !apiKey) {
    UI.providerTestResult.innerHTML = `<span class="text-err">Base URL and API key required</span>`;
    return;
  }
  UI.testProviderBtn.disabled = true;
  UI.providerTestResult.innerHTML = `<span class="text-dim">Testing connection...</span>`;
  const tmpName = name || '_test';
  
  try {
    let testRes;
    try {
      testRes = await apiCall('/api/providers/test', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ base_url: baseUrl, api_key: apiKey })
      });
    } catch (e) {
      const res = await apiCall('/api/providers', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name: tmpName, base_url: baseUrl, api_key: apiKey })
      });
      if (res.error) throw new Error(res.error);
      
      testRes = await apiCall('/api/providers/test', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name: tmpName })
      });
      
      try {
        await apiCall(`/api/providers/${encodeURIComponent(tmpName)}`, { method: 'DELETE' });
      } catch {}
    }
    
    if (testRes.ok) {
      const models = testRes.models || [];
      UI.providerTestResult.innerHTML = `<span class="text-ok">Connected - ${models.length} models detected</span>`;
    } else {
      UI.providerTestResult.innerHTML = `<span class="text-err">Connection failed</span>`;
    }
  } catch (err) {
    const m = err.message || 'Test failed';
    let hint = '';
    if (/401|403/.test(m)) hint = ' - check API key';
    else if (/404/.test(m)) hint = ' - check base URL';
    UI.providerTestResult.innerHTML = `<span class="text-err">${escapeHTML(m)}${hint}</span>`;
  } finally {
    UI.testProviderBtn.disabled = false;
  }
});

UI.providerForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('provider-name').value.trim();
  const baseUrl = document.getElementById('provider-base-url').value.trim();
  const apiKey = document.getElementById('provider-api-key').value.trim();
  
  if (!name || !baseUrl || !apiKey) return;
  
  const btn = UI.providerForm.querySelector('button[type="submit"]');
  btn.disabled = true;
  
  try {
    await apiCall('/api/providers', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name, base_url: baseUrl, api_key: apiKey })
    });
    showToast(`Provider ${name} added`);
    UI.addProviderDialog.close();
    await Promise.all([loadProviders(), loadModels()]);
  } catch (err) {
    showToast('Failed to add provider', 'error');
  } finally {
    btn.disabled = false;
  }
});

/* Combos */
const renderCombos = async () => {
  try {
    const combos = await apiCall('/api/combos');
    if (combos.length === 0) {
      UI.combosContainer.innerHTML = `<div class="empty-state">No combos created.</div>`;
      return;
    }

    UI.combosContainer.innerHTML = combos.map(c => `
      <div class="card combo-card" data-name="${escapeHTML(c.name)}">
        <div class="card-row" style="margin-bottom:0.5rem">
          <div class="card-email">
            ${escapeHTML(c.name)} 
            <span class="badge ${c.kind}">${c.kind}</span>
          </div>
          <button class="btn-icon delete-combo-btn" data-name="${escapeHTML(c.name)}" aria-label="Delete combo">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="combo-models">${escapeHTML(c.models.join(', '))}</div>
        <div class="combo-resolve skeleton-text" style="width:100%">Resolving...</div>
      </div>
    `).join('');

    document.querySelectorAll('.delete-combo-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        if (!confirm('Delete combo?')) return;
        const name = e.currentTarget.dataset.name;
        try {
          await apiCall(`/api/combos/${encodeURIComponent(name)}`, { method: 'DELETE' });
          showToast(`Deleted ${name}`);
          renderCombos();
        } catch (err) {
          showToast('Failed to delete combo', 'error');
        }
      });
    });

    document.querySelectorAll('.combo-card').forEach(async card => {
      const name = card.dataset.name;
      const resDiv = card.querySelector('.combo-resolve');
      try {
        const res = await apiCall(`/api/combo-resolve?name=${encodeURIComponent(name)}`);
        resDiv.classList.remove('skeleton-text');
        const picked = Array.isArray(res.picked) ? res.picked.join(', ') : res.picked;
        if (picked) {
          const fallback = (res.fallback || []).join(', ');
          const drained = (res.drained || []).join(', ');
          let html = `<span class="text-ok">→ ${escapeHTML(String(picked))}</span>`;
          if (fallback) html += ` <span class="text-warn">· fallback: ${escapeHTML(fallback)}</span>`;
          if (drained) html += ` <span class="text-dim">· drained: ${escapeHTML(drained)}</span>`;
          resDiv.innerHTML = html;
        } else {
          const drained = (res.drained || []).join(', ');
          resDiv.innerHTML = `<span class="text-err">${escapeHTML(res.reason || 'no model available')}</span>` + (drained ? ` <span class="text-dim">· drained: ${escapeHTML(drained)}</span>` : '');
        }
      } catch (err) {
        resDiv.classList.remove('skeleton-text');
        resDiv.innerHTML = `<span class="text-err">resolve error</span>`;
      }
    });

  } catch (err) {
    UI.combosContainer.innerHTML = `<div class="empty-state text-err">Failed to load combos</div>`;
  }
};

/* Data loaders */
const loadData = async () => {
  try {
    const [statusData, quotaData] = await Promise.all([
      apiCall('/api/status'),
      apiCall('/api/quota')
    ]);
    renderAccounts(statusData, quotaData);
  } catch (err) {
    showToast('Failed to load accounts', 'error');
  }
};

/* Actions */
UI.copyBtn.addEventListener('click', () => {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(state.apiKey).then(() => showToast('API key copied'));
  } else {
    const r = document.createRange();
    r.selectNodeContents(UI.proxyEndpoint);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(r);
    showToast('Select to copy');
  }
});

UI.refreshAllBtn.addEventListener('click', async () => {
  UI.refreshAllBtn.disabled = true;
  try {
    const res = await apiCall('/api/refresh', { method: 'POST' });
    showToast(`Refreshed ${res.refreshed.length}, failed ${res.failed.length}`);
    await loadData();
  } catch (err) {
    showToast('Refresh failed', 'error');
  } finally {
    UI.refreshAllBtn.disabled = false;
  }
});

UI.reloadQuotaBtn.addEventListener('click', async () => {
  UI.reloadQuotaBtn.disabled = true;
  try {
    await Promise.all([loadData(), loadModels()]);
    showToast('Reloaded data');
  } finally {
    UI.reloadQuotaBtn.disabled = false;
  }
});

UI.comboForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('combo-name').value.trim();
  const kind = document.getElementById('combo-kind').value;
  const models = document.getElementById('combo-models').value.split(',').map(s => s.trim()).filter(Boolean);

  if (!name || !models.length) return;
  const btn = UI.comboForm.querySelector('button');
  btn.disabled = true;

  try {
    await apiCall('/api/combos', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name, kind, models })
    });
    showToast('Combo created');
    UI.comboForm.reset();
    renderCombos();
  } catch (err) {
    showToast('Failed to create combo', 'error');
  } finally {
    btn.disabled = false;
  }
});

/* Add Account Flow */
UI.addAccountBtn.addEventListener('click', () => {
  UI.addAccountDialog.showModal();
  UI.addAccountState.innerHTML = `<button id="start-add-account" class="btn btn-primary" style="width:100%">Generate Auth Link</button>`;
  document.getElementById('start-add-account').addEventListener('click', async (e) => {
    e.currentTarget.disabled = true;
    try {
      const res = await apiCall('/api/add-account', { method: 'POST' });
      UI.addAccountState.innerHTML = `
        <a href="${escapeHTML(res.url)}" target="_blank" class="auth-link">Open Authorization Link →</a>
        <div class="text-dim" style="font-size:0.8125rem; text-align:center;">Waiting for authorization...</div>
      `;
      state.pollingAuth = true;
      pollAddAccount();
    } catch (err) {
      UI.addAccountState.innerHTML = `
        <div class="inline-err" style="text-align:center; display:block; margin-bottom:0.5rem;">Failed to start flow.</div> 
        <button id="retry-add-acc" class="btn btn-secondary" style="width:100%">Retry</button>
      `;
      document.getElementById('retry-add-acc').addEventListener('click', () => UI.addAccountBtn.click());
    }
  });
});

UI.closeAddAccountBtn.addEventListener('click', () => {
  state.pollingAuth = false;
  UI.addAccountDialog.close();
});

const pollAddAccount = async () => {
  if (!state.pollingAuth) return;
  try {
    const res = await apiCall('/api/add-account');
    if (!res.pending) {
      state.pollingAuth = false;
      if (res.error) {
        UI.addAccountState.innerHTML = `<div class="inline-err" style="text-align:center; display:block;">${escapeHTML(res.error)}</div>`;
      } else {
        UI.addAccountState.innerHTML = `<div class="text-ok mono" style="text-align:center; padding:1rem;">Added ${escapeHTML(res.email)}</div>`;
        loadData();
      }
      return;
    }
  } catch (err) {
    // keep polling
  }
  setTimeout(pollAddAccount, 2000);
};

/* Init */
const init = async () => {
  await Promise.all([loadProxy(), loadData(), renderCombos(), loadModels(), loadProviders()]).catch(() => {});
  setInterval(loadData, 60000);
  setInterval(loadProxy, 120000);
  setInterval(renderCombos, 120000);
  setInterval(loadModels, 120000);
  setInterval(loadProviders, 120000);
};

init();
