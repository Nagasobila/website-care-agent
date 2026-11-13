"""Write demo-site copy and outreach messages with a free AI model (Groq, then Gemini).
Falls back to plain templates if no AI key is set, so the agent never stops."""
import json, os, re
import requests

COPY_PROMPT = """You write website copy for a small local business in London.
Business: {name}
Type: {category}
Address: {address}

Return ONLY JSON with these keys:
  "tagline": max 8 words,
  "intro": 2 warm sentences about what this kind of business offers locals,
  "services": list of 4 short typical services for this type of business,
  "why": list of 3 short reasons to visit (generic, e.g. "Friendly local team"),
  "colour": a hex colour that suits the business type.
Rules: do NOT invent prices, opening hours, reviews, awards, years in business,
staff names or any specific claim. Keep it generic and true for any {category}."""


def _json(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else None


def ask_ai(prompt, cfg):
    if os.getenv("GROQ_API_KEY"):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", timeout=60,
                              headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
                              json={"model": cfg["ai"]["groq_model"], "temperature": 0.6,
                                    "messages": [{"role": "user", "content": prompt}]})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Groq failed: {e}")
    if os.getenv("GEMINI_API_KEY"):
        try:
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{cfg['ai']['gemini_model']}:generateContent?key={os.environ['GEMINI_API_KEY']}")
            r = requests.post(url, timeout=60,
                              json={"contents": [{"parts": [{"text": prompt}]}]})
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"Gemini failed: {e}")
    return None


def fallback_copy(lead):
    c = lead["category"]
    return {"tagline": f"Your local {c}", "colour": "#2f5d50",
            "intro": f"{lead['name']} is a friendly local {c} serving the neighbourhood. "
                     f"Drop in, call ahead, or get in touch below.",
            "services": [f"{c.title()} services", "Walk-ins welcome", "Local service",
                         "Get in touch for details"],
            "why": ["Friendly local team", "Easy to find", "Here for the community"]}


def site_copy(lead, cfg):
    text = ask_ai(COPY_PROMPT.format(**lead), cfg)
    try:
        data = _json(text) if text else None
        if data and all(k in data for k in ("tagline", "intro", "services", "why")):
            data.setdefault("colour", "#2f5d50")
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(data["colour"])):
                data["colour"] = "#2f5d50"
            return data
    except Exception as e:
        print(f"Bad AI copy for {lead['name']}: {e}")
    return fallback_copy(lead)


def outreach(lead, cfg):
    y, o = cfg["you"], cfg["offer"]
    free = " The first month of the care plan is free." if o.get("first_month_free") else ""
    walk_in = (
        f"Hi, is the owner around? I'm {y['name']}, I build websites for local businesses "
        f"here. I noticed {lead['name']} doesn't have a website, so I made you a free demo — "
        f"can I show you on my phone? It takes 30 seconds. [show {lead['demo_url']}] "
        f"If you like it, it's £{o['build_price']} to go live with your own details and photos, "
        f"then £{o['care_plan_monthly']} a month for hosting, updates and changes.{free} "
        f"No pressure — I'll leave you my card.")
    email = (
        f"Subject: A website for {lead['name']} (free demo inside)\n\n"
        f"Hi,\n\nI'm {y['name']} from {y['business_name']}, a local web designer. "
        f"I couldn't find a website for {lead['name']}, so I built a quick demo to show "
        f"what one could look like:\n\n{lead['demo_url']}\n\n"
        f"If you'd like it, I'll add your real photos, hours and menu/prices and put it live "
        f"for £{o['build_price']}, then £{o['care_plan_monthly']}/month covers hosting, "
        f"security and any changes you need.{free}\n\n"
        f"Happy to pop in for 10 minutes if easier. If you'd rather not hear from me, "
        f"just reply 'no thanks' and I won't contact you again.\n\n"
        f"{y['name']}\n{y['business_name']}\n{y['phone']}\n{y['site']}")
    return walk_in, email
