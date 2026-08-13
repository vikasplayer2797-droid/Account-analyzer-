from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import requests
import json
from pymongo import MongoClient
from parser import extract_transactions

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

MONGO_URI = os.getenv("MONGO_URI")
if MONGO_URI:
    client = MongoClient(MONGO_URI)
    collection = client["financial_db"]["statements"]

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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

        ai_summary = "{}"
        
        if GROQ_API_KEY and data:
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            # 🚀 STRICT JSON PROMPT: No stories, No 'AI' word, Only exact numbers in English.
            prompt_text = f"""You are a strict financial data processor. Analyze the bank statement text and return ONLY a raw JSON object. 
            DO NOT use the word 'AI' anywhere. Output must be strictly in English. 
            DO NOT add markdown formatting like ```json or ```.
            Extract the exact numbers and return EXACTLY this JSON structure and nothing else:
            {{
                "total_credits": "Estimated total credit amount (e.g., ₹5,40,000)",
                "total_debits": "Estimated total debit amount (e.g., ₹4,10,000)",
                "active_loans_count": "Total count of distinct active loans (e.g., 2)",
                "emi_transactions_count": "Total count of EMI payments deducted (e.g., 4)",
                "bounces_and_late_fees": "Total count of bounced cheques or late fees (e.g., 1)",
                "health_score": "Score out of 10 based on financials",
                "summary": "One line professional financial summary without using the word AI."
            }}
            
            Bank Statement Data:
            {str(data)[:20000]}"""

            models_to_try = [
                "llama-3.3-70b-versatile",
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant"
            ]
            
            headers = {
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            success = False
            for model_name in models_to_try:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt_text}],
                    "temperature": 0.1  # 🚀 Low temperature for precise JSON output
                }
                try:
                    response = requests.post(url, headers=headers, json=payload)
                    res_json = response.json()
                    
                    if "choices" in res_json:
                        # 🚀 Clean up markdown tags in case Groq adds them
                        raw_text = res_json["choices"][0]["message"]["content"]
                        ai_summary = raw_text.replace("```json", "").replace("```", "").strip()
                        success = True
                        break
                except Exception as e:
                    continue
            
            if not success:
                ai_summary = '{"error": "Failed to analyze document"}'

        if MONGO_URI and data:
            collection.insert_one({"filename": file.filename, "extracted_text_length": len(str(data)), "ai_summary": ai_summary})
            
        return {"status": 200, "message": "Success", "ai_summary": ai_summary}
    
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "File processing failed."}
