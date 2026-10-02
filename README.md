<h1 align="center">GravPool</h1>

<p align="center">
  <b>Satu perintah — semua akun Google Antigravity kamu jadi satu gateway AI.</b><br>
  Kelola akun · pantau kuota · route ke provider lain · tanpa ribet
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/dependencies-none-0f766e" alt="No dependencies">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT">
</p>

---

## GravPool itu apa?

Punya beberapa akun Google Antigravity Pro (yang punya kuota gratis buat model AI)?
Males buka-buka tiap akun buat cek sisa kuota, refresh token yang expired, atau
ganti-ganti model?

**GravPool menggabungkan semua akun itu jadi satu titik.** Sekali setup, semua
akun dikelola dari satu dashboard web: kuota live, token otomatis ke-refresh,
model langsung siap dipakai. Hasilnya satu endpoint `http://127.0.0.1:8390/v1`
yang bisa dipasang di aplikasi AI apa pun — OpenCode, Cursor, Cline, apapun.

Tidak perlu install apa-apa selain Python. Tanpa database, tanpa dependency.

---

## Instalasi (sekitar 1 menit)

Butuh: **Python 3.9+** dan **Git**. Cek dulu:

```bash
python3 --version   # harus 3.9 ke atas
git --version
```

Lalu:

```bash
curl -LsSf https://raw.githubusercontent.com/ghostedmyself/gravpool/main/install.sh | bash
gravpool gui --port 8390
```

Buka **http://127.0.0.1:8390** di browser — dashboard sudah jalan.

> Mau pakai `uv` (lebih cepat)? Ganti perintah pertama dengan:
> `uv tool install gravpool` (install uv dulu: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

---

## Langkah pertama

1. **Add Account** — login satu akun Google Antigravity. Sekali aja, lewat browser.
2. **Add Provider** — (opsional) kalau punya API key lain seperti OpenAI/OpenRouter, tinggal isi base URL + key. Modelnya otomatis dideteksi.
3. **Pakai endpoint-nya** — di aplikasi AI kamu, isi:

```
Base URL : http://127.0.0.1:8390/v1
API Key  : sk-local
```

Selesai. Semua akun kamu jalan di belakang satu alamat.

---

## Fitur

- **Satu endpoint, semua akun** — gabung banyak akun Antigravity jadi satu gateway
- **Refresh token otomatis** — token yang expired di-refresh sendiri, tanpa sentuh manual
- **Kuota live** — sisa kuota tiap akun langsung kelihatan di dashboard
- **Provider eksternal** — tambahkan API key lain (OpenAI, OpenRouter, endpoint custom) di gateway yang sama
- **Combo routing** — gabungkan beberapa model jadi satu; kalau satu kehabisan kuota otomatis pindah ke cadangan
- **Dashboard web** — semua kontrol dari browser, tidak perlu hafal perintah

---

## Perintah CLI

Semua bisa lewat dashboard, tapi kalau suka terminal:

```bash
gravpool gui           # jalankan dashboard + gateway
gravpool status        # status token tiap akun
gravpool quota         # cek kuota semua akun
gravpool refresh       # refresh token yang expired
gravpool add-account   # login akun Google baru
gravpool combo         # kelola combo model
```

---

## Update ke versi terbaru

```bash
curl -LsSf https://raw.githubusercontent.com/ghostedmyself/gravpool/main/install.sh | bash
```

Installer aman dijalankan ulang — data akun dan pengaturanmu **tidak** ikut berubah.

---

## Struktur proyek

```
gravpool/
├── gravpool/            # kode inti
│   ├── static/          #   dashboard web (HTML/CSS/JS)
│   ├── web.py           #   server + gateway /v1
│   ├── providers.py     #   provider eksternal
│   ├── quota.py         #   cek kuota live
│   ├── oauth.py         #   login & refresh token
│   ├── login_flow.py    #   alur login via browser
│   ├── proxy.py         #   pengatur binary proxy
│   ├── combo.py         #   combo model
│   ├── store.py         #   penyimpanan akun
│   ├── constants.py     #   pengaturan umum
│   └── cli.py           #   perintah terminal
├── docs/                # panduan lengkap
├── examples/            # contoh konfigurasi
├── install.sh           # installer
└── bundle.py            # unduh binary pendukung
```

---

## Lisensi

[MIT](LICENSE) © 2026 Omni.labs
