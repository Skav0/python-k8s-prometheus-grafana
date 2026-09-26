import time
import requests
from flask import Flask, Response, request, render_template_string
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- PROMETHEUS METRICS ---
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['endpoint']
)

# --- HELPER FUNCTIONS ---
def ip_to_flag_emoji(country_code):
    """Converts 2-letter country code (e.g., 'US', 'TN') into flag emoji."""
    if not country_code or len(country_code) != 2:
        return "🌐"
    return chr(ord(country_code[0].upper()) + 127397) + chr(ord(country_code[1].upper()) + 127397)

def get_client_ip():
    """Extracts client IP, respecting X-Forwarded-For headers when behind Ingress/Proxy."""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    return request.remote_addr

# --- ROUTES ---
@app.route('/')
def index():
    start_time = time.time()
    endpoint = '/'
    
    client_ip = get_client_ip()
    country_code = "UNKNOWN"
    flag = "🌐"

    try:
        # Query free IP geolocation API
        # (For local testing on '127.0.0.1', ip-api resolves your public IP automatically)
        query_ip = "" if client_ip in ["127.0.0.1", "::1"] else client_ip
        res = requests.get(f"http://ip-api.com/json/{query_ip}?fields=status,countryCode,query", timeout=3)
        
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                country_code = data.get("countryCode", "UNKNOWN")
                client_ip = data.get("query", client_ip)
                flag = ip_to_flag_emoji(country_code)
                
        status_code = '200'
    except Exception:
        status_code = '500'

    # Increment Prometheus metrics
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint, status_code=status_code).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start_time)

    # HTML Output
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Visitor Flag IP</title>
        <style>
            body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #121212; color: white; margin: 0; }
            .card { text-align: center; background: #1e1e1e; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
            .flag { font-size: 6rem; margin: 0; }
            .ip { font-size: 1.2rem; color: #aaa; margin-top: 0.5rem; }
        </style>
    </head>
    <body>
        <div class="card">
            <p class="flag">{{ flag }}</p>
            <h2>Country: {{ country_code }}</h2>
            <p class="ip">Your IP: {{ client_ip }}</p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, flag=flag, country_code=country_code, client_ip=client_ip), int(status_code)

@app.route('/metrics')
def metrics():
    """Prometheus Scrape Endpoint"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)