"""
Nassau Candy Distributor — Factory-to-Customer Shipping Route Efficiency Dashboard
Run: streamlit run nassau_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nassau Candy | Route Intelligence",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Dark industrial header */
.main-header {
    background: linear-gradient(135deg, #0f1923 0%, #1a2d3f 50%, #0d2137 100%);
    border-radius: 12px;
    padding: 28px 36px 24px;
    margin-bottom: 24px;
    border-left: 5px solid #f7a600;
    position: relative;
    overflow: hidden;
}
.main-header::after {
    content: "🍬";
    position: absolute;
    right: 32px; top: 16px;
    font-size: 52px;
    opacity: 0.15;
}
.main-header h1 {
    color: #ffffff; font-size: 1.85rem; font-weight: 700;
    margin: 0 0 4px; letter-spacing: -0.5px;
}
.main-header p { color: #8da9c4; font-size: 0.9rem; margin: 0; }
.main-header .badge {
    display: inline-block; background: #f7a600; color: #0f1923;
    font-size: 0.72rem; font-weight: 700; padding: 2px 10px;
    border-radius: 20px; margin-top: 10px; letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* KPI cards */
.kpi-card {
    background: #ffffff;
    border: 1px solid #e8edf2;
    border-radius: 10px;
    padding: 18px 20px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    transition: box-shadow 0.2s;
}
.kpi-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.kpi-value { font-size: 2rem; font-weight: 700; color: #0f1923; font-family: 'DM Mono', monospace; }
.kpi-label { font-size: 0.78rem; color: #667d91; font-weight: 500; text-transform: uppercase; letter-spacing: 0.6px; margin-top: 4px; }
.kpi-delta { font-size: 0.78rem; margin-top: 6px; }
.kpi-bad  { color: #d7263d; }
.kpi-good { color: #1a936f; }
.kpi-neutral { color: #667d91; }

/* Section headers */
.section-header {
    font-size: 1.05rem; font-weight: 700; color: #0f1923;
    border-bottom: 2px solid #f7a600;
    padding-bottom: 6px; margin: 28px 0 16px;
    letter-spacing: -0.2px;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: #0f1923 !important;
}
section[data-testid="stSidebar"] * { color: #c9dae8 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stSlider label { color: #8da9c4 !important; font-size: 0.82rem !important; }

/* Table */
.route-table { font-size: 0.85rem; }

/* Alert boxes */
.alert-box {
    padding: 12px 16px; border-radius: 8px;
    font-size: 0.85rem; margin: 8px 0;
}
.alert-danger { background: #fff0f2; border-left: 4px solid #d7263d; color: #7a0e1e; }
.alert-success { background: #f0fff8; border-left: 4px solid #1a936f; color: #0a4d34; }
.alert-warning { background: #fffbf0; border-left: 4px solid #f7a600; color: #7a4e00; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
PRODUCT_FACTORY = {
    "Wonka Bar - Nutty Crunch Surprise":  "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows":          "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious":     "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate":         "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel":  "Wicked Choccy's",
    "Laffy Taffy":                        "Sugar Shack",
    "SweeTARTS":                          "Sugar Shack",
    "Nerds":                              "Sugar Shack",
    "Fun Dip":                            "Sugar Shack",
    "Fizzy Lifting Drinks":              "Sugar Shack",
    "Everlasting Gobstopper":             "Secret Factory",
    "Hair Toffee":                        "The Other Factory",
    "Lickable Wallpaper":                 "Secret Factory",
    "Wonka Gum":                          "Secret Factory",
    "Kazookles":                          "The Other Factory",
}

FACTORY_COLORS = {
    "Lot's O' Nuts":     "#f7a600",
    "Wicked Choccy's":   "#d7263d",
    "Sugar Shack":       "#1a936f",
    "Secret Factory":    "#4361ee",
    "The Other Factory": "#9b5de5",
}

REGION_COLORS = {
    "Atlantic": "#2196f3",
    "Gulf":     "#f7a600",
    "Interior": "#9b5de5",
    "Pacific":  "#1a936f",
}

# ── Data loading & caching ─────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau Candy Distributor.csv")

    df["Order Date"] = pd.to_datetime(
        df["Order Date"], dayfirst=True, errors="coerce"
    )
    df["Ship Date"] = pd.to_datetime(
        df["Ship Date"], dayfirst=True, errors="coerce"
    )

    df.dropna(subset=["Order Date", "Ship Date"], inplace=True)

    df["Lead_Time"] = (
        df["Ship Date"] - df["Order Date"]
    ).dt.days

    df = df[df["Lead_Time"] >= 0].copy()

    for col in ["State/Province", "Region", "City"]:
        df[col] = df[col].str.strip().str.title()

    df["Ship Mode"] = df["Ship Mode"].str.strip()

    df["Factory"] = df["Product Name"].map(PRODUCT_FACTORY)
    df["Route_Region"] = df["Factory"] + " → " + df["Region"]
    df["Route_State"] = df["Factory"] + " → " + df["State/Province"]

    df["Mode_Category"] = df["Ship Mode"].apply(
        lambda x: "Expedited" if x in ["First Class", "Same Day"] else "Standard"
    )

    df["Order_Month"] = df["Order Date"].dt.to_period("M").astype(str)
    df["Order_Year"] = df["Order Date"].dt.year

    return df


df_full = load_data()

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎛 Filters")
    st.markdown("---")

    date_min = df_full["Order Date"].min().date()
    date_max = df_full["Order Date"].max().date()
    date_range = st.date_input("Order Date Range", value=(date_min, date_max),
                               min_value=date_min, max_value=date_max)

    regions = st.multiselect("Customer Region",
                             options=sorted(df_full["Region"].unique()),
                             default=sorted(df_full["Region"].unique()))

    factories = st.multiselect("Factory",
                               options=sorted(df_full["Factory"].dropna().unique()),
                               default=sorted(df_full["Factory"].dropna().unique()))

    ship_modes = st.multiselect("Ship Mode",
                                options=sorted(df_full["Ship Mode"].unique()),
                                default=sorted(df_full["Ship Mode"].unique()))

    lt_min_val = int(df_full["Lead_Time"].min())
    lt_max_val = int(df_full["Lead_Time"].max())
    lt_range = st.slider("Lead Time Range (days)",
                         min_value=lt_min_val, max_value=lt_max_val,
                         value=(lt_min_val, lt_max_val))

    delay_pct_threshold = st.slider("Delay Threshold (percentile)",
                                    min_value=50, max_value=95,
                                    value=75, step=5,
                                    help="Shipments above this lead-time percentile are flagged as delayed.")

    st.markdown("---")
    st.markdown('<p style="font-size:0.72rem;color:#4a6580;">Nassau Candy Distributor<br>Logistics Intelligence Platform</p>',
                unsafe_allow_html=True)

# ── Apply filters ──────────────────────────────────────────────────────────────
if len(date_range) == 2:
    d0, d1 = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    d0, d1 = df_full["Order Date"].min(), df_full["Order Date"].max()

df = df_full[
    (df_full["Order Date"] >= d0) &
    (df_full["Order Date"] <= d1) &
    (df_full["Region"].isin(regions)) &
    (df_full["Factory"].isin(factories)) &
    (df_full["Ship Mode"].isin(ship_modes)) &
    (df_full["Lead_Time"] >= lt_range[0]) &
    (df_full["Lead_Time"] <= lt_range[1])
].copy()

delay_threshold = df_full["Lead_Time"].quantile(delay_pct_threshold / 100)
df["Is_Delayed"] = df["Lead_Time"] > delay_threshold

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>Nassau Candy Distributor</h1>
  <p>Factory-to-Customer Shipping Route Efficiency Intelligence</p>
  <span class="badge">Live Analytics</span>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.warning("No data matches the selected filters. Please adjust your selections.")
    st.stop()

# ── KPI Row ────────────────────────────────────────────────────────────────────
total_orders  = len(df)
avg_lt        = df["Lead_Time"].mean()
median_lt     = df["Lead_Time"].median()
delay_rate    = df["Is_Delayed"].mean() * 100
unique_routes = df["Route_State"].nunique()
total_sales   = df["Sales"].sum()

col1, col2, col3, col4, col5, col6 = st.columns(6)

kpi_data = [
    (col1, f"{total_orders:,}",        "Total Orders",         ""),
    (col2, f"{avg_lt:.0f}d",           "Avg Lead Time",        ""),
    (col3, f"{median_lt:.0f}d",        "Median Lead Time",     ""),
    (col4, f"{delay_rate:.1f}%",       "Delay Rate",           "kpi-bad" if delay_rate > 30 else "kpi-good"),
    (col5, f"{unique_routes}",         "Active Routes",        ""),
    (col6, f"${total_sales/1e3:.0f}K", "Total Sales",          "kpi-good"),
]

for col, val, label, css in kpi_data:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{val}</div>
            <div class="kpi-label">{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB LAYOUT
# ════════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Route Efficiency Overview",
    "🗺️ Geographic Analysis",
    "🚚 Ship Mode Comparison",
    "🔍 Route Drill-Down",
])

# ─── TAB 1: Route Efficiency Overview ─────────────────────────────────────────
with tab1:
    # Route aggregation
    route_state = (df.groupby("Route_State").agg(
        Total_Shipments  = ("Row ID",      "count"),
        Avg_Lead_Time    = ("Lead_Time",   "mean"),
        Median_Lead_Time = ("Lead_Time",   "median"),
        Std_Lead_Time    = ("Lead_Time",   "std"),
        Total_Sales      = ("Sales",       "sum"),
        Total_Profit     = ("Gross Profit","sum"),
        Delay_Rate       = ("Is_Delayed",  "mean"),
    ).reset_index().round(2))

    lt_min_ = route_state["Avg_Lead_Time"].min()
    lt_max_ = route_state["Avg_Lead_Time"].max()
    if lt_max_ > lt_min_:
        route_state["Efficiency_Score"] = (
            (lt_max_ - route_state["Avg_Lead_Time"]) / (lt_max_ - lt_min_) * 100
        ).round(1)
    else:
        route_state["Efficiency_Score"] = 100.0
    route_state["Delay_Rate_%"] = (route_state["Delay_Rate"] * 100).round(1)

    route_sorted = route_state.sort_values("Efficiency_Score", ascending=False).reset_index(drop=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-header">Top 10 Most Efficient Routes</div>', unsafe_allow_html=True)
        top10 = route_sorted.head(10)
        fig = px.bar(top10, x="Avg_Lead_Time", y="Route_State",
                     orientation="h",
                     color="Efficiency_Score",
                     color_continuous_scale=["#d7263d","#f7a600","#1a936f"],
                     hover_data=["Total_Shipments","Delay_Rate_%"],
                     labels={"Avg_Lead_Time":"Avg Lead Time (days)","Route_State":"Route","Efficiency_Score":"Score"})
        fig.update_layout(
            height=360, margin=dict(l=0,r=20,t=10,b=10),
            yaxis={"categoryorder":"total ascending"},
            coloraxis_showscale=False,
            plot_bgcolor="white", paper_bgcolor="white",
            font_family="DM Sans",
        )
        fig.update_traces(text=top10["Avg_Lead_Time"].round(0).astype(str)+"d",
                          textposition="outside", textfont_size=10)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="section-header">Bottom 10 Least Efficient Routes</div>', unsafe_allow_html=True)
        bot10 = route_sorted.tail(10).sort_values("Avg_Lead_Time", ascending=False)
        fig2 = px.bar(bot10, x="Avg_Lead_Time", y="Route_State",
                      orientation="h",
                      color="Avg_Lead_Time",
                      color_continuous_scale=["#f7a600","#d7263d","#7a0e1e"],
                      hover_data=["Total_Shipments","Delay_Rate_%"],
                      labels={"Avg_Lead_Time":"Avg Lead Time (days)","Route_State":"Route"})
        fig2.update_layout(
            height=360, margin=dict(l=0,r=20,t=10,b=10),
            yaxis={"categoryorder":"total ascending"},
            coloraxis_showscale=False,
            plot_bgcolor="white", paper_bgcolor="white",
            font_family="DM Sans",
        )
        fig2.update_traces(text=bot10["Avg_Lead_Time"].round(0).astype(str)+"d",
                           textposition="outside", textfont_size=10)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-header">Route Performance Leaderboard</div>', unsafe_allow_html=True)

    def color_score(val):
        if val >= 70: return "color: #1a936f; font-weight:600"
        elif val >= 40: return "color: #f7a600; font-weight:600"
        else: return "color: #d7263d; font-weight:600"

    display_df = route_sorted[[
        "Route_State","Total_Shipments","Avg_Lead_Time",
        "Median_Lead_Time","Std_Lead_Time","Delay_Rate_%","Efficiency_Score"
    ]].rename(columns={
        "Route_State":"Route",
        "Total_Shipments":"Shipments",
        "Avg_Lead_Time":"Avg Lead Time (d)",
        "Median_Lead_Time":"Median (d)",
        "Std_Lead_Time":"Std Dev",
        "Delay_Rate_%":"Delay Rate %",
        "Efficiency_Score":"Efficiency Score",
    })

    st.dataframe(
        display_df.style.applymap(color_score, subset=["Efficiency Score"]),
        use_container_width=True, height=400,
    )

    # Factory comparison
    st.markdown('<div class="section-header">Factory Performance Comparison</div>', unsafe_allow_html=True)
    factory_agg = (df.groupby("Factory").agg(
        Shipments     = ("Row ID",     "count"),
        Avg_Lead_Time = ("Lead_Time",  "mean"),
        Delay_Rate    = ("Is_Delayed", "mean"),
        Total_Profit  = ("Gross Profit","sum"),
    ).reset_index().round(2))
    factory_agg["Delay_Rate_%"] = (factory_agg["Delay_Rate"] * 100).round(1)
    factory_agg["Color"] = factory_agg["Factory"].map(FACTORY_COLORS)

    fig3 = px.scatter(factory_agg,
                      x="Avg_Lead_Time", y="Delay_Rate_%",
                      size="Shipments", color="Factory",
                      color_discrete_map=FACTORY_COLORS,
                      hover_data=["Shipments","Total_Profit"],
                      labels={"Avg_Lead_Time":"Avg Lead Time (days)","Delay_Rate_%":"Delay Rate %","Factory":"Factory"},
                      size_max=55)
    fig3.update_layout(
        height=380, margin=dict(l=0,r=0,t=10,b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="DM Sans",
    )
    fig3.add_hline(y=delay_rate, line_dash="dot", line_color="#667d91",
                   annotation_text="Overall delay rate", annotation_position="top right")
    st.plotly_chart(fig3, use_container_width=True)

# ─── TAB 2: Geographic Analysis ───────────────────────────────────────────────
with tab2:
    # State-level aggregation
    state_agg = (df.groupby("State/Province").agg(
        Shipments     = ("Row ID",     "count"),
        Avg_Lead_Time = ("Lead_Time",  "mean"),
        Std_Lead_Time = ("Lead_Time",  "std"),
        Delay_Rate    = ("Is_Delayed", "mean"),
        Total_Sales   = ("Sales",      "sum"),
    ).reset_index().round(2))
    state_agg["Delay_Rate_%"] = (state_agg["Delay_Rate"] * 100).round(1)

    # US state abbreviation map (50 states + DC + territories)
    state_abbrev = {
        "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
        "Colorado":"CO","Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA",
        "Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA",
        "Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD",
        "Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS",
        "Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH",
        "New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC",
        "North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA",
        "Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN",
        "Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA",
        "West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY","District Of Columbia":"DC",
    }
    state_agg["State_Code"] = state_agg["State/Province"].map(state_abbrev)

    col_map1, col_map2 = st.columns(2)

    with col_map1:
        st.markdown('<div class="section-header">Avg Lead Time by State</div>', unsafe_allow_html=True)
        fig_map1 = px.choropleth(
            state_agg.dropna(subset=["State_Code"]),
            locations="State_Code", locationmode="USA-states",
            color="Avg_Lead_Time",
            scope="usa",
            color_continuous_scale=["#1a936f","#f7a600","#d7263d"],
            hover_name="State/Province",
            hover_data={"Shipments":True,"Avg_Lead_Time":":.1f","Delay_Rate_%":":.1f","State_Code":False},
            labels={"Avg_Lead_Time":"Avg Lead Time (d)"},
        )
        fig_map1.update_layout(
            height=370, margin=dict(l=0,r=0,t=0,b=0),
            font_family="DM Sans",
            coloraxis_colorbar=dict(title="Days"),
        )
        st.plotly_chart(fig_map1, use_container_width=True)

    with col_map2:
        st.markdown('<div class="section-header">Delay Rate (%) by State</div>', unsafe_allow_html=True)
        fig_map2 = px.choropleth(
            state_agg.dropna(subset=["State_Code"]),
            locations="State_Code", locationmode="USA-states",
            color="Delay_Rate_%",
            scope="usa",
            color_continuous_scale=["#e8f5e9","#f7a600","#7a0e1e"],
            hover_name="State/Province",
            hover_data={"Shipments":True,"Avg_Lead_Time":":.1f","Delay_Rate_%":":.1f","State_Code":False},
            labels={"Delay_Rate_%":"Delay Rate %"},
        )
        fig_map2.update_layout(
            height=370, margin=dict(l=0,r=0,t=0,b=0),
            font_family="DM Sans",
            coloraxis_colorbar=dict(title="Delay %"),
        )
        st.plotly_chart(fig_map2, use_container_width=True)

    # Regional heatmap
    st.markdown('<div class="section-header">Factory × Region Lead Time Heatmap</div>', unsafe_allow_html=True)
    heatmap_data = (df.groupby(["Factory","Region"])["Lead_Time"]
                      .mean().unstack(fill_value=np.nan).round(1))

    fig_heat = px.imshow(
        heatmap_data,
        color_continuous_scale=["#1a936f","#fffbf0","#d7263d"],
        text_auto=".0f",
        aspect="auto",
        labels={"color":"Avg Lead Time (d)"},
    )
    fig_heat.update_layout(
        height=280, margin=dict(l=0,r=0,t=10,b=0),
        font_family="DM Sans", coloraxis_showscale=True,
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig_heat.update_traces(textfont_size=13)
    st.plotly_chart(fig_heat, use_container_width=True)

    # Bottleneck table
    st.markdown('<div class="section-header">High-Volume / High-Delay Bottleneck States</div>', unsafe_allow_html=True)
    vol_thresh = state_agg["Shipments"].quantile(0.5)
    lt_thresh  = state_agg["Avg_Lead_Time"].quantile(0.6)
    bottleneck = state_agg[(state_agg["Shipments"] >= vol_thresh) &
                           (state_agg["Avg_Lead_Time"] >= lt_thresh)].sort_values("Avg_Lead_Time", ascending=False)

    if bottleneck.empty:
        st.markdown('<div class="alert-box alert-success">✅ No significant bottleneck states detected with current filters.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert-box alert-warning">⚠️ {len(bottleneck)} state(s) flagged as high-volume + high-delay.</div>',
                    unsafe_allow_html=True)
        st.dataframe(
            bottleneck[["State/Province","Shipments","Avg_Lead_Time","Delay_Rate_%"]].rename(columns={
                "State/Province":"State","Avg_Lead_Time":"Avg Lead Time (d)","Delay_Rate_%":"Delay Rate %"
            }),
            use_container_width=True, height=280,
        )

# ─── TAB 3: Ship Mode Comparison ──────────────────────────────────────────────
with tab3:
    mode_agg = (df.groupby("Ship Mode").agg(
        Shipments     = ("Row ID",      "count"),
        Avg_Lead_Time = ("Lead_Time",   "mean"),
        Med_Lead_Time = ("Lead_Time",   "median"),
        Std_Lead_Time = ("Lead_Time",   "std"),
        Avg_Cost      = ("Cost",        "mean"),
        Avg_Sales     = ("Sales",       "mean"),
        Avg_Profit    = ("Gross Profit","mean"),
        Delay_Rate    = ("Is_Delayed",  "mean"),
    ).reset_index().sort_values("Avg_Lead_Time").round(2))
    mode_agg["Delay_Rate_%"] = (mode_agg["Delay_Rate"] * 100).round(1)

    c3a, c3b = st.columns(2)

    with c3a:
        st.markdown('<div class="section-header">Lead Time by Ship Mode</div>', unsafe_allow_html=True)
        fig_mode1 = go.Figure()
        colors_mode = ["#1a936f","#4361ee","#f7a600","#d7263d"]
        for i, row in mode_agg.iterrows():
            fig_mode1.add_trace(go.Bar(
                x=[row["Ship Mode"]],
                y=[row["Avg_Lead_Time"]],
                name=row["Ship Mode"],
                marker_color=colors_mode[i % len(colors_mode)],
                error_y=dict(type="data", array=[row["Std_Lead_Time"]], visible=True, color="#666"),
                text=[f"{row['Avg_Lead_Time']:.0f}d"],
                textposition="outside",
            ))
        fig_mode1.update_layout(
            height=360, showlegend=False,
            margin=dict(l=0,r=0,t=20,b=10),
            plot_bgcolor="white", paper_bgcolor="white",
            font_family="DM Sans", yaxis_title="Avg Lead Time (days)",
        )
        st.plotly_chart(fig_mode1, use_container_width=True)

    with c3b:
        st.markdown('<div class="section-header">Cost vs. Profit by Ship Mode</div>', unsafe_allow_html=True)
        fig_mode2 = go.Figure()
        fig_mode2.add_trace(go.Bar(
            name="Avg Cost", x=mode_agg["Ship Mode"], y=mode_agg["Avg_Cost"],
            marker_color="#d7263d", text=mode_agg["Avg_Cost"].round(2),
            textposition="outside",
        ))
        fig_mode2.add_trace(go.Bar(
            name="Avg Profit", x=mode_agg["Ship Mode"], y=mode_agg["Avg_Profit"],
            marker_color="#1a936f", text=mode_agg["Avg_Profit"].round(2),
            textposition="outside",
        ))
        fig_mode2.update_layout(
            barmode="group", height=360,
            margin=dict(l=0,r=0,t=20,b=10),
            plot_bgcolor="white", paper_bgcolor="white",
            font_family="DM Sans", yaxis_title="USD",
            legend=dict(orientation="h", y=1.08),
        )
        st.plotly_chart(fig_mode2, use_container_width=True)

    # Violin
    st.markdown('<div class="section-header">Lead Time Distribution per Ship Mode</div>', unsafe_allow_html=True)
    mode_order = df.groupby("Ship Mode")["Lead_Time"].mean().sort_values().index.tolist()
    fig_violin = go.Figure()
    for i, mode in enumerate(mode_order):
        sub = df[df["Ship Mode"] == mode]["Lead_Time"]
        fig_violin.add_trace(go.Violin(
            y=sub, name=mode, box_visible=True,
            meanline_visible=True,
            fillcolor=colors_mode[i % len(colors_mode)],
            opacity=0.7,
            line_color="#333",
        ))
    fig_violin.update_layout(
        height=360, showlegend=False,
        margin=dict(l=0,r=0,t=10,b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="DM Sans", yaxis_title="Lead Time (days)",
    )
    st.plotly_chart(fig_violin, use_container_width=True)

    # Standard vs Expedited
    st.markdown('<div class="section-header">Standard vs. Expedited — Cost-Time Tradeoff</div>', unsafe_allow_html=True)
    cat_agg = (df.groupby("Mode_Category").agg(
        Shipments=("Row ID","count"), Avg_Lead_Time=("Lead_Time","mean"),
        Avg_Cost=("Cost","mean"), Avg_Profit=("Gross Profit","mean"),
        Delay_Rate=("Is_Delayed","mean"),
    ).reset_index().round(2))
    cat_agg["Delay_Rate_%"] = (cat_agg["Delay_Rate"] * 100).round(1)

    cc1, cc2, cc3, cc4 = st.columns(4)
    for col_, mode_cat in zip([cc1, cc2], ["Standard","Expedited"]):
        row_ = cat_agg[cat_agg["Mode_Category"] == mode_cat]
        if not row_.empty:
            r = row_.iloc[0]
            with col_:
                st.markdown(f"""
                <div class="kpi-card">
                    <div style="font-size:0.78rem;color:#667d91;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:8px;">{mode_cat}</div>
                    <div style="font-size:1.4rem;font-weight:700;color:#0f1923;font-family:'DM Mono',monospace;">{r['Avg_Lead_Time']:.0f}d</div>
                    <div style="font-size:0.78rem;color:#667d91;margin-top:4px;">Avg Lead Time</div>
                    <div style="font-size:0.9rem;font-weight:600;color:#1a936f;margin-top:6px;">${r['Avg_Profit']:.2f} profit</div>
                    <div style="font-size:0.78rem;color:#667d91;">{r['Shipments']:,} shipments</div>
                </div>""", unsafe_allow_html=True)

# ─── TAB 4: Route Drill-Down ───────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">State-Level Performance Insights</div>', unsafe_allow_html=True)

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        sel_factory = st.selectbox("Select Factory",
                                   options=["All"] + sorted(df["Factory"].dropna().unique().tolist()))
    with col_sel2:
        sel_state = st.selectbox("Select State",
                                 options=["All"] + sorted(df["State/Province"].unique().tolist()))

    df_drill = df.copy()
    if sel_factory != "All":
        df_drill = df_drill[df_drill["Factory"] == sel_factory]
    if sel_state != "All":
        df_drill = df_drill[df_drill["State/Province"] == sel_state]

    if df_drill.empty:
        st.info("No data for this combination.")
    else:
        d1_, d2_, d3_, d4_ = st.columns(4)
        d1_.metric("Orders",         f"{len(df_drill):,}")
        d2_.metric("Avg Lead Time",  f"{df_drill['Lead_Time'].mean():.0f} days")
        d3_.metric("Delay Rate",     f"{df_drill['Is_Delayed'].mean()*100:.1f}%")
        d4_.metric("Total Sales",    f"${df_drill['Sales'].sum():,.0f}")

        # Timeline
        st.markdown('<div class="section-header">Order-Level Shipment Timeline</div>', unsafe_allow_html=True)
        timeline = df_drill.sort_values("Order Date")[["Order Date","Ship Date","Lead_Time","Ship Mode","State/Province","Factory","Product Name","Sales"]].head(200)
        timeline_disp = timeline.rename(columns={
            "Order Date":"Order Date","Ship Date":"Ship Date",
            "Lead_Time":"Lead Time (d)","Ship Mode":"Ship Mode",
            "State/Province":"State","Factory":"Factory",
            "Product Name":"Product","Sales":"Sales ($)",
        })
        st.dataframe(timeline_disp, use_container_width=True, height=320)

        # Lead time distribution for this drill
        st.markdown('<div class="section-header">Lead Time Distribution</div>', unsafe_allow_html=True)
        fig_drill = px.histogram(df_drill, x="Lead_Time", color="Ship Mode",
                                 nbins=30, barmode="overlay",
                                 color_discrete_sequence=["#4361ee","#f7a600","#1a936f","#d7263d"],
                                 labels={"Lead_Time":"Lead Time (days)","count":"Shipments"})
        fig_drill.add_vline(x=df_drill["Lead_Time"].mean(), line_dash="dash",
                            line_color="#0f1923", annotation_text="Mean",
                            annotation_position="top right")
        fig_drill.update_layout(
            height=320, margin=dict(l=0,r=0,t=10,b=10),
            plot_bgcolor="white", paper_bgcolor="white",
            font_family="DM Sans",
        )
        st.plotly_chart(fig_drill, use_container_width=True)

        # Monthly trend for this selection
        st.markdown('<div class="section-header">Monthly Lead Time Trend</div>', unsafe_allow_html=True)
        monthly = (df_drill.groupby("Order_Month")["Lead_Time"]
                    .agg(Mean="mean", Median="median")
                    .reset_index())
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=monthly["Order_Month"], y=monthly["Mean"],
                                       mode="lines+markers", name="Mean",
                                       line=dict(color="#4361ee", width=2),
                                       marker=dict(size=5)))
        fig_trend.add_trace(go.Scatter(x=monthly["Order_Month"], y=monthly["Median"],
                                       mode="lines+markers", name="Median",
                                       line=dict(color="#f7a600", width=2, dash="dot"),
                                       marker=dict(size=5)))
        fig_trend.update_layout(
            height=300, margin=dict(l=0,r=0,t=10,b=10),
            plot_bgcolor="white", paper_bgcolor="white",
            font_family="DM Sans", yaxis_title="Lead Time (days)",
            legend=dict(orientation="h", y=1.08),
            xaxis=dict(tickangle=-45),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:#8da9c4;font-size:0.78rem;">'
    'Nassau Candy Distributor · Logistics Intelligence Platform · '
    f'{len(df):,} orders loaded · Delay threshold: {delay_threshold:.0f} days ({delay_pct_threshold}th pct)'
    '</p>',
    unsafe_allow_html=True
)
