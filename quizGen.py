import streamlit as st
import pdfplumber
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
client = OpenAI()

st.set_page_config(page_title="Student-ia Quiz Generator", layout="centered")
st.title("📘 Welcome to Student-ia 👋")
st.markdown("Upload a PDF and get personalized quizzes with instant feedback.")

# Upload PDF
pdf_file = st.file_uploader("📤 Upload your study PDF", type=["pdf"])

# Input number of questions
num_questions = st.number_input("🔢 How many questions to generate?", min_value=1, max_value=20, value=5)

# Helper: Extract text from PDF
def extract_pdf_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text.strip()

# Generate quiz using LLM
if st.button("🚀 Generate Quiz") and pdf_file:
    with st.spinner("Analyzing your PDF and generating quiz..."):
        text = extract_pdf_text(pdf_file)
        if not text:
            st.error("❌ No readable text found in this PDF.")
            st.stop()

        prompt = f"""
You are a professional academic quiz generator.

Your task is to create exactly {num_questions} multiple-choice questions (MCQs) based ONLY on the study material provided below.

📌 Format Rules (Follow EXACTLY):
Each question must follow this structure:

Q1: [Full question text]  
A. [Option 1 text]  
B. [Option 2 text]  
C. [Option 3 text]  
D. [Option 4 text]  
Answer: [A/B/C/D]

✅ Requirements:
- Each question must have exactly **4** clearly written answer choices labeled **A.**, **B.**, **C.**, and **D.** on **separate lines**
- Each option must contain a **complete, meaningful sentence or phrase**
- Use consistent numbering: Q1, Q2, ..., Q{num_questions}
- **Do NOT repeat** the question number inside the question text (e.g., don't say "Q1: Q1: What is...")
- Avoid ambiguous or trick questions
- Do not include explanations or additional commentary
- Only use the content in the study material below — no outside information

📚 Study Material (max 3000 characters):
\"\"\"{text[:3000]}\"\"\"
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )

        quiz_text = response.choices[0].message.content
        st.session_state["quiz"] = quiz_text
        st.session_state["answers"] = {}
        st.session_state["submitted"] = False

# Display and take quiz
if "quiz" in st.session_state:
    st.subheader("📝 Quiz Time")
    questions_raw = st.session_state["quiz"].split("Q")[1:]  # Q1, Q2, ...
    parsed_questions = []

    for i, q_raw in enumerate(questions_raw, 1):
        parts = q_raw.strip().split("Answer:")
        if len(parts) != 2:
            continue  # Skip malformed question

        q_text = "Q" + parts[0].strip()
        correct = parts[1].strip().upper()[0]  # 'A', 'B', etc.

        q_lines = q_text.split("\n")
        question_line = q_lines[0].strip()

        # Remove duplicated "Qn:" if GPT added it again in the question
        if question_line.startswith(f"Q{i}:"):
            question_line = question_line[len(f"Q{i}:"):].strip()

        options = []
        for line in q_lines[1:]:
            line = line.strip()
            if line.startswith("A.") or line.startswith("B.") or line.startswith("C.") or line.startswith("D."):
                options.append(line)

        if len(options) != 4:
            continue  # Skip if not exactly 4 options

        parsed_questions.append({
            "index": i,
            "question": question_line,
            "options": options,
            "correct": correct
        })

    # Warning if GPT didn't generate all questions
    if len(parsed_questions) < num_questions:
        st.warning(f"⚠️ Only {len(parsed_questions)} out of {num_questions} questions were properly generated.")

    # Show each question
    for q in parsed_questions:
        st.markdown(f"**Q{q['index']}: {q['question']}**")
        
        labeled_options = {opt[0]: opt for opt in q["options"]}  # {'A': 'A. Text...', etc.}

        st.session_state["answers"][f"q{q['index']}"] = st.radio(
            "Choose your answer:",
            options=list(labeled_options.keys()),  # ['A', 'B', 'C', 'D']
            format_func=lambda x: labeled_options[x],  # Show full text for each
            index=None,
            key=f"q{q['index']}_input"
        )

    if st.button("🎯 Submit Answers", disabled=st.session_state.get("submitted", False)):
        st.session_state["submitted"] = True

# Show results and feedback
if st.session_state.get("submitted"):
    st.subheader("📊 Results & Feedback")
    correct_count = 0
    feedback_prompt = "Evaluate the following answers and give a short summary:\n\n"

    for q in parsed_questions:
        user_answer = st.session_state["answers"].get(f"q{q['index']}")
        if user_answer == q["correct"]:
            st.success(f"✅ Q{q['index']}: Correct")
            correct_count += 1
        else:
            st.error(f"❌ Q{q['index']}: Incorrect (Your answer: {user_answer}, Correct: {q['correct']})")

        feedback_prompt += (
            f"Q{q['index']}: {q['question']}\n"
            f"Correct Answer: {q['correct']}\n"
            f"User Answer: {user_answer}\n\n"
        )

    total_questions = len(parsed_questions)
    accuracy = (correct_count / total_questions) * 100 if total_questions else 0
    st.markdown(f"**🧠 Your Score: {correct_count}/{total_questions} ({accuracy:.1f}%)**")

    with st.spinner("🧠 Generating feedback..."):
        feedback_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": feedback_prompt + "Give a final summary only."}]
        )
        st.info("💡 " + feedback_response.choices[0].message.content)
