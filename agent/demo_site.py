"""Render a one-page demo website for a lead."""
from html import escape as e
from urllib.parse import quote

PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{name} — demo website</title>
<style>
:root{{--c:{colour}}}
*{{box-sizing:border-box;margin:0}}body{{font-family:system-ui,Segoe UI,Arial,sans-serif;color:#1d1d1d;line-height:1.55}}
.demo{{background:#fff4c2;color:#5a4a00;font-size:13px;text-align:center;padding:8px 12px}}
header{{background:var(--c);color:#fff;padding:72px 20px 64px;text-align:center}}
h1{{font-size:clamp(30px,6vw,52px);letter-spacing:-.5px}}header p{{opacity:.9;font-size:19px;margin-top:8px}}
.btn{{display:inline-block;margin-top:22px;background:#fff;color:var(--c);padding:12px 22px;border-radius:999px;font-weight:600;text-decoration:none}}
main{{max-width:880px;margin:auto;padding:48px 20px}}section{{margin-bottom:44px}}
h2{{font-size:24px;margin-bottom:14px;color:var(--c)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}}
.card{{border:1px solid #e6e6e6;border-radius:12px;padding:18px;background:#fafafa}}
.why li{{margin:6px 0 6px 18px}}iframe{{width:100%;height:280px;border:0;border-radius:12px}}
footer{{text-align:center;color:#777;font-size:13px;padding:30px 20px;border-top:1px solid #eee}}
</style></head><body>
<div class="demo">Demo design by {studio} — not the official website of {name}. Details to be confirmed by the owner.</div>
<header><h1>{name}</h1><p>{tagline}</p>{cta}</header>
<main>
<section><h2>Welcome</h2><p>{intro}</p></section>
<section><h2>What we offer</h2><div class="grid">{services}</div></section>
<section><h2>Why locals choose us</h2><ul class="why">{why}</ul></section>
<section><h2>Find us</h2><p>{address}</p>{map}</section>
</main>
<footer>{name} · {address} &nbsp;|&nbsp; Website by {studio}</footer>
</body></html>"""


def render(lead, copy, cfg):
    phone = lead.get("phone", "")
    cta = f'<a class="btn" href="tel:{e(phone.replace(" ", ""))}">Call {e(phone)}</a>' if phone else ""
    mp = ""
    if lead.get("lat") and lead.get("lon"):
        lat, lon = float(lead["lat"]), float(lead["lon"])
        bbox = f"{lon-.004},{lat-.0025},{lon+.004},{lat+.0025}"
        mp = (f'<iframe loading="lazy" title="map" src="https://www.openstreetmap.org/export/embed.html'
              f'?bbox={quote(bbox)}&layer=mapnik&marker={lat},{lon}"></iframe>')
    return PAGE.format(
        name=e(lead["name"]), studio=e(cfg["you"]["business_name"]), colour=copy["colour"],
        tagline=e(str(copy["tagline"])), intro=e(str(copy["intro"])), cta=cta,
        services="".join(f'<div class="card">{e(str(s))}</div>' for s in copy["services"][:6]),
        why="".join(f"<li>{e(str(w))}</li>" for w in copy["why"][:5]),
        address=e(lead.get("address") or "London"), map=mp)
