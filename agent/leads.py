"""Find local businesses that have no website, using free OpenStreetMap data.

Main source: Nominatim (OpenStreetMap search) - one small query per business type,
1 request per second, as its usage policy asks.
Backup: one compact Overpass query, used only if Nominatim gives nothing.
"""
import csv, math, os, re, time
import requests

UA = {"User-Agent": "website-care-agent/1.1 (github.com/Nagasobila/website-care-agent)"}
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://overpass.private.coffee/api/interpreter"]
FIELDS = ["id", "slug", "name", "category", "address", "phone", "email",
          "lat", "lon", "found", "demo_url", "status", "notes"]
NO_SITE_TAGS = ("website", "contact:website", "url", "brand", "brand:wikidata")


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50]


def box(s):
    dl = s["radius_m"] / 111320
    dn = s["radius_m"] / (111320 * math.cos(math.radians(s["lat"])))
    return s["lat"] - dl, s["lon"] - dn, s["lat"] + dl, s["lon"] + dn


def dist_m(s, lat, lon):
    dy = (float(lat) - s["lat"]) * 111320
    dx = (float(lon) - s["lon"]) * 111320 * math.cos(math.radians(s["lat"]))
    return math.hypot(dx, dy)


def make_lead(osm_id, name, cat, tags, lat, lon, house="", road="", postcode=""):
    return {"id": osm_id, "name": name,
            "slug": slugify(name) + "-" + osm_id.split("/")[-1][-4:],
            "category": cat.replace("_", " "),
            "address": " ".join(x for x in (house, road, postcode) if x).strip(),
            "phone": tags.get("phone") or tags.get("contact:phone", ""),
            "email": tags.get("email") or tags.get("contact:email", ""),
            "lat": lat, "lon": lon, "found": time.strftime("%Y-%m-%d"),
            "demo_url": "", "status": "new", "notes": ""}


def from_nominatim(cfg):
    s = cfg["search"]
    south, west, north, east = box(s)
    viewbox = f"{west:.5f},{north:.5f},{east:.5f},{south:.5f}"
    out = []
    for cat in s["categories"]:
        key, val = cat.split("=", 1)
        params = {"q": val.replace("_", " "), "viewbox": viewbox, "bounded": 1,
                  "format": "jsonv2", "limit": 50, "extratags": 1, "addressdetails": 1}
        try:
            r = requests.get(NOMINATIM, params=params, headers=UA, timeout=30)
            r.raise_for_status()
            rows = r.json()
        except Exception as e:
            print(f"Nominatim '{val}' failed: {e}")
            rows = []
        for x in rows:
            tags = x.get("extratags") or {}
            if x.get("category") != key or x.get("type") != val or not x.get("name"):
                continue
            if any(tags.get(t) for t in NO_SITE_TAGS):
                continue
            if dist_m(s, x["lat"], x["lon"]) > s["radius_m"]:
                continue
            a = x.get("address") or {}
            out.append(make_lead(f'{x["osm_type"]}/{x["osm_id"]}', x["name"], val, tags,
                                 x["lat"], x["lon"], a.get("house_number", ""),
                                 a.get("road", ""), a.get("postcode", "")))
        print(f"  {val}: {len(rows)} found, {sum(1 for l in out if l['category'] == val.replace('_', ' '))} with no website")
        time.sleep(1.2)  # Nominatim policy: max 1 request per second
    return out


def from_overpass(cfg):
    s = cfg["search"]
    south, west, north, east = box(s)
    groups = {}
    for cat in s["categories"]:
        k, v = cat.split("=", 1)
        groups.setdefault(k, []).append(v)
    f = '["name"][!"website"][!"contact:website"][!"brand"]'
    q = (f"[out:json][timeout:60][bbox:{south:.5f},{west:.5f},{north:.5f},{east:.5f}];("
         + "".join(f'nwr["{k}"~"^({"|".join(vs)})$"]{f};' for k, vs in groups.items())
         + ");out center tags;")
    for attempt, url in enumerate(OVERPASS * 2):
        try:
            r = requests.post(url, data={"data": q}, headers=UA, timeout=75)
            r.raise_for_status()
            out = []
            for el in r.json()["elements"]:
                t = el.get("tags", {})
                cat = next((t[k] for k in ("amenity", "shop", "craft") if k in t), "business")
                lat = el.get("lat") or el.get("center", {}).get("lat")
                lon = el.get("lon") or el.get("center", {}).get("lon")
                if lat is None or dist_m(s, lat, lon) > s["radius_m"]:
                    continue
                out.append(make_lead(f'{el["type"]}/{el["id"]}', t["name"], cat, t, lat, lon,
                                     t.get("addr:housenumber", ""), t.get("addr:street", ""),
                                     t.get("addr:postcode", "")))
            return out
        except Exception as e:
            print(f"Overpass {url} failed: {e}")
            time.sleep(10 * (attempt + 1))
    return []


def fetch(cfg):
    print("Searching OpenStreetMap (Nominatim)...")
    found = from_nominatim(cfg)
    if not found:
        print("Nominatim gave nothing - trying Overpass backup...")
        found = from_overpass(cfg)
    return found


def score(lead):
    # Prefer leads you can actually find and contact.
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


def new_leads(cfg, existing, found):
    seen = {r["id"] for r in existing} | {r["name"].lower() for r in existing}
    fresh = []
    for lead in found:
        if lead["id"] in seen or lead["name"].lower() in seen:
            continue
        seen |= {lead["id"], lead["name"].lower()}
        fresh.append(lead)
    fresh.sort(key=score, reverse=True)
    return fresh[: cfg["search"]["new_leads_per_run"]]
