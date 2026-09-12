"""
server.py — Локальный HTTP бэкенд для Telegram Mini App «Поступашки».
Запуск: python server.py
Порт: 8000
"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

class PostupashkiBackendHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/metrics':
            if os.path.exists('metrics.json'):
                with open('metrics.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_error(404, "metrics.json not found. Run pipeline.py first.")
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/optimize':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            req = json.loads(body.decode('utf-8'))
            budget = float(req.get('budget', 300000))

            with open('metrics.json', 'r', encoding='utf-8') as f:
                metrics = json.load(f)
            mults = metrics.get('empirical_multipliers', {})
            
            m_bigtech = mults.get('camp_bigtech_internships', 17.7746)
            m_pro = mults.get('camp_pro_ai_ml', 8.6216)
            m_start = mults.get('camp_start_discount_55', 18.4136)
            m_nosql = mults.get('camp_free_analytics_nosql', 7.4582)
            m_ext = 4.20

            b_start = min(budget * 0.15, 60000.0)
            b_nosql = max(budget * 0.08, 15000.0)
            b_ext = max(budget * 0.04, 10000.0)

            remaining = budget - (b_start + b_nosql + b_ext)
            b_bigtech = remaining * 0.60
            b_pro = remaining * 0.40

            inc_revenue = (
                (b_bigtech * m_bigtech) +
                (b_pro * m_pro) +
                (b_start * m_start) +
                (b_nosql * m_nosql) +
                (b_ext * m_ext)
            )
            profit = inc_revenue - budget
            overall_romi = (profit / budget) * 100

            resp = {
                'total_budget': budget,
                'forecast_incremental_revenue': round(inc_revenue, 2),
                'forecast_profit': round(profit, 2),
                'forecast_romi_percent': round(overall_romi, 1),
                'split': [
                    {'name': '1. BigTech стажировки', 'budget': round(b_bigtech), 'share': f"{b_bigtech/budget*100:.1f}%", 'multiplier': round(m_bigtech, 2), 'role': 'Scale Up'},
                    {'name': '2. Флагманы ПРО & AI', 'budget': round(b_pro), 'share': f"{b_pro/budget*100:.1f}%", 'multiplier': round(m_pro, 2), 'role': 'Cash Core'},
                    {'name': '3. Распродажа СТАРТ -55%', 'budget': round(b_start), 'share': f"{b_start/budget*100:.1f}%", 'multiplier': round(m_start, 2), 'role': 'Cap (Лимит)'},
                    {'name': '4. Лид-магниты NoSQL', 'budget': round(b_nosql), 'share': f"{b_nosql/budget*100:.1f}%", 'multiplier': round(m_nosql, 2), 'role': 'ToFu Feed'},
                    {'name': '5. Внешние посевы', 'budget': round(b_ext), 'share': f"{b_ext/budget*100:.1f}%", 'multiplier': round(m_ext, 2), 'role': 'Testing'}
                ],
                'data_source': 'Generated dynamically by server.py using pipeline.py empirical multipliers'
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_error(404)

def run(port=8000):
    server = HTTPServer(('0.0.0.0', port), PostupashkiBackendHandler)
    print(f"Server running on http://localhost:{port}")
    server.serve_forever()

if __name__ == '__main__':
    run()
