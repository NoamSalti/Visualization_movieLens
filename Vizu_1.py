

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pgeocode
import json

# --- 1) Page ---
st.set_page_config(layout="wide", page_title="USA MovieLens Ratings Map")

# --- 2) Helpers ---
def calculate_weighted_rating(df, m=None):
    """
    IMDb-style weighted rating:
    WR = (v/(v+m))*R + (m/(v+m))*C
    """
    v = df["Rating_Count"]
    R = df["Avg_Rating"]
    C = df["Avg_Rating"].mean()
    if m is None:
        m = v.quantile(0.50)  # median
    df["Weighted_Score"] = (v / (v + m) * R) + (m / (v + m) * C)
    df["_C_global"] = C
    df["_m_used"] = m
    return df

@st.cache_data
def load_data():
    df = pd.read_csv("usa_ratings_lite.csv", low_memory=False)
    
    usa_df = df.copy()

    nomi = pgeocode.Nominatim("us")
    usa_df["Zip-code"] = usa_df["Zip-code"].astype(str).str.split("-").str[0].str.strip()

    unique_zips = usa_df["Zip-code"].dropna().unique()
    geo_data = nomi.query_postal_code(unique_zips)
    geo_data = geo_data.dropna(subset=["latitude", "longitude", "state_code"])

    geo_info = geo_data[["postal_code", "latitude", "longitude", "place_name", "state_code", "state_name"]].copy()
    
    geo_info.columns = ["Zip-code", "lat", "lon", "City_Name", "State_Code", "State"]
    
    geo_info["State_Code"] = geo_info["State_Code"].astype(str).str.upper()

    merged = pd.merge(usa_df, geo_info, on="Zip-code", how="inner")
    return merged

@st.cache_data
def load_zcta_geojson():
    geojson_path = r"zcta.geojson.json"
    with open(geojson_path, "r", encoding="utf-8") as f:
        return json.load(f)

# State label positions (approx. centroids) for abbreviations on the US map
STATE_LABEL_POS = {
    "AL": (32.806671, -86.791130), "AK": (64.200841, -149.493673), "AZ": (34.048928, -111.093731),
    "AR": (34.969704, -92.373123), "CA": (36.778261, -119.417932), "CO": (39.550051, -105.782067),
    "CT": (41.603221, -73.087749), "DE": (38.910832, -75.527670), "FL": (27.664827, -81.515754),
    "GA": (32.165622, -82.900075), "HI": (19.896766, -155.582782), "ID": (44.068202, -114.742041),
    "IL": (40.633125, -89.398528), "IN": (40.551217, -85.602364), "IA": (41.878003, -93.097702),
    "KS": (39.011902, -98.484246), "KY": (37.839333, -84.270018), "LA": (30.984298, -91.962333),
    "ME": (45.253783, -69.445469), "MD": (39.045755, -76.641271), "MA": (42.407211, -71.382437),
    "MI": (44.314844, -85.602364), "MN": (46.729553, -94.685900), "MS": (32.354668, -89.398528),
    "MO": (37.964253, -91.831833), "MT": (46.879682, -110.362566), "NE": (41.492537, -99.901813),
    "NV": (38.802610, -116.419389), "NH": (43.193852, -71.572395), "NJ": (40.058324, -74.405661),
    "NM": (34.519940, -105.870090), "NY": (43.299428, -74.217933), "NC": (35.759573, -79.019300),
    "ND": (47.551493, -101.002012), "OH": (40.417287, -82.907123), "OK": (35.007752, -97.092877),
    "OR": (43.804133, -120.554201), "PA": (41.203322, -77.194525), "RI": (41.580095, -71.477429),
    "SC": (33.836081, -81.163725), "SD": (43.969515, -99.901813), "TN": (35.517491, -86.580447),
    "TX": (31.968599, -99.901813), "UT": (39.320980, -111.093731), "VT": (44.558803, -72.577841),
    "VA": (37.431573, -78.656894), "WA": (47.751074, -120.740139), "WV": (38.597626, -80.454903),
    "WI": (43.784440, -88.787868), "WY": (43.075968, -107.290284),
    "DC": (38.907192, -77.036871),
}

ZCTA_KEY = "ZCTA5CE10"
zcta_geojson = load_zcta_geojson()
data = load_data()

if data is None or data.empty:
    st.error("Failed to load data.")
    st.stop()

# --- Session state ---
if "selected_state" not in st.session_state:
    st.session_state.selected_state = "All USA"

# --- Sidebar ---
st.sidebar.header("Controls")


if st.session_state.selected_state == "All USA":
    metric_mode = st.sidebar.radio(
        "Metric (States):",
        options=[
            "Number of Ratings",
            "Above/Below Global Average (Δ)"
        ],
        index=0
    )
else:
    metric_mode = st.sidebar.radio(
        "Metric (ZIPs):",
        options=[
            "Number of Ratings",
            "Average Rating",
            "Weighted Rating (IMDb formula)",
            "Above/Below Global Average (Δ)"
        ],
        index=2  # keep Weighted as default in ZIP view if you want
    )

min_zip_votes = st.sidebar.slider("Min ZIP votes (drilldown):", 0, 300, 20)

if st.session_state.selected_state != "All USA":
    if st.sidebar.button("Back to USA"):
        st.session_state.selected_state = "All USA"
        st.rerun()

# --- Aggregations ---
state_stats = data.groupby(["State_Code", "State"]).agg(
    Avg_Rating=("rating", "mean"),
    Rating_Count=("rating", "count")
).reset_index()

state_stats = state_stats.dropna(subset=["State_Code"])
state_stats = calculate_weighted_rating(state_stats)

zip_stats = data.groupby(["State_Code", "Zip-code"]).agg(
    Avg_Rating=("rating", "mean"),
    Rating_Count=("rating", "count")
).reset_index()

zip_stats = calculate_weighted_rating(zip_stats)
zip_stats["Zip-code"] = zip_stats["Zip-code"].astype(str).str.zfill(5)

# Global mean (for Δ)
C_global = float(state_stats["Avg_Rating"].mean())
state_stats["Delta"] = state_stats["Avg_Rating"] - C_global
zip_stats["Delta"] = zip_stats["Avg_Rating"] - C_global

state_stats["Delta_fmt"] = state_stats["Delta"].map(lambda x: f"{x:+.3f}")
zip_stats["Delta_fmt"] = zip_stats["Delta"].map(lambda x: f"{x:+.3f}")

# --- Color scales ---
custom_red_white_green = [
    [0.0, "rgb(200, 0, 0)"],
    [0.5, "rgb(255, 255, 255)"],
    [1.0, "rgb(0, 70, 0)"],
]
custom_blues = [
    [0.0, "rgb(255, 255, 255)"],
    [0.05, "rgb(160, 200, 255)"],
    [1.0, "rgb(0, 0, 130)"],
]

# --- Metric selection -> columns + scales ---
if metric_mode == "Average Rating":
    col = "Avg_Rating"
    colorscale = custom_red_white_green
    zmin, zmax = 1.0, 5.0
    metric_title = "Average Rating"

elif metric_mode == "Weighted Rating (IMDb formula)":
    col = "Weighted_Score"
    colorscale = custom_red_white_green
    zmin, zmax = 1.0, 5.0
    metric_title = "Weighted Rating (IMDb formula)"

elif metric_mode == "Number of Ratings":
    col = "Rating_Count"
    colorscale = custom_blues
    zmin, zmax = 0, None
    metric_title = "Number of Ratings"

else:  # Δ
    state_stats["Delta"] = state_stats["Avg_Rating"] - C_global
    zip_stats["Delta"] = zip_stats["Avg_Rating"] - C_global

    col = "Delta"
    colorscale = custom_red_white_green
    metric_title = "Δ from Global Mean"

    bound = float(state_stats["Delta"].abs().quantile(0.95))
    zmin, zmax = -bound, bound

# --- Title ---
METRIC_SUBTITLES = {
    "Number of Ratings":
        "Shows how many movie ratings were submitted in each area.",
    "Average Rating":
        "Simple mean of movie ratings — treats all areas equally, regardless of sample size.",
    "Weighted Rating (IMDb formula)":
        "Balances average rating with number of votes, reducing noise from small samples.",
    "Above/Below Global Average (Δ)":
        "Difference from the U.S. average rating."
}

st.title("How Movie Ratings Differ Across the U.S?")

st.markdown(
    f"<span style='font-size:22px; font-weight:600;'>{metric_mode}</span> "
    f"<span style='font-size:16px; color:gray;'>— {METRIC_SUBTITLES.get(metric_mode, '')}</span>",
    unsafe_allow_html=True
)

st.caption("Click a state to zoom into ZIP areas.")

# --- Sidebar: Show IMDb-style formula ---
if metric_mode == "Weighted Rating (IMDb formula)":
    with st.sidebar.expander("IMDb weighted score formula"):
        st.latex(r"WR=\frac{v}{v+m}R + \frac{m}{v+m}C")
        C_used = float(state_stats["_C_global"].iloc[0])
        m_used = float(state_stats["_m_used"].iloc[0])
        st.write(f"C (global mean): {C_used:.3f}")
        st.write(f"m (median votes): {m_used:.0f}")
        st.write("R = entity average rating, v = entity vote count")
        st.write("Higher m ⇒ stronger pull toward the global mean.")

# ---------------------------
# VIEW 1: All USA (States)
# ---------------------------
if st.session_state.selected_state == "All USA":
    fig = go.Figure()
    if metric_mode == "Number of Ratings":
        hovertemplate_state = (
            "<b>%{customdata[0]} (%{text})</b><br>"
            "Number of Ratings: %{z}<br>"
            "Average: %{customdata[2]:.3f}<br>"
            "Weighted Rating: %{customdata[3]:.3f}<br>"
            "Above/Below U.S. Average: %{customdata[4]}"
            "<extra></extra>"
        )
    else:
        hovertemplate_state = (
            "<b>%{customdata[0]} (%{text})</b><br>"
            f"{metric_title}: %{{z:.3f}}<br>"
            "Number of Ratings: %{customdata[1]}<br>"
            "Average: %{customdata[2]:.3f}<br>"
            "Weighted: %{customdata[3]:.3f}<br>"
            "Above/Below U.S. Average: %{customdata[4]}"
            "<extra></extra>"
        )

    fig.add_trace(go.Choropleth(
        locations=state_stats["State_Code"],
        z=state_stats[col],
        locationmode="USA-states",
        colorscale=colorscale,
        zmin=zmin, zmax=zmax,
        text=state_stats["State_Code"],
        customdata=state_stats[["State", "Rating_Count", "Avg_Rating", "Weighted_Score", "Delta_fmt"]],
        hovertemplate=hovertemplate_state,
        marker_line_color="white",
        marker_line_width=1,
        colorbar_title="Value"
    ))

    # State abbreviations labels
    label_lats, label_lons, label_text = [], [], []
    for sc in sorted(state_stats["State_Code"].unique()):
        if sc in STATE_LABEL_POS:
            lat, lon = STATE_LABEL_POS[sc]
            label_lats.append(lat)
            label_lons.append(lon)
            label_text.append(sc)

    fig.add_trace(go.Scattergeo(
        lat=label_lats,
        lon=label_lons,
        mode="text",
        text=label_text,
        textfont=dict(size=10),
        hoverinfo="skip"
    ))

    fig.update_layout(
        geo=dict(
            scope="usa",
            projection_type="albers usa",
            showlakes=True,
            lakecolor="rgb(255,255,255)",
        ),
        clickmode="event+select",
        margin={"r": 0, "t": 10, "l": 0, "b": 0},
        height=650
    )

    event = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points"
    )



    try:
        points = event.selection.get("points", [])
    except Exception:
        points = []

    if points:
        state_code = points[0].get("location")
        if state_code:
            st.session_state.selected_state = state_code
            st.rerun()

# ---------------------------
# VIEW 2: Drilldown (ZIP polygons) + State Outline
# ---------------------------
else:
    state_code = st.session_state.selected_state

    subset_zip = zip_stats[(zip_stats["State_Code"] == state_code) & (zip_stats["Rating_Count"] >= min_zip_votes)].copy()
    if subset_zip.empty:
        st.warning(f"No ZIP areas found for {state_code} after applying Min ZIP votes.")
        st.stop()

    zip_set = set(subset_zip["Zip-code"].astype(str))
    filtered_geojson = {
        "type": "FeatureCollection",
        "features": [
            feat for feat in zcta_geojson["features"]
            if str(feat["properties"].get(ZCTA_KEY, "")).zfill(5) in zip_set
        ]
    }

    fig = go.Figure()

    if metric_mode == "Number of Ratings":
        hovertemplate_zip = (
            "<b>ZIP: %{location}</b><br>"
            "Votes: %{z}<br>"
            "Avg: %{customdata[1]:.3f}<br>"
            "Weighted: %{customdata[2]:.3f}<br>"
            "Above/Below U.S. mean: %{customdata[3]}"
            "<extra></extra>"
        )
    else:
        hovertemplate_zip = (
            "<b>ZIP: %{location}</b><br>"
            f"{metric_title}: %{{z:.3f}}<br>"
            "Votes: %{customdata[0]}<br>"
            "Avg: %{customdata[1]:.3f}<br>"
            "Weighted: %{customdata[2]:.3f}<br>"
            "Above/Below U.S. mean: %{customdata[3]}"
            "<extra></extra>"
        )

    fig.add_trace(go.Choropleth(
        geojson=filtered_geojson,
        locations=subset_zip["Zip-code"],
        featureidkey=f"properties.{ZCTA_KEY}",
        z=subset_zip[col],
        colorscale=colorscale,
        zmin=zmin, zmax=zmax,
        marker_line_width=0.2,
        colorbar_title=metric_title,
        customdata=subset_zip[["Rating_Count", "Avg_Rating", "Weighted_Score", "Delta_fmt"]],
        hovertemplate=hovertemplate_zip,
    ))

    # State OUTLINE overlay
    fig.add_trace(go.Choropleth(
        locations=[state_code],
        z=[1],
        locationmode="USA-states",
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        showscale=False,
        marker_line_color="black",
        marker_line_width=3,
        hoverinfo="skip"
    ))

    fig.update_layout(
        geo=dict(
            scope="usa",
            projection_type="albers usa",
            fitbounds="locations",
            visible=True
        ),
        margin={"r": 0, "t": 10, "l": 0, "b": 0},
        height=650
    )

    st.subheader(f"{state_code} — ZIP-level view")
    st.plotly_chart(fig, use_container_width=True)




