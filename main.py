import pdfplumber

def extract_transactions(pdf_path):
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # पेज से टेबल निकालने की कोशिश करो
                table = page.extract_table()
                
                # अगर टेबल मिली है (None नहीं है), तभी उसे लिस्ट में जोड़ो
                if table is not None:
                    transactions.extend(table)
                    
        # अगर पूरी PDF छान मारी और एक भी टेबल नहीं मिली
        if len(transactions) == 0:
            return [["Error", "PDF में कोई टेबल नहीं मिली! क्या यह एक स्कैन की हुई फोटो या पासबुक है? कृपया असली E-Statement अपलोड करें।"]]
            
        return transactions

    except Exception as e:
        # अगर फाइल खोलने में कोई दिक्कत आए
        return [["System Error", f"PDF पढ़ने में दिक्कत: {str(e)}"]]
