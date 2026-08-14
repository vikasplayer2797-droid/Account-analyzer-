import fitz  # 🚀 PyMuPDF (The Lightweight Engine)
import re

def extract_transactions(file_path):
    try:
        full_text = ""
        
        # 🚀 Extremely fast & memory-efficient extraction
        doc = fitz.open(file_path)
        for page in doc:
            full_text += page.get_text("text") + "\n"
        doc.close()

        # 1. 🛡️ EXACT MATH (Zero AI Hallucination)
        total_credits = "N/A"
        total_debits = "N/A"
        
        # Axis Bank Regex: "TRANSACTION TOTAL   1467207.59   1490096.23"
        total_match = re.search(r'TRANSACTION TOTAL\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})', full_text, re.IGNORECASE)
        if total_match:
            total_debits = total_match.group(1)
            total_credits = total_match.group(2)

        # 2. 🛡️ THE KEYWORD SNIPER (Anti-Fake Loan System + Context Grabber)
        lines = full_text.split('\n')
        emi_lines = []
        bounces_count = 0
        
        loan_keywords = ['emi', 'ach', 'ecs', 'nach', 'loan', 'finance', 'bajaj', 'muthoot', 'auto debit', 'si ']
        ignore_keywords = ['upi', 'imps', 'neft', 'rtgs', 'p2a', 'p2m', 'vpa']
        bounce_keywords = ['bounce', 'return', 'reject', 'insufficient', 'chq ret']

        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # बाउंस गिनो
            if any(b in line_lower for b in bounce_keywords):
                bounces_count += 1
                
            # सिर्फ असली EMI निकालो
            if any(l in line_lower for l in loan_keywords):
                if not any(ign in line_lower for ign in ignore_keywords):
                    # स्मार्ट कैप्चर: ऊपर-नीचे की लाइनें लपेट लो
                    start = max(0, i - 1)
                    end = min(len(lines), i + 3)
                    context_block = " | ".join([lines[j].strip() for j in range(start, end) if lines[j].strip()])
                    emi_lines.append(context_block)

        # 3. 🛡️ HEADER EXTRACTION (For exact KYC)
        header_text = full_text[:2500]

        return {
            "status": "success",
            "header": header_text,
            "total_credits": total_credits,
            "total_debits": total_debits,
            "bounces_count": bounces_count,
            "valid_emis": "\n".join(list(set(emi_lines))[:15]) # 15 सॉलिड EMI चंक्स
        }

    except Exception as e:
        return {"status": "error", "message": f"Parser Error: {str(e)}"}
