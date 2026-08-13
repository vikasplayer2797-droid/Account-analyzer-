import pdfplumber

def extract_transactions(pdf_path):
    full_text = ""
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # यह पूरे PDF के एक-एक पेज को पढ़ेगा
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
                
                # 🚀 RAM बचाने का असली जादू: पेज पढ़ने के बाद मेमोरी साफ़ कर दो
                page.flush_cache()
                    
        # अगर PDF में कोई टेक्स्ट नहीं मिला (फोटो है)
        if len(full_text.strip()) < 50:
            return "Error: PDF में कोई टेक्स्ट नहीं मिला! कृपया असली ई-स्टेटमेंट अपलोड करें।"
            
        return full_text

    except Exception as e:
        return f"Error: PDF पढ़ने में दिक्कत - {str(e)}"
