from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

DB_NAME = "university_chatbot.db"

def get_faq_answer(user_question):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Search FAQ
    cursor.execute("SELECT answer FROM faqs WHERE question LIKE ?", (f"%{user_question}%",))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return None

def get_course_info(course_code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT title, description, credits FROM courses WHERE code = ?", (course_code,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return f"{course_code} - {result[0]} ({result[2]} credits)<br>Description: {result[1]}"
    return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_question = request.form.get("question", "").strip()

    # Try FAQs first
    answer = get_faq_answer(user_question)

    # If user asks about a course (basic detection)
    if not answer and user_question.upper().startswith("CSC"):
        answer = get_course_info(user_question.upper())

    # Default fallback
    if not answer:
        answer = "Sorry, I don’t have an answer for that yet."

    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(debug=True)
