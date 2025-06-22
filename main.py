# 📁 api-server/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
import re

load_dotenv()

app = FastAPI()

# ✅ CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ OpenRouter setup
llm = ChatOpenAI(
    model="openai/gpt-3.5-turbo",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7,
    max_tokens=800
)

# ✅ Convert raw text to frontend-compatible questions
def parse_mcqs(text):
    pattern = r"Question:\s*(.*?)\n\s*a\)\s*(.*?)\n\s*b\)\s*(.*?)\n\s*c\)\s*(.*?)\n\s*d\)\s*(.*?)\n\s*Answer:\s*([abcd])"
    matches = re.findall(pattern, text, re.DOTALL)
    mcqs = []

    for match in matches:
        question_text = match[0].strip()
        options_dict = {
            "a": match[1].strip(),
            "b": match[2].strip(),
            "c": match[3].strip(),
            "d": match[4].strip()
        }
        correct_key = match[5].strip().lower()
        mcqs.append({
            "question": question_text,
            "options": list(options_dict.values()),
            "correctAnswer": options_dict[correct_key]
        })

    return mcqs

# ✅ API Endpoint
@app.post("/generate-quiz")
async def generate_quiz(request: Request):
    body = await request.json()
    topic = body.get("topic", "") or body.get("prompt", "")

    prompt = f"""
Generate exactly 5 multiple choice questions (MCQs) on the topic '{topic}'.

Each question should have options a), b), c), d), and correct answer letter.

Format:
Question: <question text>
a) <option a>
b) <option b>
c) <option c>
d) <option d>
Answer: <correct option letter>
"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    mcqs = parse_mcqs(response.content)

    if not mcqs:
        return {"success": False, "message": "No questions generated"}

    return {"success": True, "questions": mcqs}
