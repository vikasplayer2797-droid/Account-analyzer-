from fastapi import FastAPI, UploadFile, File
import shutil
import os
from pymongo import MongoClient
from parser import extract_transactions

app = FastAPI()

# MongoDB कनेक्शन (यह Render से सुरक्षित तरीके से चाबी लेगा)
MONGO_URI = os.getenv("MONGO_URI")

# अगर चाबी मिल गई, तो डेटाबेस से जुड़ जाओ
if MONGO_URI:
    client = MongoClient(MONGO_URI)
    db = client["financial_db"]       # तेरे डेटाबेस का नाम
    collection = db["statements"]     # तेरी टेबल का नाम
else:
    print("WARNING: MONGO_URI is not set!")

@app.post("/analyze")
async def analyze_statement(file: UploadFile = File(...)):
    # 1. फाइल को सेव करो
    with open("temp.pdf", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 2. PDF से डेटा निकालो (parser.py के ज़रिए)
    data = extract_transactions("temp.pdf")
    
    # 3. निकाला हुआ डेटा MongoDB में सेव करो
    if MONGO_URI and data:
        collection.insert_one({"filename": file.filename, "extracted_data": data})
        return {"message": "Success! Data Extracted and Saved to MongoDB 🚀", "data": data}
    
    return {"message": "Success! Data Extracted (but not saved to DB).", "data": data}
