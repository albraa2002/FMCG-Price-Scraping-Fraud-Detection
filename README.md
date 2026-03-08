🛒 FMCG Price Scraping & Fraud Detection Dashboard

📌 Project Overview
This project transforms basic web scraping into actionable **Market Intelligence**. Using Python and BeautifulSoup, this script simulates scraping an e-commerce catalog of 120 Fast-Moving Consumer Goods (FMCG). The goal is to clean the raw HTML data and apply a rigorous business logic algorithm to detect retail pricing fraud (e.g., "Fake Discounts") and measure market inflation.

🚀 Key Business Insights
  Fraud Identification: The algorithm successfully flagged **33.3%** of the product catalog (40 out of 120 items) as fraudulent promotions.
  Pricing Manipulation Logic: Detected items where the "Old Price" was artificially inflated (over 40% above baseline) to create a deceptive illusion of a massive discount.
  Market Inflation Tracking: Calculated an average hidden market inflation of **27.9%** across essential product categories (Dairy, Pantry, Beverages).
  Visual Evidence: Utilized a Plotly Scatter Matrix (Old vs. New Price) to visually expose fake discounts clustering tightly around the baseline diagonal.

🛠️ Tech Stack
  Web Scraping & Parsing: Python, `BeautifulSoup4` (`bs4`)
  Data Manipulation: Pandas, Regex (`re`)
  Data Visualization: Plotly (Scatter, Donut, Bar charts)
  UI/UX: Standalone HTML/CSS Grid (Dark Market Tracker Command Center UI)

👤 Author
Albaraa Ehab
Role: Data Analyst / Market Intelligence
