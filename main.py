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
        
        # 🚀 1. कॉल Python Rule Engine (No AI involved yet)
        parsed_data = extract_transactions("temp.pdf")
        
        if parsed_data.get("status") == "error":
            return {"status": 400, "message": parsed_data.get("message")}

        ai_summary = "{}"
        
        if GROQ_API_KEY:
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            # 🚀 2. Send PRE-CALCULATED data to AI
            prompt_text = f"""You are a JSON formatting engine. I have already extracted the exact financial data using a deterministic Python engine. 
            Do NOT alter the amounts provided. Do NOT hallucinate.
            
            PRE-CALCULATED DATA GIVEN TO YOU:
            - Header Text (Find Account Name, A/C No, IFSC here): {parsed_data['header']}
            - Exact Total Credits: {parsed_data['total_credits']}
            - Exact Total Debits: {parsed_data['total_debits']}
            - Exact Bounces Count: {parsed_data['bounces_count']}
            - Filtered EMI Lines (These are confirmed non-UPI loans. Extract Name and Amount from these lines): 
            {parsed_data['valid_emis']}
            
            RULES:
            1. Account Name MUST be extracted from the top of the Header Text. Do NOT use any UPI names.
            2. For loans, ONLY use the 'Filtered EMI Lines' provided. Extract the company name and the exact amount from that line.
            
            Return exactly this JSON structure:
            {{
                "kyc_details": {{
                    "account_name": "...",
                    "bank_name": "...",
                    "account_number": "...",
                    "ifsc_code": "...",
                    "statement_period": "..."
                }},
                "core_financials": {{
                    "total_credits": "{parsed_data['total_credits'] if parsed_data['total_credits'] != 'N/A' else '₹... '}",
                    "total_debits": "{parsed_data['total_debits'] if parsed_data['total_debits'] != 'N/A' else '₹... '}",
                    "opening_balance": "N/A",
                    "closing_balance": "N/A",
                    "average_monthly_balance": "N/A"
                }},
                "loans_and_emis": [
                    {{"company": "...", "amount": "...", "category": "EMI", "status": "Active"}}
                ],
                "risk_and_red_flags": {{
                    "bounced_transactions_count": {parsed_data['bounces_count']},
                    "hidden_bank_charges": "N/A",
                    "risk_level": "Calculate based on bounces"
                }},
                "behavioral_insights": {{
                    "primary_income_source": "Estimate from header",
                    "salary_consistency": "N/A",
                    "top_spending_categories": ["..."]
                }},
                "health_score": {{
                    "score": 85,
                    "out_of": 100,
                    "verdict": "Provide a 1 line summary."
                }}
            }}"""

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt_text}],
                "temperature": 0.0,
                "response_format": {"type": "json_object"}
            }
            
            headers = {
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                res_json = response.json()
                if "choices" in res_json:
                    ai_summary = res_json["choices"][0]["message"]["content"].strip()
            except Exception as e:
                return {"status": 500, "error": "AI API Failed", "message": str(e)}

        return {"status": 200, "message": "Success", "ai_summary": ai_summary}
    
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "System Error"}
