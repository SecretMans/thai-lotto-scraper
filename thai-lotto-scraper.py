import requests
from bs4 import BeautifulSoup
import json
from time import sleep
from datetime import datetime
from collections import OrderedDict
import os
import subprocess

# 🔁 แปลงเดือนภาษาไทย -> อังกฤษ แล้วแปลงเป็น datetime
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

# 🔧 เรียง key
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

# 💾 เซฟแยกไฟล์ตามวันที่
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

# 📦 รวมทุกงวดไว้ใน lotto_history.json
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

# 🚀 Push ขึ้น GitHub
def git_push(new_data):
    try:
        # ✅ Commit ทีละไฟล์ใน lotto_history/
        for entry in new_data:
            try:
                date_obj = thai_date_to_datetime(entry["date"])
                filename = f"lotto_history/{date_obj.strftime('%Y-%m-%d')}.json"
                commit_msg = f"🎯 Lottery result for {date_obj.strftime('%d %B %Y')}"
                
                subprocess.run(["git", "add", filename], check=True)
                subprocess.run(["git", "commit", "-m", commit_msg], check=True)
                print(f"✅ Git commit: {filename} → {commit_msg}")
            except Exception as e:
                print(f"⚠️ Skip commit for entry {entry.get('id')}: {e}")

        # ✅ Commit รวมไฟล์หลักท้ายสุด
        subprocess.run(["git", "add", "lotto_history.json"], check=True)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        main_commit_msg = f"🗃️ Update main lotto_history.json at {now}"
        subprocess.run(["git", "commit", "-m", main_commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f"🚀 Git push success!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")


# 🕵️‍♂️ เริ่มลุย!
metaurl = "https://news.sanook.com/lotto/check/{:02d}{:02d}{}"
links = []
today = datetime.today()
current_year = today.year
current_month = today.month
current_day = today.day

# 🔗 วนลูปทุกงวดตั้งแต่ปี 2007 จนถึงปัจจุบัน
for year in range(2007, current_year + 1):
    for month in range(1, 13):
        for day in [1, 16]:
            if (year == current_year and month == current_month and day > current_day) or \
               (year == current_year and month > current_month):
                continue

            eday, emonth = day, month
            if day == 1 and month == 1:
                eday, emonth = 30, 12
                year_adj = year - 1
            elif day == 1 and month == 5:
                eday = 2
                year_adj = year
            elif day == 1 and month == 6 and year == 2015:
                eday = 2
                year_adj = year
            elif day == 16 and month == 1 and year >= 2016:
                eday = 17
                year_adj = year
            elif day == 16 and month == 12 and year == 2015:
                eday = 17
                year_adj = year
            else:
                year_adj = year

            url = metaurl.format(eday, emonth, year_adj + 543)
            links.append(url)

# 🔍 ดึงข้อมูลแต่ละงวด
lotto_data = []
for url in links:
    print(f"🔍 กำลังดึง: {url}")
    try:
        page_id = url.split("/")[-1]
        if not (page_id.isdigit() and len(page_id) == 8):
            print(f"⚠️ ลิงก์เพี้ยน: {url}")
            continue

        while True:
            try:
                response = requests.get(url, timeout=10)
                response.encoding = "utf-8"
                break
            except Exception as e:
                print(f"❌ ERROR: {e} ที่ {url} → ลองใหม่อีกที...")
                sleep(3)

        soup = BeautifulSoup(response.text, "html.parser")
        def extract(css): return [x.get_text(strip=True) for x in soup.select(css)]

        columns = soup.select(".lottocheck__column")
        result = {
            "id": page_id,
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
            print(f"🤔 ไม่รู้จักรูปแบบ column {len(columns)} คอลัมน์ ที่ {url}")
            result["status"] = "unknown-template"

        lotto_data.append(result)
        save_per_date(result)
        print(f"✅ ดึงสำเร็จ: {result['date']}")
        sleep(1)

    except Exception as e:
        print(f"❌ ERROR: {e} ที่ {url}")
        lotto_data.append({
            "id": page_id,
            "url": url,
            "status": f"error: {str(e)}"
        })

# ✅ รวม + push
update_main_json(lotto_data)
git_push(lotto_data)

print("\n📦 เสร็จแล้ว! แยกเก็บไฟล์ไว้ใน lotto_history/, รวมไว้ใน lotto_history.json และอัปขึ้น GitHub เรียบร้อย! ✅")
