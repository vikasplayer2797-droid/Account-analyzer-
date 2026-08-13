from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import requests
import json
import re  # 🚀 नई लाइब्रेरी जो फालतू स्पेस साफ करेगी
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
            
            # 🚀 DATA COMPRESSOR: फालतू स्पेस और न्यू-लाइन हटाकर डेटा को निचोड़ देगा!
            raw_text = str(data)
            compressed_data = re.sub(r'\s+', ' ', raw_text).strip()
            
            # 🚀 15,000 कैरेक्टर्स की सेफ लिमिट (Groq Free Tier के लिए एकदम परफेक्ट)
            final_payload = compressed_data[:15000]
            
            prompt_text = f"""You are an elite Underwriting System. Analyze this bank statement and extract deep financial insights. 
            Rules:
            1. Output ONLY a RAW, valid JSON object. Do not output anything else.
            2. If any data is missing, output "N/A" or 0.
            
            Extract and return exactly this JSON structure:
            {{
                "kyc_details": {{
                    "account_name": "Name of the account holder",
                    "bank_name": "Name of the Bank",
                    "account_number": "Last 4 digits or full if available",
                    "ifsc_code": "IFSC or Branch name",
                    "statement_period": "e.g., 01-Jan-2025 to 30-Jun-2025"
                }},
                "core_financials": {{
                    "total_credits": "e.g., ₹5,40,000",
                    "total_debits": "e.g., ₹4,10,000",
                    "opening_balance": "e.g., ₹12,000",
                    "closing_balance": "e.g., ₹25,000",
                    "average_monthly_balance": "Estimated AMB e.g., ₹30,000"
                }},
                "loans_and_emis": [
                    {{"company": "e.g., Bajaj Finance", "amount": "e.g., ₹4500", "category": "e.g., Auto Loan", "status": "e.g., Paid / Bounced"}}
                ],
                "risk_and_red_flags": {{
                    "bounced_transactions_count": 0,
                    "hidden_bank_charges": "Total amount deducted as SMS/Penalty/Maintenance fees",
                    "risk_level": "Low / Medium / High"
                }},
                "behavioral_insights": {{
                    "primary_income_source": "e.g., Salary / Business / Cash Deposit",
                    "salary_consistency": "e.g., Consistent / Irregular / N/A",
                    "top_spending_categories": ["e.g., E-commerce", "Food", "Cash Withdrawals"]
                }},
                "health_score": {{
                    "score": 85,
                    "out_of": 100,
                    "verdict": "One line professional verdict on financial health."
                }}
            }}
            
            Bank Statement Data:
            {final_payload}"""

            models_to_try = [
                "mixtral-8x7b-32768",
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant"
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
                    "messages": [{"role": "user", "content": prompt_text}],
                    "temperature": 0.0,
                    "response_format": {"type": "json_object"}
                }
                try:
                    response = requests.post(url, headers=headers, json=payload)
                    res_json = response.json()
                    
                    if "choices" in res_json:
                        raw_text = res_json["choices"][0]["message"]["content"].strip()
                        start_idx = raw_text.find('{')
                        end_idx = raw_text.rfind('}')
                        if start_idx != -1 and end_idx != -1:
                            ai_summary = raw_text[start_idx:end_idx+1]
                        else:
                            ai_summary = raw_text
                        success = True
                        break
                    else:
                        last_error = json.dumps(res_json)
                except Exception as e:
                    last_error = str(e)
                    continue
            
            if not success:
                return {"status": 500, "error": f"API Rejected: {last_error}", "message": "API Error"}

        if MONGO_URI and data:
            collection.insert_one({"filename": file.filename, "extracted_text_length": len(str(data)), "ai_summary": ai_summary})
            
        return {"status": 200, "message": "Success", "ai_summary": ai_summary}
    
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "File processing failed."}
