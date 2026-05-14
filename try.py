from flask import Flask, render_template, make_response
import pdfkit
from PyPDF2 import PdfReader, PdfWriter
import io
import json

app = Flask(__name__)

# ---------------- DATA ---------------- #
value = """
{
  "name": "Allwin Joseph",
  "email": "allwinjoseph.2605@gmail.com",
  "phone": "+91-8122930388",
  "linkedin": "https://www.linkedin.com/in/allwin-joseph-0b03ba291",
  "github": "https://github.com/allwinjoseph26",
  "profile_summary": "Artificial Intelligence and Data Science undergraduate with hands-on experience in machine learning, deep learning, and NLP. Skilled in building end-to-end ML solutions involving data preprocessing, feature engineering, model development, and evaluation. Developed real-world projects including student risk classification, skin disease prediction using computer vision, and fake news detection using Bi-LSTM models. Proficient in Python, SQL, Django, and data visualization tools, with a strong track record in hackathons and competitive problem-solving environments.",
  "functional_areas": ["Machine Learning", "Deep Learning", "Prompt Engineering", "Data Visualization", "Data Preprocessing"],
  "technical_skills": ["Programming: Python, SQL","Data Handling & Analysis: Pandas, Excel","Machine Learning: Model building, classification algorithms, data preprocessing, evaluation metrics","Backend Development: Django","Project Mangement: Notion, Azure Boards"],
  "project1_title": "Student Risk Classification System",
  "project1_duration": "09/2025 – 09/2025",
  "project1_points": ["Identified academically at-risk students using key performance indicators", "Developed machine learning model to predict student risk levels", "Performed data preprocessing, feature engineering, and model evaluation", "Enabled early academic interventions to improve student success outcomes"],
  "project2_title": "Skin Disease Prediction using Machine Learning",
  "project2_duration": "11/2024 – 11/2024",
  "project2_points": ["Built image-based classification model for skin diseases", "Processed and cleaned dermatology image datasets effectively", "Trained and validated model for reliable disease detection", "Improved diagnostic accuracy using computer vision techniques"],
  "project3_title": "Fake News Detection",
  "project3_duration": "10/2025 – 11/2025",
  "project3_points": ["Built Bi-LSTM model for fake news detection", "Analyzed contextual text patterns bidirectionally", "Applied NLP preprocessing and feature engineering", "Achieved 90–97% accuracy using TensorFlow"],
  "achievements": [
    "Won multiple prizes in hackathons and coding competitions",
    "Shortlisted among the Top 150 teams in Smart India Hackathon (SIH) 2025",
    "Recognized for consistent performance in technical and problem-solving events"
  ],
  "education": {
    "degree": "Bachelor of Technology [B.Tech] in Artificial Intelligence and Data Science",
    "duration": "08/2023 – Present",
    "institute": "Rajalakshmi Engineering College"
  }
}
"""

RESUME_DATA = json.loads(value)

# ---------------- ROUTE ---------------- #
@app.route("/")
def generate_pdf():
    # Render HTML
    html = render_template("allwin.html", data=RESUME_DATA)

    # Generate PDF
    pdf_bytes = pdfkit.from_string(html, False)

    # Keep only first page (optional)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    writer.add_page(reader.pages[0])

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)

    response = make_response(output.read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=resume.pdf"
    return response

if __name__ == "__main__":
    app.run(debug=True)