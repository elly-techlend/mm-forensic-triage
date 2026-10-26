import subprocess
import hashlib
import os
import json
from datetime import datetime

class Acquisition:
    def __init__(self, case_id, evidence_dir="evidence"):
        self.case_id = case_id
        self.evidence_dir = os.path.join(evidence_dir, case_id)
        self.log_file = os.path.join(self.evidence_dir, "case_log.txt")
        os.makedirs(self.evidence_dir, exist_ok=True)
        self.manifest = {}
        self.serial = None

    def _log(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        with open(self.log_file, "a") as f:
            f.write(line + "\n")

    def _run(self, cmd):
        self._log(f"EXEC: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            self._log("ERROR: Command timed out")
            return "", "timeout"

    def check_device(self):
        out, _ = self._run(["adb", "devices"])
        lines = [l for l in out.split("\n")[1:] if l.strip()]
        if not lines:
            raise Exception("No device connected")
        serial, status = lines[0].split("\t")
        if status != "device":
            raise Exception(f"Device not ready: {status}")
        self._log(f"Device found: {serial}")
        self.serial = serial
        return serial

    def collect_device_info(self):
        props = {}
        for prop in ["ro.product.model", "ro.product.manufacturer",
                     "ro.build.version.release", "ro.serialno"]:
            out, _ = self._run(["adb", "shell", "getprop", prop])
            props[prop] = out
        self._log(f"Device info: {json.dumps(props)}")
        info_path = os.path.join(self.evidence_dir, "device_info.json")
        with open(info_path, "w") as f:
            json.dump(props, f, indent=2)
        self._hash_file(info_path)
        return props

    def _hash_file(self, path):
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        digest = sha256.hexdigest()
        self.manifest[os.path.basename(path)] = digest
        self._log(f"HASH {os.path.basename(path)}: {digest}")
        return digest

    def pull_sms_content_provider(self):
        """Pulls SMS using the Android Content Provider (works without root)"""
        self._log("Querying SMS content provider...")
        out, err = self._run(["adb", "shell", "content", "query", 
                              "--uri", "content://sms/", 
                              "--projection", "_id:address:body:date:type"])
        
        if "Permission Denial" in err or not out:
            self._log(f"Content query failed: {err}")
            return None
            
        local = os.path.join(self.evidence_dir, "sms_raw.txt")
        with open(local, "w") as f:
            f.write(out)
        
        self._hash_file(local)
        self._log(f"Successfully saved SMS raw data to {local}")
        return local

    def pull_via_backup(self, package):
        backup_file = os.path.join(self.evidence_dir, f"{package}.ab")
        self._run(["adb", "backup", "-f", backup_file, "-noapk", package])
        if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
            self._hash_file(backup_file)
            self._log(f"Backup created: {backup_file}")
            return backup_file
        return None

    def pull_call_logs(self):
        remote = "/data/data/com.android.providers.contacts/databases/calllog.db"
        local = os.path.join(self.evidence_dir, "calllog.db")
        self._run(["adb", "pull", remote, local])
        if os.path.exists(local) and os.path.getsize(local) > 0:
            self._hash_file(local)
            return local
        return None

    def verify_integrity(self):
        """Re-hashes all files and compares them to the manifest."""
        manifest_path = os.path.join(self.evidence_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            return False, "Manifest not found."
            
        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)
            
        original_hashes = manifest_data.get("files", {})
        results = []
        
        for filename, original_hash in original_hashes.items():
            file_path = os.path.join(self.evidence_dir, filename)
            if not os.path.exists(file_path):
                results.append(f"❌ MISSING: {filename}")
                continue
                
            # Re-hash
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            new_hash = sha256.hexdigest()
            
            if new_hash == original_hash:
                results.append(f"✅ VERIFIED: {filename}")
            else:
                results.append(f"❌ TAMPERED: {filename} (Expected {original_hash[:8]}... Got {new_hash[:8]}...)")
                
        return True, results

    def list_packages(self):
        out, _ = self._run(["adb", "shell", "pm", "list", "packages"])
        path = os.path.join(self.evidence_dir, "packages.txt")
        with open(path, "w") as f:
            f.write(out)
        self._hash_file(path)
        return out

    def save_manifest(self):
        path = os.path.join(self.evidence_dir, "manifest.json")
        with open(path, "w") as f:
            json.dump({
                "case_id": self.case_id,
                "created": datetime.now().isoformat(),
                "files": self.manifest
            }, f, indent=2)
        self._log(f"Manifest saved: {path}")
        return path
    
    def pull_call_logs_content_provider(self):
        self._log("Querying Call Logs content provider...")
        # Pull call logs: number, duration, date, type (1=incoming, 2=outgoing, 3=missed)
        out, err = self._run(["adb", "shell", "content", "query", 
                              "--uri", "content://call_log/calls", 
                              "--projection", "number:duration:date:type"])
        
        if out and "Row:" in out:
            local = os.path.join(self.evidence_dir, "calls_raw.txt")
            with open(local, "w") as f:
                f.write(out)
            self._hash_file(local)
            self._log(f"Successfully saved Call Logs to {local}")
            return local
        return None

    
