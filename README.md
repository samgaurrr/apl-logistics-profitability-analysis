# APL Logistics: Customer, Product & Profitability Performance Analysis

Interactive Streamlit dashboard for customer, product, category, market and discount profitability analysis.

## Live Dashboard
Add the deployed Streamlit URL after deployment.

## Dataset
The supplied dataset contains 180,519 order lines and 40 original columns. The app uses `data/apl_clean.csv.gz`, a cleaned dataset with personal address fields and coordinates removed. There is no order-date field, so the dashboard does not invent calendar trends.

## Key results
- Revenue: **$36.78M**
- Profit: **$3.97M**
- Profit margin: **10.78%**
- Loss-making order lines: **18.7%**
- Net loss-making customers: **4,069**
- Loss-making products: **3**
- A 15% discount-cap scenario indicates about **$429K** potential additional profit if volumes remain constant.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Structure
```text
app.py
requirements.txt
README.md
research_paper.md
executive_summary.md
data/apl_clean.csv.gz
```

## Tech stack
Python, Pandas, NumPy, Plotly, Streamlit.

## Author
**Sambhav Gaur** — BCA, Jagannath Institute of Management Sciences

## Project context
Unified Mentor program.
