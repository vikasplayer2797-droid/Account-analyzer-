from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from pymongo import MongoClient
import google.generativeai as genai
from parser import extract_transactions

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Database 
MONGO_URI = os.getenv("MONGO_URI")
if MONGO_URI:
    client = MongoClient(MONGO_URI)
    collection = client["financial_db"]["statements"]

# AI Configuration (Gemini)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# 1. UI Route - वेबसाइट यहाँ दिखेगी!
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# 2. API Route - असली काम यहाँ होगा
@app.post("/analyze")
async def analyze_statement(file: UploadFile = File(...)):
    try:
        with open("temp.pdf", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        data = extract_transactions("temp.pdf")
        
        # अगर पासबुक है, तो AI को मत भेजो
        if data and data[0][0] == "Error":
            return {"status": 400, "message": data[0][1]}

        ai_summary = "AI Summary unavailable (API Key missing)."
        
        # Gemini AI को डेटा भेजो (सिर्फ शुरुआत का 2000 अक्षर ताकि सर्वर क्रैश न हो)
        if GEMINI_API_KEY and data:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"You are a strict financial analyst. Read this bank statement JSON data and provide a 3-point summary in Hindi/English mix: 1. Total overview. 2. Red flags (bounces/loans). 3. Financial Health score out of 10. Keep it short. Data: {str(data)[:2500]}"
                response = model.generate_content(prompt)
                ai_summary = response.text
            except Exception as e:
                ai_summary = "AI Error: Model Timeout."

        if MONGO_URI and data:
            collection.insert_one({"filename": file.filename, "extracted_data": data, "ai_summary": ai_summary})
            
        return {"status": 200, "message": "Success", "ai_summary": ai_summary}
    
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "File processing failed."}
