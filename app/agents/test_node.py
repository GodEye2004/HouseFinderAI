"""
تست جامع سیستم مشاور املاک
"""

import requests
import json
import time
from typing import Optional

BASE_URL = "http://localhost:8000"


def test_health():
    """تست سلامت سیستم"""
    print("\n" + "=" * 60)
    print("🏥 تست سلامت سیستم")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/health")
    data = response.json()

    print(f"✅ وضعیت: {data['status']}")
    print(f"📊 آمار املاک: {data['properties_stats']}")

    return data['status'] == 'healthy'


def test_conversation_flow():
    """تست flow کامل گفتگو"""
    print("\n" + "=" * 60)
    print("💬 تست Flow گفتگو")
    print("=" * 60)

    # ایجاد session
    session_response = requests.post(f"{BASE_URL}/session/new")
    session_id = session_response.json()['session_id']
    print(f"✅ Session: {session_id}")

    # گفتگوی کامل
    conversation = [
        ("سلام", "باید خوشامد بگه"),
        ("می‌خوام ملک بخرم", "باید بپرسه چه نوع ملکی"),
        ("آپارتمان", "باید بپرسه کجا"),
        ("تهران", "باید بپرسه بودجه"),
        ("5 میلیارد", "باید بپرسه متراژ یا جستجو کنه"),
        ("حدود 90 متر", "باید جستجو کنه و نتایج نشون بده"),
    ]

    for i, (message, expected) in enumerate(conversation, 1):
        print(f"\n📍 مرحله {i}:")
        print(f"   👤 کاربر: {message}")
        print(f"   🎯 انتظار: {expected}")

        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": message,
                "session_id": session_id
            }
        )

        data = response.json()
        print(f"   🤖 سیستم: {data['response'][:100]}...")
        print(f"   📊 وضعیت: {data['state']}")

        if data.get('recommended_properties'):
            print(f"   🏠 تعداد املاک: {len(data['recommended_properties'])}")

        time.sleep(0.5)  # تاخیر کوچک

    return session_id


def test_search_functionality(session_id: str):
    """تست قابلیت جستجو"""
    print("\n" + "=" * 60)
    print("🔍 تست جستجو")
    print("=" * 60)

    # جستجوی با فیلترهای مشخص
    test_cases = [
        {
            "message": "می‌خوام آپارتمان در تهران با بودجه 10 میلیارد و متراژ 100 متر",
            "expected_results": True
        },
        {
            "message": "ویلا در شمال با بودجه 8 میلیارد",
            "expected_results": True
        },
    ]

    for test in test_cases:
        print(f"\n📝 تست: {test['message']}")

        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": test['message'],
                "session_id": session_id
            }
        )

        data = response.json()
        has_results = data.get('recommended_properties') is not None

        print(f"   {'✅' if has_results == test['expected_results'] else '❌'} نتایج: {has_results}")

        if has_results:
            print(f"   🏠 تعداد: {len(data['recommended_properties'])}")


def test_memory():
    """تست حافظه مکالمه"""
    print("\n" + "=" * 60)
    print("🧠 تست حافظه")
    print("=" * 60)

    # ایجاد session جدید
    session_response = requests.post(f"{BASE_URL}/session/new")
    session_id = session_response.json()['session_id']

    # اطلاعات رو به تدریج بده
    messages = [
        "بودجه‌م 5 میلیاره",
        "تهران",
        "آپارتمان می‌خوام",
        "90 متر",
    ]

    for msg in messages:
        print(f"   📤 {msg}")
        requests.post(
            f"{BASE_URL}/chat",
            json={"message": msg, "session_id": session_id}
        )
        time.sleep(0.3)

    # چک کردن حافظه
    memory_response = requests.get(f"{BASE_URL}/session/{session_id}/memory")
    memory = memory_response.json()

    print(f"\n📊 حافظه:")
    print(memory['summary'])

    return 'بودجه' in memory['summary']


def test_exchange():
    """تست معاوضه"""
    print("\n" + "=" * 60)
    print("🔄 تست معاوضه")
    print("=" * 60)

    session_response = requests.post(f"{BASE_URL}/session/new")
    session_id = session_response.json()['session_id']

    messages = [
        "می‌خوام ملک بخرم",
        "آپارتمان در تهران با بودجه 9 میلیارد",
        "یه ماشین دارم می‌خوام معاوضه کنم",
        "پراید، ارزشش 500 میلیون",
    ]

    for msg in messages:
        print(f"   📤 {msg}")
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": msg, "session_id": session_id}
        )
        print(f"   📥 {response.json()['response'][:80]}...")
        time.sleep(0.3)


def test_property_submission():
    """تست ثبت آگهی"""
    print("\n" + "=" * 60)
    print("📝 تست ثبت آگهی")
    print("=" * 60)

    property_data = {
        "title": "آپارتمان تست 100 متری",
        "property_type": "آپارتمان",
        "transaction_type": "فروش",
        "price": 5000000000,
        "area": 100,
        "city": "تهران",
        "district": "سعادت‌آباد",
        "description": "این یک آگهی تستی است برای بررسی سیستم",
        "owner_phone": "09121234567",
        "has_parking": True,
        "has_elevator": True,
        "has_storage": True
    }

    response = requests.post(
        f"{BASE_URL}/properties/submit",
        json=property_data
    )

    data = response.json()

    if data['success']:
        print(f"   ✅ آگهی ثبت شد: {data['property_id']}")
        print(f"   📝 پیام: {data['message']}")

        # بررسی لیست آگهی‌ها
        submissions = requests.get(f"{BASE_URL}/properties/submissions")
        print(f"   📊 تعداد کل آگهی‌ها: {submissions.json()['count']}")

        return True
    else:
        print(f"   ❌ خطا: {data.get('message')}")
        return False


def test_fallback_mode():
    """تست حالت fallback (بدون LLM)"""
    print("\n" + "=" * 60)
    print("⚠️ تست حالت Fallback")
    print("=" * 60)
    print("این تست بررسی می‌کنه که سیستم بدون LLM هم کار کنه")

    session_response = requests.post(f"{BASE_URL}/session/new")
    session_id = session_response.json()['session_id']

    # حتی اگه LLM کار نکنه، این باید جواب بده
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "سلام", "session_id": session_id}
    )

    data = response.json()
    has_response = len(data['response']) > 0

    print(f"   {'✅' if has_response else '❌'} پاسخ دریافت شد")
    print(f"   📝 {data['response'][:100]}...")

    return has_response


def run_all_tests():
    """اجرای تمام تست‌ها"""
    print("\n" + "🚀" * 30)
    print(" " * 20 + "شروع تست‌های جامع")
    print("🚀" * 30)

    results = {}

    try:
        # 1. تست سلامت
        results['health'] = test_health()
        time.sleep(1)

        # 2. تست گفتگو
        session_id = test_conversation_flow()
        results['conversation'] = True
        time.sleep(1)

        # 3. تست جستجو
        test_search_functionality(session_id)
        results['search'] = True
        time.sleep(1)

        # 4. تست حافظه
        results['memory'] = test_memory()
        time.sleep(1)

        # 5. تست معاوضه
        test_exchange()
        results['exchange'] = True
        time.sleep(1)

        # 6. تست ثبت آگهی
        results['submission'] = test_property_submission()
        time.sleep(1)

        # 7. تست fallback
        results['fallback'] = test_fallback_mode()

    except Exception as e:
        print(f"\n❌ خطای کلی: {e}")
        import traceback
        traceback.print_exc()

    # نمایش نتایج
    print("\n" + "=" * 60)
    print("📊 نتایج نهایی")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ موفق" if result else "❌ ناموفق"
        print(f"   {test_name.ljust(20)}: {status}")

    success_rate = sum(results.values()) / len(results) * 100
    print(f"\n🎯 درصد موفقیت: {success_rate:.1f}%")

    if success_rate == 100:
        print("🎉 تمام تست‌ها موفق بودند!")
    elif success_rate >= 80:
        print("✅ اکثر تست‌ها موفق بودند")
    else:
        print("⚠️ برخی تست‌ها ناموفق بودند")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️ تست‌ها توسط کاربر متوقف شد")
    except Exception as e:
        print(f"\n❌ خطای کلی: {e}")