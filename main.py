from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from pymongo import MongoClient
from parser import extract_transactions

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI")
if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI)
        db = client["financial_db"]
        collection = db["statements"]
        print("Connected to MongoDB!")
    except Exception as e:
        print(f"DB Connection Error: {e}")

@app.post("/analyze")
async def analyze_statement(file: UploadFile = File(...)):
    try:
        with open("temp.pdf", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        data = extract_transactions("temp.pdf")
        
        if MONGO_URI and data:
            collection.insert_one({"filename": file.filename, "extracted_data": data})
            return {"status": 200, "message": "Success! Data Extracted and Saved to MongoDB 🚀", "data": data}
        
        return {"status": 200, "message": "Success! Extracted but not saved.", "data": data}
    
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "File processing failed. Please check the PDF format."}
