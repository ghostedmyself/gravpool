# Instalasi di laptop (tanpa VPS)

GravPool jalan **penuh di laptop lokal** — tidak butuh VPS.
Kredensial OAuth publik sudah built-in, jadi tidak ada file config yang harus
di-copy atau di-edit. Cukup Python 3.9+ dan satu command login.

**Yang kamu butuhkan:**

| Prasyarat | Untuk apa |
|---|---|
| Python 3.9+ | jalankan pool tool (stdlib only, tanpa dependency) |
| Akun Google (akses Antigravity) | login sekali, hasilkan auth file |
| `cli-proxy-api` *(opsional)* | hanya untuk endpoint OpenAI-compatible |

---

## Cara tercepat (satu command)

Setelah download/extract repo, tinggal:

- **Windows:** double-click `install.bat`, atau:
  ```cmd
  install.bat
  ```
- **macOS / Linux:**
  ```bash
  chmod +x install.sh && ./install.sh
  ```

Script ini cek Python, lalu langsung buka browser untuk login Google.
Ulangi untuk tiap akun yang mau ditambah.

---

## Manual (tanpa script)

### Windows

1. Download: `https://github.com/ghostedmyself/gravpool` → **Code → Download ZIP** → extract.
2. Pastikan Python: `python --version` (kalau belum: python.org/downloads, centang *Add Python to PATH*).
3. Login akun:
   ```cmd
   python -m gravpool.cli add-account --auth-dir auth
   ```
   Browser kebuka → login Google → consent → auth file tersimpan otomatis.
   (Headless: tambah `--no-browser`, lalu buka URL yang dicetak.)
4. Jalankan:
   ```cmd
   python -m gravpool.cli status --auth-dirs auth
   python -m gravpool.cli quota  --auth-dirs auth
   python -m gravpool.cli gui    --auth-dirs auth
   ```
   Dashboard: http://127.0.0.1:8390

### macOS / Linux

```bash
git clone https://github.com/ghostedmyself/gravpool.git
cd gravpool

# login akun (bisa diulang untuk banyak akun):
python3 -m gravpool.cli add-account --auth-dir auth

# jalankan:
python3 -m gravpool.cli status --auth-dirs auth
python3 -m gravpool.cli gui    --auth-dirs auth   # → http://127.0.0.1:8390
```

---

## Kredensial OAuth (opsional)

Kredensial publik Antigravity sudah **built-in**, jadi kamu tidak perlu
copy/edit file. Kalau mau memakai client OAuth sendiri:

```bash
cp gravpool/_local_creds.py.example gravpool/_local_creds.py
# isi CLIENT_ID + CLIENT_SECRET
```

(atau export `ANTIGRAVITY_CLIENT_ID` / `ANTIGRAVITY_CLIENT_SECRET`)

---

## Combo model (fallback otomatis)

```bash
python -m gravpool.cli combo add coding gemini-2.5-pro claude-sonnet-4-6
python -m gravpool.cli combo resolve coding
```

---

## Opsional: endpoint OpenAI-compatible + OpenCode

Kalau mau pakai OpenCode (atau klien OpenAI lain) langsung di laptop:

1. Pasang `cli-proxy-api` (binary sesuai OS dari releases).
2. Buat config:
   ```yaml
   host: 127.0.0.1
   port: 8317
   auth-dir: ./auth
   api-keys: ["sk-local"]
   ```
3. Jalankan `cli-proxy-api --config config.yaml`
4. Arahkan OpenCode (`examples/opencode.json`), env:
   ```bash
   export ANTIGRAVITY_BASE_URL="http://127.0.0.1:8317/v1"
   export ANTIGRAVITY_API_KEY="sk-local"
   ```

Detail: [`docs/opencode.md`](opencode.md).

---

## FAQ

**Apakah butuh VPS sama sekali?** Tidak. Seluruh alur (login OAuth, refresh,
kuota, rotasi, GUI, endpoint) jalan lokal.

**Akun Antigravity-nya dari mana?** Akun Google biasa yang login ke
Antigravity (Pro). `add-account` menghasilkan auth file otomatis.