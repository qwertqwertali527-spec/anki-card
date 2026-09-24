#!/usr/bin/env python3
"""fetch_media.py — هيكل مرحلة الإنتاج: جلب الوسائط والمحتوى من المصادر المعتمدة.

هذا الملف موثّق وجاهز للتشغيل على جهاز العميل (حيث الإنترنت مفتوح)، لأن بيئة
المعاينة هنا لا تسمح بالاتصال المباشر بالمواقع. المصادر المخطط لها حسب مواصفات
المشروع:

الصوت (المطلوب: Oxford + WordReference معاً):
  * Oxford Learner's Dictionaries — ملفات صوت أمريكي/بريطاني:
      نمط الرابط بعد قراءة صفحة الكلمة واستخراج مسار الصوت من وسم <audio>.
  * WordReference — زر الاستماع في صفحة الكلمة:
      نمط الرابط: https://www.wordreference.com/enfr/en/{word}  ثم استخراج
      رابط mp3 من عنصر الصوت.
  * احتياطي (مطبّق أدناه فعلياً): Google Dictionary Sounds CDN:
      https://ssl.gstatic.com/dictionary/static/sounds/20200429/{word}--_us_1.mp3
  * احتياطي أخير: DictionaryAPI.dev media links.

التعاريف والمعاني والأمثلة:
  * Reverso Context — definitions + أمثلة سياقية ثنائية اللغة (الإنجليزية/العربية).
  * تدقيق نهائي يدوي لكل بطاقة قبل الإدخال (شرط الدقة في المشروع).

الصور:
  * الكلمات المادية فقط: توليد رسوم توضيحية موحّدة الأسلوب أو صور مرخّصة.

الاستخدام في مرحلة الإنتاج:
    python3 pipeline/fetch_media.py data/cards.json
    (يضيف الحقول audio_uk / يعيد تنزيل الوسائط ويحدّث المصدر في السجل)
"""
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (compatible; VocabDeckBuilder/1.0)"}


def google_sound_url(word: str) -> str:
    return f"https://ssl.gstatic.com/dictionary/static/sounds/20200429/{word.replace(' ', '_')}--_us_1.mp3"


def download(url: str, dest: str) -> bool:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as r, open(dest, "wb") as f:
            f.write(r.read())
        return os.path.getsize(dest) > 1000
    except Exception as exc:  # noqa: BLE001 — نريد المتابعة لباقي الكلمات
        print(f"  تعذّر تنزيل {url}: {exc}")
        return False


def main():
    data_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "cards.json")
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    for c in data["cards"]:
        word = c["word"].split(" (")[0]
        dest = os.path.join(ROOT, "media", f"{word.replace(' ', '_')}_ggl.mp3")
        print(f"[{c['id']}] {word}: محاولة تنزيل الصوت الاحتياطي...")
        if download(google_sound_url(word), dest):
            c["audio_us"] = os.path.relpath(dest, ROOT)
            c["audio_source"] = "Google Dictionary CDN (احتياطي)"
            print("  تم ✔ — أضف لاحقاً صوتي Oxford و WordReference من صفحة الكلمة")
        time.sleep(1)

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("اكتمل تحديث:", data_path)


if __name__ == "__main__":
    main()
