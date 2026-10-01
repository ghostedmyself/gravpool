# Instalasi Satu-Bundle (Tanpa VPS)

GravPool sekarang hadir dalam alur satu-bundle via script `bundle.py`. Proses ini otomatis mendownload CLIProxyAPI, mengatur login Google, dan membuatkan `config.yaml`. Semuanya jalan penuh di laptop lokal.

**Yang kamu butuhkan:**
- Python 3.9+
- Akun Google (akses Antigravity)

---

## Cara tercepat (1 Langkah)

Setelah download/extract repo, tinggal jalankan script entry point:

- **Windows:** double-click `install.bat`, atau:
  ```cmd
  install.bat
  ```
- **macOS / Linux:**
  ```bash
  chmod +x install.sh && ./install.sh
  ```

### Apa yang bundle ini lakukan?
1. **Login Akun:** Membuka browser untuk otorisasi Google Antigravity dan menyimpan auth file di folder `auth/`.
2. **Download Proxy:** Otomatis menarik binary `cli-proxy-api` terbaru ke dalam folder `bin/`.
3. **Generate Config:** Membuat file `config.yaml` dengan setup standar (port 8317, key `sk-local`).

*(Catatan: kamu bisa bypass login dengan `--no-login` atau bypass download proxy dengan `--no-proxy` jika menjalankan `python bundle.py` manual).*

---

## Cara Pakai

Setelah instalasi selesai, kamu punya dua komponen utama:

**1. Dashboard GravPool (Manajemen Akun/Kuota)**
Jalankan di terminal:
```bash
python -m gravpool.cli gui --auth-dirs auth
```
Akses di browser: http://127.0.0.1:8390

**2. Endpoint OpenAI-Compatible (Proxy)**
Buka terminal baru, jalankan:
```bash
bin/cli-proxy-api --config config.yaml
```
Sekarang klien AI apa pun (seperti OpenCode) bisa connect ke:
- **Base URL:** `http://127.0.0.1:8317/v1`
- **API Key:** `sk-local`

---

## FAQ

**Apakah butuh VPS sama sekali?**
Tidak. Seluruh alur (login OAuth, refresh, kuota, rotasi, GUI, endpoint) jalan lokal.

**Akun Antigravity-nya dari mana?**
Akun Google biasa yang login ke Antigravity (Pro).

**Mau tambah akun lagi?**
Jalankan ulang `install.sh` / `install.bat`, atau manual:
`python -m gravpool.cli add-account --auth-dir auth`
