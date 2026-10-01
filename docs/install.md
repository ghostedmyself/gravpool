# Instalasi di laptop (tanpa VPS)

`antigravity-pool` bisa jalan **penuh di laptop lokal** — tidak butuh VPS.
Satu-satunya syarat adalah punya **auth file** (kredensial OAuth akun
Antigravity), dan auth file itu bisa dibuat langsung di laptop pakai browser
(justru lebih gampang daripada di server headless).

**Yang kamu butuhkan:**

| Prasyarat | Untuk apa |
|---|---|
| Python 3.9+ | jalankan pool tool (stdlib only) |
| auth file (`antigravity-*.json`) | kredensial akun — login baru **atau** copy dari VPS |
| `cli-proxy-api` *(opsional)* | tambah akun baru & endpoint OpenAI-compatible |

---

## Windows

### 1. Download repo

Paling gampang tanpa git: buka
`https://github.com/ghostedmyself/antigravity-pool` → **Code → Download ZIP**
→ extract. (Atau `git clone` jika git sudah ada.)

### 2. Pastikan Python terpasang

```cmd
python --version
```

Kalau belum ada: https://www.python.org/downloads/ → centang *"Add Python to PATH"* saat install.

### 3. Setup kredensial OAuth (sekali)

```cmd
cd antigravity-pool
copy antigravity\_local_creds.py.example antigravity\_local_creds.py
```

Edit `antigravity\_local_creds.py`, isi `CLIENT_ID` dan `CLIENT_SECRET`.
(Nilai-nya publik — lihat README bagian **Catatan**.)

### 4. Siapkan auth file

**Opsi A — login akun baru di laptop (disarankan):**

1. Download binary: https://github.com/router-for-me/CLIProxyAPI/releases →
   `CLIProxyAPI_*_windows_amd64.zip` → extract
2. Jalankan flow login:
   ```cmd
   cli-proxy-api.exe --config config.yaml --antigravity-login
   ```
   Browser kebuka → login Google → consent → auth file tersimpan otomatis.

**Opsi B — copy dari VPS:**

```cmd
scp root@VPS-IP:/root/.cli-proxy-api/antigravity-*.json auth\
```

### 5. Jalankan

```cmd
python -m antigravity.cli status --auth-dirs auth
python -m antigravity.cli quota  --auth-dirs auth
python -m antigravity.cli gui    --auth-dirs auth
```

Buka `http://127.0.0.1:8390` di browser untuk dashboard.

---

## macOS / Linux

```bash
git clone https://github.com/ghostedmyself/antigravity-pool.git
cd antigravity-pool
pip install -e .                              # opsional

cp antigravity/_local_creds.py.example antigravity/_local_creds.py
# isi CLIENT_ID + CLIENT_SECRET

# auth file: login baru (binary mac/linux dari releases) atau copy dari VPS
scp root@VPS-IP:/root/.cli-proxy-api/antigravity-*.json ./auth/

python -m antigravity.cli status --auth-dirs ./auth
python -m antigravity.cli gui    --auth-dirs ./auth
```

---

## Opsional: endpoint OpenAI-compatible + OpenCode di laptop

Kalau mau pakai OpenCode (atau klien OpenAI lain) langsung di laptop:

1. Pasang `cli-proxy-api` (binary sesuai OS dari releases).
2. Buat config:
   ```yaml
   # config.yaml
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
5. Pakai:
   ```bash
   opencode run "..." --model antigravity/claude-sonnet-4-6
   ```

Detail selengkapnya: [`docs/opencode.md`](opencode.md).

---

## FAQ

**Apakah butuh VPS sama sekali?** Tidak. Seluruh alur (login OAuth, refresh,
kuota, rotasi, GUI, endpoint) jalan lokal. VPS cuma dipakai kalau kamu ingin
auth file yang sudah ada di server dipakai dari mana pun tanpa copy.

**Akun Antigravity-nya dari mana?** Akun Google biasa yang login ke
Antigravity (Pro). Login via `--antigravity-login` menghasilkan auth file
secara otomatis.