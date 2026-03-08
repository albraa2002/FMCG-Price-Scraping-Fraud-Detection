# ============================================================
#  FMCG Price Scraping & Fraud Detection Dashboard
#  Single-Cell Google Colab Script  |  Senior Data Analyst
# ============================================================

# ── Install dependencies ──────────────────────────────────
import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "beautifulsoup4", "--quiet"], check=True)

# ── Imports ───────────────────────────────────────────────
import random, re
import pandas as pd
import plotly.graph_objects as go
from bs4 import BeautifulSoup
from google.colab import files

random.seed(42)

# ═══════════════════════════════════════════════════════════
#  STEP 1 — Simulate Target E-commerce HTML (120 products)
# ═══════════════════════════════════════════════════════════

PRODUCTS = {
    "Dairy":      [("Full-Fat Milk 1L",50),("Skimmed Milk 1L",48),("UHT Milk 6-Pack",285),
                   ("Fresh Yogurt 500g",42),("Greek Yogurt 400g",65),("Labneh 500g",58),
                   ("Cheddar Cheese 400g",120),("White Cheese 500g",95),("Butter 200g",88),
                   ("Cream 200ml",55),("Ghee 500g",175),("Feta Cheese 250g",110)],
    "Pantry":     [("Basmati Rice 5kg",185),("Egyptian Rice 5kg",145),("Pasta 500g",28),
                   ("Spaghetti 500g",32),("Lentils 1kg",55),("Chickpeas 1kg",60),
                   ("Fava Beans 800g",38),("Corn Flour 1kg",30),("Wheat Flour 2kg",62),
                   ("Bread Crumbs 500g",35),("Oats 1kg",75),("Quinoa 500g",140),
                   ("Couscous 500g",85),("Bulgur 1kg",50),("White Sugar 1kg",42)],
    "Oils & Fats":[("Sunflower Oil 1.5L",110),("Corn Oil 1.5L",115),("Olive Oil 500ml",185),
                   ("Canola Oil 1.5L",105),("Vegetable Oil 3L",195),("Extra Virgin Olive 750ml",245),
                   ("Coconut Oil 300ml",165),("Sesame Oil 250ml",88)],
    "Beverages":  [("Nescafé Classic 200g",145),("Turkish Coffee 250g",95),("Lipton Tea 100-Bag",85),
                   ("Green Tea 25-Bag",55),("Orange Juice 1L",52),("Mango Juice 1L",48),
                   ("Guava Nectar 1L",45),("Tomato Juice 1L",40),("Sports Drink 500ml",38),
                   ("Mineral Water 1.5L",12),("Sparkling Water 1L",25),("Herbal Tea Mix",70)],
    "Snacks":     [("Potato Chips 150g",38),("Corn Chips 120g",32),("Rice Cakes 100g",28),
                   ("Dark Chocolate 100g",55),("Milk Chocolate 100g",48),("Mixed Nuts 250g",125),
                   ("Cashews 200g",145),("Almonds 200g",135),("Peanut Butter 400g",95),
                   ("Tahini 400g",72),("Honey 500g",145),("Jam 450g",58)],
    "Household":  [("Laundry Powder 3kg",145),("Fabric Softener 1L",68),("Dish Soap 750ml",42),
                   ("All-Purpose Cleaner",55),("Bleach 1L",28),("Toilet Cleaner 500ml",35),
                   ("Kitchen Towels 4-Roll",48),("Trash Bags 30-Pack",38),("Sponges 6-Pack",22),
                   ("Aluminum Foil 30m",45),("Cling Wrap 30m",38),("Baking Soda 500g",18)],
    "Personal Care":[("Shampoo 400ml",85),("Conditioner 400ml",78),("Body Wash 500ml",72),
                     ("Hand Soap 250ml",32),("Toothpaste 120ml",38),("Mouthwash 500ml",62),
                     ("Deodorant 150ml",72),("Sunscreen SPF50",110),("Moisturizer 200ml",95),
                     ("Lip Balm",28),("Cotton Pads 100-Pack",35),("Wet Wipes 80-Pack",42)],
}

# Flatten product list and ensure exactly 120
all_products = []
for cat, items in PRODUCTS.items():
    for name, base in items:
        all_products.append((name, cat, base))

random.shuffle(all_products)
all_products = (all_products * 3)[:120]

def generate_price_card(name, cat, base_egp, fraud=False):
    if fraud:
        fraud_type = random.choice(["tiny_discount", "inflated_old"])
        if fraud_type == "tiny_discount":
            old_price = round(base_egp * random.uniform(1.01, 1.04), 2)
            new_price = round(base_egp * random.uniform(0.97, 1.0), 2)
            new_price = min(new_price, old_price - 0.01)
        else:  # inflated old price
            old_price = round(base_egp * random.uniform(1.55, 2.20), 2)
            new_price = round(base_egp * random.uniform(0.98, 1.12), 2)
    else:
        old_price = round(base_egp * random.uniform(1.08, 1.35), 2)
        new_price = round(base_egp * random.uniform(0.82, 0.96), 2)
        new_price = min(new_price, old_price - 1.0)

    return (f'<div class="product-card">'
            f'<h3 class="title">{name}</h3>'
            f'<span class="category">{cat}</span>'
            f'<span class="price-old">EGP {old_price:.2f}</span>'
            f'<span class="price-new">EGP {new_price:.2f}</span>'
            f'</div>')

html_parts = ['<html><body><div id="catalog">']
for i, (name, cat, base) in enumerate(all_products):
    is_fraud = (i % 3 == 0)   # ~35% fraud injection
    html_parts.append(generate_price_card(name, cat, base, fraud=is_fraud))
html_parts.append('</div></body></html>')
html_content = "\n".join(html_parts)

print(f"✅ Step 1 Done — HTML generated ({len(all_products)} product cards)")

# ═══════════════════════════════════════════════════════════
#  STEP 2 — Web Scraping with BeautifulSoup
# ═══════════════════════════════════════════════════════════

soup = BeautifulSoup(html_content, "html.parser")
cards = soup.find_all("div", class_="product-card")

records = []
for card in cards:
    title    = card.find("h3",   class_="title").get_text(strip=True)
    category = card.find("span", class_="category").get_text(strip=True)
    old_raw  = card.find("span", class_="price-old").get_text(strip=True)
    new_raw  = card.find("span", class_="price-new").get_text(strip=True)
    records.append({"Title": title, "Category": category,
                    "Old_Price_Raw": old_raw, "New_Price_Raw": new_raw})

df = pd.DataFrame(records)
print(f"✅ Step 2 Done — Scraped {len(df)} records from HTML")

# ═══════════════════════════════════════════════════════════
#  STEP 3 — Data Cleaning & Feature Engineering
# ═══════════════════════════════════════════════════════════

def clean_price(s):
    return float(re.sub(r"[^\d.]", "", s.replace(",", "")))

df["Old_Price"] = df["Old_Price_Raw"].apply(clean_price)
df["New_Price"] = df["New_Price_Raw"].apply(clean_price)
df["Discount_Pct"] = ((df["Old_Price"] - df["New_Price"]) / df["Old_Price"]) * 100

# Category baseline (median new price per category)
baseline = df.groupby("Category")["New_Price"].median().rename("Baseline")
df = df.join(baseline, on="Category")

def fraud_flag(row):
    tiny_discount   = row["Discount_Pct"] < 5
    inflated_old    = (row["Old_Price"] > row["Baseline"] * 1.40) and (row["Discount_Pct"] > 20)
    return "Fake Discount 🔴" if (tiny_discount or inflated_old) else "Legit Discount ✅"

df["Fraud_Flag"] = df.apply(fraud_flag, axis=1)

n_total  = len(df)
n_fake   = (df["Fraud_Flag"] == "Fake Discount 🔴").sum()
n_legit  = n_total - n_fake
avg_inf  = round(((df["Old_Price"] / df["Baseline"]) - 1).mean() * 100, 1)

print(f"✅ Step 3 Done — Fake: {n_fake} | Legit: {n_legit} | Avg Inflation: {avg_inf}%")

# ═══════════════════════════════════════════════════════════
#  STEP 4 — Three Independent Plotly Figures
# ═══════════════════════════════════════════════════════════

# ── Palette ──────────────────────────────────────────────
BG        = "#0f172a"
CARD_BG   = "#1e293b"
FRAUD_RED = "#ef4444"
LEGIT_GRN = "#10b981"
ACCENT    = "#38bdf8"
TEXT      = "#e2e8f0"
GRID_CLR  = "#334155"

BASE_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=CARD_BG,
    font=dict(family="IBM Plex Mono, monospace", color=TEXT, size=12),
    margin=dict(l=40, r=40, t=60, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
)

# ── Figure 1: Donut — Fraud Breakdown ────────────────────
fraud_counts = df["Fraud_Flag"].value_counts()
fig_fraud_pie = go.Figure(go.Pie(
    labels=fraud_counts.index.tolist(),
    values=fraud_counts.values.tolist(),
    hole=0.60,
    marker=dict(
        colors=[FRAUD_RED if "Fake" in lbl else LEGIT_GRN
                for lbl in fraud_counts.index],
        line=dict(color=BG, width=3)
    ),
    textinfo="label+percent",
    textfont=dict(size=13, color=TEXT),
    hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
))
fig_fraud_pie.update_layout(
    **BASE_LAYOUT,
    title=dict(text="Fake vs Legit Discount Distribution", x=0.5,
               font=dict(size=15, color=ACCENT)),
    annotations=[dict(text=f"<b>{n_total}</b><br>Products",
                      x=0.5, y=0.5, font_size=16, font_color=TEXT,
                      showarrow=False)]
)

# ── Figure 2: Bar — Avg Discount % by Category ───────────
cat_stats = (df.groupby("Category")
               .agg(Avg_Discount=("Discount_Pct","mean"),
                    Fake_Count=("Fraud_Flag", lambda x:(x=="Fake Discount 🔴").sum()))
               .reset_index()
               .sort_values("Avg_Discount", ascending=True))

bar_colors = [FRAUD_RED if f > 3 else LEGIT_GRN for f in cat_stats["Fake_Count"]]

fig_category = go.Figure(go.Bar(
    x=cat_stats["Avg_Discount"],
    y=cat_stats["Category"],
    orientation="h",
    marker=dict(color=bar_colors, line=dict(color=BG, width=1)),
    text=[f'{v:.1f}%  ({f} fake)' for v, f in
          zip(cat_stats["Avg_Discount"], cat_stats["Fake_Count"])],
    textposition="outside",
    textfont=dict(size=11, color=TEXT),
    hovertemplate="<b>%{y}</b><br>Avg Discount: %{x:.1f}%<extra></extra>",
))
fig_category.update_layout(
    **BASE_LAYOUT,
    title=dict(text="Avg Discount % by Category  (red = >3 fake items)", x=0.5,
               font=dict(size=15, color=ACCENT)),
    xaxis=dict(title="Avg Discount (%)", gridcolor=GRID_CLR, zerolinecolor=GRID_CLR),
    yaxis=dict(gridcolor=GRID_CLR),
    bargap=0.3,
)

# ── Figure 3: Scatter — Old vs New Price, colour=Fraud ───
color_map = {"Fake Discount 🔴": FRAUD_RED, "Legit Discount ✅": LEGIT_GRN}

fig_scatter = go.Figure()

for flag, grp in df.groupby("Fraud_Flag"):
    fig_scatter.add_trace(go.Scatter(
        x=grp["Old_Price"],
        y=grp["New_Price"],
        mode="markers",
        name=flag,
        marker=dict(color=color_map[flag], size=8, opacity=0.80,
                    line=dict(color=BG, width=0.5)),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Category: %{customdata[1]}<br>"
            "Old: EGP %{x:.2f}<br>"
            "New: EGP %{y:.2f}<br>"
            "Discount: %{customdata[2]:.1f}%<extra></extra>"
        ),
        customdata=grp[["Title","Category","Discount_Pct"]].values,
    ))

price_max = df[["Old_Price","New_Price"]].values.max() * 1.05
fig_scatter.add_trace(go.Scatter(
    x=[0, price_max], y=[0, price_max],
    mode="lines",
    line=dict(color=ACCENT, dash="dash", width=1.5),
    name="y = x  (zero discount)",
    hoverinfo="skip",
))
fig_scatter.update_layout(
    **BASE_LAYOUT,
    title=dict(text="Old Price vs New Price  — dots near dashed line = fake discounts",
               x=0.5, font=dict(size=15, color=ACCENT)),
    xaxis=dict(title="Old Price (EGP)", gridcolor=GRID_CLR, zerolinecolor=GRID_CLR, range=[0, price_max]),
    yaxis=dict(title="New Price (EGP)", gridcolor=GRID_CLR, zerolinecolor=GRID_CLR, range=[0, price_max]),
)

print("✅ Step 4 Done — 3 Plotly figures created")

# ═══════════════════════════════════════════════════════════
#  STEP 5 — Build Pure HTML/CSS Dashboard
# ═══════════════════════════════════════════════════════════

pie_html   = fig_fraud_pie.to_html(full_html=False, include_plotlyjs=False, config={"responsive":True})
bar_html   = fig_category.to_html(full_html=False, include_plotlyjs=False, config={"responsive":True})
scat_html  = fig_scatter.to_html(full_html=False,  include_plotlyjs=False, config={"responsive":True})

dashboard_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FMCG Fraud Detection Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg:          #0f172a;
    --card:        #1e293b;
    --card-border: #334155;
    --red:         #ef4444;
    --green:       #10b981;
    --blue:        #38bdf8;
    --text:        #e2e8f0;
    --muted:       #94a3b8;
    --font-mono:   'IBM Plex Mono', monospace;
    --font-sans:   'IBM Plex Sans', sans-serif;
  }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-sans);
    min-height: 100vh;
    padding: 0 0 48px;
  }}

  /* ── Header ─────────────────────────────────────── */
  .header {{
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    border-bottom: 1px solid var(--card-border);
    padding: 28px 48px 24px;
    display: flex;
    align-items: center;
    gap: 20px;
    position: relative;
    overflow: hidden;
  }}
  .header::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
      90deg,
      transparent,
      transparent 80px,
      rgba(56,189,248,.03) 80px,
      rgba(56,189,248,.03) 81px
    );
  }}
  .header-icon {{
    font-size: 2.4rem;
    filter: drop-shadow(0 0 12px rgba(239,68,68,.6));
  }}
  .header-text h1 {{
    font-family: var(--font-mono);
    font-size: 1.55rem;
    font-weight: 700;
    color: var(--blue);
    letter-spacing: -0.5px;
  }}
  .header-text p {{
    font-size: .82rem;
    color: var(--muted);
    margin-top: 3px;
    letter-spacing: .5px;
    text-transform: uppercase;
  }}
  .badge {{
    margin-left: auto;
    background: rgba(239,68,68,.15);
    border: 1px solid rgba(239,68,68,.4);
    color: var(--red);
    font-family: var(--font-mono);
    font-size: .72rem;
    padding: 5px 12px;
    border-radius: 4px;
    letter-spacing: .8px;
    text-transform: uppercase;
  }}

  /* ── Main layout ─────────────────────────────────── */
  .main {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 36px 32px 0;
    display: grid;
    gap: 24px;
  }}

  /* ── KPI row ─────────────────────────────────────── */
  .kpi-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }}
  .kpi-card {{
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 22px 26px;
    position: relative;
    overflow: hidden;
    transition: transform .2s;
  }}
  .kpi-card:hover {{ transform: translateY(-2px); }}
  .kpi-card::after {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 12px 12px 0 0;
  }}
  .kpi-card.blue::after  {{ background: var(--blue); }}
  .kpi-card.green::after {{ background: var(--green); }}
  .kpi-card.red::after   {{ background: var(--red); }}

  .kpi-label {{
    font-family: var(--font-mono);
    font-size: .70rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
  }}
  .kpi-value {{
    font-family: var(--font-mono);
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1;
  }}
  .kpi-card.blue  .kpi-value {{ color: var(--blue); }}
  .kpi-card.green .kpi-value {{ color: var(--green); }}
  .kpi-card.red   .kpi-value {{ color: var(--red); }}
  .kpi-sub {{
    font-size: .76rem;
    color: var(--muted);
    margin-top: 8px;
  }}

  /* ── Chart cards ─────────────────────────────────── */
  .chart-row {{
    display: grid;
    gap: 20px;
  }}
  .chart-row.two-col {{ grid-template-columns: 1fr 1fr; }}
  .chart-row.one-col {{ grid-template-columns: 1fr; }}

  .chart-card {{
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 20px;
    overflow: hidden;
  }}
  .chart-card .plotly-graph-div {{
    width: 100% !important;
  }}

  /* ── Footer ──────────────────────────────────────── */
  .footer {{
    text-align: center;
    font-family: var(--font-mono);
    font-size: .68rem;
    color: var(--muted);
    margin-top: 40px;
    letter-spacing: .5px;
  }}

  /* ── Responsive ──────────────────────────────────── */
  @media (max-width: 900px) {{
    .kpi-row {{ grid-template-columns: 1fr; }}
    .chart-row.two-col {{ grid-template-columns: 1fr; }}
    .header {{ padding: 20px 24px; }}
    .main   {{ padding: 24px 16px 0; }}
  }}
</style>
</head>
<body>

<!-- ── Header ─────────────────────────────────────── -->
<div class="header">
  <div class="header-icon">🛡️</div>
  <div class="header-text">
    <h1>FMCG MARKET TRACKER — FRAUD DETECTION</h1>
    <p>Price Scraping Intelligence &amp; Discount Authenticity Analysis</p>
  </div>
  <div class="badge">⚠ Live Audit</div>
</div>

<!-- ── Main ───────────────────────────────────────── -->
<div class="main">

  <!-- KPI Row -->
  <div class="kpi-row">
    <div class="kpi-card blue">
      <div class="kpi-label">📦 Total Items Scraped</div>
      <div class="kpi-value">{n_total}</div>
      <div class="kpi-sub">Across {df['Category'].nunique()} product categories</div>
    </div>
    <div class="kpi-card green">
      <div class="kpi-label">📈 Avg Market Inflation</div>
      <div class="kpi-value">+{avg_inf}%</div>
      <div class="kpi-sub">Old prices vs category baseline median</div>
    </div>
    <div class="kpi-card red">
      <div class="kpi-label">🔴 Fake Discounts Detected</div>
      <div class="kpi-value">{n_fake}</div>
      <div class="kpi-sub">{round(n_fake/n_total*100,1)}% of catalogue flagged as fraudulent</div>
    </div>
  </div>

  <!-- Middle row: Donut + Bar -->
  <div class="chart-row two-col">
    <div class="chart-card">{pie_html}</div>
    <div class="chart-card">{bar_html}</div>
  </div>

  <!-- Bottom row: Scatter full-width -->
  <div class="chart-row one-col">
    <div class="chart-card">{scat_html}</div>
  </div>

  <div class="footer">
    Generated by FMCG Fraud Detection Engine &nbsp;|&nbsp;
    BeautifulSoup + Plotly + Python &nbsp;|&nbsp;
    Methodology: Tiny-Discount &lt;5% &amp; Inflated-Old-Price &gt;40% above baseline
  </div>

</div>
</body>
</html>"""

print("✅ Step 5 Done — HTML dashboard string built")

# ═══════════════════════════════════════════════════════════
#  STEP 6 — Export & Auto-Download
# ═══════════════════════════════════════════════════════════

OUTPUT_FILE = "FMCG_Scraping_Fraud_Dashboard.html"
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(dashboard_html)

print(f"✅ Step 6 Done — Saved as '{OUTPUT_FILE}'  ({len(dashboard_html):,} bytes)")
print("⬇️  Triggering download …")
files.download(OUTPUT_FILE)
print("\n🎉 All done! Dashboard downloaded successfully.")
