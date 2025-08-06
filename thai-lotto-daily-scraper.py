import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from collections import OrderedDict
import os
import subprocess
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

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
        return filename
    except Exception as e:
        print(f"Save per date failed: {e}")
        return None

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

    # จัดเรียงตามวันที่ จากใหม่ไปเก่า
    def get_date(entry):
        try:
            return thai_date_to_datetime(entry["date"])
        except:
            return datetime.min  # ถ้า parse ไม่ได้ เอาไว้ท้ายสุด

    existing.sort(key=get_date, reverse=False)

    # เรียง key ตามลำดับที่ต้องการ
    final_data = reorder_json_keys(existing)
    with open(main_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

def git_push(json_file, result):
    try:
        subprocess.run(["git", "add", json_file], check=True)
        subprocess.run(["git", "add", "lotto_history.json"], check=True)

        date_obj = thai_date_to_datetime(result["date"])
        subprocess.run(["git", "commit", "-m", f"🎯 Lottery result for {date_obj.strftime('%d %B %Y')}"], check=True)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subprocess.run(["git", "commit", "--allow-empty", "-m", f"🗃️ Update main lotto_history.json at {now}"], check=True)

        subprocess.run(["git", "push"], check=True)
        print("Git push success")
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}")

# ตรวจว่าวันนี้ตรงกับวันหวยออกมั้ย
today = datetime.today()
# if today.day not in [1, 16]:
#     print("Today is not lottery day. Skipping.")
#     sys.exit(0)

# เตรียมลิงก์
draw_day = today.day
draw_month = today.month
draw_year = today.year

# Debug
# draw_day = 1
# draw_month = 8
# draw_year = 2025

url = f"https://news.sanook.com/lotto/check/{draw_day:02d}{draw_month:02d}{draw_year + 543}"
print(f"Checking lotto result from: {url}")

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
        print("Unknown template. Skipping.")
        sys.exit(0)

    if result["first_prize"]:  # ตรวจว่ามีข้อมูลจริง
        print(f"Lottery found for {result['date']}")
        json_file = save_per_date(result)
        if json_file:
            update_main_json([result])
            git_push(json_file, result)
    else:
        print("No valid lottery data yet. Skipping.")

except Exception as e:
    print(f"ERROR: {e}")
