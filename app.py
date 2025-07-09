from flask import Flask, request, render_template_string
import google.generativeai as genai
import PyPDF2
import requests
from io import BytesIO
import re

app = Flask(__name__)

# ✅ Configure Gemini
genai.configure(api_key="AIzaSyBZMgmYKkduWGWp_USHQ4SsiPOw1glOCmg")

# ✅ Google Drive PDF link
pdf_drive_link = "https://drive.google.com/uc?export=download&id=1FNkl1Ny-mIKlxSLzWtwlUq-Hk9h4tD33"

# ✅ Function to extract PDF text
def extract_pdf_text(pdf_url):
    response = requests.get(pdf_url)
    pdf_file = BytesIO(response.content)
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# ✅ Load PDF on start
pdf_text = extract_pdf_text(pdf_drive_link)

# ✅ Load Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

# ✅ Web UI template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Strata Assistant</title>
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
        }
        .navbar {
            background-color: #2c3e50;
            color: #fff;
            padding: 15px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
        }
        .container {
    margin: 20px auto;       /* previously 50px */
    width: 60%;
    background-color: #ffffff;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

        h2 {
            text-align: center;
            color: #333;
            margin-bottom: 15px;
        }
        form {
            display: flex;
            justify-content: center;
            margin-bottom: 15px; /* reduced */
        }
        input[type="text"] {
            width: 70%;
            padding: 10px; /* reduced */
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-right: 8px;
        }
        input[type="submit"] {
            padding: 10px 16px; /* reduced */
            background-color: #2980b9;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        input[type="submit"]:hover {
            background-color: #3498db;
        }
        .qa-section {
    margin: 10px 0;         /* reduced vertical space above and below */
    background-color: #ecf0f1;
    padding: 12px 16px;     /* reduced padding */
    border-radius: 10px;
    line-height: 1.5;       /* slightly tighter line spacing */
    white-space: pre-wrap;
}

        .qa-block {
            margin-bottom: 10px; /* reduced */
        }
        .qa-text {
            text-align: justify;
            margin-top: 4px; /* reduced */
        }
    </style>
</head>
<body>

    <div class="navbar">Strata Assistant</div>

    <div class="container">
        <h2>Ask anything!</h2>
        <form method="post">
            <input type="text" name="question" placeholder="Type your question here..." required>
            <input type="submit" value="Ask">
        </form>

        {% if question and answer %}
        <div class="qa-section">
            <div class="qa-block">
                <strong>Question:</strong>
                <div class="qa-text">{{ question }}</div>
            </div>
            <div class="qa-block">
                <strong>Answer:</strong>
                <div class="qa-text">{{ answer }}</div>
            </div>
        </div>
        {% endif %}
    </div>

</body>
</html>
"""


# ✅ Route logic
@app.route("/", methods=["GET", "POST"])
def chatbot():
    answer = None
    question = None

    if request.method == "POST":
        question = request.form["question"]

        prompt = f"""
You are a helpful assistant. The following is extracted from a PDF document:

{pdf_text[:12000]}

Answer the question below based strictly on the document content, using plain text only.
Avoid repeating the question. Do not include HTML tags or extra numbering if already numbered.

Question: {question}
"""

        try:
            response = model.generate_content(prompt)
            answer = response.text

            # Strip HTML if any
            answer = re.sub(r'<[^>]+>', '', answer)

            # Clean and renumber lines
            lines = [line.strip() for line in answer.splitlines() if line.strip()]
            formatted = ""
            for i, line in enumerate(lines, start=1):
                if not re.match(r"^\d+\.", line):  # skip if already numbered
                    line = f"{i}. {line}"
                formatted += line + "\n"
            answer = formatted.strip()

        except Exception as e:
            answer = f"An error occurred: {str(e)}"

    return render_template_string(HTML_TEMPLATE, question=question, answer=answer)

# ✅ Run app
if __name__ == "__main__":
    app.run(debug=True)
