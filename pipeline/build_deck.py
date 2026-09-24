#!/usr/bin/env python3
"""build_deck.py — بناء حزمة أنكي (.apkg) من ملف واحد لبيانات البطاقات.

المصدر الوحيد للحقيقة: data/cards.json
المخرج: output/sample_deck.apkg

التصميم وفق مواصفات المشروع:
  * وجه البطاقة: إنجليزي بالكامل (الكلمة + النطق + الصوت + الصورة + مثال سياقي).
  * ظهر البطاقة: جميع المعاني العربية + التعاريف الإنجليزية + المرادفات +
    الأمثلة مع ترجمتها + جدول المشتقات + الملاحظات.
  * بطاقة عكسية اختيارية (عربي ← إنجليزي) مبنية على نفس نوع الملاحظة.
"""
import json
import os
import re

import genanki

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "cards.json")
OUT = os.path.join(ROOT, "output", "sample_deck.apkg")

MODEL_ID = 1789001234
DECK_ID = 2059400110

FIELDS = [
    {"name": "Word"},
    {"name": "Type"},
    {"name": "ID"},
    {"name": "PDFPage"},
    {"name": "IPA_US"},
    {"name": "IPA_UK"},
    {"name": "AudioUS"},
    {"name": "AudioUK"},
    {"name": "DefinitionEN"},
    {"name": "MeaningsAR"},
    {"name": "Synonyms"},
    {"name": "ExamplesEN"},
    {"name": "ExampleHint"},
    {"name": "Image"},
    {"name": "WordFamily"},
    {"name": "Notes"},
]

CSS = """
.card { font-family: "Segoe UI", "Noto Sans Arabic", "Noto Naskh Arabic", Tahoma, Arial, sans-serif;
        background: #f6f8fa; color: #1f2937; text-align: left; line-height: 1.55; padding: 6px; }
.wrap { max-width: 680px; margin: 0 auto; }
.badge { display: inline-block; background: #0f766e; color: #ffffff; border-radius: 999px;
         padding: 2px 12px; font-size: 12px; letter-spacing: .5px; margin-bottom: 10px; }
.word { font-size: 40px; font-weight: 700; color: #0f172a; margin: 4px 0 2px; }
.ipa { font-size: 17px; color: #475569; margin-bottom: 6px; }
.ipa .uk { color: #94a3b8; }
.audio { font-size: 26px; margin: 2px 0 8px; }
.img { margin: 10px 0; text-align: center; }
.img img { max-width: 78%; max-height: 240px; border-radius: 14px;
           box-shadow: 0 4px 14px rgba(15, 23, 42, .12); }
.caption { font-size: 13px; color: #64748b; margin-top: 4px; }
.hint { background: #eef6f6; border-left: 4px solid #0f766e; border-radius: 8px;
        padding: 10px 14px; margin-top: 14px; font-size: 16px; color: #334155; font-style: italic; }
hr.sep { border: none; border-top: 1px solid #e2e8f0; margin: 14px 0; }
h3.sec { font-size: 15px; text-transform: uppercase; letter-spacing: 1px; color: #0f766e;
         border-bottom: 2px solid #ccfbf1; padding-bottom: 3px; margin: 18px 0 8px; }
.ar { direction: rtl; text-align: right; font-size: 20px; background: #fffbeb;
      border: 1px solid #fde68a; border-radius: 10px; padding: 10px 14px; margin: 6px 0; }
.ar b { color: #b45309; }
.definitions li { margin-bottom: 6px; }
.definitions .pos { font-weight: 700; color: #0f766e; }
.chips span { display: inline-block; background: #e0f2fe; color: #075985; border-radius: 999px;
              padding: 2px 10px; margin: 2px 4px 2px 0; font-size: 14px; }
ol.examples { padding-left: 20px; }
ol.examples li { margin-bottom: 8px; }
ol.examples .en { font-weight: 600; }
ol.examples .artr { direction: rtl; text-align: right; color: #7c5e10; font-size: 15px; display: block; }
table.fam { border-collapse: collapse; width: 100%; font-size: 14px; }
table.fam th { background: #0f766e; color: #fff; padding: 6px 8px; text-align: left; }
table.fam td { border: 1px solid #d1d5db; padding: 6px 8px; vertical-align: top; }
table.fam tr:nth-child(even) td { background: #f1f5f9; }
table.fam td.far { direction: rtl; text-align: right; font-size: 15px; }
.note { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px;
        padding: 8px 12px; font-size: 14px; color: #166534; margin-top: 12px; }
.small { font-size: 13px; color: #94a3b8; }
.back-word { font-size: 30px; font-weight: 700; color: #0f172a; }
"""

FRONT = """
<div class="wrap">
  <div class="badge">{{Type}}</div>
  <div class="word">{{Word}}</div>
  <div class="ipa">{{IPA_US}} &nbsp;<span class="uk">UK {{IPA_UK}}</span></div>
  <div class="audio">{{AudioUS}} {{AudioUK}}</div>
  {{#Image}}<div class="img">{{Image}}</div>{{/Image}}
  {{#ExampleHint}}<div class="hint">&ldquo;{{ExampleHint}}&rdquo;</div>{{/ExampleHint}}
</div>
"""

BACK = """
<div class="wrap">
  <div class="badge">{{Type}}</div>
  <div class="back-word">{{Word}}</div>
  <div class="ipa">{{IPA_US}} &nbsp;<span class="uk">UK {{IPA_UK}}</span></div>
  <div class="audio">{{AudioUS}} {{AudioUK}}</div>

  <h3 class="sec">المعاني بالعربية</h3>
  {{MeaningsAR}}

  <h3 class="sec">Definitions (EN)</h3>
  {{DefinitionEN}}

  <h3 class="sec">Synonyms</h3>
  <div class="chips">{{Synonyms}}</div>

  <h3 class="sec">Examples</h3>
  {{ExamplesEN}}

  {{#Image}}<div class="img">{{Image}}</div>{{/Image}}

  <h3 class="sec">Word Family &amp; Derivatives — الاشتقاقات والتفرعات</h3>
  {{WordFamily}}

  {{#Notes}}<div class="note">{{Notes}}</div>{{/Notes}}
  <div class="small" style="margin-top:10px">ID {{ID}} · PDF p.{{PDFPage}}</div>
</div>
"""

REVERSE_FRONT = """
<div class="wrap">
  <div class="badge">{{Type}} · عكسي</div>
  <h3 class="sec">المعاني بالعربية — ما الكلمة الإنجليزية؟</h3>
  {{MeaningsAR}}
  {{#Image}}<div class="img">{{Image}}</div>{{/Image}}
</div>
"""

REVERSE_BACK = """
<div class="wrap">
  <div class="word">{{Word}}</div>
  <div class="ipa">{{IPA_US}}</div>
  <div class="audio">{{AudioUS}} {{AudioUK}}</div>
  {{DefinitionEN}}
  <hr class="sep">
  {{MeaningsAR}}
</div>
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def base(path: str) -> str:
    return os.path.basename(path) if path else ""


def build():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)

    model = genanki.Model(
        MODEL_ID,
        "Vocab Pro — EN→AR + Reverse",
        fields=FIELDS,
        templates=[
            {"name": "EN → AR (Full)", "qfmt": FRONT, "afmt": BACK},
            {"name": "AR → EN (Reverse)", "qfmt": REVERSE_FRONT, "afmt": REVERSE_BACK},
        ],
        css=CSS,
    )
    deck = genanki.Deck(DECK_ID, data["deck_name"], description=data.get("deck_description", ""))

    media_files = []
    for c in data["cards"]:
        audio_us = base(c.get("audio_us", ""))
        audio_uk = base(c.get("audio_uk", ""))
        img = base(c.get("image", ""))

        defs_html = ""
        for pos in c["pos"]:
            defs_html += f'<div class="pos">{esc(pos["label"])}</div><ol class="definitions">'
            defs_html += "".join(f"<li>{esc(d)}</li>" for d in pos["definitions_en"])
            defs_html += "</ol>"

        ar_html = "".join(
            f'<div class="ar"><b>{esc(k)}:</b> {esc(v)}</div>' for k, v in c["meanings_ar"].items()
        )

        syn_html = "".join(f"<span>{esc(s)}</span>" for s in c["synonyms"])

        ex_html = "<ol class='examples'>"
        for ex in c["examples"]:
            ex_html += f'<li><span class="en">{esc(ex["en"])}</span>'
            if ex.get("ar"):
                ex_html += f'<span class="artr">{esc(ex["ar"])}</span>'
            ex_html += "</li>"
        ex_html += "</ol>"

        hint = esc(c["examples"][0]["en"]) if c["examples"] else ""

        fam_html = (
            "<table class='fam'><tr><th>Form</th><th>Type</th>"
            "<th>Definition (EN)</th><th>المعنى (عربي)</th></tr>"
        )
        for w in c["word_family"]:
            fam_html += (
                f"<tr><td><b>{esc(w['form'])}</b></td><td>{esc(w['form_type'])}</td>"
                f"<td>{esc(w['def_en'])}</td><td class='far'>{esc(w['ar'])}</td></tr>"
            )
        fam_html += "</table>"

        note = genanki.Note(
            model=model,
            fields=[
                c["word"],
                c["type"],
                c["id"],
                str(c.get("pdf_page", "—")),
                c.get("ipa_us", ""),
                c.get("ipa_uk", ""),
                f"[sound:{audio_us}]" if audio_us else "",
                f"[sound:{audio_uk}]" if audio_uk else "",
                defs_html,
                ar_html,
                syn_html,
                ex_html,
                hint,
                f'<img src="{img}">' if img else "",
                fam_html,
                c.get("notes", ""),
            ],
            guid=genanki.guid_for(c["id"]),
            tags=["sample", re.sub(r"[^a-z0-9-]", "-", c["type"].lower())],
        )
        deck.add_note(note)

        for p in (c.get("audio_us"), c.get("audio_uk"), c.get("image")):
            if p:
                full = os.path.join(ROOT, p)
                if os.path.exists(full):
                    media_files.append(full)
                else:
                    raise SystemExit(f"media missing: {full}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    genanki.Package(deck, media_files).write_to_file(OUT)
    print(f"OK: {OUT} — {len(data['cards'])} notes, {len(media_files)} media files")


if __name__ == "__main__":
    build()
