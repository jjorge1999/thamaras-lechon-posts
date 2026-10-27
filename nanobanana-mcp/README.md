# Nano Banana MCP connector

A Cloudflare Worker that lets Claude generate images with Google's Nano Banana (Gemini image model).
Images are stored in the R2 bucket `nanobanana-images` and served publicly at `/img/<key>` so Buffer can attach them.

Deploys automatically from GitHub Actions (`.github/workflows/deploy-nanobanana.yml`) when this folder changes,
or manually from the Actions tab ("Deploy Nano Banana connector" → Run workflow).

Repository secrets required: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `GEMINI_API_KEY`, `MCP_TOKEN`.

Connector URL to add in Claude (Settings → Connectors → Add custom connector):
`https://nanobanana-mcp.<your-subdomain>.workers.dev/mcp/<MCP_TOKEN>`
