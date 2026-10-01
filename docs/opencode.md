# Using the pool from OpenCode

The pool doesn't expose Antigravity's raw API — it exposes an
**OpenAI-compatible** endpoint through `cli-proxy-api`. OpenCode connects to
it with the built-in `@ai-sdk/openai-compatible` provider. No plugin needed.

## One-time setup

1. Install OpenCode: `npm i -g opencode-ai@latest`
2. Run CLIProxyAPI in front of your auth dir (see README "Pairing with
   CLIProxyAPI"). It listens on `http://127.0.0.1:8317/v1`.
3. Copy [`examples/opencode.json`](../examples/opencode.json) to your project
   root (or merge its `provider` block into your existing config).

## Configure credentials

The example reads from env vars so the key never lands in git:

```bash
export ANTIGRAVITY_BASE_URL="http://127.0.0.1:8317/v1"
export ANTIGRAVITY_API_KEY="mrt_…"   # api-key from /opt/cliproxy-config.yaml
```

## Use it

```bash
# one-shot
opencode run "Explain this codebase" --model antigravity/claude-sonnet-4-6

# interactive (pick the model from the TUI, or force it)
opencode --model antigravity/gemini-pro-agent
```

## Available models

Everything the proxy's `/v1/models` reports — as of writing:

- `claude-sonnet-4-6`, `claude-opus-4-6-thinking`
- `gemini-pro-agent`, `gemini-3-flash`, `gemini-3.1-pro-low`,
  `gemini-3.1-flash-lite`, `gemini-3.5-flash-lite`, `gemini-3.6-flash-high`,
  `gemini-3.7-flash-high`, `gemini-3.8-flash-high`, `gemini-3.1-flash-image`
- `gpt-oss-120b-medium`

Refresh the list with:

```bash
curl -s http://127.0.0.1:8317/v1/models -H "Authorization: Bearer $ANTIGRAVITY_API_KEY" | python3 -c "import sys,json; print('\n'.join(m['id'] for m in json.load(sys.stdin)['data']))"
```

## Why this works

OpenCode's `@ai-sdk/openai-compatible` provider only needs `baseURL` +
`apiKey`; CLIProxyAPI speaks chat completions on `/v1`, which the Antigravity
(Cloud Code) backend serves through its OAuth accounts. Your repo's
`antigravity-pool` handles the account lifecycle (refresh/quota/rotation)
behind the scenes — OpenCode just sees a normal OpenAI endpoint.