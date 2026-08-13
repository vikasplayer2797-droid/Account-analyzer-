import pdfplumber

def extract_transactions(pdf_path):
    transactions = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                # यहाँ तू अपनी बैंक का फॉर्मेट देख लेना, ये सिम्पल टेबल डेटा लेगा
                transactions.extend(table)
    return transactions
