import pdfplumber

def extract_transactions(pdf_path):
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table is not None:
                    transactions.extend(table)
                    
        if len(transactions) == 0:
            return [["Error", "PDF में कोई टेबल नहीं मिली! क्या यह एक स्कैन की हुई फोटो या पासबुक है? कृपया असली E-Statement अपलोड करें।"]]
            
        return transactions

    except Exception as e:
        return [["System Error", f"PDF पढ़ने में दिक्कत: {str(e)}"]]
