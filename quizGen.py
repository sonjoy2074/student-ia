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

# Step 1: Upload PDF
pdf_file = st.file_uploader("📤 Upload your study PDF", type=["pdf"])

# Step 2: Input number of questions
num_questions = st.number_input("🔢 How many questions to generate?", min_value=1, max_value=20, value=5)

# Helper: Extract text from PDF
def extract_pdf_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# Step 3: Generate quiz using LLM
if st.button("🚀 Generate Quiz") and pdf_file:
    with st.spinner("Analyzing your PDF and generating quiz..."):
        text = extract_pdf_text(pdf_file)
        prompt = f"""You are a quiz master. Based on the following study material, generate {num_questions} multiple-choice questions with 4 options each and one correct answer.

Study Material:
\"\"\"{text[:3000]}\"\"\"

Format:
Q1: [Question text]
A. Option 1
B. Option 2
C. Option 3
D. Option 4
Answer: [Correct option letter]
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        quiz_text = response.choices[0].message.content
        st.session_state["quiz"] = quiz_text
        st.session_state["answers"] = {}
        st.session_state["submitted"] = False

# Step 4: Display and take quiz
if "quiz" in st.session_state:
    st.subheader("📝 Your Quiz")
    questions = st.session_state["quiz"].split("Q")[1:]  # Split questions
    for i, q_raw in enumerate(questions, 1):
        parts = q_raw.strip().split("Answer:")
        
        # Skip if "Answer:" not present
        if len(parts) != 2:
            st.warning(f"⚠️ Skipping malformed question Q{i}: 'Answer:' missing.")
            continue

        q_text = "Q" + parts[0].strip()
        correct = parts[1].strip()

        # Format options
        q_lines = q_text.split("\n")
        question_line = q_lines[0].strip()
        options = [line.strip() for line in q_lines[1:] if line.strip() and line.strip()[0] in "ABCD"]

        st.markdown(f"**{question_line}**")
        for opt in options:
            st.markdown(opt)

        # Show radio without default
        option_key = f"q{i}"
        st.session_state["answers"][option_key] = st.radio(
            f"Select your answer for Q{i}:", 
            ["A", "B", "C", "D"], 
            index=None,
            key=option_key + "_input"
        )

    if st.button("🎯 Submit Answers"):
        st.session_state["submitted"] = True



# Step 5: Analyze answers
if st.session_state.get("submitted"):
    st.subheader("📊 Results & Feedback")
    correct_count = 0
    feedback_prompt = "Evaluate the following answers and provide brief feedback:\n\n"

    for i, q_raw in enumerate(questions, 1):
        parts = q_raw.strip().split("Answer:")
        q_text = "Q" + parts[0].strip()
        correct = parts[1].strip()
        user_answer = st.session_state["answers"][f"q{i}"]

        if user_answer == correct:
            st.success(f"✅ Q{i}: Correct")
            correct_count += 1
        else:
            st.error(f"❌ Q{i}: Incorrect (Your answer: {user_answer}, Correct: {correct})")

        feedback_prompt += f"Q{i}: {q_text}\nCorrect Answer: {correct}\nUser Answer: {user_answer}\n\n"

    accuracy = (correct_count / len(questions)) * 100
    st.markdown(f"**🧠 Your Score: {correct_count}/{len(questions)} ({accuracy:.1f}%)**")

    with st.spinner("🧠 Generating feedback..."):
        feedback_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": feedback_prompt + "\nGive a summary feedback."}]
        )
        st.info("💡 " + feedback_response.choices[0].message.content)
