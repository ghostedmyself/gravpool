# Instalasi Ulang (1 Perintah)

GravPool install ke `~/.local/share/gravpool`, dan memasang launcher `gravpool`
di PATH. Aman dijalankan ulang (idempotent) untuk update ke versi terbaru.

**Yang kamu butuhkan:**
- Python 3.9+
- Git
- Akun Google (akses Antigravity, opsional)

---

## Cara tercepat

```bash
curl -LsSf https://raw.githubusercontent.com/ghostedmyself/gravpool/main/install.sh | bash
```

Script ini:
1. Clone/update repo ke `~/.local/share/gravpool`
2. Fetch binary `cli-proxy-api` (idempotent — skip kalau sudah ada)
3. Pasang launcher `gravpool` di `~/.local/bin`
4. Cetak langkah selanjutnya

> **Windows:** jalankan `install.bat` setelah clone repo, atau aktifkan WSL
> lalu pakai perintah di atas.

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

## Pindah ke versi terbaru

```bash
# installer idempotent — cukup jalankan lagi
curl -LsSf https://raw.githubusercontent.com/ghostedmyself/gravpool/main/install.sh | bash
```

## FAQ

**Butuh VPS?** Tidak. Semua jalan lokal dalam satu proses di port 8390.

**Pakai /v1 dari klien AI (OpenCode/Cursor/Cline)?**
- Base URL: `http://127.0.0.1:8390/v1`
- API Key: `sk-local`

**Mau tambah model/provider eksternal?** Klik **Add Provider** di dashboard,
isi base URL + API key, lalu Test Connection — model otomatis ter-detect dan
langsung tersedia di endpoint yang sama.
