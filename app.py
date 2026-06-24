from flask import Flask, render_template, make_response, request, jsonify, send_from_directory
# pyrefly: ignore [missing-import]
import pdfkit
# pyrefly: ignore [missing-import]
from PyPDF2 import PdfReader, PdfWriter
import io
import json
import shutil
import subprocess
from pathlib import Path
import tempfile
import os
import urllib.request

app = Flask(__name__, template_folder='templates')

def find_chrome():
    candidates = [
        shutil.which('chrome'),
        shutil.which('chrome.exe'),
        shutil.which('msedge'),
        shutil.which('msedge.exe'),
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None

def render_with_browserless(rendered, token):
    """Uses Browserless.io Cloud REST API to render PDF (ideal for Vercel/Serverless)."""
    url = f"https://production-sfo.browserless.io/pdf?token={token}"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "html": rendered,
        "options": {
            "printBackground": True,
            "format": "A4",
            "margin": {
                "top": "0.32in",
                "bottom": "0.32in",
                "left": "0.32in",
                "right": "0.32in"
            }
        }
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'), 
        headers=headers,
        method='POST'
    )
    
    with urllib.request.urlopen(req) as response:
        return response.read()

def render_with_chrome(rendered):
    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = Path(tmpdir) / "temp_resume.html"
        pdf_path = Path(tmpdir) / "temp_resume.pdf"
        
        html_path.write_text(rendered, encoding='utf-8')
        
        chrome = find_chrome()
        if not chrome:
            raise RuntimeError('wkhtmltopdf is missing and Chrome/Edge was not found for fallback PDF generation. On Vercel, configure BROWSERLESS_TOKEN env variable.')
            
        profile_dir = Path(tmpdir) / "profile"
        profile_dir.mkdir(exist_ok=True)
        
        subprocess.run(
            [
                chrome,
                '--headless=new',
                '--disable-gpu',
                '--no-sandbox',
                '--disable-crash-reporter',
                '--disable-breakpad',
                f'--user-data-dir={profile_dir}',
                '--no-pdf-header-footer',
                f'--print-to-pdf={pdf_path.resolve()}',
                html_path.as_uri(),
            ],
            check=True,
            capture_output=True
        )
        return pdf_path.read_bytes()

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/builder")
def builder():
    return render_template("index.html")

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('resume assests', filename)

@app.route("/preview", methods=["POST"])
def preview():
    payload = request.get_json()
    if not payload:
        return "Invalid JSON", 400
    
    if "data" in payload and isinstance(payload["data"], dict):
        parsed_dict = payload["data"]
    else:
        parsed_dict = payload

    try:
        rendered = render_template("template.html", data=parsed_dict)
        return rendered
    except Exception as e:
        return f"<div style='color:red; padding:20px; font-family:sans-serif;'>Error rendering preview: {str(e)}</div>", 500

@app.route("/pdf", methods=["POST"])
def generate_pdf():
    payload = request.get_json()

    if not payload:
        return jsonify({"error": "Invalid or missing JSON"}), 400
    
    # Extract data and user-chosen filename
    if "data" in payload and isinstance(payload["data"], dict):
        parsed_dict = payload["data"]
        filename = payload.get("filename", "resume_one_page.pdf")
    else:
        parsed_dict = payload
        filename = "resume_one_page.pdf"

    try:
        # Render HTML with Jinja2
        rendered = render_template("template.html", data=parsed_dict)

        # Determine generation pipeline
        token = os.environ.get("BROWSERLESS_TOKEN")
        
        if token:
            # Priority 1: Browserless Cloud (Great for serverless like Vercel)
            full_pdf = render_with_browserless(rendered, token)
        elif shutil.which('wkhtmltopdf'):
            # Priority 2: Local wkhtmltopdf
            full_pdf = pdfkit.from_string(rendered, False, options={"enable-local-file-access": ""})
        else:
            # Priority 3: Headless Chrome fallback (Windows dev)
            full_pdf = render_with_chrome(rendered)

        # Slice to only first page using PyPDF2
        pdf_reader = PdfReader(io.BytesIO(full_pdf))
        pdf_writer = PdfWriter()
        pdf_writer.add_page(pdf_reader.pages[0])

        output_stream = io.BytesIO()
        pdf_writer.write(output_stream)
        output_stream.seek(0)

        # Return sliced PDF as downloadable file with dynamic filename
        response = make_response(output_stream.read())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
        
    except Exception as e:
        return jsonify({"error": f"PDF Generation Failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)