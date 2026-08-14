import pdfplumber
import re

def extract_transactions(file_path):
    try:
        full_text = ""
        # 🚀 pdfplumber (layout=True) कॉलम और स्पेस को हिलने नहीं देता!
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text(layout=True)
                if extracted:
                    full_text += extracted + "\n"

        # 1. 🛡️ EXACT MATH (Zero AI Hallucination)
        total_credits = "N/A"
        total_debits = "N/A"
        
        # Axis Bank का फिक्स पैटर्न: "TRANSACTION TOTAL   1467207.59   1490096.23"
        # ये Regex बिना गलती के एग्जैक्ट अमाउंट निकालेगा
        total_match = re.search(r'TRANSACTION TOTAL\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})', full_text, re.IGNORECASE)
        if total_match:
            total_debits = total_match.group(1)
            total_credits = total_match.group(2)

        # 2. 🛡️ THE KEYWORD SNIPER (Anti-Fake Loan System)
        lines = full_text.split('\n')
        emi_lines = []
        bounces_count = 0
        
        loan_keywords = ['emi', 'ach', 'ecs', 'nach', 'loan', 'finance', 'bajaj', 'muthoot', 'auto debit', 'si ']
        ignore_keywords = ['upi', 'imps', 'neft', 'rtgs', 'p2a', 'p2m', 'vpa']
        bounce_keywords = ['bounce', 'return', 'reject', 'insufficient', 'chq ret']

        for line in lines:
            line_lower = line.lower()
            
            # बाउंस गिनो
            if any(b in line_lower for b in bounce_keywords):
                bounces_count += 1
                
            # सिर्फ असली EMI निकालो (UPI/IMPS को इग्नोर करो)
            if any(l in line_lower for l in loan_keywords):
                if not any(ign in line_lower for ign in ignore_keywords):
                    # अगर लाइन में अमाउंट (जैसे 4500.00) है, तभी उसे लो
                    if re.search(r'[\d,]+\.\d{2}', line):
                        emi_lines.append(line.strip())

        # 3. 🛡️ HEADER EXTRACTION (For exact KYC)
        header_text = full_text[:2500]

        return {
            "status": "success",
            "header": header_text,
            "total_credits": total_credits,
            "total_debits": total_debits,
            "bounces_count": bounces_count,
            "valid_emis": "\n".join(list(set(emi_lines))[:20]) # Duplicate हटाकर सिर्फ असली EMI
        }

    except Exception as e:
        return {"status": "error", "message": f"Parser Error: {str(e)}"}
