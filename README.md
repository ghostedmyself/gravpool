<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/stdlib-only-0f766e" alt="stdlib only">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT">
  <img src="https://img.shields.io/github/v/release/ghostedmyself/gravpool" alt="release">
</p>

<h1 align="center">GravPool</h1>
<p align="center"><b>Satu perintah → gateway AI OpenAI-compatible yang selalu sehat.</b><br>
kelola akun Google Antigravity Pro · tambah provider eksternal · dashboard web</p>

<p align="center">
  <code>curl -LsSf https://raw.githubusercontent.com/ghostedmyself/gravpool/main/install.sh | bash</code>
</p>

---

GravPool mengubah kredensial **Google Antigravity Pro** menjadi *credential pool*
yang bisa di-refresh dan dimonitor otomatis, lalu diekspos lewat satu endpoint
OpenAI-compatible di depan Gemini/Claude/GPT. Kamu juga bisa menyuntikkan
**API key provider eksternal** (OpenAI, OpenRouter, atau endpoint custom) ke
gateway yang sama — semua diakses lewat satu `sk-local`.

Tanpa dependency apa pun (pure Python stdlib). Teruji live terhadap akun Pro.

---

## ⚡ Mulai dalam 60 detik

**Cara A — pip / uv (seperti `npm install -g`, direkomendasikan):**

```bash
# butuh uv (https://astral.sh/uv) — sekali saja: curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install gravpool        # ATAU dari repo lokal: uv tool install /path/ke/gravpool

gravpool gui --port 8390
```

**Cara B — installer satu-perintah (fallback, tanpa uv):**

```bash
curl -LsSf https://raw.githubusercontent.com/ghostedmyself/gravpool/main/install.sh | bash
gravpool gui --port 8390
```

Buka dashboard di **http://127.0.0.1:8390**, lalu:
- **Add Account** — login akun Google Antigravity (sekali, lewat browser)
- **Add Provider** — masukkan API key eksternal + base URL, otomatis detect model
- Gunakan endpoint `http://127.0.0.1:8390/v1` dengan API key `sk-local` dari
  OpenCode, Cline, Cursor, atau tool apa pun.

> Kredensial OAuth publik sudah **built-in** — tidak perlu setup client sendiri.
> Query ulang pakai `gravpool gui` untuk update ke versi terbaru (idempotent).

## ✨ Fitur

- **Unified gateway** — Antigravity + provider eksternal, satu endpoint, satu key `sk-local`.
- **Provider auto-detect** — isi base URL + key, GravPool langsung cari model via `/models`.
- **Refresh & quota otomatis** — token expired di-refresh otomatis, kuota live per akun.
- **Auth verify** — token dites ke API quota setelah login → status "verified, N models".
- **Combo routing** — gabungkan model dengan fallback/fusion otomatis (skip yang kuota habis).
- **Dashboard Obsidian** — pemantauan kuota, token countdown, dan manajemen dalam satu panel.

## 🔌 Cara pakai endpoint

```bash
# di tool AI apa pun (OpenCode, Cline, Cursor, …)
BASE_URL=http://127.0.0.1:8390/v1
API_KEY=sk-local
MODEL=muse            # dari provider eksternal
MODEL=claude-sonnet-4-6   # dari akun Antigravity
```

Config OpenCode siap pakai ada di [`examples/opencode.json`](examples/opencode.json),
panduan di [`docs/opencode.md`](docs/opencode.md).

## 🛠️ CLI

```bash
gravpool status        # state token tiap akun
gravpool quota         # snapshot kuota live
gravpool refresh       # refresh semua token expired
gravpool gui           # dashboard + gateway (default port 8390)
gravpool add-account   # login akun Google baru (browser consent)
gravpool combo         # kelola combo fallback/fusion
```

Semua perintah menerima `--auth-dirs DIR [DIR ...]` untuk menunjuk lokasi auth file.

## 🏗️ Struktur

```
gravpool/
├── gravpool/            # paket inti (stdlib only)
│   ├── static/          #   UI dashboard (index.html, style.css, app.js)
│   ├── web.py           #   dashboard + reverse-proxy /v1
│   ├── providers.py     #   provider eksternal (auto-detect model)
│   ├── quota.py         #   fetchAvailableModels live
│   ├── store.py         #   auth file CLIProxyAPI-compatible
│   ├── oauth.py         #   refresh / login
│   ├── combo.py         #   combo virtual (fallback/fusion)
│   └── cli.py           #   antarmuka command-line
├── docs/                # panduan install & integrasi
├── examples/            # config siap pakai
├── install.sh           # installer satu-perintah (fallback)
└── bundle.py            # fetch CLIProxyAPI proxy binary
```

## 📄 Lisensi

[MIT](LICENSE) © 2026 Omni.labs
