/**
 * Nano Banana MCP connector (Cloudflare Worker).
 *
 * Remote MCP server (Streamable HTTP, JSON responses) exposing one tool, generate_image,
 * which calls Google's Gemini image model ("Nano Banana") with GEMINI_API_KEY, stores the
 * result in R2 and returns a public URL (served by this Worker at /img/<key>) plus a preview.
 *
 * Endpoint:  https://<worker>/mcp/<MCP_TOKEN>      (the token in the path is the password)
 * Images:    https://<worker>/img/<key>
 */
const PROTOCOL = "2025-06-18";
const API = "https://generativelanguage.googleapis.com/v1beta";
const RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"];

const TOOLS = [{
  name: "generate_image",
  description:
    "Generate (or edit) an image with Google's Nano Banana (Gemini image model). " +
    "Write the exact text you want rendered inside quotes in the prompt. Optionally pass reference image URLs " +
    "(e.g. a product photo to keep realistic, or an earlier image to edit). Returns a public image URL and a preview.",
  inputSchema: {
    type: "object",
    properties: {
      prompt: { type: "string", description: "Full description of the image, including any exact text to render." },
      aspect_ratio: { type: "string", enum: RATIOS, default: "4:5", description: "4:5 is best for Facebook feed posts, 9:16 for reels/stories." },
      image_size: { type: "string", enum: ["1K", "2K", "4K"], default: "2K" },
      reference_image_urls: { type: "array", items: { type: "string" }, maxItems: 6, description: "Optional public image URLs to use as references." },
      model: { type: "string", description: "Optional model override, e.g. gemini-3-pro-image." },
    },
    required: ["prompt"],
  },
}];

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const parts = url.pathname.split("/").filter(Boolean);

    if (parts[0] === "img" && parts[1] && req.method === "GET") {
      const obj = await env.IMAGES.get(parts.slice(1).join("/"));
      if (!obj) return new Response("not found", { status: 404 });
      return new Response(obj.body, {
        headers: { "content-type": obj.httpMetadata?.contentType || "image/png", "cache-control": "public, max-age=31536000, immutable" },
      });
    }

    if (parts[0] === "mcp") {
      if (!env.MCP_TOKEN || parts[1] !== env.MCP_TOKEN) return new Response("unauthorized", { status: 401 });
      if (req.method === "GET") return new Response("method not allowed", { status: 405, headers: { allow: "POST" } });
      if (req.method === "DELETE") return new Response(null, { status: 204 });
      if (req.method !== "POST") return new Response("method not allowed", { status: 405 });
      let body;
      try { body = await req.json(); } catch { return json(rpcError(null, -32700, "parse error")); }
      const batch = Array.isArray(body);
      const out = [];
      for (const msg of batch ? body : [body]) {
        const r = await handle(msg, env, url.origin);
        if (r) out.push(r);
      }
      if (!out.length) return new Response(null, { status: 202 });
      return json(batch ? out : out[0]);
    }

    return new Response("Nano Banana MCP connector is running.", { headers: { "content-type": "text/plain" } });
  },
};

async function handle(msg, env, origin) {
  const { id, method, params } = msg || {};
  const isNotification = id === undefined || id === null;
  try {
    switch (method) {
      case "initialize":
        return rpcResult(id, {
          protocolVersion: params?.protocolVersion || PROTOCOL,
          capabilities: { tools: { listChanged: false } },
          serverInfo: { name: "nanobanana", version: "1.0.0" },
          instructions: "Use generate_image to create marketing images with Nano Banana. Images are returned as public URLs.",
        });
      case "ping":
        return rpcResult(id, {});
      case "tools/list":
        return rpcResult(id, { tools: TOOLS });
      case "tools/call":
        if (params?.name !== "generate_image") return rpcError(id, -32602, `unknown tool ${params?.name}`);
        return rpcResult(id, await generateImage(params.arguments || {}, env, origin));
      default:
        if (isNotification) return null; // e.g. notifications/initialized
        return rpcError(id, -32601, `method not found: ${method}`);
    }
  } catch (e) {
    return rpcResult(id, { isError: true, content: [{ type: "text", text: `Error: ${e.message || e}` }] });
  }
}

async function generateImage(args, env, origin) {
  const prompt = String(args.prompt || "").trim();
  if (!prompt) throw new Error("prompt is required");
  const aspect = RATIOS.includes(args.aspect_ratio) ? args.aspect_ratio : "4:5";
  const size = ["1K", "2K", "4K"].includes(args.image_size) ? args.image_size : "2K";
  const model = args.model || env.MODEL || "gemini-nano-banana-2.1";
  const fallback = env.FALLBACK_MODEL || "gemini-2.5-flash-image";

  const refs = [];
  for (const u of (args.reference_image_urls || []).slice(0, 6)) {
    const r = await fetch(u);
    if (!r.ok) throw new Error(`could not fetch reference image ${u} (${r.status})`);
    refs.push({ mime: (r.headers.get("content-type") || "image/jpeg").split(";")[0], data: b64(await r.arrayBuffer()) });
  }

  const errors = [];
  let img = null, used = null;
  for (const [fn, m] of [[viaGenerateContent, model], [viaInteractions, model], [viaGenerateContent, fallback]]) {
    try { img = await fn(env, m, prompt, refs, aspect, size); if (img) { used = `${fn.name}:${m}`; break; } }
    catch (e) { errors.push(`${fn.name}(${m}): ${e.message}`); }
  }
  if (!img) throw new Error("image generation failed. " + errors.join(" | "));

  const ext = img.mime.includes("jpeg") ? "jpg" : img.mime.includes("webp") ? "webp" : "png";
  const key = `${new Date().toISOString().slice(0, 10)}/${crypto.randomUUID()}.${ext}`;
  const bytes = Uint8Array.from(atob(img.data), c => c.charCodeAt(0));
  await env.IMAGES.put(key, bytes, { httpMetadata: { contentType: img.mime } });
  const publicUrl = `${origin}/img/${key}`;

  const content = [{ type: "text", text: `Image URL: ${publicUrl}\nModel: ${used}\nAspect ratio: ${aspect}, size: ${size}, ${Math.round(bytes.length / 1024)} KB` }];
  if (bytes.length <= 4.5 * 1024 * 1024) content.push({ type: "image", data: img.data, mimeType: img.mime });
  return { content };
}

async function viaGenerateContent(env, model, prompt, refs, aspect, size) {
  const parts = [{ text: prompt }, ...refs.map(r => ({ inlineData: { mimeType: r.mime, data: r.data } }))];
  const res = await fetch(`${API}/models/${model}:generateContent`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-goog-api-key": env.GEMINI_API_KEY },
    body: JSON.stringify({
      contents: [{ role: "user", parts }],
      generationConfig: { responseModalities: ["IMAGE", "TEXT"], imageConfig: { aspectRatio: aspect, imageSize: size } },
    }),
  });
  const j = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`${res.status} ${j?.error?.message || ""}`.trim());
  return findImage(j);
}

async function viaInteractions(env, model, prompt, refs, aspect, size) {
  const input = refs.length
    ? [{ type: "text", text: prompt }, ...refs.map(r => ({ type: "image", mime_type: r.mime, data: r.data }))]
    : prompt;
  const res = await fetch(`${API}/interactions`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-goog-api-key": env.GEMINI_API_KEY },
    body: JSON.stringify({ model, input, response_format: { type: "image", mime_type: "image/png", aspect_ratio: aspect, image_size: size } }),
  });
  const j = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`${res.status} ${j?.error?.message || ""}`.trim());
  return findImage(j);
}

// Walk any response shape and return the first base64 image found.
function findImage(node, depth = 0) {
  if (!node || typeof node !== "object" || depth > 12) return null;
  const inline = node.inlineData || node.inline_data;
  if (inline?.data) return { data: inline.data, mime: inline.mimeType || inline.mime_type || "image/png" };
  if (typeof node.data === "string" && node.data.length > 1000 && (node.type === "image" || node.mime_type || node.mimeType))
    return { data: node.data, mime: node.mime_type || node.mimeType || "image/png" };
  for (const v of Array.isArray(node) ? node : Object.values(node)) {
    const f = findImage(v, depth + 1);
    if (f) return f;
  }
  return null;
}

function b64(buf) {
  let s = ""; const a = new Uint8Array(buf);
  for (let i = 0; i < a.length; i += 0x8000) s += String.fromCharCode.apply(null, a.subarray(i, i + 0x8000));
  return btoa(s);
}
const json = (o) => new Response(JSON.stringify(o), { headers: { "content-type": "application/json" } });
const rpcResult = (id, result) => ({ jsonrpc: "2.0", id, result });
const rpcError = (id, code, message) => ({ jsonrpc: "2.0", id, error: { code, message } });
