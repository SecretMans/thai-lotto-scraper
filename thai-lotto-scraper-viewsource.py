import requests
import re
import json
from datetime import datetime, timedelta
import os
import subprocess

START_DATE = datetime(2006, 12, 30)
TODAY = datetime.today()

# 💬 แปลงวันเป็นรูปแบบลิงก์แบบไทย (ddmmปีพ.ศ.)
def to_thai_id(dt):
    return dt.strftime("%d%m") + str(dt.year + 543)

# 💾 เซฟเป็นไฟล์ตามวัน
def save_per_date(result):
    if not os.path.exists("lotto_history"):
        os.makedirs("lotto_history")
    try:
        date_obj = datetime.strptime(result["date"], "%d %B %Y")
        filename = date_obj.strftime("lotto_history/%Y-%m-%d.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ ERROR: Save per date fail: {e}")

# 📦 รวมเก็บใน main file
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

    with open(main_file, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

# 🚀 Push GitHub
def git_push(new_data):
    try:
        for entry in new_data:
            try:
                date_obj = datetime.strptime(entry["date"], "%d %B %Y")
                filename = f"lotto_history/{date_obj.strftime('%Y-%m-%d')}.json"
                
                # ⬇️ commit message
                commit_msg = f"Lottery result for {date_obj.strftime('%Y-%m-%d')}"
                
                subprocess.run(["git", "add", filename], check=True)
                subprocess.run(["git", "commit", "-m", commit_msg], check=True)
                print(f"✅ Git commit: {filename}")
            except Exception as e:
                print(f"⚠️ Skip commit: {e}")

        subprocess.run(["git", "add", "lotto_history.json"], check=True)
        now = datetime.now()
        # ⬇️ แสดงปีเป็น พ.ศ.
        buddhist_now = f"{now.strftime('%Y')}"
        buddhist_now = str(int(buddhist_now) + 543)
        now_thai = now.strftime(f"%d-%m-{buddhist_now} %H:%M:%S")
        subprocess.run(["git", "commit", "-m", f"Update main lotto_history.json at {now_thai}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 Git push success!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")

# 🕵️‍♂️ เริ่มไล่ดึง
lotto_data = []
current_date = START_DATE
while current_date <= TODAY:
    thai_id = to_thai_id(current_date)
    url = f"https://news.sanook.com/lotto/check/{thai_id}/"
    print(f"🔍 Checking {url}")

    try:
        res = requests.get(url, timeout=10)
        res.encoding = "utf-8"

        match = re.search(r"var\s+lottoResult\s*=\s*(\{.*?\});", res.text, re.DOTALL)
        if not match:
            print("❌ ไม่มีผลหวยในหน้านี้")
            current_date += timedelta(days=1)
            continue

        raw_json = match.group(1)
        lotto_json = json.loads(raw_json)

        # ⬇️ แสดง date ด้วยปี พ.ศ.
        buddhist_year = current_date.year + 543
        date_thai = current_date.strftime(f"%d %B {buddhist_year}")

        result = {
            "id": thai_id,
            "url": url,
            "date": date_thai,
            "prize": lotto_json.get("prize", {}),
            "wording": lotto_json.get("wording", {})
        }

        lotto_data.append(result)
        save_per_date(result)
        print(f"✅ บันทึกผลหวย: {result['date']}")

    except Exception as e:
        print(f"❌ ERROR: {e} ที่ {url}")
        lotto_data.append({
            "id": thai_id,
            "url": url,
            "status": f"error: {str(e)}"
        })

    current_date += timedelta(days=1)

# 📦 รวมทั้งหมด และ push
update_main_json(lotto_data)
git_push(lotto_data)

print("📦 เสร็จแล้ว! ดึงหวยย้อนหลังครบ + บันทึก + Git push ✅")
