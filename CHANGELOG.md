# Changelog

Semua perubahan penting pada proyek ini dicatat di sini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/id/1.0.0/),
dan proyek ini mengikuti [Semantic Versioning](https://semver.org/lang/id/).

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
