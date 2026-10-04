import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="APL Logistics | Profitability Analytics", page_icon="📊", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("data/apl_clean.csv.gz", compression="gzip", low_memory=False)
    nums = ["Days for shipping (real)","Days for shipment (scheduled)","Benefit per order","Sales per customer",
            "Late_delivery_risk","Category Id","Customer Id","Department Id","Order Customer Id",
            "Order Item Discount","Order Item Discount Rate","Order Item Product Price","Order Item Profit Ratio",
            "Order Item Quantity","Sales","Order Item Total","Order Profit Per Order","Product Price"]
    for c in nums:
        if c in df: df[c] = pd.to_numeric(df[c], errors="coerce")
    df["Margin"] = np.where(df.Sales != 0, df["Order Profit Per Order"]/df.Sales, np.nan)
    df["Discount %"] = df["Order Item Discount Rate"].fillna(0)*100
    df["Discount Band"] = pd.cut(df["Discount %"], [-.001,0,5,10,15,20,25,100],
                                 labels=["0%","0–5%","5–10%","10–15%","15–20%","20–25%","25%+"],
                                 include_lowest=True)
    return df

df=load_data()
st.title("📊 APL Logistics")
st.subheader("Customer, Product & Profitability Performance Analysis")
st.caption("Supply Chain Operations • Interactive Streamlit Dashboard")

with st.sidebar:
    st.header("🔎 Filters")
    exclude = st.checkbox("Exclude cancelled & suspected-fraud orders", True)
    seg=st.multiselect("Customer Segment", sorted(df["Customer Segment"].dropna().unique()),
                       default=sorted(df["Customer Segment"].dropna().unique()))
    market=st.multiselect("Market", sorted(df.Market.dropna().unique()), default=sorted(df.Market.dropna().unique()))
    region=st.multiselect("Order Region", sorted(df["Order Region"].dropna().unique()), default=sorted(df["Order Region"].dropna().unique()))
    cat=st.multiselect("Category", sorted(df["Category Name"].dropna().unique()), default=sorted(df["Category Name"].dropna().unique()))
    product=st.multiselect("Product", sorted(df["Product Name"].dropna().unique()), default=sorted(df["Product Name"].dropna().unique()))
    dmax=float(np.ceil(df["Discount %"].max()))
    dr=st.slider("Discount rate (%)",0.0,max(1.0,dmax),(0.0,max(1.0,dmax)),0.5)

f=df.copy()
if exclude: f=f[~f["Order Status"].astype(str).str.upper().isin(["CANCELED","CANCELLED","SUSPECTED_FRAUD","SUSPECTED FRAUD"])]
f=f[f["Customer Segment"].isin(seg)&f.Market.isin(market)&f["Order Region"].isin(region)&f["Category Name"].isin(cat)&f["Product Name"].isin(product)&f["Discount %"].between(*dr)]
if f.empty: st.warning("No data matches the selected filters."); st.stop()

sales=f.Sales.sum(); profit=f["Order Profit Per Order"].sum(); margin=profit/sales if sales else 0
ncustomers=f["Customer Id"].nunique(); cvi=profit/ncustomers if ncustomers else 0
catm=f.groupby("Category Name").apply(lambda x:x["Order Profit Per Order"].sum()/x.Sales.sum() if x.Sales.sum() else np.nan).mean()
disc=f["Order Item Discount"].sum(); ratio=disc/(profit+disc) if profit+disc else np.nan
k=st.columns(6)
for col,label,val in zip(k,["Total Revenue","Total Profit","Profit Margin","Customers","Customer Value Index","Discount Impact Ratio"],
                         [f"${sales/1e6:.2f}M",f"${profit/1e6:.2f}M",f"{margin*100:.2f}%",f"{ncustomers:,}",f"${cvi:,.0f}",f"{ratio*100:.2f}%"]):
    col.metric(label,val)

t1,t2,t3,t4,t5,t6=st.tabs(["📈 Revenue & Profit","👥 Customer Value","📦 Product & Category","🏷️ Discount Impact","🌍 Market & Region","📋 Data"])

with t1:
    a,b=st.columns(2)
    m=f.groupby("Market",as_index=False).agg(Sales=("Sales","sum"),Profit=("Order Profit Per Order","sum"))
    m["Margin %"]=m.Profit/m.Sales*100
    a.plotly_chart(px.bar(m.sort_values("Margin %"),x="Market",y="Margin %",text_auto=".1f",title="Profit Margin by Market"),use_container_width=True)
    bd=f.groupby("Discount Band",observed=False,as_index=False).agg(Sales=("Sales","sum"),Profit=("Order Profit Per Order","sum"))
    bd["Margin %"]=bd.Profit/bd.Sales*100
    b.plotly_chart(px.line(bd,x="Discount Band",y="Margin %",markers=True,title="Margin Trend by Discount Band"),use_container_width=True)
    c=f.groupby("Customer Id",as_index=False).Profit if False else f.groupby("Customer Id",as_index=False).agg(Profit=("Order Profit Per Order","sum"))
    c=c.sort_values("Profit",ascending=False); c["Cumulative %"]=c.Profit.cumsum()/c.Profit.sum()*100
    st.plotly_chart(px.line(c,y="Cumulative %",title="Customer Profit Concentration (Pareto)"),use_container_width=True)
    st.caption("No order-date field is supplied, so calendar trends are not fabricated; discount-band trends are used instead.")

with t2:
    c=f.groupby(["Customer Id","Customer Segment"],as_index=False).agg(Sales=("Sales","sum"),Profit=("Order Profit Per Order","sum"),Orders=("Order Customer Id","count"))
    c["Margin %"]=c.Profit/c.Sales*100
    q50,q80=c.Profit.quantile(.5),c.Profit.quantile(.8)
    c["Value Tier"]=np.select([c.Profit<0,c.Profit>=q80,c.Profit>=q50],["Loss-making","High","Medium"],default="Low")
    a,b=st.columns(2)
    a.plotly_chart(px.bar(c.nlargest(10,"Profit").sort_values("Profit"),x="Profit",y="Customer Id",orientation="h",title="Top 10 Customers by Profit"),use_container_width=True)
    b.plotly_chart(px.bar(c.nsmallest(10,"Profit").sort_values("Profit"),x="Profit",y="Customer Id",orientation="h",title="Bottom 10 Customers by Profit"),use_container_width=True)
    s=c.groupby("Customer Segment",as_index=False).agg(Profit=("Profit","sum"))
    st.plotly_chart(px.bar(s,x="Customer Segment",y="Profit",text_auto=".2s",title="Customer Segment Contribution"),use_container_width=True)
    st.plotly_chart(px.bar(c["Value Tier"].value_counts().reindex(["High","Medium","Low","Loss-making"]).fillna(0).rename_axis("Value Tier").reset_index(name="Customers"),
                     x="Value Tier",y="Customers",text_auto=True,title="Customer Value Tiers"),use_container_width=True)
    st.download_button("⬇️ Download Customer Profitability CSV",c.to_csv(index=False).encode(),"customer_profitability.csv","text/csv")

with t3:
    p=f.groupby("Product Name",as_index=False).agg(Sales=("Sales","sum"),Profit=("Order Profit Per Order","sum")); p["Margin %"]=p.Profit/p.Sales*100
    a,b=st.columns(2)
    a.plotly_chart(px.bar(p.nsmallest(10,"Margin %").sort_values("Margin %"),x="Margin %",y="Product Name",orientation="h",title="Lowest-Margin Products"),use_container_width=True)
    b.plotly_chart(px.bar(p.nlargest(10,"Margin %").sort_values("Margin %"),x="Margin %",y="Product Name",orientation="h",title="Highest-Margin Products"),use_container_width=True)
    h=f.groupby(["Category Name","Market"],as_index=False).agg(Sales=("Sales","sum"),Profit=("Order Profit Per Order","sum")); h["Margin %"]=h.Profit/h.Sales*100
    st.plotly_chart(px.imshow(h.pivot(index="Category Name",columns="Market",values="Margin %"),aspect="auto",color_continuous_scale="RdYlGn",title="Category Margin by Market (%)"),use_container_width=True)
    candidates=p[(p.Sales>=p.Sales.quantile(.75))&(p["Margin %"]<=p["Margin %"].median())].sort_values("Sales",ascending=False)
    st.subheader("High-Revenue / Low-Margin Products"); st.dataframe(candidates,use_container_width=True,hide_index=True)
    loss=p[p.Profit<0].sort_values("Profit")
    if not loss.empty: st.subheader("Loss-Making Products"); st.dataframe(loss,use_container_width=True,hide_index=True)

with t4:
    bd=f.groupby("Discount Band",observed=False,as_index=False).agg(Sales=("Sales","sum"),Profit=("Order Profit Per Order","sum"),Discount=("Order Item Discount","sum")); bd["Margin %"]=bd.Profit/bd.Sales*100
    a,b=st.columns(2)
    a.plotly_chart(px.bar(bd,x="Discount Band",y="Margin %",text_auto=".2f",title="Profit Margin by Discount Band"),use_container_width=True)
    sample=f.sample(min(15000,len(f)),random_state=42)
    b.plotly_chart(px.scatter(sample,x="Discount %",y="Order Profit Per Order",size="Sales",hover_data=["Product Name","Market"],title="Discount vs Profit"),use_container_width=True)
    nd=f[f["Discount %"]==0]; dd=f[f["Discount %"]>0]
    x=st.columns(3)
    x[0].metric("No-discount margin",f"{nd['Order Profit Per Order'].sum()/nd.Sales.sum()*100:.2f}%" if len(nd) else "N/A")
    x[1].metric("Discounted margin",f"{dd['Order Profit Per Order'].sum()/dd.Sales.sum()*100:.2f}%" if len(dd) else "N/A")
    x[2].metric("Loss-making lines",f"{(f['Order Profit Per Order']<0).mean()*100:.1f}%")
    st.subheader("What-if Discount Cap")
    cap=st.slider("Discount cap (%)",0,30,15,1)
    gross=f["Order Item Product Price"]*f["Order Item Quantity"]
    gain=((f["Order Item Discount Rate"]-cap/100).clip(lower=0)*gross).sum()
    st.metric("Estimated additional profit",f"${gain:,.0f}")
    st.caption("Scenario assumes volumes stay constant and discount reduction flows directly to profit; it is not a forecast.")

with t5:
    for field,title in [("Market","Market"),("Order Region","Order Region"),("Order Country","Country")]:
        g=f.groupby(field,as_index=False).agg(Sales=("Sales","sum"),Profit=("Order Profit Per Order","sum")); g["Margin %"]=g.Profit/g.Sales*100
        st.plotly_chart(px.bar(g.sort_values("Margin %"),x=field,y="Margin %",text_auto=".1f",title=f"Profit Margin by {title}"),use_container_width=True)

with t6:
    st.write(f"Filtered rows: **{len(f):,}**")
    st.download_button("⬇️ Download Filtered Data",f.to_csv(index=False).encode(),"apl_filtered_data.csv","text/csv")
    st.dataframe(f.head(1000),use_container_width=True,hide_index=True)
    st.info("The supplied dataset has 180,519 order lines and no calendar date field. Personal address fields and coordinates were removed from the cleaned app dataset.")
