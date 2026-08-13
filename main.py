from fastapi import FastAPI, UploadFile, File
import shutil
from parser import extract_transactions

app = FastAPI()

@app.post("/analyze")
async def analyze_statement(file: UploadFile = File(...)):
    # फाइल को सेव करो
    with open("temp.pdf", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # डेटा निकालो
    data = extract_transactions("temp.pdf")
    
    # यहाँ तू MongoDB में डेटा डाल सकता है
    return {"message": "Success", "data": data}
