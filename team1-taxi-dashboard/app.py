import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# --- App Config ---
st.set_page_config(page_title="Taxi Analytics Dashboard", layout="wide")
st.title("\U0001F695 Team 1 Taxi Analytics Dashboard")
st.caption("Gold Star Schema Dashboard — Revenue, Zone Performance & Service Quality KPIs")

# --- Load Data from Local Files ---
DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_zones():
    return pd.read_csv(DATA_DIR / "dim_zone.csv")


@st.cache_data
def load_dates():
    df = pd.read_csv(DATA_DIR / "dim_date.csv")
    df["full_date"] = pd.to_datetime(df["full_date"])
    return df


@st.cache_data
def load_kpis():
    df = pd.read_csv(DATA_DIR / "gold_daily_kpis.csv")
    df["full_date"] = pd.to_datetime(df["full_date"])
    return df


@st.cache_data
def load_zone_daily_agg():
    return pd.read_csv(DATA_DIR / "fact_zone_daily_agg.csv")


@st.cache_data
def load_trips_sample():
    return pd.read_csv(DATA_DIR / "fact_trip_sample.csv")


@st.cache_data
def load_hourly_trips():
    df = pd.read_csv(DATA_DIR / "trips_per_hour_by_day.csv")
    df["trip_date"] = pd.to_datetime(df["trip_date"])
    return df


zones_df = load_zones()
dates_df = load_dates()
kpis_df = load_kpis()
zone_daily_df = load_zone_daily_agg()
trips_df = load_trips_sample()
hourly_df = load_hourly_trips()

# --- Sidebar Filters (matching Databricks dashboard filters) ---
st.sidebar.header("\U0001F50D Filters")

# Date range
min_date = dates_df["full_date"].min().date()
max_date = dates_df["full_date"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# Pickup Zone multiselect (matches dashboard "Filter: Pickup Zone")
zone_options = sorted(zones_df["zone_code"].tolist())
selected_zones = st.sidebar.multiselect("Pickup Zone", options=zone_options, default=[])

# Day of week (matches dashboard "Filter: Day of Week")
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
selected_days = st.sidebar.multiselect("Day of Week", options=days_of_week, default=[])

# Payment Type filter (matches dashboard "Filter: Payment Type")
payment_types = sorted(trips_df["payment_type"].dropna().unique().tolist())
selected_payment_types = st.sidebar.multiselect("Payment Type", options=payment_types, default=[])

# Hour of Day filter (matches dashboard "Filter: Hour of Day")
hour_options = list(range(24))
selected_hours = st.sidebar.multiselect("Hour of Day", options=hour_options, default=[], format_func=lambda x: f"{x:02d}:00")

# Weather Condition filter
weather_options = sorted(dates_df["weather_desc"].dropna().unique().tolist())
selected_weather = st.sidebar.multiselect("Weather Condition", options=weather_options, default=[])

# Derive valid date_keys for weather filter (used across all filter functions)
if selected_weather:
    weather_date_keys = dates_df[dates_df["weather_desc"].isin(selected_weather)]["date_key"].tolist()
else:
    weather_date_keys = None


# --- Apply Filters ---
def filter_kpis(df):
    """Filter the KPIs dataframe based on sidebar selections."""
    filtered = df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        filtered = filtered[
            (filtered["full_date"].dt.date >= date_range[0]) &
            (filtered["full_date"].dt.date <= date_range[1])
        ]
    if selected_days:
        filtered = filtered[filtered["day_name"].isin(selected_days)]
    return filtered


def filter_zone_agg(df):
    """Filter the zone daily aggregation dataframe."""
    filtered = df.merge(dates_df[["date_key", "full_date", "day_name"]],
                        left_on="trip_booked_for_date_key", right_on="date_key", how="inner")
    if isinstance(date_range, tuple) and len(date_range) == 2:
        filtered = filtered[
            (filtered["full_date"].dt.date >= date_range[0]) &
            (filtered["full_date"].dt.date <= date_range[1])
        ]
    if selected_days:
        filtered = filtered[filtered["day_name"].isin(selected_days)]
    if selected_zones:
        zone_keys = zones_df[zones_df["zone_code"].isin(selected_zones)]["zone_key"].tolist()
        filtered = filtered[filtered["pickup_zone_key"].isin(zone_keys)]
    return filtered


def filter_trips(df):
    """Filter the trips dataframe based on sidebar selections."""
    filtered = df.merge(dates_df[["date_key", "full_date", "day_name"]],
                        left_on="trip_booked_for_date_key", right_on="date_key", how="inner")
    if isinstance(date_range, tuple) and len(date_range) == 2:
        filtered = filtered[
            (filtered["full_date"].dt.date >= date_range[0]) &
            (filtered["full_date"].dt.date <= date_range[1])
        ]
    if selected_days:
        filtered = filtered[filtered["day_name"].isin(selected_days)]
    if selected_zones:
        zone_keys = zones_df[zones_df["zone_code"].isin(selected_zones)]["zone_key"].tolist()
        filtered = filtered[filtered["pickup_zone_key"].isin(zone_keys)]
    if selected_payment_types:
        filtered = filtered[filtered["payment_type"].isin(selected_payment_types)]
    return filtered


filtered_trips = filter_trips(trips_df)

# --- KPI Section ---
st.markdown("---")
st.subheader("\U0001F4CA Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)
if not filtered_trips.empty:
    col1.metric("\U0001F4B0 Total Revenue", f"\u00a3{filtered_trips['fare_amount'].sum():,.2f}")
    col2.metric("\U0001F696 Total Trips", f"{len(filtered_trips):,}")
    col3.metric("\u23F1\uFE0F Avg Duration", f"{filtered_trips['trip_duration_minutes'].mean():.1f} min")
    col4.metric("\U0001F4CF Avg Distance", f"{filtered_trips['distance'].mean():.1f} km")
else:
    col1.metric("\U0001F4B0 Total Revenue", "\u00a30.00")
    col2.metric("\U0001F696 Total Trips", "0")
    col3.metric("\u23F1\uFE0F Avg Duration", "- min")
    col4.metric("\U0001F4CF Avg Distance", "- km")

# --- Charts Section ---
st.markdown("---")
st.subheader("\U0001F4C8 Analytics")

# Row 1: Monthly Revenue Trend (LINE) + Top 15 Zones by Revenue (BAR)
chart_col1, chart_col2 = st.columns(2)

# Monthly Revenue Trend — LINE chart (matches dashboard)
with chart_col1:
    st.markdown("**Monthly Revenue Trend**")
    if not filtered_trips.empty:
        # Aggregate to monthly level using filtered trips (responds to all filters)
        monthly_df = filtered_trips.copy()
        monthly_df["month_name"] = monthly_df["full_date"].dt.strftime("%B")
        monthly_df["month_num"] = monthly_df["full_date"].dt.month
        monthly_revenue = monthly_df.groupby(["month_num", "month_name"], as_index=False)["fare_amount"].sum()
        monthly_revenue = monthly_revenue.sort_values("month_num")
        fig = px.line(monthly_revenue, x="month_name", y="fare_amount",
                      labels={"month_name": "Month", "fare_amount": "Total Revenue (\u00a3)"},
                      markers=True)
        fig.update_layout(xaxis_title="Month", yaxis_title="Total Revenue")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for selected filters.")

# Top 15 Zones by Revenue — BAR chart (matches dashboard)
with chart_col2:
    st.markdown("**Top 15 Zones by Revenue**")
    if not filtered_trips.empty:
        # Derive zone revenue from filtered trips (responds to all filters)
        zone_rev = filtered_trips.merge(zones_df[["zone_key", "zone_code"]],
                                         left_on="pickup_zone_key", right_on="zone_key", how="left")
        top_zones = zone_rev.groupby("zone_code", as_index=False)["fare_amount"].sum()
        top_zones = top_zones.rename(columns={"fare_amount": "revenue"})
        top_zones = top_zones.nlargest(15, "revenue")
        fig = px.bar(top_zones.sort_values("revenue", ascending=True),
                     x="revenue", y="zone_code", orientation="h",
                     color="zone_code",
                     labels={"zone_code": "Pickup Zone", "revenue": "Revenue (\u00a3)"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for selected filters.")

# Row 2: Avg Wait Time by Day of Week (BAR) + Revenue by Payment Type & Zone (BAR)
chart_col3, chart_col4 = st.columns(2)

# Avg Trip Duration by Day of Week — BAR chart (matches dashboard's "Avg Wait Time by Day")
with chart_col3:
    st.markdown("**Avg Trip Duration by Day of Week**")
    if not filtered_trips.empty:
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_duration = filtered_trips.groupby("day_name", as_index=False)["trip_duration_minutes"].mean()
        day_duration = day_duration.rename(columns={"trip_duration_minutes": "avg_duration_min"})
        day_duration["day_name"] = pd.Categorical(day_duration["day_name"], categories=day_order, ordered=True)
        day_duration = day_duration.sort_values("day_name").dropna(subset=["day_name"])

        if len(day_duration) <= 1:
            if len(day_duration) == 1:
                day_val = day_duration.iloc[0]
                st.metric(
                    label=f"{day_val['day_name']}",
                    value=f"{day_val['avg_duration_min']:.1f} min"
                )
            else:
                st.info("No data for selected filters.")
            st.caption("\u2139\uFE0F Select multiple days to see the bar chart comparison.")
        else:
            fig = px.bar(day_duration, x="day_name", y="avg_duration_min",
                         color="day_name",
                         labels={"day_name": "Day of Week", "avg_duration_min": "Avg Duration (min)"})
            fig.update_layout(showlegend=False, xaxis_title="Day of Week", yaxis_title="Avg Duration (min)")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for selected filters.")

# Revenue by Payment Type & Zone — Stacked BAR chart (matches dashboard)
with chart_col4:
    st.markdown("**Revenue by Payment Type & Zone**")
    if not filtered_trips.empty:
        # Aggregate revenue by zone and payment type
        trip_rev = filtered_trips.merge(zones_df[["zone_key", "zone_code"]],
                                         left_on="pickup_zone_key", right_on="zone_key", how="left")
        rev_by_pay_zone = trip_rev.groupby(["zone_code", "payment_type"], as_index=False)["fare_amount"].sum()
        rev_by_pay_zone = rev_by_pay_zone.rename(columns={"fare_amount": "revenue"})
        # Limit to top 10 zones by total revenue for readability
        top_zone_list = rev_by_pay_zone.groupby("zone_code")["revenue"].sum().nlargest(10).index.tolist()
        rev_by_pay_zone = rev_by_pay_zone[rev_by_pay_zone["zone_code"].isin(top_zone_list)]
        if not rev_by_pay_zone.empty:
            fig = px.bar(rev_by_pay_zone, x="zone_code", y="revenue", color="payment_type",
                         barmode="stack",
                         labels={"zone_code": "Zone", "revenue": "Revenue (\u00a3)", "payment_type": "Payment Type"})
            fig.update_layout(xaxis_title="Zone", yaxis_title="Revenue (\u00a3)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for selected filters.")
    else:
        st.info("No data for selected filters.")

# --- Interactive Zone Revenue Map ---
st.markdown("---")
st.subheader("\U0001F5FA Zone Revenue Heatmap \u2014 City of Derry")

# Build zone-level revenue data from filtered zone_daily_agg
filtered_zone_map = filter_zone_agg(zone_daily_df)

if not filtered_zone_map.empty:
    zone_revenue_map = (
        filtered_zone_map
        .groupby("pickup_zone_key", as_index=False)["total_revenue"]
        .sum()
        .merge(zones_df, left_on="pickup_zone_key", right_on="zone_key", how="inner")
    )

    # Map controls
    map_col1, map_col2 = st.columns([1, 3])
    with map_col1:
        map_metric = st.radio(
            "Colour by",
            ["Total Revenue", "Revenue per Trip"],
            index=0,
            key="map_metric"
        )
        radius_val = st.slider("Heatmap radius", min_value=5, max_value=40, value=20, key="map_radius")
        opacity_val = st.slider("Opacity", min_value=0.2, max_value=1.0, value=0.7, step=0.1, key="map_opacity")

    # Compute trips per zone for per-trip metric
    if map_metric == "Revenue per Trip":
        zone_trips = (
            filtered_zone_map
            .groupby("pickup_zone_key", as_index=False)["total_trips"]
            .sum()
        )
        zone_revenue_map = zone_revenue_map.merge(zone_trips, on="pickup_zone_key", how="left")
        zone_revenue_map["revenue_per_trip"] = (
            zone_revenue_map["total_revenue"] / zone_revenue_map["total_trips"].replace(0, 1)
        )
        z_col = "revenue_per_trip"
        hover_label = "Revenue/Trip (\u00a3)"
    else:
        z_col = "total_revenue"
        hover_label = "Total Revenue (\u00a3)"

    with map_col2:
        fig_map = px.density_mapbox(
            zone_revenue_map,
            lat="latitude",
            lon="longitude",
            z=z_col,
            radius=radius_val,
            opacity=opacity_val,
            center={"lat": 55.006, "lon": -7.32},
            zoom=11.5,
            mapbox_style="open-street-map",
            color_continuous_scale="YlOrRd",
            hover_name="zone_code",
            hover_data={z_col: ":.2f", "latitude": False, "longitude": False},
            labels={z_col: hover_label},
        )
        fig_map.update_layout(
            height=600,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            coloraxis_colorbar=dict(title=hover_label),
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # Summary table beneath the map
    st.markdown("**Zone Revenue Summary (filtered)**")
    summary_df = (
        zone_revenue_map[["zone_code", "total_revenue"]]
        .rename(columns={"zone_code": "Zone", "total_revenue": "Revenue (\u00a3)"})
        .sort_values("Revenue (\u00a3)", ascending=False)
        .reset_index(drop=True)
    )
    summary_df["Revenue (\u00a3)"] = summary_df["Revenue (\u00a3)"].map(lambda x: f"{x:,.2f}")
    st.dataframe(summary_df, use_container_width=True, height=250)
else:
    st.info("No zone data for the selected filters.")

# --- Hourly Analysis Section (matches dashboard heatmap + line) ---
st.markdown("---")
st.subheader("\U0001F552 Hourly Trip Analysis")

# Filter hourly data by Day of Week, Hour of Day, and Date Range
filtered_hourly = hourly_df.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    filtered_hourly = filtered_hourly[
        (filtered_hourly["trip_date"].dt.date >= date_range[0]) &
        (filtered_hourly["trip_date"].dt.date <= date_range[1])
    ]
if selected_days:
    filtered_hourly = filtered_hourly[filtered_hourly["day_name"].isin(selected_days)]
if selected_hours:
    filtered_hourly = filtered_hourly[filtered_hourly["hour_of_day"].isin(selected_hours)]
if weather_date_keys is not None:
    hourly_with_keys = filtered_hourly.merge(dates_df[["full_date", "date_key"]], left_on="trip_date", right_on="full_date", how="inner")
    filtered_hourly = hourly_with_keys[hourly_with_keys["date_key"].isin(weather_date_keys)].drop(columns=["full_date", "date_key"])

# Trips per Hour by Day of Week — LINE chart (matches dashboard)
st.markdown("**Trips per Hour by Day of Week**")
if not filtered_hourly.empty:
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # Aggregate across dates: SUM trips per (hour, day) to match dashboard
    hourly_agg = filtered_hourly.groupby(["hour_of_day", "day_name"], as_index=False)["trip_count"].sum()
    hourly_agg["day_name"] = pd.Categorical(
        hourly_agg["day_name"], categories=day_order, ordered=True
    )
    fig = px.line(
        hourly_agg.sort_values(["day_name", "hour_of_day"]),
        x="hour_of_day", y="trip_count", color="day_name",
        labels={"hour_of_day": "Hour of Day", "trip_count": "Number of Trips", "day_name": "Day of Week"},
        markers=True,
        category_orders={"day_name": day_order}
    )
    fig.update_layout(xaxis_title="Hour of Day", yaxis_title="Number of Trips",
                      legend_title="Day of Week")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data for selected filters.")

# --- Heatmaps Section (from Taxi Analytics Dashboard) ---
st.markdown("---")
st.subheader("\U0001F525 Trip Heatmaps")

# Heatmaps use the same filtered_hourly from above (Date Range, Day of Week, Hour of Day all applied)

heat_col1, heat_col2 = st.columns(2)

day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Heatmap 1: Average Trips per Hour by Day of Week
with heat_col1:
    st.markdown("**Average Trips per Hour by Day of Week**")
    if not filtered_hourly.empty:
        avg_pivot = filtered_hourly.groupby(["day_name", "hour_of_day"], as_index=False)["trip_count"].mean()
        avg_matrix = avg_pivot.pivot(index="day_name", columns="hour_of_day", values="trip_count")
        # Reorder days
        available_days = [d for d in day_order if d in avg_matrix.index]
        avg_matrix = avg_matrix.reindex(available_days)
        fig = px.imshow(
            avg_matrix,
            labels=dict(x="Hour of Day", y="Day of Week", color="Number of Trips"),
            x=[str(h) for h in avg_matrix.columns],
            y=avg_matrix.index.tolist(),
            color_continuous_scale="YlOrRd",
            aspect="auto"
        )
        fig.update_layout(title="", xaxis_title="Hour of Day", yaxis_title="Day of Week")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for selected filters.")

# Heatmap 2: Total Trips per Hour by Day of Week
with heat_col2:
    st.markdown("**Trips per Month Hour by Day of Week**")
    if not filtered_hourly.empty:
        sum_pivot = filtered_hourly.groupby(["day_name", "hour_of_day"], as_index=False)["trip_count"].sum()
        sum_matrix = sum_pivot.pivot(index="day_name", columns="hour_of_day", values="trip_count")
        # Reorder days
        available_days = [d for d in day_order if d in sum_matrix.index]
        sum_matrix = sum_matrix.reindex(available_days)
        fig = px.imshow(
            sum_matrix,
            labels=dict(x="Hour of Day", y="Day of Week", color="Total Trips"),
            x=[str(h) for h in sum_matrix.columns],
            y=sum_matrix.index.tolist(),
            color_continuous_scale="YlOrRd",
            aspect="auto"
        )
        fig.update_layout(title="", xaxis_title="Hour of Day", yaxis_title="Day of Week")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for selected filters.")

# --- Weather Impact Section ---
st.markdown("---")
st.subheader("\U0001F326\uFE0F Weather Impact on Trips")

# Merge KPIs with weather data from dim_date
weather_kpi_df = kpis_df.merge(
    dates_df[["full_date", "avg_temp_c", "total_precip_mm", "avg_wind_speed_kmph",
              "avg_humidity", "weather_desc"]],
    on="full_date", how="inner"
).dropna(subset=["avg_temp_c"])

# Apply date range filter
if isinstance(date_range, tuple) and len(date_range) == 2:
    weather_kpi_df = weather_kpi_df[
        (weather_kpi_df["full_date"].dt.date >= date_range[0]) &
        (weather_kpi_df["full_date"].dt.date <= date_range[1])
    ]
if selected_days:
    weather_kpi_df = weather_kpi_df[weather_kpi_df["day_name"].isin(selected_days)]
if selected_weather:
    weather_kpi_df = weather_kpi_df[weather_kpi_df["weather_desc"].isin(selected_weather)]

# Row 1: Avg Trips by Weather Condition (BAR) + Weather x Day Heatmap
weather_row1_col1, weather_row1_col2 = st.columns(2)

# Chart 1: Avg Daily Trips by Weather Condition — horizontal BAR (matches "Avg Wait Time by Day")
with weather_row1_col1:
    st.markdown("**Avg Daily Trips by Weather Condition**")
    if not weather_kpi_df.empty:
        weather_trips = weather_kpi_df.groupby("weather_desc", as_index=False).agg(
            avg_trips=("total_trips", "mean"),
            count_days=("total_trips", "count")
        ).sort_values("avg_trips", ascending=True)
        weather_trips = weather_trips[weather_trips["count_days"] >= 3]
        if not weather_trips.empty:
            fig = px.bar(
                weather_trips, x="avg_trips", y="weather_desc", orientation="h",
                color="weather_desc",
                labels={"avg_trips": "Avg Trips per Day", "weather_desc": "Weather Condition"}
            )
            fig.update_layout(showlegend=False, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data points per weather condition.")
    else:
        st.info("No data for selected filters.")

# Chart 2: Trips by Day of Week & Weather Group — stacked BAR (matches "Revenue by Payment Type & Zone")
with weather_row1_col2:
    st.markdown("**Trips by Day of Week & Weather Group**")
    if not weather_kpi_df.empty:
        def weather_group_chart2(desc):
            desc_lower = str(desc).lower()
            if any(w in desc_lower for w in ["snow", "blizzard", "sleet", "ice"]):
                return "Snow/Ice"
            elif any(w in desc_lower for w in ["heavy rain", "moderate rain", "torrential"]):
                return "Heavy Rain"
            elif any(w in desc_lower for w in ["light rain", "drizzle", "patchy rain", "shower"]):
                return "Light Rain"
            elif any(w in desc_lower for w in ["fog", "mist", "overcast", "cloudy"]):
                return "Overcast/Fog"
            else:
                return "Dry/Clear"

        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_weather = weather_kpi_df.copy()
        day_weather["weather_group"] = day_weather["weather_desc"].apply(weather_group_chart2)
        day_weather_agg = day_weather.groupby(["day_name", "weather_group"], as_index=False)["total_trips"].sum()
        day_weather_agg["day_name"] = pd.Categorical(day_weather_agg["day_name"], categories=day_order, ordered=True)
        day_weather_agg = day_weather_agg.sort_values("day_name")

        group_order = ["Dry/Clear", "Overcast/Fog", "Light Rain", "Heavy Rain", "Snow/Ice"]
        fig = px.bar(
            day_weather_agg, x="day_name", y="total_trips", color="weather_group",
            barmode="stack",
            category_orders={"weather_group": group_order},
            labels={"day_name": "Day of Week", "total_trips": "Total Trips", "weather_group": "Weather Group"}
        )
        fig.update_layout(xaxis_title="Day of Week", yaxis_title="Total Trips")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for selected filters.")

# Row 2: Avg Revenue by Weather Group (BAR) + Avg Trip Duration by Weather (BAR)
weather_row2_col1, weather_row2_col2 = st.columns(2)

# Chart 3: Avg Daily Revenue by Weather Group — BAR (matches "Avg Wait Time by Day")
with weather_row2_col1:
    st.markdown("**Avg Daily Revenue by Weather Group**")
    if not weather_kpi_df.empty:
        def weather_group(desc):
            desc_lower = str(desc).lower()
            if any(w in desc_lower for w in ["snow", "blizzard", "sleet", "ice"]):
                return "Snow/Ice"
            elif any(w in desc_lower for w in ["heavy rain", "moderate rain", "torrential"]):
                return "Heavy Rain"
            elif any(w in desc_lower for w in ["light rain", "drizzle", "patchy rain", "shower"]):
                return "Light Rain"
            elif any(w in desc_lower for w in ["fog", "mist", "overcast", "cloudy"]):
                return "Overcast/Fog"
            else:
                return "Dry/Clear"

        grouped_weather = weather_kpi_df.copy()
        grouped_weather["weather_group"] = grouped_weather["weather_desc"].apply(weather_group)
        group_rev = grouped_weather.groupby("weather_group", as_index=False)["total_revenue"].mean()
        group_rev = group_rev.rename(columns={"total_revenue": "avg_daily_revenue"})

        group_order = ["Dry/Clear", "Overcast/Fog", "Light Rain", "Heavy Rain", "Snow/Ice"]
        group_rev["weather_group"] = pd.Categorical(group_rev["weather_group"], categories=group_order, ordered=True)
        group_rev = group_rev.sort_values("weather_group")

        fig = px.bar(
            group_rev, x="weather_group", y="avg_daily_revenue",
            color="weather_group",
            labels={"weather_group": "Weather Group", "avg_daily_revenue": "Avg Daily Revenue (\u00a3)"},
        )
        fig.update_layout(showlegend=False, xaxis_title="Weather Group", yaxis_title="Avg Daily Revenue (\u00a3)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for selected filters.")

# Chart 4: Avg Trip Duration by Weather Condition — BAR (matches "Avg Wait Time by Day")
with weather_row2_col2:
    st.markdown("**Avg Trip Duration by Weather Condition**")
    if not weather_kpi_df.empty:
        weather_duration = weather_kpi_df.groupby("weather_desc", as_index=False).agg(
            avg_duration=("avg_trip_duration_min", "mean"),
            count_days=("avg_trip_duration_min", "count")
        ).sort_values("avg_duration", ascending=True)
        weather_duration = weather_duration[weather_duration["count_days"] >= 3]
        if not weather_duration.empty:
            fig = px.bar(
                weather_duration, x="avg_duration", y="weather_desc", orientation="h",
                color="weather_desc",
                labels={"avg_duration": "Avg Duration (min)", "weather_desc": "Weather Condition"}
            )
            fig.update_layout(showlegend=False, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data points per weather condition.")
    else:
        st.info("No data for selected filters.")

# --- Data Table Section ---
st.markdown("---")
st.subheader("\U0001F4DD Filtered Trip Details")

if not filtered_trips.empty:
    display_df = filtered_trips.merge(zones_df[["zone_key", "zone_code"]],
                                       left_on="pickup_zone_key", right_on="zone_key", how="left")
    display_df = display_df[[
        "booking_id", "full_date", "day_name", "zone_code", "status",
        "payment_type", "fare_amount", "distance", "trip_duration_minutes",
        "booking_source", "priority_level"
    ]].rename(columns={"zone_code": "pickup_zone"})
    display_df = display_df.sort_values("full_date", ascending=False).head(500)
    st.dataframe(display_df, use_container_width=True, height=400)
    st.caption(f"Showing {len(display_df)} rows (limited to 500)")
else:
    st.info("No trip data for the selected filters.")
