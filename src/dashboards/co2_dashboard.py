# src/dashboards/co2_dashboard.py
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL")


@st.cache_data
def get_table_stats():
    """Get row counts for all tables"""
    engine = create_engine(DATABASE_URL)
    
    stats = {}
    tables = {
        "CO2 Calculations": "crewcarbon_co2_removal_calculation",
        "Lab Readings": "crewcarbon_lab_reading",
        "Plant Metadata": "wastewater_plant_metadata",
        "Plant Operations": "wastewater_plant_operation"
    }
    
    with engine.connect() as conn:
        for display_name, table_name in tables.items():
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                stats[display_name] = count
            except Exception as e:
                stats[display_name] = f"Error: {e}"
    
    return stats


@st.cache_data
def load_co2_data(plant_id=None, start_date=None, end_date=None, quality_flags=None):
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
        FROM crewcarbon_co2_removal_calculation
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
    if quality_flags:
        placeholders = ", ".join([f"%(flag_{i})s" for i in range(len(quality_flags))])
        query += f" AND quality_flag IN ({placeholders})"
        for i, flag in enumerate(quality_flags):
            params[f"flag_{i}"] = flag

    query += " ORDER BY date"

    df = pd.read_sql(query, engine, params=params)
    if not df.empty:
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
        FROM crewcarbon_lab_reading
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
    if not df.empty:
        df["datetime"] = pd.to_datetime(df["datetime"])
    return df


# Dashboard
st.set_page_config(page_title="CO2 Removal Dashboard", layout="wide")

st.title("CO2 Removal Dashboard")
st.markdown("Monitor Ca levels and CO2 removal in wastewater plants")

# Sidebar filters
st.sidebar.header("Filters")

# Database Stats
st.sidebar.header("Database Statistics")
table_stats = get_table_stats()
for table_name, count in table_stats.items():
    st.sidebar.metric(table_name, count)

st.sidebar.markdown("---")

# Get available plants
engine = create_engine(DATABASE_URL)
try:
    plants_df = pd.read_sql(
        "SELECT DISTINCT plant_id FROM crewcarbon_co2_removal_calculation ORDER BY plant_id",
        engine,
    )
    plant_options = ["All"] + plants_df["plant_id"].tolist()
except Exception as e:
    st.error(f"Error loading plants: {e}")
    plant_options = ["All"]

selected_plant = st.sidebar.selectbox("Select Plant", plant_options)
plant_filter = None if selected_plant == "All" else selected_plant

# Date range
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=date(2025, 4, 1))
with col2:
    end_date = st.date_input("End Date", value=date(2025, 6, 30))

# Quality flag filter
st.sidebar.header("Data Quality")
show_valid = st.sidebar.checkbox("Show VALID", value=True)
show_invalid = st.sidebar.checkbox("Show INVALID", value=True)

# Determine which quality flags to include
quality_flags = []
if show_valid:
    quality_flags.append("VALID")
if show_invalid:
    quality_flags.append("INVALID")

# Load data
if quality_flags:
    co2_df = load_co2_data(plant_filter, start_date, end_date, quality_flags)
else:
    co2_df = pd.DataFrame()

ca_df = load_calcium_readings(plant_filter, start_date, end_date)

# Show data quality breakdown
if not co2_df.empty:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtered Data Quality")
    quality_counts = co2_df["quality_flag"].value_counts()
    for flag, count in quality_counts.items():
        st.sidebar.metric(f"{flag} records", count)

# KPIs
st.header("Key Metrics")

if not co2_df.empty:
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
    st.header("CO2 Removal Over Time")
    
    color_col = None
    if show_valid and show_invalid:
        color_col = "quality_flag"
    elif selected_plant == "All":
        color_col = "plant_id"
    
    fig_co2 = px.line(
        co2_df,
        x="date",
        y="co2_removed_metric_tons_per_day",
        color=color_col,
        title="Daily CO2 Removal",
        labels={
            "co2_removed_metric_tons_per_day": "CO2 Removed (MT/day)",
            "date": "Date",
            "quality_flag": "Quality"
        },
    )
    fig_co2.update_layout(height=400)
    st.plotly_chart(fig_co2, use_container_width=True)

    # Calcium Levels
    st.header("Calcium Levels Over Time")

    # Upstream vs Downstream - Full Width
    fig_ca_calc = go.Figure()

    if selected_plant == "All":
        for plant in co2_df["plant_id"].unique():
            plant_data = co2_df[co2_df["plant_id"] == plant]
            
            if show_valid and show_invalid:
                for flag in plant_data["quality_flag"].unique():
                    flag_data = plant_data[plant_data["quality_flag"] == flag]
                    line_style = "solid" if flag == "VALID" else "dot"
                    
                    fig_ca_calc.add_trace(
                        go.Scatter(
                            x=flag_data["date"],
                            y=flag_data["ca_upstream_mg_per_l"],
                            name=f"{plant} Upstream ({flag})",
                            mode="lines",
                            line=dict(dash=line_style),
                        )
                    )
                    fig_ca_calc.add_trace(
                        go.Scatter(
                            x=flag_data["date"],
                            y=flag_data["ca_downstream_mg_per_l"],
                            name=f"{plant} Downstream ({flag})",
                            mode="lines",
                            line=dict(dash="dash" if line_style == "solid" else "dashdot"),
                        )
                    )
            else:
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
        if show_valid and show_invalid:
            for flag in co2_df["quality_flag"].unique():
                flag_data = co2_df[co2_df["quality_flag"] == flag]
                line_style = "solid" if flag == "VALID" else "dot"
                
                fig_ca_calc.add_trace(
                    go.Scatter(
                        x=flag_data["date"],
                        y=flag_data["ca_upstream_mg_per_l"],
                        name=f"Upstream ({flag})",
                        mode="lines",
                        line=dict(dash=line_style),
                    )
                )
                fig_ca_calc.add_trace(
                    go.Scatter(
                        x=flag_data["date"],
                        y=flag_data["ca_downstream_mg_per_l"],
                        name=f"Downstream ({flag})",
                        mode="lines",
                        line=dict(dash="dash" if line_style == "solid" else "dashdot"),
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

    # Calcium Delta - Full Width
    color_col_delta = None
    if show_valid and show_invalid:
        color_col_delta = "quality_flag"
    elif selected_plant == "All":
        color_col_delta = "plant_id"
    
    fig_ca_delta = px.bar(
        co2_df,
        x="date",
        y="ca_delta_mg_per_l",
        color=color_col_delta,
        title="Calcium Delta (Downstream - Upstream)",
        labels={
            "ca_delta_mg_per_l": "Ca Delta (mg/L)",
            "date": "Date",
            "quality_flag": "Quality"
        },
    )
    fig_ca_delta.update_layout(height=400)
    st.plotly_chart(fig_ca_delta, use_container_width=True)

    # Flow Rate
    st.header("Flow Rate Over Time")
    
    color_col_flow = None
    if show_valid and show_invalid:
        color_col_flow = "quality_flag"
    elif selected_plant == "All":
        color_col_flow = "plant_id"
    
    fig_flow = px.line(
        co2_df,
        x="date",
        y="flow_mgd",
        color=color_col_flow,
        title="Wastewater Flow Rate",
        labels={
            "flow_mgd": "Flow Rate (MGD)",
            "date": "Date",
            "quality_flag": "Quality"
        },
    )
    fig_flow.update_layout(height=400)
    st.plotly_chart(fig_flow, use_container_width=True)

    # Data Table
    st.header("Raw Data")
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
                "quality_flag",
            ]
        ],
        use_container_width=True,
    )

    # Download button
    csv = co2_df.to_csv(index=False)
    st.download_button(
        label="Download Data as CSV",
        data=csv,
        file_name=f"co2_removal_{start_date}_{end_date}.csv",
        mime="text/csv",
    )
else:
    st.warning("No data available for selected filters")
