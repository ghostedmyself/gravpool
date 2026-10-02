# Changelog

Semua perubahan penting pada proyek ini dicatat di sini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/id/1.0.0/),
dan proyek ini mengikuti [Semantic Versioning](https://semver.org/lang/id/).

## [1.0.0] - 2026-10-02

Public release — instalasi satu-perintah & dokumentasi profesional.

### Ditambahkan
- Instalasi **satu-perintah** via `curl -LsSf …/install.sh | bash` — install ke
  `~/.local/share/gravpool`, launcher `gravpool` di PATH, otomatis fetch proxy binary.
- README ditulis ulang untuk rilis publik (one-command install, feature bullets,
  struktur bersih tanpa bagian duplikat).

### Dihapus
- Subcommand CLI `login-binary` (kode lama yang tidak diperlukan).
- Semua referensi stale (`rotate.py`, `rotasi`) dari kode & dokumentasi.

### Diubah
- Bump versi ke **1.0.0**.

## [0.4.3] - 2026-10-02

### Dihapus
- `rotate.py` — kode mati (round-robin rotator) yang tidak pernah dipakai internal; semua referensi dihapus dari README.
- Subcommand CLI `login-binary` dari docstring usage.

### Diubah
- `cli.py` — docstring usage dirapikan agar akurat dengan subcommand yang ada.

## [0.4.2] - 2026-10-02

### Ditambahkan
- Desain UI Obsidian/Black-Gold yang baru untuk Dashboard.
- Provider Auto-Detect: Tombol Test Connection untuk otomatis fetch `/models` dari provider eksternal.
- Quota Grouping: Pengelompokan kuota model berdasarkan tier (2-3 bar) menggantikan bar terpisah yang panjang.

## [0.4.1] - 2026-10-02

### Ditambahkan
- External Providers: Mendukung penambahan API endpoint eksternal ke dalam pool gateway `sk-local`. Request dirouting otomatis berdasarkan nama model.
- Auth Verify: Pengetesan token otomatis ke API quota pasca callback OAuth (status 'verified, N models').
- Token Refresh Countdown: Dashboard kini menampilkan indikator sisa waktu expiry tiap akun (e.g., 'refresh in 35m').

## [0.4.0] - 2026-10-01

### Ditambahkan
- Endpoint proxy terintegrasi langsung di dalam `gravpool.cli gui` lewat reverse-proxy streaming di `/v1`.
- Satu perintah, satu port (`8390` default) untuk UI dashboard dan OpenAI-compatible endpoint secara bersamaan.
- UI redesign penuh dengan fitur toggle enable/disable akun, dan status proxy + `add-account` langsung dari dalam dashboard.

### Diubah
- Alur bundle disesuaikan untuk mengarahkan pengguna hanya pada satu perintah jalan `python -m gravpool.cli gui`.

## [0.3.0] - 2026-10-01

### Ditambahkan
- Alur instalasi satu-bundle (`bundle.py`, `install.sh`, `install.bat`) yang menyatukan login akun, download `cli-proxy-api`, dan pembuatan `config.yaml` otomatis.
- Opsi bypass `--no-login` dan `--no-proxy` pada script bundle.

### Diubah
- Pembaruan dokumentasi (README, install.md, opencode.md) menjadi flow instalasi 1-langkah dan penambahan referensi endpoint OpenAI-compatible lokal secara eksplisit.

## [0.2.0] - 2026-10-01

### Ditambahkan
- `add-account` — login akun baru satu-command lewat browser consent (tanpa
  binary CLIProxyAPI), dengan local callback server dan `--no-browser` untuk
  mode headless.
- `combo` — model virtual `fallback` / `fusion` (`list` / `add` / `rm` /
  `resolve`) dengan resolver yang melewati model yang kuota-nya habis.
- Dashboard web: kelola combo (CRUD + resolve) dan UI yang di-polish
  (palet gelap `#0b0e14`, aksen teal, aksesibilitas, tanpa dependency).
- Modul `login_flow.py` dan `combo.py`.

### Diubah
- README dan `docs/install.md` diperbarui untuk mencerminkan alur login baru
  tanpa binary.

## [0.1.0] - 2026-10-01

### Ditambahkan
- Rilis awal: pool kredensial OAuth Antigravity.
- `status` / `quota` / `refresh` / `gui` / `login-binary`.
- Rotasi round-robin, refresh token otomatis, snapshot kuota, dashboard web
  zero-dependency.
