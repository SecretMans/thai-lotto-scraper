import requests
import re
import json
from datetime import datetime
import os
import subprocess
import sys

repo_path = r"D:\thai-lotto-scraper"
os.chdir(repo_path)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 🧠 แปลงเป็นรหัสแบบ พ.ศ. เช่น 05082568
def get_thai_lotto_id(dt):
    return dt.strftime("%d%m") + str(dt.year + 543)

# 💾 บันทึกแยกวัน
def save_per_date(result):
    if not os.path.exists("lotto_history"):
        os.makedirs("lotto_history")
    try:
        date_obj = datetime.strptime(result["date"], "%d %B %Y")  # ยังต้องใช้ปี ค.ศ.
        filename = date_obj.strftime("lotto_history/%Y-%m-%d.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return filename
    except Exception as e:
        print(f"❌ Save per date failed: {e}")
        return None

# 🧷 อัปเดตไฟล์รวม
def update_main_json(new_data):
    main_file = "lotto_history.json"
    if os.path.exists(main_file):
        with open(main_file, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except:
                existing = []
    else:
        existing = []

    existing_ids = {entry["id"] for entry in existing}
    for entry in new_data:
        if entry["id"] not in existing_ids:
            existing.append(entry)

    existing.sort(key=lambda e: e["id"])
    with open(main_file, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

# 🚀 Git push
def git_push(json_file, result):
    try:
        date_obj = datetime.strptime(result["date"], "%d %B %Y")
        commit_msg = f"Lottery result for {date_obj.strftime('%Y-%m-%d')}"

        # ✅ Step 1: Add และ commit เฉพาะไฟล์หวยรายวัน
        subprocess.run(["git", "add", json_file], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print(f"✅ Git commit: {commit_msg}")

        # ✅ Step 2: Add และทำ empty commit แยกให้กับ lotto_history.json
        subprocess.run(["git", "add", "lotto_history.json"], check=True)

        now = datetime.now()
        now_thai = now.strftime(f"{now.year + 543}-%m-%d %H:%M")
        subprocess.run(["git", "commit", "--allow-empty", "-m", f"Update main lotto_history.json at {now_thai}"], check=True)

        # ✅ Step 3: Push ทั้งหมด
        subprocess.run(["git", "push"], check=True)
        print("🚀 Git push success")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")

# 🕵️‍♂️ เริ่มทำงานวันนี้
today = datetime.today()
lotto_id = get_thai_lotto_id(today)
url = f"https://news.sanook.com/lotto/check/{lotto_id}"
print(f"🔍 Checking lotto result from: {url}")

try:
    res = requests.get(url, timeout=10)
    res.encoding = "utf-8"

    match = re.search(r"var\s+lottoResult\s*=\s*(\{.*?\});", res.text, re.DOTALL)
    if not match:
        print("❌ No lottoResult found on page. Skipping.")
        sys.exit(0)

    raw_json = match.group(1)
    lotto_json = json.loads(raw_json)

    buddhist_year = today.year + 543
    result = {
        "id": lotto_id,
        "url": url,
        "date": today.strftime(f"%d %B {buddhist_year}"),
        "prize": lotto_json.get("prize", {}),
        "wording": lotto_json.get("wording", {})
    }

    print(f"✅ Lottery result found for {result['date']}")
    json_file = save_per_date(result)
    if json_file:
        update_main_json([result])
        git_push(json_file, result)

except Exception as e:
    print(f"❌ ERROR: {e}")
