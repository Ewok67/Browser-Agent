#!/usr/bin/env python3
"""
AI Search Guard - Lokaler Server
Servet die Rule-Check API und die Blocked Page.
Ruft llama.cpp für LLM-Evaluierung auf.
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Pfade
BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "server" / "config.json"
BLOCKED_PAGE_DIR = BASE_DIR / "blocked-page"
RULES_PATH = BASE_DIR / "server" / "rules.json"
EXTENSION_RULES_PATH = BASE_DIR / "extension" / "rules-default.json"

DEFAULT_CONFIG = {
    "llama_host": "localhost",
    "llama_port": 8080,
    "server_port": 8081,
    "max_tokens": 16,
    "temperature": 0.0
}


class RuleChecker:
    def __init__(self):
        self.config = self._load_config()
        self.rules = self._load_rules()

    def _load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        return DEFAULT_CONFIG

    def _load_rules(self):
        if RULES_PATH.exists():
            with open(RULES_PATH) as f:
                return json.load(f)
        if EXTENSION_RULES_PATH.exists():
            with open(EXTENSION_RULES_PATH) as f:
                return json.load(f)
        return []

    def check_query(self, query: str) -> dict:
        """Sende Query an llama.cpp mit Regeln, gib Urteil zurück."""
        rules_text = "\n".join(f"- {r}" for r in self.rules)
        prompt = (
            "You are a strict search query filter. Classify this query based ONLY on the rules below.\n"
            "Reply with exactly one word: ALLOW, or BLOCK: <short reason>.\n\n"
            f"Rules:\n{rules_text}\n\n"
            f"Search query: {query}\n"
            "Classification:"
        )

        try:
            req_data = json.dumps({
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.config.get("max_tokens", 50),
                "temperature": self.config.get("temperature", 0.1)
            }).encode("utf-8")

            url = (f"http://{self.config['llama_host']}:"
                   f"{self.config['llama_port']}/v1/chat/completions")
            req = urllib.request.Request(
                url, data=req_data,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())

            content = result["choices"][0]["message"]["content"].strip()

            if content.upper().startswith("BLOCK"):
                reason = content.split(":", 1)[1].strip() if ":" in content else "Regelverstoß"
                return {"blocked": True, "reason": reason, "raw": content}
            return {"blocked": False, "raw": content}

        except urllib.error.URLError as e:
            return {"blocked": False, "error": f"llama.cpp nicht erreichbar: {e}"}
        except Exception as e:
            return {"blocked": False, "error": str(e)}


checker = RuleChecker()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok", "rules_count": len(checker.rules)})

        elif parsed.path == "/blocked":
            qs = urllib.parse.parse_qs(parsed.query)
            query = qs.get("query", [""])[0]
            reason = qs.get("reason", ["Regelverstoß"])[0]
            self._serve_blocked_page(query, reason)

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/check":
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))
            result = checker.check_query(data.get("query", ""))
            self._send_json(result)

        elif parsed.path == "/rules":
            length = int(self.headers.get("Content-Length", 0))
            rules = json.loads(self.rfile.read(length)).get("rules", [])
            with open(RULES_PATH, "w") as f:
                json.dump(rules, f, indent=2, ensure_ascii=False)
            checker.rules = rules
            self._send_json({"status": "ok", "rules_count": len(rules)})

        else:
            self._send_json({"error": "Not found"}, 404)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _serve_blocked_page(self, query, reason):
        html_path = BLOCKED_PAGE_DIR / "index.html"
        css_path = BLOCKED_PAGE_DIR / "styles.css"

        html = html_path.read_text(encoding="utf-8") if html_path.exists() else "<h1>Blocked</h1>"
        css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

        html = (html
                .replace("{{QUERY}}", query)
                .replace("{{REASON}}", reason)
                .replace("{{CSS}}", f"<style>{css}</style>"))

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


if __name__ == "__main__":
    port = checker.config.get("server_port", 8081)
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"🤖 AI Search Guard Server läuft auf http://localhost:{port}")
    print(f"   llama.cpp erwartet auf http://localhost:{checker.config['llama_port']}")
    print(f"   Regeln geladen: {len(checker.rules)}")
    print(f"   Blocked page: http://localhost:{port}/blocked")
    print("\nDrücke Ctrl+C zum Beenden\n")
    server.serve_forever()
