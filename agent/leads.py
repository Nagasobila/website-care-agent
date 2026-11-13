"""Find local businesses that have no website, using free OpenStreetMap data."""
import csv, os, re, time
import requests

OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"]
FIELDS = ["id", "slug", "name", "category", "address", "phone", "email",
          "lat", "lon", "found", "demo_url", "status", "notes"]


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50]


def build_query(cfg):
    s = cfg["search"]
    parts = []
    for cat in s["categories"]:
        k, v = cat.split("=", 1)
        for kind in ("node", "way"):
            parts.append(f'{kind}["{k}"="{v}"]["name"][!"website"][!"contact:website"]'
                         f'[!"brand"](around:{s["radius_m"]},{s["lat"]},{s["lon"]});')
    return "[out:json][timeout:60];(" + "".join(parts) + ");out center tags;"


def fetch_osm(cfg):
    q = build_query(cfg)
    for url in OVERPASS:
        try:
            r = requests.post(url, data={"data": q}, timeout=90,
                              headers={"User-Agent": "website-care-agent/1.0"})
            r.raise_for_status()
            return r.json()["elements"]
        except Exception as e:
            print(f"Overpass {url} failed: {e}")
            time.sleep(5)
    return []


def parse(el):
    t = el.get("tags", {})
    cat = next((f"{k}={t[k]}" for k in ("amenity", "shop", "craft") if k in t), "business")
    addr = " ".join(x for x in [t.get("addr:housenumber", ""), t.get("addr:street", ""),
                                t.get("addr:postcode", "")] if x).strip()
    lat = el.get("lat") or el.get("center", {}).get("lat")
    lon = el.get("lon") or el.get("center", {}).get("lon")
    return {"id": f'{el["type"]}/{el["id"]}', "name": t["name"],
            "slug": slugify(t["name"]) + "-" + str(el["id"])[-4:],
            "category": cat.split("=")[-1].replace("_", " "), "address": addr,
            "phone": t.get("phone") or t.get("contact:phone", ""),
            "email": t.get("email") or t.get("contact:email", ""),
            "lat": lat, "lon": lon, "found": time.strftime("%Y-%m-%d"),
            "demo_url": "", "status": "new", "notes": ""}


def score(lead):
    # Prefer leads you can actually contact and find.
    return bool(lead["address"]) * 2 + bool(lead["phone"]) * 2 + bool(lead["email"])


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def new_leads(cfg, existing, elements):
    seen = {r["id"] for r in existing} | {r["name"].lower() for r in existing}
    fresh = []
    for el in elements:
        if "name" not in el.get("tags", {}):
            continue
        lead = parse(el)
        if lead["id"] in seen or lead["name"].lower() in seen:
            continue
        seen |= {lead["id"], lead["name"].lower()}
        fresh.append(lead)
    fresh.sort(key=score, reverse=True)
    return fresh[: cfg["search"]["new_leads_per_run"]]
