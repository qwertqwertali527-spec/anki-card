#!/usr/bin/env python3
"""render_preview.py — توليد صفحة معاينة تفاعلية من data/cards.json.

تعرض كل بطاقة بوجهيها (أمامي/خلفي) بنفس تنسيق قالب أنكي، مع أزرار تنقّل،
حتى يعتمد العميل التصميم قبل بناء الحزمة الكاملة.
"""
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "cards.json")
OUT_DIR = os.path.join(ROOT, "preview")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(os.path.join(OUT_DIR, "media"), exist_ok=True)
    for c in data["cards"]:
        for p in (c.get("audio_us"), c.get("image")):
            if p and os.path.exists(os.path.join(ROOT, p)):
                shutil.copy2(os.path.join(ROOT, p), os.path.join(OUT_DIR, "media", os.path.basename(p)))

    slides = []
    for idx, c in enumerate(data["cards"]):
        audio = (
            f'<audio controls src="media/{os.path.basename(c["audio_us"])}"></audio>' if c.get("audio_us") else ""
        )
        img = (
            f'<div class="img"><img src="media/{os.path.basename(c["image"])}">'
            f'<div class="caption">{esc(c.get("image_caption", ""))}</div></div>'
            if c.get("image")
            else ""
        )

        front = f"""
        <div class="card-face">
          <div class="badge">{esc(c['type'])}</div>
          <div class="word">{esc(c['word'])}</div>
          <div class="ipa">{esc(c['ipa_us'])} &nbsp;<span class="uk">UK {esc(c.get('ipa_uk',''))}</span></div>
          <div class="audio">{audio}</div>
          {img}
          {f'<div class="hint">&ldquo;{esc(c["examples"][0]["en"])}&rdquo;</div>' if c.get('examples') else ''}
        </div>"""

        defs = ""
        for pos in c["pos"]:
            defs += f'<div class="pos">{esc(pos["label"])}</div><ol class="definitions">'
            defs += "".join(f"<li>{esc(d)}</li>" for d in pos["definitions_en"]) + "</ol>"
        ar = "".join(f'<div class="ar"><b>{esc(k)}:</b> {esc(v)}</div>' for k, v in c["meanings_ar"].items())
        syn = "".join(f"<span>{esc(s)}</span>" for s in c["synonyms"])
        exs = "<ol class='examples'>" + "".join(
            f'<li><span class="en">{esc(e["en"])}</span><span class="artr">{esc(e.get("ar",""))}</span>'
            f'<span class="src">{esc(e.get("source",""))}</span></li>'
            for e in c["examples"]
        ) + "</ol>"
        fam = (
            "<table class='fam'><tr><th>Form</th><th>Type</th><th>Definition (EN)</th><th>المعنى (عربي)</th></tr>"
            + "".join(
                f"<tr><td><b>{esc(w['form'])}</b></td><td>{esc(w['form_type'])}</td>"
                f"<td>{esc(w['def_en'])}</td><td class='far'>{esc(w['ar'])}</td></tr>"
                for w in c["word_family"]
            )
            + "</table>"
        )

        back = f"""
        <div class="card-face">
          <div class="badge">{esc(c['type'])} · الوجه الخلفي</div>
          <div class="back-word">{esc(c['word'])}</div>
          <div class="ipa">{esc(c['ipa_us'])} &nbsp;<span class="uk">UK {esc(c.get('ipa_uk',''))}</span></div>
          <div class="audio">{audio}</div>
          <h3 class="sec">المعاني بالعربية</h3>{ar}
          <h3 class="sec">Definitions (EN)</h3>{defs}
          <h3 class="sec">Synonyms — المرادفات</h3><div class="chips">{syn}</div>
          <h3 class="sec">Examples — أمثلة سياقية</h3>{exs}
          {img}
          <h3 class="sec">Word Family — الاشتقاقات والتفرعات</h3>{fam}
          {f'<div class="note">{esc(c["notes"])}</div>' if c.get('notes') else ''}
          <div class="small">ID {esc(c['id'])} · PDF p. {esc(c.get('pdf_page','—'))}</div>
        </div>"""

        slides.append({"front": front, "back": back, "word": c["word"]})

    nav = "".join(
        f'<button class="nav-btn" data-i="{i}">{esc(s["word"])}</button>' for i, s in enumerate(slides)
    )
    bodies = "".join(
        f'<section class="slide" data-i="{i}"><div class="side front-side">{s["front"]}</div>'
        f'<div class="side back-side hidden">{s["back"]}</div></section>'
        for i, s in enumerate(slides)
    )

    css = open(os.path.join(ROOT, "pipeline", "preview.css"), encoding="utf-8").read()
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>عينة بطاقات Anki — English Vocabulary</title>
<style>{css}</style>
</head>
<body>
<header>
  <h1>English Vocabulary — عينة البطاقات</h1>
  <p>نفس التصميم المطبَّق داخل Anki · اضغط البطاقة لقلبها</p>
  <nav>{nav}</nav>
</header>
<main>{bodies}</main>
<footer>عينة من 3 بطاقات: كلمة (produce) · اسم مادي بصورة (umbrella) · فعل مركّب (give up)</footer>
<script>
const slides=[...document.querySelectorAll('.slide')];
let cur=0;
function show(i){{cur=i;slides.forEach((s,j)=>s.classList.toggle('active',i===j));
document.querySelectorAll('.nav-btn').forEach((b,j)=>b.classList.toggle('active',i===j));
slides[i].querySelectorAll('.side').forEach((el,k)=>el.classList.toggle('hidden',k>0));
window.scrollTo({{top:0,behavior:'smooth'}});}}
slides.forEach(s=>s.addEventListener('click',()=>{{
 const f=s.querySelector('.front-side'),b=s.querySelector('.back-side');
 const showBack=f.classList.contains('hidden');
 f.classList.toggle('hidden',showBack);b.classList.toggle('hidden',!showBack);
}}));
document.querySelectorAll('.nav-btn').forEach(b=>b.addEventListener('click',e=>{{e.stopPropagation();show(+b.dataset.i);}}));
show(0);
</script>
</body>
</html>"""
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("OK:", os.path.join(OUT_DIR, "index.html"))


if __name__ == "__main__":
    build()
