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

        ai_summary = "AI Summary unavailable."
        
        if GROQ_API_KEY and data:
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            prompt_text = f"""You are an expert Financial Analyst. Read this bank statement text and give a strict report in Hindi/English mix.
            Provide exact details for these 4 points:
            1. 💰 टर्नओवर (Turnover): Total estimated yearly/monthly credit flow.
            2. 🏦 चल रहे लोन (Active Loans & EMIs): List the exact names of companies cutting EMIs and the EMI amount.
            3. ❌ बाउंस और पेनल्टी (Bounces & Late Fees): Find any bounced EMIs, ECS Returns, or late payment charges.
            4. 📊 फाइनेंशियल स्कोर (Health Score): Give a score out of 10 based on repayment behavior.
            
            Bank Statement Data:
            {str(data)[:20000]}"""

            # 🚀 TERMINATOR LOOP FOR GROQ (4 लेटेस्ट और सबसे फ़ास्ट मॉडल्स)
            models_to_try = [
                "llama-3.3-70b-versatile",
                "llama-3.1-70b-versatile", 
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768"
            ]
            
            headers = {
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            success = False
            last_error = ""
            
            for model_name in models_to_try:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt_text}]
                }
                try:
                    response = requests.post(url, headers=headers, json=payload)
                    res_json = response.json()
                    
                    if "choices" in res_json:
                        ai_summary = res_json["choices"][0]["message"]["content"]
                        success = True
                        break  # 🚀 मॉडल चल गया, लूप रोक दो!
                    else:
                        last_error = json.dumps(res_json)
                except Exception as e:
                    last_error = str(e)
                    continue
            
            if not success:
                ai_summary = f"API Error: 4 मॉडल्स ट्राई किए, सब फेल! Last Error: {last_error}"

        if MONGO_URI and data:
            collection.insert_one({"filename": file.filename, "extracted_text_length": len(str(data)), "ai_summary": ai_summary})
            
        return {"status": 200, "message": "Success", "ai_summary": ai_summary}
    
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "File processing failed."}
