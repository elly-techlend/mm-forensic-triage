import argparse
import json
import os
from core.acquisition import Acquisition
from parsers.sms_parser import parse_sms_content
from parsers.call_parser import parse_call_logs # <-- NEW IMPORT

def main():
    p = argparse.ArgumentParser(description="Mobile Money Forensic Triage Tool")
    p.add_argument("--case", required=True, help="Case ID e.g. UPF-2026-001")
    p.add_argument("--skip-acquire", action="store_true", help="Skip acquisition, just parse")
    args = p.parse_args()

    a = Acquisition(args.case)
    
    if not args.skip_acquire:
        a.check_device()
        a.collect_device_info()
        a.list_packages()
        raw_sms = a.pull_sms_content_provider()
        raw_calls = a.pull_call_logs_content_provider() # <-- UPDATED VARIABLE
        a.save_manifest()
    else:
        raw_sms = os.path.join(a.evidence_dir, "sms_raw.txt")
        raw_calls = os.path.join(a.evidence_dir, "calls_raw.txt")

    # Parse SMS
    if raw_sms and os.path.exists(raw_sms):
        print("\n[*] Parsing SMS data...")
        results = parse_sms_content(raw_sms)
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        out_json = os.path.join(a.evidence_dir, "sms_parsed.json")
        with open(out_json, "w") as f:
            json.dump(results, f, indent=2)
        print(f"[+] Parsed {len(results)} financial SMS messages.")
        
    # Parse Calls (NEW)
    if raw_calls and os.path.exists(raw_calls):
        print("\n[*] Parsing Call Logs...")
        call_results = parse_call_logs(raw_calls)
        out_calls_json = os.path.join(a.evidence_dir, "calls_parsed.json")
        with open(out_calls_json, "w") as f:
            json.dump(call_results, f, indent=2)
        print(f"[+] Parsed {len(call_results)} call logs.")

    print(f"[+] Case evidence saved in: {a.evidence_dir}")

if __name__ == "__main__":
    main()