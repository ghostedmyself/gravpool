# Instalasi (1 Perintah)

GravPool sekarang **bisa di-install sebagai package CLI** (seperti `npm install -g`),
sekaligus tetap punya installer satu-perintah untuk yang tidak pakai uv/pip.

---

## Cara A — uv / pip (direkomendasikan, seperti `npm install -g`)

```bash
# sekali saja kalau uv belum ada
curl -LsSf https://astral.sh/uv/install.sh | sh

# install dari PyPI (setelah release) atau langsung dari repo lokal:
uv tool install gravpool
# ATAU
uv tool install /path/ke/repo/gravpool

# jalankan
gravpool gui --port 8390
```

`uv tool install` memasang binary `gravpool` di PATH, dashboard + static assets
ikut dibundle di dalam package — tidak perlu clone repo manual.

> Tanpa uv tapi punya pipx: `pipx install gravpool`. Tanpa keduanya, pakai Cara B.

---

## Cara B — installer satu-perintah (fallback)

```bash
curl -LsSf https://raw.githubusercontent.com/ghostedmyself/gravpool/main/install.sh | bash
gravpool gui --port 8390
```

Script ini:
1. Clone/update repo ke `~/.local/share/gravpool`
2. Fetch binary `cli-proxy-api` (idempotent — skip kalau sudah ada)
3. Pasang launcher `gravpool` di `~/.local/bin`
4. Cetak langkah selanjutnya

> **Windows:** jalankan `install.bat`, atau pakai WSL lalu perintah di atas.

---

## Pakai

**1. Login akun Google** (sekali, atau nambah akun kapan saja):

```bash
gravpool add-account
```

*(Atau klik tombol **Add Account** langsung di dashboard.)*

**2. Jalankan gateway + dashboard:**

```bash
gravpool gui --port 8390
```

Ini memulai:
- **Dashboard** — http://127.0.0.1:8390 (kelola akun, kuota, combo, provider)
- **Endpoint OpenAI-compatible** — `http://127.0.0.1:8390/v1` dengan key `sk-local`

## Update ke versi terbaru

```bash
uv tool upgrade gravpool        # Cara A
# atau jalankan install.sh lagi (Cara B, idempotent)
```

## FAQ

**Butuh VPS?** Tidak. Semua jalan lokal dalam satu proses di port 8390.

**Pakai /v1 dari klien AI (OpenCode/Cursor/Cline)?**
- Base URL: `http://127.0.0.1:8390/v1`
- API Key: `sk-local`

**Mau tambah model/provider eksternal?** Klik **Add Provider** di dashboard,
isi base URL + API key, lalu Test Connection — model otomatis ter-detect dan
langsung tersedia di endpoint yang sama.

**Proxy binary (`cli-proxy-api`) tidak ikut?** Benar — binary itu diperlakukan
sebagai runtime optional (di-fetch `bundle.py` ke folder `bin/` di repo/install).
Antigravity account pool dan semua provider eksternal tetap jalan tanpa binary
(`--no-proxy`): yang berkurang hanya lapisan `/v1` buat Antigravity di depan
binary. Bahwa dashboard + routing tetap penuh.
