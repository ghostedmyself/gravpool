# Instalasi

Butuh **Python 3.9+** dan **Git**. Cek dulu: `python3 --version`

## Cara paling mudah

```bash
curl -LsSf https://raw.githubusercontent.com/ghostedmyself/gravpool/main/install.sh | bash
gravpool gui --port 8390
```

Yang dilakukan script:
1. Clone repo ke `~/.local/share/gravpool`
2. Unduh binary pendukung `cli-proxy-api` (sekali; skip kalau sudah ada)
3. Pasang perintah `gravpool` di `~/.local/bin`
4. Dashboard siap jalan

**Windows:** pakai WSL, atau jalankan `install.bat` setelah clone repo.

## Pakai uv (opsional, lebih cepat)

Kalau suka pakai `uv` (pengelola paket Python modern):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh      # sekali saja
uv tool install gravpool                              # dari PyPI nanti
# ATAU dari repo lokal:
uv tool install /path/ke/gravpool

gravpool gui --port 8390
```

Tanpa `uv` tapi punya `pipx`: `pipx install gravpool` juga bisa.

## Mulai pakai

1. **Login akun Google**: `gravpool add-account` — atau klik **Add Account** di dashboard.
2. **Jalankan**: `gravpool gui --port 8390`
3. **Dashboard**: http://127.0.0.1:8390
4. **Endpoint API**: `http://127.0.0.1:8390/v1` dengan key `sk-local`

## Update

```bash
# cara installer:
curl -LsSf https://raw.githubusercontent.com/ghostedmyself/gravpool/main/install.sh | bash
# cara uv:
uv tool upgrade gravpool
```

Keduanya aman — akun dan pengaturan tidak berubah.

## FAQ

**Perlu VPS?** Tidak. Semua jalan di komputer sendiri, satu proses, port 8390.

**Mau pasang di aplikasi AI (OpenCode/Cursor/Cline)?**
- Base URL: `http://127.0.0.1:8390/v1`
- API Key: `sk-local`

**Mau tambah model dari provider lain?** Klik **Add Provider** di dashboard, isi
base URL + API key, lalu **Test Connection** — model otomatis ter-detect.

**Binary `cli-proxy-api` tidak ikut terpasang?** Tenang — itu opsional. Tanpa
binary, akun Antigravity dan semua provider eksternal tetap jalan, hanya lapisan
`/v1` khusus Antigravity yang perlu binary. Dashboard dan routing tetap penuh.