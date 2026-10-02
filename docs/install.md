# Instalasi Satu-Bundle (Tanpa VPS)

GravPool sekarang hadir dalam alur satu-bundle via script `bundle.py`. Proses ini otomatis mendownload CLIProxyAPI dan membuatkan `config.yaml`. Semuanya jalan penuh di laptop lokal.

**Yang kamu butuhkan:**
- Python 3.9+
- Akun Google (akses Antigravity)

---

## Cara tercepat (1 Langkah)

Setelah download/extract repo, tinggal jalankan script entry point untuk download proxy:

- **Windows:** double-click `install.bat` (atau `python bundle.py --no-login`), atau:
  ```cmd
  install.bat
  ```
- **macOS / Linux:**
  ```bash
  chmod +x install.sh && ./install.sh
  ```

*(Catatan: script bundle secara otomatis menarik binary `cli-proxy-api` terbaru ke folder `bin/` dan mengenerate `config.yaml`.)*

## Cara Pakai (Alur Unified)

Setelah setup awal, ikuti 2 langkah ini:

**1. Login Akun**
Lakukan ini sekali, atau kapan saja kamu mau nambah akun baru. Bisa dari command line:
```bash
python -m gravpool.cli add-account --auth-dir auth
```
*(Atau, kamu bisa menggunakan tombol Add Account langsung dari dashboard nantinya)*.

**2. Jalankan GravPool (Satu Perintah, Satu Port)**
Sekarang jalankan GUI:
```bash
python -m gravpool.cli gui --auth-dirs auth --port 8390
```

Ini akan memulai:
- **Dashboard GravPool:** Buka di browser http://127.0.0.1:8390
- **External Providers:** Bisa menambah API eksternal via Dashboard. (untuk kelola akun, kuota, combo).
- **Endpoint OpenAI-Compatible (Proxy):** Proxy API otomatis ter-embed dan dijalankan di background, bisa diakses dari AI client kamu di base URL `http://127.0.0.1:8390/v1` dengan API key `sk-local`.

---

## FAQ

**Apakah butuh VPS sama sekali?**
Tidak. Seluruh alur (login OAuth, refresh, kuota, rotasi, GUI, endpoint) jalan lokal, semuanya jadi satu di port 8390.

**Kenapa proxy nggak perlu dijalankan terpisah?**
Sekarang `gravpool.cli gui` menjalankan reverse-proxy secara internal ke *child process* `cli-proxy-api`. Artinya, kamu nggak perlu buka dua terminal lagi; semuanya cukup 1 command.

*(Note: Kalau kamu mau jalankan `cli-proxy-api` secara standalone tanpa dashboard, kamu masih bisa menjalankan `bin/cli-proxy-api --config config.yaml` seperti dulu).*

**Bagaimana pakai /v1 dari klien?**
Di client AI kamu (misal: OpenCode, Cursor, Cline):
- **Base URL:** `http://127.0.0.1:8390/v1`
- **API Key:** `sk-local`

**Akun Antigravity-nya dari mana?**
Akun Google biasa yang login ke Antigravity (Pro).
