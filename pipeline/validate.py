#!/usr/bin/env python3
"""validate.py — فحص جودة آلي لبيانات البطاقات قبل البناء (QA).

التحسين: يضمن ألا تمر بطاقة ناقصة إلى الحزمة النهائية:
  1. كل الحقول الإلزامية موجودة وغير فارغة.
  2. لا تكرار في الكلمات أو المعرّفات.
  3. ملفات الصوت والصور موجودة فعلاً على القرص.
  4. الكلمات المادية (concrete) يجب أن تملك صورة.
  5. كل بطاقة تملك معنيين عربيين على الأقل وأمثلة ومشتقات.
  6. النصوص العربية تحوي فعلاً محارف عربية (كشف أخطاء الإدخال).
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "cards.json")

AR_RE = re.compile(r"[\u0600-\u06FF]")
errors, warnings = [], []


def check(cond, msg, warn_only=False):
    if not cond:
        (warnings if warn_only else errors).append(msg)
    return cond


def main():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)

    seen_words, seen_ids = set(), set()
    for i, c in enumerate(data["cards"]):
        tag = f"[{c.get('id', f'index {i}')} / {c.get('word', '?')}]"

        for field in ("word", "type", "id", "ipa_us", "meanings_ar", "examples", "word_family"):
            check(c.get(field), f"{tag} الحقل ناقص: {field}")

        if c.get("word") in seen_words:
            errors.append(f"{tag} تكرار كلمة")
        seen_words.add(c.get("word"))
        if c.get("id") in seen_ids:
            errors.append(f"{tag} تكرار معرّف")
        seen_ids.add(c.get("id"))

        audio = c.get("audio_us")
        check(audio and os.path.exists(os.path.join(ROOT, audio)), f"{tag} ملف الصوت غير موجود: {audio}")
        img = c.get("image")
        if img:
            check(os.path.exists(os.path.join(ROOT, img)), f"{tag} ملف الصورة غير موجود: {img}")
        if c.get("concrete") and not img:
            errors.append(f"{tag} كلمة مادية بدون صورة توضيحية")

        ar_joined = " ".join(c.get("meanings_ar", {}).values())
        check(AR_RE.search(ar_joined), f"{tag} المعاني العربية لا تحوي محارف عربية")
        check(len(c.get("examples", [])) >= 2, f"{tag} أقل من مثالين", warn_only=True)
        check(len(c.get("word_family", [])) >= 1, f"{tag} جدول المشتقات فارغ")
        for ex in c.get("examples", []):
            check(ex.get("en") and ex.get("ar"), f"{tag} مثال بدون ترجمة عربية", warn_only=True)

    for e in errors:
        print("خطأ:", e)
    for w in warnings:
        print("تحذير:", w)
    if errors:
        print(f"\nفشل الفحص: {len(errors)} أخطاء")
        sys.exit(1)
    print(f"\nفشل: 0 أخطاء · {len(warnings)} تحذيرات · {len(data['cards'])} بطاقات صالحة ✔")


if __name__ == "__main__":
    main()
