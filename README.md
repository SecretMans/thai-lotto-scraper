# 🎯 Thai Lotto Scraper

> เก็บผลสลากกินแบ่งรัฐบาลไทยตั้งแต่ปี พ.ศ.2550 จนถึงปัจจุบัน พร้อมแยกเก็บไฟล์รายงวด + รวมไฟล์หลัก

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Sanook](https://img.shields.io/badge/Data%20Source-Sanook.com-orange)
![Auto Commit](https://img.shields.io/badge/Git-Auto%20Commit-green)
![MIT License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 📦 Features

- ดึงผลสลากฯ จาก **Sanook.com** ทุกงวด (1 และ 16 ของทุกเดือน)
- รองรับ **template เก่า-ใหม่** ของหน้าเว็บ Sanook
- บันทึกไฟล์แยกเป็นรายงวด (`lotto_history/YYYY-MM-DD.json`)
- รวมข้อมูลทั้งหมดไว้ใน `lotto_history.json`

---

## 🧠 ตัวอย่างผลลัพธ์ (`.json`)
```json
{
  "id": "30122549",
  "url": "https://news.sanook.com/lotto/check/30122549",
  "status": "success",
  "date": "30 ธันวาคม 2549",
  "first_prize": "000000",
  "three_front": [],
  "three_last": ["123", "456"],
  "two_digit": "89",
  "near_first": ["000001", "999999"],
  "second_prize": ["123456", "654321"],
  "third_prize": [...],
  "fourth_prize": [...],
  "fifth_prize": [...]
}
