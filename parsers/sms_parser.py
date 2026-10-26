import re
from datetime import datetime
import os

UGANDA_TELECOMS = {
    "MTN": r"(?i)\bmtn\b",
    "Airtel": r"(?i)\bairtel\b",
    "dfcu": r"(?i)\bdfcu\b"
}

# We only want ACTUAL transaction alerts
TRANSACTION_INDICATORS = r"(?i)(sent|received|deducted|withdrawn|deposited|collected|bought|paid)"
MONEY_KEYWORDS = r"(?i)(ugx|shs|/=)"
# Extract Transaction IDs (MTN uses ID: 12345, Airtel uses TID 12345)
TXN_ID_RE = r"(?i)(?:txnid|id|ref|transaction id)[\s:-]*([A-Z0-9]{8,})"
AMOUNT_RE = r"(?:UGX|SHS)\s*(?:UGX\s*)?([\d,]+)"

def classify(body):
    b = body.lower()
    
    # Ignore marketing messages
    if any(k in b for k in ["miss you", "dial *", "get 500mb", "loan request"]):
        return "ignore"
        
    # Must contain a transaction indicator AND a money keyword to be valid
    if not (re.search(TRANSACTION_INDICATORS, b) and re.search(MONEY_KEYWORDS, b)):
        return "ignore"

    if any(k in b for k in ["sent", "withdraw", "deducted", "collected", "paid", "bought"]):
        return "debit"
    if any(k in b for k in ["received", "deposited", "credited", "payout"]):
        return "credit"
    return "ignore"

def parse_sms_content(raw_text_path):
    results = []
    if not os.path.exists(raw_text_path):
        return results

    with open(raw_text_path, "r") as f:
        lines = f.readlines()

    pattern = re.compile(r"_id=(\d+), address=(.*?), body=(.*?), date=(\d+), type=(\d+)")
    
    for line in lines:
        match = pattern.search(line)
        if not match:
            continue
            
        _id, address, body, date_ms, msg_type = match.groups()
        
        txn_type = classify(body)
        if txn_type == "ignore":
            continue
            
        telecom = None
        for name, pat in UGANDA_TELECOMS.items():
            if re.search(pat, body) or re.search(pat, address):
                telecom = name
                break
                
        amounts = re.findall(AMOUNT_RE, body)
        
        txn_id_match = re.search(TXN_ID_RE, body)
        txn_id = txn_id_match.group(1) if txn_id_match else "N/A"

        results.append({
            "id": _id,
            "sender": address,
            "body": body,
            "timestamp": datetime.fromtimestamp(int(date_ms)/1000).isoformat(),
            "direction": "incoming" if msg_type == "1" else "outgoing",
            "telecom": telecom,
            "type": txn_type,
            "txn_id": txn_id, # NEW
            "amounts": amounts[:1] if amounts else []
        })
    return results