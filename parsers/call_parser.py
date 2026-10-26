import re
from datetime import datetime

def parse_call_logs(raw_text_path):
    results = []
    try:
        with open(raw_text_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return results

    # Pattern to match the content query output for calls
    pattern = re.compile(r"number=(.*?), duration=(\d+), date=(\d+), type=(\d+)")
    
    for line in lines:
        match = pattern.search(line)
        if not match:
            continue
            
        number, duration, date_ms, call_type = match.groups()
        
        # Convert type to readable format
        # 1 = Incoming, 2 = Outgoing, 3 = Missed
        type_map = {"1": "Incoming", "2": "Outgoing", "3": "Missed"}
        
        results.append({
            "number": number,
            "duration_sec": int(duration),
            "timestamp": datetime.fromtimestamp(int(date_ms)/1000).isoformat(),
            "type": type_map.get(call_type, "Unknown")
        })
    return results