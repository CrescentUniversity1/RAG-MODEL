import sqlite3

def insert_sample_data():
    conn = sqlite3.connect("university_chatbot.db")
    cursor = conn.cursor()

    # Departments
    cursor.execute("INSERT OR IGNORE INTO departments (name, description) VALUES (?, ?)",
                   ("Computer Science", "CS Department offers AI, ML, and Software courses."))

    # Staff
    cursor.execute("INSERT OR IGNORE INTO staff (name, email, role, department_id) VALUES (?, ?, ?, ?)",
                   ("Dr. John Smith", "john.smith@university.edu", "Lecturer", 1))

    # Courses
    cursor.execute("INSERT OR IGNORE INTO courses (code, title, description, credits, department_id) VALUES (?, ?, ?, ?, ?)",
                   ("CSC101", "Introduction to Computer Science", "Basics of computing and programming.", 3, 1))

    # FAQs
    cursor.execute("INSERT OR IGNORE INTO faqs (question, answer, category) VALUES (?, ?, ?)",
                   ("How do I apply for transcripts?", "You can apply online via the student portal.", "Administration"))

    conn.commit()
    conn.close()
    print("Sample data inserted!")

if __name__ == "__main__":
    insert_sample_data()
