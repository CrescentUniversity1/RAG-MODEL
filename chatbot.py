import sqlite3

def get_faq_answer(user_question):
    conn = sqlite3.connect("university_chatbot.db")
    cursor = conn.cursor()

    # Simple search (can be improved with NLP later)
    cursor.execute("SELECT answer FROM faqs WHERE question LIKE ?", (f"%{user_question}%",))
    result = cursor.fetchone()

    conn.close()
    return result[0] if result else "Sorry, I don’t have an answer for that yet."

def get_course_info(course_code):
    conn = sqlite3.connect("university_chatbot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT title, description, credits FROM courses WHERE code = ?", (course_code,))
    result = cursor.fetchone()

    conn.close()
    if result:
        return f"{course_code} - {result[0]} ({result[2]} credits)\nDescription: {result[1]}"
    return "Course not found."

# Example usage
if __name__ == "__main__":
    print("Q: How do I apply for transcripts?")
    print("Bot:", get_faq_answer("apply for transcripts"))

    print("\nQ: Tell me about CSC101")
    print("Bot:", get_course_info("CSC101"))
