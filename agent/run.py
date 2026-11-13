"""Website Care Agent: find businesses with no website -> build a demo -> draft the pitch."""
import os, shutil, sys, time
from urllib.parse import quote_plus
import yaml

sys.dont_write_bytecode = True  # keep cache files out of the repo

sys.path.insert(0, os.path.dirname(__file__))
import leads as L, writer as W, demo_site as S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def pages_url():
    if os.getenv("PAGES_URL"):
        return os.environ["PAGES_URL"].rstrip("/") + "/"
    repo = os.getenv("GITHUB_REPOSITORY", "you/website-care-agent")
    owner, name = repo.split("/")
    return f"https://{owner.lower()}.github.io/{name}/"


def main(found=None):
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    rows = L.load("leads.csv")
    if found is None:
        found = L.fetch(cfg)
    print(f"OpenStreetMap: {len(found)} businesses with no website listed")
    fresh = L.new_leads(cfg, rows, found)
    if not fresh:
        print("No new leads this run. Try a bigger radius or new categories in config.yaml.")
        return

    day = time.strftime("%Y-%m-%d")
    header = [f"# Outreach — {day}\n",
             "OpenStreetMap only says no website is *listed*. Google each one before you visit "
             "(link below) and skip any that already have a site.\n",
             "Visit in person first (works best). Use email only if they listed one.\n",
             "After each contact, update `status` in leads.csv: "
             "contacted / interested / won / no.\n"]
    notes = list(header)
    for lead in fresh:
        copy = W.site_copy(lead, cfg)
        os.makedirs(f"docs/demos/{lead['slug']}", exist_ok=True)
        with open(f"docs/demos/{lead['slug']}/index.html", "w", encoding="utf-8") as f:
            f.write(S.render(lead, copy, cfg))
        lead["demo_url"] = pages_url() + f"demos/{lead['slug']}/"
        walk_in, email = W.outreach(lead, cfg)
        notes += [f"\n---\n\n## {lead['name']} ({lead['category']})",
                  f"- Address: {lead['address'] or 'not listed — check the map pin'}",
                  f"- Phone: {lead['phone'] or '—'}   Email: {lead['email'] or '—'}",
                  f"- Demo: {lead['demo_url']}",
                  f"- Map: https://www.openstreetmap.org/{lead['id']}",
                  f"- **Check first** they really have no site: "
                  f"https://www.google.com/search?q={quote_plus(lead['name'] + ' ' + (lead['address'] or 'London'))}\n",
                  "**Walk-in / phone script**\n", f"> {walk_in}\n"]
        if lead["email"]:
            notes += ["**Email draft** (send from your own inbox, one at a time)\n",
                      "```", email, "```"]
        rows.append(lead)
        print(f"Built demo for {lead['name']}")

    L.save("leads.csv", rows)
    os.makedirs("outreach", exist_ok=True)
    sheet = f"outreach/{day}.md"
    if os.path.exists(sheet):          # second run the same day: add, don't overwrite
        notes = notes[len(header):]
    with open(sheet, "a", encoding="utf-8") as f:
        f.write("\n".join(notes) + "\n")
    if not os.path.exists("docs/index.html"):
        open("docs/index.html", "w").write("<!doctype html><title>Demos</title><p>Demo sites.</p>")
    open("docs/.nojekyll", "w").close()
    shutil.rmtree("agent/__pycache__", ignore_errors=True)
    print(f"Done: {len(fresh)} demos, pitch sheet in outreach/{day}.md")


if __name__ == "__main__":
    main()
