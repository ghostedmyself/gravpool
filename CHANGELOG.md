# Changelog

Semua perubahan penting pada proyek ini dicatat di sini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/id/1.0.0/),
dan proyek ini mengikuti [Semantic Versioning](https://semver.org/lang/id/).

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
