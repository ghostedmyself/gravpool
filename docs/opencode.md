# Menggunakan GravPool dari OpenCode

Melalui setup satu-bundle, endpoint **OpenAI-compatible** sudah disiapkan untukmu lewat `cli-proxy-api`. OpenCode bisa connect langsung menggunakan provider bawaan `@ai-sdk/openai-compatible`.

## Setup (Setelah Instalasi Bundle)

1. Pastikan OpenCode terinstall: `npm i -g opencode-ai@latest`
2. Pastikan proxy GravPool sudah berjalan di terminalmu:
   ```bash
   bin/cli-proxy-api --config config.yaml
   ```
   *(Proxy ini otomatis dibuat saat kamu menjalankan `install.sh` atau `bundle.py`).*
3. Atur kredensial. Contohnya lewat environment variable agar aman:
   ```bash
   export ANTIGRAVITY_BASE_URL="http://127.0.0.1:8317/v1"
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

Semua model yang dilaporkan oleh proxy `/v1/models`. Contohnya:
- `claude-sonnet-4-6`, `claude-opus-4-6-thinking`
- `gemini-pro-agent`, `gemini-3.1-pro-low`, `gemini-3.7-flash-high`, dll.
- `gpt-oss-120b-medium`

## Kenapa ini berjalan lancar?

OpenCode menggunakan `@ai-sdk/openai-compatible` yang hanya butuh `baseURL` dan `apiKey`. `cli-proxy-api` melayani permintaan chat completions di rute `/v1`. Di belakang layar, **GravPool** otomatis menangani rotasi akun, kuota, dan auto-refresh. Semuanya sudah terintegrasi dan siap pakai berkat alur satu-bundle.
