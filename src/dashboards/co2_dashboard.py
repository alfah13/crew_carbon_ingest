# src/dashboards/co2_dashboard.py
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL")


@st.cache_data
def load_co2_data(plant_id=None, start_date=None, end_date=None):
    """Load CO2 calculation data"""
    engine = create_engine(DATABASE_URL)

    query = """
        SELECT 
            plant_id,
            date,
            ca_upstream_mg_per_l,
            ca_downstream_mg_per_l,
            ca_delta_mg_per_l,
            flow_mgd,
            co2_removed_metric_tons_per_day,
            quality_flag
        FROM crew_carbon_co2_removal_calculations
        WHERE 1=1
    """

    params = {}
    if plant_id:
        query += " AND plant_id = %(plant_id)s"
        params["plant_id"] = plant_id
    if start_date:
        query += " AND date >= %(start_date)s"
        params["start_date"] = start_date
    if end_date:
        query += " AND date <= %(end_date)s"
        params["end_date"] = end_date

    query += " ORDER BY date"

    df = pd.read_sql(query, engine, params=params)
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data
def load_calcium_readings(plant_id=None, start_date=None, end_date=None):
    """Load raw calcium readings"""
    engine = create_engine(DATABASE_URL)

    query = """
        SELECT 
            plant_id,
            plant_unit_id,
            datetime,
            parameter_name,
            value,
            unit
        FROM crew_carbon_lab_readings
        WHERE parameter_name = 'calcium'
    """

    params = {}
    if plant_id:
        query += " AND plant_id = %(plant_id)s"
        params["plant_id"] = plant_id
    if start_date:
        query += " AND datetime >= %(start_date)s"
        params["start_date"] = start_date
    if end_date:
        query += " AND datetime <= %(end_date)s"
        params["end_date"] = end_date

    query += " ORDER BY datetime"

    df = pd.read_sql(query, engine, params=params)
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df


# Dashboard
st.set_page_config(page_title="CO2 Removal Dashboard", layout="wide")

st.title("🌍 CO2 Removal Dashboard")
st.markdown("Monitor Ca levels and CO2 removal in wastewater plants")

# Sidebar filters
st.sidebar.header("Filters")

# Get available plants
engine = create_engine(DATABASE_URL)
plants_df = pd.read_sql(
    "SELECT DISTINCT plant_id FROM crew_carbon_co2_removal_calculations "
    "ORDER BY plant_id",
    engine,
)
plant_options = ["All"] + plants_df["plant_id"].tolist()

selected_plant = st.sidebar.selectbox("Select Plant", plant_options)
plant_filter = None if selected_plant == "All" else selected_plant

# Date range
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=date(2025, 4, 1))
with col2:
    end_date = st.date_input("End Date", value=date(2025, 6, 30))

# Load data
co2_df = load_co2_data(plant_filter, start_date, end_date)
ca_df = load_calcium_readings(plant_filter, start_date, end_date)

# KPIs
st.header("📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_co2 = co2_df["co2_removed_metric_tons_per_day"].sum()
    st.metric("Total CO2 Removed", f"{total_co2:.2f} MT")

with col2:
    avg_co2 = co2_df["co2_removed_metric_tons_per_day"].mean()
    st.metric("Avg Daily CO2", f"{avg_co2:.4f} MT/day")

with col3:
    avg_ca_delta = co2_df["ca_delta_mg_per_l"].mean()
    st.metric("Avg Ca Delta", f"{avg_ca_delta:.2f} mg/L")

with col4:
    total_days = len(co2_df)
    st.metric("Days Monitored", total_days)

# CO2 Removal Over Time
st.header("📈 CO2 Removal Over Time")
fig_co2 = px.line(
    co2_df,
    x="date",
    y="co2_removed_metric_tons_per_day",
    color="plant_id" if selected_plant == "All" else None,
    title="Daily CO2 Removal",
    labels={
        "co2_removed_metric_tons_per_day": "CO2 Removed (MT/day)",
        "date": "Date"},
)
fig_co2.update_layout(height=400)
st.plotly_chart(fig_co2, use_container_width=True)

# Calcium Levels
st.header("🧪 Calcium Levels Over Time")

col1, col2 = st.columns(2)

with col1:
    # Upstream vs Downstream
    fig_ca_calc = go.Figure()

    if selected_plant == "All":
        for plant in co2_df["plant_id"].unique():
            plant_data = co2_df[co2_df["plant_id"] == plant]
            fig_ca_calc.add_trace(
                go.Scatter(
                    x=plant_data["date"],
                    y=plant_data["ca_upstream_mg_per_l"],
                    name=f"{plant} Upstream",
                    mode="lines",
                )
            )
            fig_ca_calc.add_trace(
                go.Scatter(
                    x=plant_data["date"],
                    y=plant_data["ca_downstream_mg_per_l"],
                    name=f"{plant} Downstream",
                    mode="lines",
                    line=dict(dash="dash"),
                )
            )
    else:
        fig_ca_calc.add_trace(
            go.Scatter(
                x=co2_df["date"],
                y=co2_df["ca_upstream_mg_per_l"],
                name="Upstream",
                mode="lines",
            )
        )
        fig_ca_calc.add_trace(
            go.Scatter(
                x=co2_df["date"],
                y=co2_df["ca_downstream_mg_per_l"],
                name="Downstream",
                mode="lines",
                line=dict(dash="dash"),
            )
        )

    fig_ca_calc.update_layout(
        title="Calcium: Upstream vs Downstream",
        xaxis_title="Date",
        yaxis_title="Calcium (mg/L)",
        height=400,
    )
    st.plotly_chart(fig_ca_calc, use_container_width=True)

with col2:
    # Calcium Delta
    fig_ca_delta = px.bar(
        co2_df,
        x="date",
        y="ca_delta_mg_per_l",
        color="plant_id" if selected_plant == "All" else None,
        title="Calcium Delta (Downstream - Upstream)",
        labels={"ca_delta_mg_per_l": "Ca Delta (mg/L)", "date": "Date"},
    )
    fig_ca_delta.update_layout(height=400)
    st.plotly_chart(fig_ca_delta, use_container_width=True)

# Flow Rate
st.header("💧 Flow Rate Over Time")
fig_flow = px.line(
    co2_df,
    x="date",
    y="flow_mgd",
    color="plant_id" if selected_plant == "All" else None,
    title="Wastewater Flow Rate",
    labels={"flow_mgd": "Flow Rate (MGD)", "date": "Date"},
)
fig_flow.update_layout(height=400)
st.plotly_chart(fig_flow, use_container_width=True)

# Data Table
st.header("📋 Raw Data")
st.dataframe(
    co2_df[
        [
            "date",
            "plant_id",
            "ca_upstream_mg_per_l",
            "ca_downstream_mg_per_l",
            "ca_delta_mg_per_l",
            "flow_mgd",
            "co2_removed_metric_tons_per_day",
        ]
    ],
    use_container_width=True,
)

# Download button
csv = co2_df.to_csv(index=False)
st.download_button(
    label="📥 Download Data as CSV",
    data=csv,
    file_name=f"co2_removal_{start_date}_{end_date}.csv",
    mime="text/csv",
)
