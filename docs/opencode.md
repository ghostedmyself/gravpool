# Menggunakan GravPool dari OpenCode

Melalui setup satu-bundle, endpoint **OpenAI-compatible** sudah disiapkan untukmu dan terintegrasi di dalam dashboard GUI. OpenCode bisa connect langsung menggunakan provider bawaan `@ai-sdk/openai-compatible`. Proxy kini *embedded* di dalam proses GUI (tidak butuh dijalankan terpisah).

## Setup (Setelah Instalasi Bundle)

1. Pastikan OpenCode terinstall: `npm i -g opencode-ai@latest`
2. Pastikan dashboard GravPool sudah berjalan di terminalmu:
   ```bash
   python -m gravpool.cli gui --auth-dirs auth --port 8390
   ```
3. Atur kredensial. Contohnya lewat environment variable agar aman:
   ```bash
   export ANTIGRAVITY_BASE_URL="http://127.0.0.1:8390/v1"
   export ANTIGRAVITY_API_KEY="sk-local"
   ```

## Cara Pakai

```bash
# Sekali jalan
opencode run "Explain this codebase" --model antigravity/claude-sonnet-4-6

# Mode interaktif (pilih model dari TUI)
opencode --model antigravity/gemini-pro-agent
```

## Model yang Tersedia

Semua model yang dilaporkan oleh proxy `/v1/models` (baik dari Antigravity maupun External Providers). Contohnya:
- `claude-sonnet-4-6`, `claude-opus-4-6-thinking`
- `gemini-pro-agent`, `gemini-3.1-pro-low`, `gemini-3.7-flash-high`, dll.
- `gpt-oss-120b-medium`

## Kenapa ini berjalan lancar?

OpenCode menggunakan `@ai-sdk/openai-compatible` yang hanya butuh `baseURL` dan `apiKey`. `cli-proxy-api` melayani permintaan chat completions di rute `/v1`. Di belakang layar, **GravPool** otomatis menangani refresh akun, kuota, dan gateway. Semuanya sudah terintegrasi dan siap pakai berkat alur satu-bundle.
