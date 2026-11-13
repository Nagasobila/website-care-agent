# Website Care Agent

An AI agent that earns money by selling **website care plans** to local businesses.

Twice a week it:
1. **Finds leads.** It searches free OpenStreetMap data for cafés, restaurants, salons, florists, tradespeople and similar businesses within 3 km of Bayswater that have **no website** listed.
2. **Builds each one a free demo site.** A free AI model (Groq or Gemini) writes the copy, and the agent publishes a mobile-friendly one-page site on GitHub Pages.
3. **Drafts your pitch.** It writes a walk-in or phone script for every lead, plus an email draft when the business lists an email address. The drafts land in `outreach/DATE.md`.

**You** do the selling. Walk in, show the demo on your phone, and close the deal.
The money comes from **£149 to set up the site + £39 a month for care**. 25 clients ≈ £1,000 a month.

Everything runs in your browser and on GitHub. Nothing to install.

---

## Setup (about 20 minutes, browser only)

1. **Create the repo.** On GitHub, click **New repository**, name it `website-care-agent`, and make it **Public** (GitHub Pages is free only for public repos). Then click **uploading an existing file**, drag in *everything* from this zip (including the `.github` folder), and commit.
   - If `.github` doesn't upload: click **Add file → Create new file**, type `.github/workflows/agent.yml`, and paste in the contents of that file.
2. **Free AI keys** (one is enough, both is safer):
   - Groq: console.groq.com → API Keys → Create
   - Gemini: aistudio.google.com → Get API key

   In the repo, go to **Settings → Secrets and variables → Actions → New repository secret** and add `GROQ_API_KEY` and/or `GEMINI_API_KEY`.
   Without a key, the agent still runs but uses plain template copy.
3. **Turn on Pages.** Go to **Settings → Pages → Source: Deploy from a branch → `main` / `/docs`** and save.
4. **Edit `config.yaml`** (pencil icon): add your name, business name, phone and email. You can also change the area and the prices.
5. **First run.** Go to **Actions → Website Care Agent → Run workflow**. After about 2 minutes, open `outreach/` for the pitch sheet. The demo links go live roughly a minute after that.

After that it runs on its own every Monday and Thursday morning.

## Your weekly routine (≈2–3 hours)

- Open the newest `outreach/DATE.md`, then visit 5 businesses on your way to or from work. Walk-ins convert far better than emails.
- After each visit, edit `leads.csv` and set `status` to `contacted`, `interested`, `won` or `no`.
- When someone says yes, collect their real photos, opening hours and menu or prices. Swap these into their demo, remove the yellow "demo" banner, and point their domain at it. You can also ask me to turn it into a fuller site.

## How to spend the ₹5,000 (≈ £45)

| Item | Approx. cost | Why |
|---|---|---|
| Your own domain (.co.uk or .com) | ~£5–12 / year | Looks professional on cards and emails |
| Business email on that domain | £0 (Zoho Mail free plan or Cloudflare Email Routing) | — |
| 100–250 business cards with a QR code to your site | ~£10–20 | Leave one at every walk-in |
| **Reserve** | ~£15–25 | Your first client's domain, if they don't have one |
| AI and hosting | £0 | Groq/Gemini free tiers, GitHub Pages |

Your first client covers all of this (£149).

## Rules the agent follows, and you should too

- **Demos are labelled.** Every demo carries a "Demo design by … — not the official website" banner and is hidden from Google (noindex). Never present a demo as the business's real site.
- **No made-up facts.** The AI is told not to invent prices, hours, reviews or awards. Check the copy before you show it anyway.
- **Email carefully (UK PECR rules).** Cold emails to limited companies are allowed if you include an opt-out. Sole traders and partnerships count as individuals and need consent first, so **walk in or phone first**. Send emails one at a time from your own inbox, never in bulk, and honour every "no thanks".
- **Check your day job and visa first.** Check your Hilton contract for clauses on outside work, and check that your visa allows self-employment. Register the income with HMRC.

## Files

| File | What it does |
|---|---|
| `config.yaml` | Your details, search area, business types, prices |
| `agent/leads.py` | Finds businesses on OpenStreetMap with no website |
| `agent/writer.py` | AI copy and pitch drafts (Groq → Gemini → template) |
| `agent/demo_site.py` | Turns copy into the demo web page |
| `agent/run.py` | Runs the whole thing |
| `leads.csv` | Your lead tracker (update `status` here) |
| `docs/demos/` | Published demo sites |
| `outreach/` | Pitch sheets, one per run |
