"""
اسکریپت تست برای چت با سیستم مشاور املاک (نسخه 2.0)
هماهنگ با ساختار حافظه، current_stage جدید و پاسخ‌های ChatResponse
"""

import requests
import json
from typing import Optional


class RealEstateChatTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None

    # -----------------------------
    #   ایجاد Session
    # -----------------------------
    def create_session(self):
        response = requests.post(f"{self.base_url}/session/new")
        data = response.json()
        self.session_id = data["session_id"]
        print(f"✅ Session ایجاد شد: {self.session_id}\n")
        return self.session_id

    # -----------------------------
    #   ارسال پیام
    # -----------------------------
    def send_message(self, message: str):
        payload = {
            "message": message,
            "session_id": self.session_id
        }

        response = requests.post(f"{self.base_url}/chat", json=payload)
        data = response.json()

        print(f"👤 شما: {message}")
        print(f"🤖 سیستم:\n{data['response']}\n")
        print("=" * 60 + "\n")

        # چاپ نتایج جستجو (در صورت وجود)
        if data.get("recommended_properties"):
            print("📋 املاک پیشنهادی:")
            for i, prop in enumerate(data["recommended_properties"], 1):
                print(f"   {i}. {prop['title']} - تطابق: {prop['match_percentage']}%")
            print()

        # چاپ فیلدهای ناقص
        if data.get("missing_fields"):
            print(f"❌ فیلدهای ناقص: {', '.join(data['missing_fields'])}\n")

        return data

    # -----------------------------
    #   اجرای گفتگو (Demo)
    # -----------------------------
    def run_test_conversation(self):
        print("=" * 60)
        print("🏡 تست سیستم مشاور املاک هوشمند")
        print("=" * 60 + "\n")

        self.create_session()

        messages = [
            "سلام",
            "می‌خوام یه آپارتمان در تهران بخرم",
            "بودجه‌م حدود 6 میلیارد تومنه",
            "متراژ حدود 100 متر می‌خوام",
            "ترجیحا تو پونک",
            "اگه بشه نصفش رو با طلا معاوضه کنم"
        ]

        for msg in messages:
            self.send_message(msg)
            input("⏎ Enter برای ادامه...")
            print()


# -----------------------------
#   تست کوئری پیچیده
# -----------------------------
def test_complex_query():
        tester = RealEstateChatTester()
        tester.create_session()

        complex_message = """می‌خوام یه آپارتمان تو سعادت‌آباد بخرم. 
بودجم ۵ میلیارد، حداقل ۸۵ متر، سال ساخت ۱۳۹۸، 
آسانسور، پارکینگ و انباری، سند تک‌برگ."""

        print("📝 ارسال کوئری پیچیده...\n")
        result = tester.send_message(complex_message)

        # اگر سیستم ارزش طلا خواست
        if result.get("requires_input"):
            gold_value = "3 میلیارد تومان"
            print(f"💬 سیستم ازت ورودی خواسته؛ ارسال می‌کنم: {gold_value}\n")
            result = tester.send_message(gold_value)

        print("\n📊 نتیجه نهایی:")
        print(f"   وضعیت: {result.get('state')}")
        print(f"   تعداد املاک یافت‌شده: {len(result.get('recommended_properties', []))}")

        if result.get("recommended_properties"):
            print("\n📋 لیست املاک پیشنهادی:")
            for i, prop in enumerate(result["recommended_properties"], 1):
                print(f"   {i}. {prop['title']} - امتیاز: {prop['match_percentage']}%")


# -----------------------------
#   تست سناریوی معاوضه
# -----------------------------
def test_exchange_scenario():
    print("\n" + "="*60)
    print("🔄 تست سناریوی معاوضه")
    print("="*60 + "\n")

    tester = RealEstateChatTester()
    tester.create_session()

    messages = [
        "سلام، می‌خوام ملک بخرم",
        "یه آپارتمان 100 متری در تهران با بودجه 9 میلیارد",
        "یه ماشینم دارم برای معاوضه",
        "ماشین پراید به ارزش 500 میلیون"
    ]

    for msg in messages:
        tester.send_message(msg)
        input("⏎ Enter برای ادامه...")
        print()


# -----------------------------
#   تست کامل API
# -----------------------------
def test_api_endpoints():
    base_url = "http://localhost:8000"

    print("\n" + "="*60)
    print("🧪 تست Endpoint‌ها")
    print("="*60 + "\n")

    # health
    print("1) Health Check:")
    res = requests.get(f"{base_url}/health")
    print(res.json(), "\n")

    # properties
    print("2) Properties:")
    res = requests.get(f"{base_url}/properties")
    props = res.json()
    print(f"تعداد املاک: {props['count']}\n")

    # new session
    print("3) Session جدید:")
    res = requests.post(f"{base_url}/session/new")
    print(res.json(), "\n")

    # get session
    print("4) اطلاعات Session:")
    sid = res.json()["session_id"]
    res = requests.get(f"{base_url}/session/{sid}")
    print(res.json(), "\n")

    print("✅ API کاملا سالم است")


# -----------------------------
#   ورود به برنامه
# -----------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "api":
            test_api_endpoints()
        elif sys.argv[1] == "exchange":
            test_exchange_scenario()
        elif sys.argv[1] == "complex":
            test_complex_query()
        else:
            print("استفاده: python test_chat.py [api|exchange|complex]")
    else:
        test_complex_query()
