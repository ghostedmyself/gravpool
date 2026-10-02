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
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(`API Error (${url}):`, err);
    throw err;
  }
};

/* ─── Proxy status ─── */
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

/* ─── Accounts ─── */
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

    if (qData && qData.error) {
      quotaHtml = `<div class="inline-err">Quota error: ${escapeHTML(qData.error)}</div>`;
    } else if (qData && qData.models) {
      const models = Object.entries(qData.models)
        .map(([model, data]) => ({ model, ...data }))
        .sort((a, b) => a.remaining - b.remaining);

      quotaHtml = models.map(m => {
        const pct = m.remaining * 100;
        const colorClass = pct < 20 ? 'low' : pct < 50 ? 'mid' : 'high';
        const resetStr = m.reset ? `<span class="quota-reset">reset ${escapeHTML(m.reset)}</span>` : '';
        return `
          <div class="quota-item">
            <div class="quota-label">
              <span>${escapeHTML(m.model)}</span>
              <span>${pct.toFixed(1)}% ${resetStr}</span>
            </div>
            <div class="quota-track">
              <div class="quota-fill ${colorClass}" style="width: ${pct}%"></div>
            </div>
          </div>
        `;
      }).join('');
    } else {
      quotaHtml = `<div class="quota-label"><span>No quota data</span></div>`;
    }

    const toggleAction = acc.state === 'disabled' ? 'Enable' : 'Disable';
    const isDisabling = acc.state !== 'disabled';

    return `
      <div class="card">
        <div class="card-row">
          <div class="card-email">${escapeHTML(acc.email)}</div>
          <div class="card-actions">
            <span class="badge ${acc.state}">${acc.state}</span>
            <button class="btn-icon toggle-acc-btn" data-email="${escapeHTML(acc.email)}" data-disable="${isDisabling}" title="${toggleAction}" aria-label="${toggleAction} account">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                ${isDisabling ? '<path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line>' : '<polygon points="5 3 19 12 5 21 5 3"></polygon>'}
              </svg>
            </button>
          </div>
        </div>
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

/* ─── Models ─── */
const loadModels = async () => {
  try {
    const res = await apiCall('/api/models');
    const models = (res.data || []).filter(m => m && m.id);
    if (!models.length) {
      UI.modelsGrid.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;">No models — proxy offline.</div>`;
      UI.modelsCount.textContent = '0';
      return;
    }
    UI.modelsCount.textContent = `${models.length} models`;
    UI.modelsGrid.innerHTML = models.map(m => {
      const id = m.id;
      let vendor = 'antigravity';
      if (id.startsWith('gemini')) vendor = 'gemini';
      else if (id.startsWith('claude')) vendor = 'claude';
      else if (id.startsWith('gpt')) vendor = 'gpt';
      return `
        <div class="model-card" title="${escapeHTML(id)}">
          <div class="model-id">${escapeHTML(id)}</div>
          <div class="model-vendor">${escapeHTML(vendor)}</div>
        </div>
      `;
    }).join('');
  } catch (err) {
    UI.modelsGrid.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;">Failed to load models.</div>`;
    UI.modelsCount.textContent = '—';
  }
};

/* ─── Combos ─── */
const renderCombos = async () => {
  try {
    const combos = await apiCall('/api/combos');
    if (combos.length === 0) {
      UI.combosContainer.innerHTML = `<div class="empty-state">No combos.</div>`;
      return;
    }

    UI.combosContainer.innerHTML = combos.map(c => `
      <div class="card combo-card" data-name="${escapeHTML(c.name)}">
        <div class="card-row" style="margin-bottom:0.375rem">
          <div class="card-email">${escapeHTML(c.name)} <span class="badge ${c.kind}">${c.kind}</span></div>
          <button class="btn-icon delete-combo-btn" data-name="${escapeHTML(c.name)}" aria-label="Delete combo">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="combo-models">${escapeHTML(c.models.join(', '))}</div>
        <div class="combo-resolve skeleton-text" style="width:100%"></div>
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
          if (fallback) html += ` <span class="text-warn">· fb: ${escapeHTML(fallback)}</span>`;
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

/* ─── Data loaders ─── */
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

/* ─── Actions ─── */
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
    showToast('Reloaded');
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

/* ─── Add Account Flow ─── */
UI.addAccountBtn.addEventListener('click', () => {
  UI.addAccountDialog.showModal();
  UI.addAccountState.innerHTML = `<button id="start-add-account" class="btn btn-primary btn-block">Generate Auth Link</button>`;
  document.getElementById('start-add-account').addEventListener('click', async (e) => {
    e.currentTarget.disabled = true;
    try {
      const res = await apiCall('/api/add-account', { method: 'POST' });
      UI.addAccountState.innerHTML = `
        <a href="${escapeHTML(res.url)}" target="_blank" class="auth-link">Open Authorization Link →</a>
        <div class="mono text-dim" style="font-size:0.8125rem; text-align:center;">Waiting for authorization…</div>
      `;
      state.pollingAuth = true;
      pollAddAccount();
    } catch (err) {
      UI.addAccountState.innerHTML = `<div class="inline-err" style="text-align:center; display:block; margin-bottom:0.5rem;">Failed to start flow.</div> <button id="retry-add-acc" class="btn btn-block">Retry</button>`;
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

/* ─── Init ─── */
const init = async () => {
  await Promise.all([loadProxy(), loadData(), renderCombos(), loadModels()]).catch(() => {});
  setInterval(loadData, 60000);
  setInterval(loadProxy, 120000);
  setInterval(renderCombos, 120000);
  setInterval(loadModels, 120000);
};

init();
