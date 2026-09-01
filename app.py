import streamlit as st
import pandas as pd
import subprocess
import json
from pathlib import Path
import plotly.graph_objects as go


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Flight Fare Forecaster",
    page_icon="✈️",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent

SAMPLE_DATA = (
    BASE_DIR
    / "data"
    / "sample_flight_prices.csv"
)

R_SCRIPT = (
    BASE_DIR
    / "r_analysis"
    / "flight_forecast.R"
)

# Your confirmed Rscript location
R_SCRIPT_EXE = Path(
    r"C:\Program Files\R\R-4.6.1\bin\Rscript.exe"
)

# ============================================================
# BACKGROUND IMAGE
# ============================================================

BACKGROUND_IMAGE = BASE_DIR / "flight.JPG"

if BACKGROUND_IMAGE.exists():
    import base64

    with open(BACKGROUND_IMAGE, "rb") as image_file:
        encoded_image = base64.b64encode(
            image_file.read()
        ).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_image}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.78);
            z-index: -1;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.warning(
        f"Background image not found: {BACKGROUND_IMAGE}"
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def calculate_month_difference(start_date, end_date):
    """Calculate number of months between two dates."""

    return (
        (end_date.year - start_date.year) * 12
        + (end_date.month - start_date.month)
    )


def validate_r_environment():
    """Check that Rscript and the R analysis script exist."""

    if not R_SCRIPT_EXE.exists():
        st.error(
            "Rscript.exe was not found."
        )

        st.code(str(R_SCRIPT_EXE))

        st.info(
            "Please verify that this file exists on your computer."
        )

        return False

    if not R_SCRIPT.exists():
        st.error(
            "The R analysis script was not found."
        )

        st.code(str(R_SCRIPT))

        return False

    return True


def run_r_analysis(
    csv_file,
    origin,
    destination,
    forecast_horizon
):
    """Run the R time-series analysis and return JSON."""

    command = [
        str(R_SCRIPT_EXE),
        str(R_SCRIPT),
        str(csv_file),
        str(origin),
        str(destination),
        str(forecast_horizon)
    ]

    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR)
    )

    if process.returncode != 0:

        raise RuntimeError(
            "R analysis failed.\n\n"
            + process.stderr
        )

    if not process.stdout.strip():

        raise RuntimeError(
            "R completed but returned no output."
        )

    try:

        result = json.loads(
            process.stdout
        )

    except json.JSONDecodeError as e:

        raise RuntimeError(
            "R returned output that could not be "
            "converted to JSON.\n\n"
            f"R output:\n{process.stdout}\n\n"
            f"JSON error:\n{e}"
        )

    return result, command


# ============================================================
# HEADER
# ============================================================

st.title("✈️ Flight Fare Forecaster")

st.write(
    "Forecast future monthly flight fares using "
    "historical time-series patterns and ARIMA."
)

st.divider()


# ============================================================
# DATA SOURCE
# ============================================================

st.subheader("📂 Dataset")

data_source = st.radio(
    "Choose data source:",
    [
        "Use Sample Dataset",
        "Upload My Dataset"
    ],
    horizontal=True
)


# ============================================================
# LOAD DATA
# ============================================================

if data_source == "Use Sample Dataset":

    if not SAMPLE_DATA.exists():

        st.error(
            "Sample dataset not found."
        )

        st.code(
            str(SAMPLE_DATA)
        )

        st.stop()

    try:

        df = pd.read_csv(
            SAMPLE_DATA
        )

    except Exception as e:

        st.error(
            f"Unable to read sample dataset: {e}"
        )

        st.stop()

else:

    uploaded_file = st.file_uploader(
        "Upload your flight-price CSV",
        type=["csv"]
    )

    if uploaded_file is None:

        st.info(
            "Please upload a CSV file to continue."
        )

        st.stop()

    try:

        df = pd.read_csv(
            uploaded_file
        )

    except Exception as e:

        st.error(
            f"Unable to read uploaded CSV: {e}"
        )

        st.stop()


# ============================================================
# BASIC VALIDATION
# ============================================================

required_columns = [
    "Date",
    "Origin",
    "Destination",
    "Average_Price"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    st.error(
        "Missing required columns:"
    )

    st.write(
        ", ".join(missing_columns)
    )

    st.info(
        "Your CSV must contain these columns:"
    )

    st.code(
        "Date, Origin, Destination, Average_Price"
    )

    st.stop()


# ============================================================
# CLEAN DATA
# ============================================================

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

df["Average_Price"] = pd.to_numeric(
    df["Average_Price"],
    errors="coerce"
)

df["Origin"] = (
    df["Origin"]
    .astype(str)
    .str.strip()
)

df["Destination"] = (
    df["Destination"]
    .astype(str)
    .str.strip()
)

df = df.dropna(
    subset=[
        "Date",
        "Origin",
        "Destination",
        "Average_Price"
    ]
)

df = df[
    df["Average_Price"] > 0
]

df = df.sort_values(
    "Date"
)


if df.empty:

    st.error(
        "No valid data remains after cleaning."
    )

    st.stop()


# ============================================================
# DATASET INFORMATION
# ============================================================

st.subheader("📊 Dataset Preview")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Observations",
        len(df)
    )

with col2:

    number_routes = (
        df[
            ["Origin", "Destination"]
        ]
        .drop_duplicates()
        .shape[0]
    )

    st.metric(
        "Routes",
        number_routes
    )

with col3:

    st.metric(
        "Start Date",
        df["Date"]
        .min()
        .strftime("%b %Y")
    )

with col4:

    st.metric(
        "End Date",
        df["Date"]
        .max()
        .strftime("%b %Y")
    )

st.dataframe(
    df.head(10),
    use_container_width=True
)


# ============================================================
# ROUTE SELECTION
# ============================================================

st.divider()

st.subheader("✈️ Select Flight Route")

origins = sorted(
    df["Origin"]
    .dropna()
    .unique()
)

if len(origins) == 0:

    st.error(
        "No departure locations found."
    )

    st.stop()

origin = st.selectbox(
    "Departure",
    origins
)


destinations = sorted(
    df.loc[
        df["Origin"] == origin,
        "Destination"
    ]
    .dropna()
    .unique()
)

if len(destinations) == 0:

    st.error(
        "No destinations found for this departure."
    )

    st.stop()

destination = st.selectbox(
    "Destination",
    destinations
)


# ============================================================
# FILTER SELECTED ROUTE
# ============================================================

route_df = df[
    (df["Origin"] == origin)
    &
    (df["Destination"] == destination)
].copy()

route_df = route_df.sort_values(
    "Date"
)


if route_df.empty:

    st.error(
        "No data found for the selected route."
    )

    st.stop()


if len(route_df) < 24:

    st.warning(
        "This route contains fewer than "
        "24 observations. Forecast reliability "
        "may be limited."
    )


# ============================================================
# HISTORICAL DATA
# ============================================================

st.subheader(
    f"📈 Historical Fare: {origin} → {destination}"
)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=route_df["Date"],
        y=route_df["Average_Price"],
        mode="lines+markers",
        name="Historical Fare"
    )
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Average Fare (₹)",
    hovermode="x unified"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# FORECAST SETTINGS
# ============================================================

st.divider()

st.subheader("🔮 Forecast Settings")

latest_date = route_df["Date"].max()

latest_year = latest_date.year

available_years = sorted(
    route_df["Date"]
    .dt
    .year
    .unique()
)

# Historical years + next 2 years
year_options = sorted(
    set(
        list(available_years)
        + [
            latest_year + 1,
            latest_year + 2
        ]
    )
)

target_year = st.selectbox(
    "Forecast Year",
    year_options,
    index=len(year_options) - 1
)


month_names = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
]

target_month_name = st.selectbox(
    "Forecast Month",
    month_names
)

target_month = (
    month_names.index(
        target_month_name
    )
    + 1
)


# ============================================================
# TARGET DATE
# ============================================================

target_date = pd.Timestamp(
    year=target_year,
    month=target_month,
    day=1
)


# ============================================================
# CHECK WHETHER TARGET IS FUTURE
# ============================================================

if target_date <= latest_date:

    st.warning(
        f"{target_month_name} {target_year} "
        "is not a future month relative to "
        f"the latest available data "
        f"({latest_date.strftime('%B %Y')})."
    )

    st.info(
        "Please select a month after the latest "
        "historical observation."
    )

    valid_target = False

else:

    valid_target = True


# ============================================================
# FORECAST HORIZON
# ============================================================

if valid_target:

    forecast_horizon = calculate_month_difference(
        latest_date,
        target_date
    )

    st.info(
        f"Latest available data: "
        f"{latest_date.strftime('%B %Y')}\n\n"
        f"Target month: "
        f"{target_month_name} {target_year}\n\n"
        f"Forecast horizon: "
        f"{forecast_horizon} month(s)"
    )


# ============================================================
# RUN FORECAST BUTTON
# ============================================================

st.divider()

run_forecast = st.button(
    "🚀 Run Time Series Analysis",
    type="primary",
    use_container_width=True
)


# ============================================================
# RUN ANALYSIS
# ============================================================

if run_forecast:

    if not valid_target:

        st.error(
            "Please select a valid future month."
        )

        st.stop()


    # --------------------------------------------------------
    # Check R environment
    # --------------------------------------------------------

    if not validate_r_environment():

        st.stop()


    # --------------------------------------------------------
    # Prepare CSV
    # --------------------------------------------------------

    if data_source == "Use Sample Dataset":

        csv_for_r = SAMPLE_DATA

    else:

        uploaded_csv = (
            BASE_DIR
            / "outputs"
            / "uploaded_data.csv"
        )

        uploaded_csv.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        df.to_csv(
            uploaded_csv,
            index=False
        )

        csv_for_r = uploaded_csv


    # --------------------------------------------------------
    # Execute R
    # --------------------------------------------------------

    with st.spinner(
        "Running R time-series analysis..."
    ):

        try:

            result, command = run_r_analysis(
                csv_for_r,
                origin,
                destination,
                forecast_horizon
            )

        except Exception as e:

            st.error(
                "❌ R analysis failed."
            )

            with st.expander(
                "🔧 Technical Error Details"
            ):

                st.write(
                    "Rscript executable:"
                )

                st.code(
                    str(R_SCRIPT_EXE)
                )

                st.write(
                    "R analysis script:"
                )

                st.code(
                    str(R_SCRIPT)
                )

                st.write(
                    "CSV sent to R:"
                )

                st.code(
                    str(csv_for_r)
                )

                st.write(
                    "Command:"
                )

                st.code(
                    " ".join(
                        command
                    )
                    if "command" in locals()
                    else "Command could not be created."
                )

                st.write(
                    "Error:"
                )

                st.code(
                    str(e)
                )

            st.stop()


    # ========================================================
    # SUCCESS
    # ========================================================

    st.success(
        "✅ Time-series analysis completed successfully!"
    )


    # ========================================================
    # FORECAST VALUES
    # ========================================================

    forecast_values = [
        float(value)
        for value in result["forecast"]
    ]

    lower_values = [
        float(value)
        for value in result["lower_80"]
    ]

    upper_values = [
        float(value)
        for value in result["upper_80"]
    ]


    target_index = (
        forecast_horizon - 1
    )


    predicted_price = (
        forecast_values[target_index]
    )

    lower_price = (
        lower_values[target_index]
    )

    upper_price = (
        upper_values[target_index]
    )


    # ========================================================
    # FORECAST SUMMARY
    # ========================================================

    st.subheader(
        "📊 Forecast Summary"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Predicted Fare",
            f"₹{predicted_price:,.0f}"
        )

    with col2:

        st.metric(
            "Lower 80%",
            f"₹{lower_price:,.0f}"
        )

    with col3:

        st.metric(
            "Upper 80%",
            f"₹{upper_price:,.0f}"
        )


    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    st.subheader(
        "🤖 Time Series Model"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "ARIMA Model",
            f"ARIMA({result['arima_model']})"
        )

    with col2:

        st.metric(
            "ADF p-value",
            f"{float(result['adf_p_value']):.4f}"
        )

    with col3:

        if bool(result["stationary"]):

            st.metric(
                "Stationarity",
                "Stationary"
            )

        else:

            st.metric(
                "Stationarity",
                "Non-stationary"
            )


    # ========================================================
    # ADDITIONAL MODEL INFORMATION
    # ========================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Observations Used",
            result["observations"]
        )

    with col2:

        st.metric(
            "Historical Mean",
            f"₹{float(result['mean_price']):,.0f}"
        )

    with col3:

        st.metric(
            "AIC",
            f"{float(result['aic']):,.2f}"
        )


    # ========================================================
    # FORECAST TABLE
    # ========================================================

    st.subheader(
        "🔮 Forecasted Monthly Fares"
    )

    forecast_dates = pd.date_range(
        start=latest_date
        + pd.DateOffset(months=1),
        periods=forecast_horizon,
        freq="MS"
    )

    forecast_df = pd.DataFrame({

        "Date": forecast_dates,

        "Forecast": forecast_values,

        "Lower 80%": lower_values,

        "Upper 80%": upper_values

    })

    display_forecast = forecast_df.copy()

    display_forecast["Date"] = (
        display_forecast["Date"]
        .dt
        .strftime("%B %Y")
    )

    display_forecast["Forecast"] = (
        display_forecast["Forecast"]
        .map(lambda x: f"₹{x:,.0f}")
    )

    display_forecast["Lower 80%"] = (
        display_forecast["Lower 80%"]
        .map(lambda x: f"₹{x:,.0f}")
    )

    display_forecast["Upper 80%"] = (
        display_forecast["Upper 80%"]
        .map(lambda x: f"₹{x:,.0f}")
    )

    st.dataframe(
        display_forecast,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # HISTORICAL + FORECAST GRAPH
    # ========================================================

    st.subheader(
        "📈 Historical + Forecast"
    )

    forecast_fig = go.Figure()


    # Historical
    forecast_fig.add_trace(
        go.Scatter(
            x=route_df["Date"],
            y=route_df["Average_Price"],
            mode="lines+markers",
            name="Historical"
        )
    )


    # Forecast
    forecast_fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=forecast_values,
            mode="lines+markers",
            name="Forecast"
        )
    )


    # Upper interval
    forecast_fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=upper_values,
            mode="lines",
            line=dict(
                width=0
            ),
            showlegend=False
        )
    )


    # Lower interval
    forecast_fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=lower_values,
            mode="lines",
            fill="tonexty",
            line=dict(
                width=0
            ),
            name="80% Prediction Interval"
        )
    )


    forecast_fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Average Fare (₹)",
        hovermode="x unified"
    )


    st.plotly_chart(
        forecast_fig,
        use_container_width=True
    )


    # ========================================================
    # MOVING AVERAGE
    # ========================================================

    st.subheader(
        "📉 Moving Average"
    )

    ma_df = route_df.copy()

    ma_df["Moving_Average_3M"] = (
        ma_df["Average_Price"]
        .rolling(
            window=3
        )
        .mean()
    )

    ma_fig = go.Figure()

    ma_fig.add_trace(
        go.Scatter(
            x=ma_df["Date"],
            y=ma_df["Average_Price"],
            mode="lines",
            name="Actual Fare"
        )
    )

    ma_fig.add_trace(
        go.Scatter(
            x=ma_df["Date"],
            y=ma_df["Moving_Average_3M"],
            mode="lines",
            name="3-Month Moving Average"
        )
    )

    ma_fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Average Fare (₹)",
        hovermode="x unified"
    )

    st.plotly_chart(
        ma_fig,
        use_container_width=True
    )


    # ========================================================
    # AUTOMATIC INTERPRETATION
    # ========================================================

    st.subheader(
        "🧠 Automatic Interpretation"
    )

    historical_mean = (
        route_df["Average_Price"]
        .mean()
    )

    recent_values = (
        route_df["Average_Price"]
        .tail(6)
    )

    recent_mean = (
        recent_values.mean()
    )


    if recent_mean > historical_mean * 1.05:

        trend_text = "increasing"

    elif recent_mean < historical_mean * 0.95:

        trend_text = "decreasing"

    else:

        trend_text = "relatively stable"


    if predicted_price > historical_mean * 1.10:

        fare_level = "high"

    elif predicted_price < historical_mean * 0.90:

        fare_level = "low"

    else:

        fare_level = "moderate"


    st.write(
        f"""
        • The recent fare trend is **{trend_text}**.

        • Historical average fare:
        **₹{historical_mean:,.0f}**

        • Forecasted fare for
        **{target_month_name} {target_year}**:
        **₹{predicted_price:,.0f}**

        • Relative to the historical average,
        the forecast is classified as **{fare_level}**.

        • Selected model:
        **ARIMA({result['arima_model']})**

        • ADF p-value:
        **{float(result['adf_p_value']):.4f}**

        • 80% prediction interval:
        **₹{lower_price:,.0f} – ₹{upper_price:,.0f}**
        """
    )


    # ========================================================
    # TECHNICAL DETAILS
    # ========================================================

    with st.expander(
        "🔧 Technical Details"
    ):

        st.write(
            "Rscript executable:"
        )

        st.code(
            str(R_SCRIPT_EXE)
        )

        st.write(
            "R analysis script:"
        )

        st.code(
            str(R_SCRIPT)
        )

        st.write(
            "CSV:"
        )

        st.code(
            str(csv_for_r)
        )

        st.write(
            "Route:"
        )

        st.code(
            f"{origin} → {destination}"
        )

        st.write(
            "Forecast horizon:"
        )

        st.code(
            str(forecast_horizon)
        )