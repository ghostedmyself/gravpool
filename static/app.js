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

const loadProxy = async () => {
  try {
    const data = await apiCall('/api/proxy');
    UI.proxyStatus.classList.remove('skeleton');
    UI.proxyEndpoint.classList.remove('skeleton-text');
    if (data.running && data.healthy) {
      UI.proxyStatus.dataset.state = 'running';
      UI.proxyStatus.innerHTML = `<span class="status-dot"></span> <span class="status-text">Proxy Running</span>`;
    } else {
      UI.proxyStatus.dataset.state = 'down';
      UI.proxyStatus.innerHTML = `<span class="status-dot"></span> <span class="status-text">Proxy Down / Unhealthy</span>`;
    }
    
    UI.proxyEndpoint.textContent = escapeHTML(data.endpoint);
    state.apiKey = data.api_key;
    UI.copyBtn.disabled = false;
  } catch (err) {
    UI.proxyStatus.classList.remove('skeleton');
    UI.proxyStatus.dataset.state = 'down';
    UI.proxyStatus.innerHTML = `<span class="status-dot"></span> <span class="status-text">Proxy Offline</span>`;
    UI.proxyEndpoint.textContent = 'Unavailable';
  }
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

  // Sort: ok > expired > disabled
  const order = { ok: 1, expired: 2, disabled: 3 };
  statusData.sort((a, b) => order[a.state] - order[b.state]);

  UI.accountsContainer.innerHTML = statusData.map(acc => {
    const qData = quotaData.accounts?.[acc.email];
    let quotaHtml = '';
    
    if (qData && qData.error) {
      quotaHtml = `<div class="inline-error">Quota error: ${escapeHTML(qData.error)}</div>`;
    } else if (qData && qData.models) {
      const models = Object.entries(qData.models)
        .map(([model, data]) => ({ model, ...data }))
        .sort((a, b) => a.remaining - b.remaining);
      
      quotaHtml = models.map(m => {
        const pct = m.remaining * 100;
        const colorClass = pct < 20 ? 'low' : pct < 50 ? 'mid' : 'high';
        const resetStr = m.reset ? `(Resets ${escapeHTML(m.reset)})` : '';
        return `
          <div class="quota-item">
            <div class="quota-label">
              <span>${escapeHTML(m.model)}</span>
              <span>${pct.toFixed(1)}% ${escapeHTML(resetStr)}</span>
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
        <div class="card-header">
          <div class="card-title">${escapeHTML(acc.email)}</div>
          <div style="display:flex; gap:8px; align-items:center;">
            <span class="badge ${acc.state}">${acc.state}</span>
            <button class="btn btn-icon toggle-acc-btn" data-email="${escapeHTML(acc.email)}" data-disable="${isDisabling}" title="${toggleAction}" aria-label="${toggleAction} account">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                ${isDisabling ? '<path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line>' : '<polygon points="5 3 19 12 5 21 5 3"></polygon>'}
              </svg>
            </button>
          </div>
        </div>
        <div class="card-body">
          ${quotaHtml}
        </div>
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

const renderCombos = async () => {
  try {
    const combos = await apiCall('/api/combos');
    if (combos.length === 0) {
      UI.combosContainer.innerHTML = `<div class="empty-state">No combos configured.</div>`;
      return;
    }
    
    UI.combosContainer.innerHTML = combos.map(c => `
      <div class="card combo-card" data-name="${escapeHTML(c.name)}">
        <div class="card-header" style="margin-bottom:8px">
          <div class="card-title">${escapeHTML(c.name)} <span class="badge ${c.kind}">${c.kind}</span></div>
          <button class="btn btn-icon delete-combo-btn" data-name="${escapeHTML(c.name)}" aria-label="Delete combo">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="combo-models mono" style="font-size:0.75rem; color:var(--text-muted); margin-bottom:8px;">
          ${escapeHTML(c.models.join(', '))}
        </div>
        <div class="combo-resolve mono skeleton-text" style="font-size:0.75rem; width:100%; min-height:16px;"></div>
      </div>
    `).join('');

    // Delete handlers
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

    // Resolve live statuses
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
          let html = `<span class="text-green">Picked: ${escapeHTML(String(picked))}</span>`;
          if (fallback) html += ` · <span class="text-amber">Fallback: ${escapeHTML(fallback)}</span>`;
          if (drained) html += ` · <span class="text-gray">Drained: ${escapeHTML(drained)}</span>`;
          resDiv.innerHTML = html;
        } else {
          const drained = (res.drained || []).join(', ');
          resDiv.innerHTML = `<span class="text-red">${escapeHTML(res.reason || 'No model available')}</span>` + (drained ? ` · <span class="text-gray">Drained: ${escapeHTML(drained)}</span>` : '');
        }
      } catch (err) {
        resDiv.classList.remove('skeleton-text');
        resDiv.innerHTML = `<span class="text-red">Resolve error</span>`;
      }
    });

  } catch (err) {
    UI.combosContainer.innerHTML = `<div class="empty-state text-red">Failed to load combos</div>`;
  }
};

const loadData = async () => {
  try {
    const [statusData, quotaData] = await Promise.all([
      apiCall('/api/status'),
      apiCall('/api/quota')
    ]);
    renderAccounts(statusData, quotaData);
  } catch (err) {
    showToast('Failed to load accounts data', 'error');
  }
};

// Actions
UI.copyBtn.addEventListener('click', () => {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(state.apiKey).then(() => showToast('API Key copied'));
  } else {
    // Fallback selection
    const r = document.createRange();
    r.selectNodeContents(UI.proxyEndpoint);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(r);
    showToast('Select to copy (clipboard API missing)');
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
    await loadData();
    showToast('Quota reloaded');
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

// Add Account Flow
UI.addAccountBtn.addEventListener('click', () => {
  UI.addAccountDialog.showModal();
  UI.addAccountState.innerHTML = `<button id="start-add-account" class="btn btn-primary w-full">Generate Auth Link</button>`;
  document.getElementById('start-add-account').addEventListener('click', async (e) => {
    e.currentTarget.disabled = true;
    try {
      const res = await apiCall('/api/add-account', { method: 'POST' });
      UI.addAccountState.innerHTML = `
        <a href="${escapeHTML(res.url)}" target="_blank" class="auth-link">Open Authorization Link &rarr;</a>
        <div class="mono text-gray" style="font-size:0.875rem; text-align:center;">Waiting for authorization...</div>
      `;
      state.pollingAuth = true;
      pollAddAccount();
    } catch (err) {
      UI.addAccountState.innerHTML = `<div class="inline-error text-center" style="margin-bottom:8px;">Failed to start flow.</div> <button id="retry-add-acc" class="btn w-full">Retry</button>`;
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
        UI.addAccountState.innerHTML = `<div class="inline-error text-center">${escapeHTML(res.error)}</div>`;
      } else {
        UI.addAccountState.innerHTML = `<div class="text-green text-center mono" style="padding:16px;">Added ${escapeHTML(res.email)}</div>`;
        loadData();
      }
      return;
    }
  } catch (err) {
    // silently continue polling
  }
  setTimeout(pollAddAccount, 2000);
};

// Init & Timers
const init = async () => {
  // Fetch initial data but ignore errors for the skeleton demo
  await Promise.all([loadProxy(), loadData(), renderCombos()]).catch(() => {});
  
  setInterval(loadData, 60000); // 60s quota/status
  setInterval(loadProxy, 120000); // 120s proxy
  setInterval(renderCombos, 120000);
};

init();