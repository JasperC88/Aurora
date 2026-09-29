"""
Tactical Radar Local Web Server for Project Aurora
Serves the real-map slippy map visualizer (CartoDB Dark tiles, OpenSky, ADS-B Exchange).
Usage:
    python3 -m aurora.visualization.tactical_server --port 8050
"""

import http.server
import socketserver
import os
import sys
import webbrowser
import argparse
import json
import logging
from ..ingestion.adsb_exchange import LiveADSBClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aurora.tactical_server")


class TacticalRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving the visualizer and providing backend API proxies."""

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html_path = os.path.join(
                os.path.dirname(__file__), "tactical_map.html"
            )
            with open(html_path, "rb") as f:
                self.wfile.write(f.read())
            return

        elif self.path.startswith("/api/adsb/taiwan"):
            # Proxy live ADS-B Exchange call from Python
            df = LiveADSBClient.fetch_adsb_exchange_radius(lat=23.5, lon=119.5, dist_nm=250)
            data = df.to_dict(orient="records")
            self.send_json_response({"ac": data})
            return

        elif self.path.startswith("/api/opensky/taiwan"):
            # Proxy live OpenSky call from Python
            df = LiveADSBClient.fetch_opensky_live_bbox(20.0, 26.0, 116.0, 124.0)
            data = df.to_dict(orient="records")
            self.send_json_response({"ac": data})
            return

        return super().do_GET()

    def send_json_response(self, obj):
        content = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def run_server(port: int = 8050, auto_open: bool = True):
    # Set CWD to directory of script
    handler = TacticalRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}"
        logger.info(f"Project Aurora Tactical Map Server running at: {url}")
        print(f"\n=======================================================")
        print(f"🚀 Project Aurora Tactical Radar Live Map: {url}")
        print(f"📡 Real Basemap: CartoDB Dark Matter / OSM")
        print(f"✈️  Feeds: ADS-B Exchange (readsb) & OpenSky Network")
        print(f"🎯 Boundary Layers: Taiwan ADIZ & GIUK Gap")
        print(f"=======================================================\n")
        if auto_open:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server shutting down.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aurora Tactical Radar Server")
    parser.add_argument("--port", type=int, default=8050, help="Local HTTP port")
    parser.add_argument("--no-open", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()
    run_server(port=args.port, auto_open=not args.no_open)
