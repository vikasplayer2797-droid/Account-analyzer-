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

MONGO_URI = os.getenv("MONGO_URI")
if MONGO_URI:
    client = MongoClient(MONGO_URI)
    collection = client["financial_db"]["statements"]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/analyze")
async def analyze_statement(file: UploadFile = File(...)):
    try:
        with open("temp.pdf", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        data = extract_transactions("temp.pdf")
        
        if isinstance(data, str) and data.startswith("Error"):
            return {"status": 400, "message": data}

        ai_summary = "AI Summary unavailable."
        
        if GEMINI_API_KEY and data:
            try:
                # 🚀 FIX: Universal Model 'gemini-pro' जो कभी फेल नहीं होता
                model = genai.GenerativeModel('gemini-pro')
                
                prompt = f"""You are an expert Financial Analyst. Read this bank statement text and give a strict report in Hindi/English mix.
                Provide exact details for these 4 points:
                1. 💰 टर्नओवर (Turnover): Total estimated yearly/monthly credit flow.
                2. 🏦 चल रहे लोन (Active Loans & EMIs): List the exact names of companies cutting EMIs and the EMI amount.
                3. ❌ बाउंस और पेनल्टी (Bounces & Late Fees): Find any bounced EMIs, ECS Returns, or late payment charges.
                4. 📊 फाइनेंशियल स्कोर (Health Score): Give a score out of 10 based on repayment behavior.
                
                Bank Statement Data:
                {str(data)[:30000]}""" # 🚀 Limit set to avoid any overload
                
                response = model.generate_content(prompt)
                ai_summary = response.text
            except Exception as e:
                ai_summary = f"AI Analysis Error: {str(e)}"

        if MONGO_URI and data:
            collection.insert_one({"filename": file.filename, "extracted_text_length": len(str(data)), "ai_summary": ai_summary})
            
        return {"status": 200, "message": "Success", "ai_summary": ai_summary}
    
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "File processing failed."}
