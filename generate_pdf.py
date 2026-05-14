import json
import pdfkit
from flask import Flask, render_template
import io
import shutil
import subprocess
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter

app = Flask(__name__, template_folder='templates')

OUTPUT_FILE = 'resume_one_page.pdf'

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

def write_pdf_with_chrome(rendered, output_path):
    html_path = Path('rendered_resume.html').resolve()
    html_path.write_text(rendered, encoding='utf-8')

    chrome = find_chrome()
    if not chrome:
        raise RuntimeError('wkhtmltopdf is missing and Chrome/Edge was not found for fallback PDF generation.')

    profile_dir = Path('chrome-profile').resolve()
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
            f'--print-to-pdf={Path(output_path).resolve()}',
            html_path.as_uri(),
        ],
        check=True,
    )

import sys

def generate():
    # Allow specifying input and output files from CLI
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'dhanush.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'resume_one_page.pdf'
    
    try:
        print(f"Reading data from {input_file}...")
        # Load the updated details
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Render the template
        with app.app_context():
            rendered = render_template('template.html', data=data)
        
        if shutil.which('wkhtmltopdf'):
            full_pdf = pdfkit.from_string(rendered, False, options={"enable-local-file-access": ""})
            
            # Slice to only first page (as done in app.py)
            pdf_reader = PdfReader(io.BytesIO(full_pdf))
            pdf_writer = PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[0])
            
            with open(output_file, 'wb') as f:
                pdf_writer.write(f)
        else:
            write_pdf_with_chrome(rendered, output_file)
            
        print(f"Successfully generated: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Install wkhtmltopdf or Chrome/Edge to generate the PDF.")

if __name__ == "__main__":
    generate()
