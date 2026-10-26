import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, jsonify, request, send_file
import json, re
from collections import Counter
from core.acquisition import Acquisition
from pdf_generator import generate_pdf
from dashboard_pdf import generate_dashboard_pdf

app = Flask(__name__)
EVIDENCE_ROOT = os.path.expanduser("~/mm_triage/evidence")

@app.route("/")
def index():
    cases = []
    if os.path.exists(EVIDENCE_ROOT):
        cases = [d for d in os.listdir(EVIDENCE_ROOT) if os.path.isdir(os.path.join(EVIDENCE_ROOT, d))]
    return render_template("index.html", cases=cases)

@app.route("/case/<case_id>")
def case_view(case_id):
    case_dir = os.path.join(EVIDENCE_ROOT, case_id)
    json_path = os.path.join(case_dir, "sms_parsed.json")
    calls_path = os.path.join(case_dir, "calls_parsed.json") # <-- ADD THIS
    manifest_path = os.path.join(case_dir, "manifest.json")
    
    messages = []
    if os.path.exists(json_path):
        with open(json_path) as f:
            messages = json.load(f)
            
    calls = []
    if os.path.exists(calls_path):
        with open(calls_path) as f:
            calls = json.load(f)
            
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)

    # Integrity Check
    a = Acquisition(case_id, evidence_dir=EVIDENCE_ROOT)
    _, integrity_results = a.verify_integrity()

    # --- PAGINATION LOGIC ---
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    total_messages = len(messages)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_messages = messages[start_idx:end_idx]
    
    import math
    total_pages = math.ceil(total_messages / per_page) if total_messages > 0 else 1

    return render_template("case.html", 
                           case_id=case_id, 
                           messages=paginated_messages,
                           total_messages=total_messages,
                           page=page,
                           total_pages=total_pages,
                           start_idx=start_idx + 1 if total_messages > 0 else 0,
                           end_idx=min(end_idx, total_messages),
                           manifest=manifest, 
                           integrity=integrity_results,
                           calls=calls) 

@app.route("/generate_pdf/<case_id>")
def download_pdf(case_id):
    case_dir = os.path.join(EVIDENCE_ROOT, case_id)
    json_path = os.path.join(case_dir, "sms_parsed.json")
    calls_path = os.path.join(case_dir, "calls_parsed.json")
    manifest_path = os.path.join(case_dir, "manifest.json")
    
    messages = []
    if os.path.exists(json_path):
        with open(json_path) as f: messages = json.load(f)
        
    calls = []
    if os.path.exists(calls_path):
        with open(calls_path) as f: calls = json.load(f)
        
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path) as f: manifest = json.load(f)

    # Calculate totals for the PDF summary
    total_debits = sum(int(m["amounts"][0].replace(",", "")) for m in messages if m["amounts"] and m["type"] == "debit")
    total_credits = sum(int(m["amounts"][0].replace(",", "")) for m in messages if m["amounts"] and m["type"] == "credit")
        
    pdf_path = generate_pdf(case_id, case_dir, messages, calls, manifest, total_debits, total_credits)
    return send_file(pdf_path, as_attachment=True)

@app.route("/generate_dashboard_pdf/<case_id>")
def download_dashboard_pdf(case_id):
    case_dir = os.path.join(EVIDENCE_ROOT, case_id)
    json_path = os.path.join(case_dir, "sms_parsed.json")
    
    messages = []
    if os.path.exists(json_path):
        with open(json_path) as f: 
            messages = json.load(f)
        
    # Recalculate everything from scratch for the PDF
    total_debits = 0
    total_credits = 0
    counterparties = Counter()
    telecom_counts = Counter()
    
    for m in messages:
        amt = 0
        if m.get("amounts"):
            try:
                amt = int(m["amounts"][0].replace(",", ""))
            except:
                pass
                
        if m["type"] == "debit":
            total_debits += amt
            name_match = re.search(r"to\s+([A-Z\s]{3,})", m["body"])
            if name_match:
                counterparties[name_match.group(1).strip()] += 1
                
        elif m["type"] == "credit":
            total_credits += amt
            name_match = re.search(r"from\s+([A-Z\s]{3,})", m["body"])
            if name_match:
                counterparties[name_match.group(1).strip()] += 1
                
        if m.get("telecom"):
            telecom_counts[m["telecom"]] += 1
            
    # Pass the calculated lists to the PDF generator
    pdf_path = generate_dashboard_pdf(
        case_id, 
        case_dir, 
        total_debits, 
        total_credits, 
        counterparties.most_common(5), # Top 5
        telecom_counts.most_common()
    )
    return send_file(pdf_path, as_attachment=True)

@app.route("/search/<case_id>")
def search(case_id):
    query = request.args.get("q", "").lower()
    case_dir = os.path.join(EVIDENCE_ROOT, case_id)
    json_path = os.path.join(case_dir, "sms_parsed.json")
    calls_path = os.path.join(case_dir, "calls_parsed.json") # <-- FIXED: Defined path
    
    messages = []
    if os.path.exists(json_path):
        with open(json_path) as f:
            all_msgs = json.load(f)
            # Filter based on search query
            messages = [m for m in all_msgs if query in m["body"].lower()]

    calls = []
    if os.path.exists(calls_path):
        with open(calls_path) as f:
            calls = json.load(f)
            
    return render_template("case.html", 
                           case_id=case_id, 
                           messages=messages, 
                           total_messages=len(messages),
                           page=1,
                           total_pages=1,
                           start_idx=1 if len(messages) > 0 else 0,
                           end_idx=len(messages),
                           manifest={}, 
                           integrity=[],
                           calls=calls) 

@app.route("/dashboard/<case_id>")
def dashboard(case_id):
    case_dir = os.path.join(EVIDENCE_ROOT, case_id)
    json_path = os.path.join(case_dir, "sms_parsed.json")
    calls_path = os.path.join(case_dir, "calls_parsed.json")
    
    messages = []
    if os.path.exists(json_path):
        with open(json_path) as f:
            messages = json.load(f)

    calls = []
    if os.path.exists(calls_path):
        with open(calls_path) as f:
            calls = json.load(f)

    # 1. CAPTURE FILTERS FROM THE URL
    filter_type = request.args.get("type", "")
    filter_telecom = request.args.get("telecom", "")
    filter_min_amount = request.args.get("min_amount", "")
    filter_start_date = request.args.get("start_date", "") # NEW
    filter_end_date = request.args.get("end_date", "")     # NEW

    # 2. APPLY FILTERS TO MESSAGES
    filtered_messages = []
    for m in messages:
        if filter_type and m.get('type') != filter_type: 
            continue
        if filter_telecom and m.get('telecom') != filter_telecom: 
            continue
        if filter_min_amount:
            amt = 0
            if m.get("amounts"):
                try: 
                    amt = int(m["amounts"][0].replace(",", ""))
                except: 
                    pass
            try:
                if amt < int(filter_min_amount): 
                    continue
            except ValueError:
                pass
                
        # DATE FILTER LOGIC (NEW)
        # Extract just the "YYYY-MM-DD" part of the timestamp
        msg_date = m['timestamp'][:10] 
        if filter_start_date and msg_date < filter_start_date:
            continue
        if filter_end_date and msg_date > filter_end_date:
            continue

        filtered_messages.append(m)

    # 3. AGGREGATE DATA BASED ON FILTERED MESSAGES
    total_debits = 0
    total_credits = 0
    counterparties = Counter()
    telecom_counts = Counter()
    
    for m in filtered_messages:
        amt = 0
        if m["amounts"]:
            try:
                amt = int(m["amounts"][0].replace(",", ""))
            except:
                pass
                
        if m["type"] == "debit":
            total_debits += amt
            name_match = re.search(r"to\s+([A-Z\s]{3,})", m["body"])
            if name_match:
                counterparties[name_match.group(1).strip()] += 1
                
        elif m["type"] == "credit":
            total_credits += amt
            name_match = re.search(r"from\s+([A-Z\s]{3,})", m["body"])
            if name_match:
                counterparties[name_match.group(1).strip()] += 1
                
        if m["telecom"]:
            telecom_counts[m["telecom"]] += 1

    recent_calls = calls[:10]

    return render_template("dashboard.html", 
                           case_id=case_id, 
                           total_debits=total_debits,
                           total_credits=total_credits,
                           counterparties=counterparties.most_common(5),
                           telecoms=telecom_counts.most_common(),
                           recent_calls=recent_calls,
                           filter_type=filter_type,
                           filter_telecom=filter_telecom,
                           filter_min_amount=filter_min_amount,
                           filter_start_date=filter_start_date, # NEW
                           filter_end_date=filter_end_date)     # NEW

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)