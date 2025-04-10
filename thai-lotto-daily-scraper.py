import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from collections import OrderedDict
import os
import subprocess

def thai_date_to_datetime(thai_date_str):
    thai_months = {
        "มกราคม": "January", "กุมภาพันธ์": "February", "มีนาคม": "March",
        "เมษายน": "April", "พฤษภาคม": "May", "มิถุนายน": "June",
        "กรกฎาคม": "July", "สิงหาคม": "August", "กันยายน": "September",
        "ตุลาคม": "October", "พฤศจิกายน": "November", "ธันวาคม": "December"
    }
    for th, en in thai_months.items():
        if th in thai_date_str:
            thai_date_str = thai_date_str.replace(th, en)
            break
    return datetime.strptime(thai_date_str, "%d %B %Y")

def reorder_json_keys(data_list):
    key_order = [
        "id", "url", "status", "date",
        "first_prize", "three_front", "three_last", "two_digit",
        "near_first", "second_prize", "third_prize", "fourth_prize", "fifth_prize"
    ]
    ordered_data = []
    for entry in data_list:
        ordered_entry = OrderedDict()
        for key in key_order:
            ordered_entry[key] = entry.get(key, [] if 'prize' in key or 'three' in key or 'near' in key else "")
        ordered_data.append(ordered_entry)
    return ordered_data

def save_per_date(result):
    if not os.path.exists("lotto_history"):
        os.makedirs("lotto_history")
    try:
        date_obj = thai_date_to_datetime(result["date"])
        filename = date_obj.strftime("lotto_history/%Y-%m-%d.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(reorder_json_keys([result])[0], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ ERROR: Save per date fail: {e}")

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

    final_data = reorder_json_keys(existing)
    with open(main_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

def git_push(new_data):
    try:
        subprocess.run(["git", "add", "lotto_history/*.json"], check=True)
        subprocess.run(["git", "add", "lotto_history.json"], check=True)

        last_date = new_data[-1]["date"]
        dt = thai_date_to_datetime(last_date)
        commit_msg = f"🎯 Lottery result for {dt.strftime('%d %B %Y')}"

        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f"✅ Git push success: {commit_msg}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")

# 🔍 ตรวจหวยของวันนี้
today = datetime.today()
url = f"https://news.sanook.com/lotto/check/{today.day:02d}{today.month:02d}{today.year + 543}"
print(f"🔍 Checking lotto result from: {url}")

try:
    response = requests.get(url, timeout=10)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    def extract(css): return [x.get_text(strip=True) for x in soup.select(css)]

    columns = soup.select(".lottocheck__column")
    result = {
        "id": url.split("/")[-1],
        "url": url,
        "status": "success",
        "date": soup.select_one("h2.content__title--sub").get_text(strip=True).replace("งวดวันที่ ", "") if soup.select_one("h2.content__title--sub") else "N/A",
        "first_prize": extract(".lotto__number--first")[0] if extract(".lotto__number--first") else "",
        "near_first": extract(".lottocheck__sec--nearby .lotto__number"),
        "second_prize": extract(".lottocheck__sec:nth-of-type(2) .lotto__number") or extract(".lottocheck__sec:has(span:-soup-contains('รางวัลที่ 2')) .lotto__number"),
        "third_prize": extract(".lottocheck__sec:nth-of-type(3) .lotto__number") or extract(".lottocheck__sec:has(span:-soup-contains('รางวัลที่ 3')) .lotto__number"),
        "fourth_prize": extract(".lottocheck__sec:nth-of-type(5) .lotto__number") or extract(".lottocheck__sec:has(span:-soup-contains('รางวัลที่ 4')) .lotto__number"),
        "fifth_prize": extract(".lottocheck__sec:nth-of-type(6) .lotto__number") or extract(".lottocheck__sec:has(span:-soup-contains('รางวัลที่ 5')) .lotto__number"),
    }

    if len(columns) == 3:
        result["three_front"] = []
        result["three_last"] = extract(".lottocheck__column:nth-of-type(2) .lotto__number")
        result["two_digit"] = extract(".lottocheck__column:nth-of-type(3) .lotto__number")[0] if extract(".lottocheck__column:nth-of-type(3) .lotto__number") else ""
    elif len(columns) == 4:
        result["three_front"] = extract(".lottocheck__column:nth-of-type(2) .lotto__number")
        result["three_last"] = extract(".lottocheck__column:nth-of-type(3) .lotto__number")
        result["two_digit"] = extract(".lottocheck__column:nth-of-type(4) .lotto__number")[0] if extract(".lottocheck__column:nth-of-type(4) .lotto__number") else ""
    else:
        print(f"🤔 ไม่รู้จักรูปแบบ column {len(columns)} คอลัมน์")
        result["status"] = "unknown-template"

    # 🔍 ถ้าไม่มีรางวัลที่ 1 ก็ถือว่ายังไม่ประกาศ
    if result["first_prize"]:
        print(f"✅ พบข้อมูลงวด: {result['date']}")
        save_per_date(result)
        update_main_json([result])
        git_push([result])
    else:
        print("⚠️ ยังไม่มีข้อมูลรางวัลที่ 1 งวดนี้ (ยังไม่ต้องบันทึก)")

except Exception as e:
    print(f"❌ ERROR: {e} ที่ {url}")
