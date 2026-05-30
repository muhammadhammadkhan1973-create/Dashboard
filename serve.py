"""
Local dashboard server — injects ANTHROPIC_API_KEY into index.html at runtime.
Run: python serve.py
Then open: http://localhost:8000
The API key is NEVER written to disk or committed to git.
"""

import os
import http.server
import socketserver
import urllib.parse

PORT = 8000
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

if not API_KEY:
    print("WARNING: ANTHROPIC_API_KEY not set. IM3 scoring will fall back to claude.ai.")
    print("  Set it with:  export ANTHROPIC_API_KEY=sk-ant-...")
else:
    print(f"  API key loaded: {API_KEY[:12]}...{API_KEY[-4:]}")

PLACEHOLDER = "/* __IM3_API_KEY_PLACEHOLDER__ */"
INJECTION   = f"const IM3_API_KEY = '{API_KEY}';"


class DashboardHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        # Only intercept index.html — serve everything else (data.json, etc.) normally
        path = urllib.parse.urlparse(self.path).path
        if path in ('/', '/index.html', ''):
            self.serve_injected_html()
        else:
            super().do_GET()

    def serve_injected_html(self):
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                content = f.read()

            # Inject API key constant into the script
            if PLACEHOLDER in content:
                content = content.replace(PLACEHOLDER, INJECTION)
            else:
                # Fallback: inject just before closing </script>
                content = content.replace(
                    '</script>\n</body>',
                    f'{INJECTION}\n</script>\n</body>'
                )

            encoded = content.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(encoded)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(encoded)
        except FileNotFoundError:
            self.send_error(404, 'index.html not found')

    def log_message(self, fmt, *args):
        # Suppress per-request logs — just show startup
        pass


print(f"\nDashboard running at http://localhost:{PORT}")
print("Press Ctrl+C to stop.\n")

with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
    httpd.serve_forever()
