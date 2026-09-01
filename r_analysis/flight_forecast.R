# ============================================================
# FLIGHT FARE FORECASTING ENGINE
# R TIME SERIES ANALYSIS
# ============================================================

library(forecast)
library(tseries)
library(zoo)
library(jsonlite)

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 4) {
  stop(
    "Usage: Rscript flight_forecast.R ",
    "<csv> <origin> <destination> <horizon>"
  )
}

csv_file <- args[1]
origin <- args[2]
destination <- args[3]
horizon <- as.numeric(args[4])

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------

data <- read.csv(csv_file, stringsAsFactors = FALSE)

data$Date <- as.Date(data$Date)

# ------------------------------------------------------------
# FILTER ROUTE
# ------------------------------------------------------------

route_data <- data[
  data$Origin == origin &
    data$Destination == destination,
]

if (nrow(route_data) < 24) {
  stop("Not enough historical observations for this route.")
}

route_data <- route_data[
  order(route_data$Date),
]

# ------------------------------------------------------------
# CREATE TIME SERIES
# ------------------------------------------------------------

start_year <- as.numeric(format(
  min(route_data$Date),
  "%Y"
))

start_month <- as.numeric(format(
  min(route_data$Date),
  "%m"
))

price_ts <- ts(
  route_data$Average_Price,
  start = c(start_year, start_month),
  frequency = 12
)

# ------------------------------------------------------------
# DECOMPOSITION
# ------------------------------------------------------------

decomp <- stl(
  price_ts,
  s.window = "periodic"
)

# ------------------------------------------------------------
# ADF STATIONARITY TEST
# ------------------------------------------------------------

adf_result <- adf.test(price_ts)

# ------------------------------------------------------------
# ARIMA MODEL
# ------------------------------------------------------------

model <- auto.arima(
  price_ts,
  seasonal = TRUE
)

# ------------------------------------------------------------
# FORECAST
# ------------------------------------------------------------

forecast_result <- forecast(
  model,
  h = horizon
)

# ------------------------------------------------------------
# RESULTS
# ------------------------------------------------------------

forecast_values <- as.numeric(
  forecast_result$mean
)

lower_values <- as.numeric(
  forecast_result$lower[, 2]
)

upper_values <- as.numeric(
  forecast_result$upper[, 2]
)

# ------------------------------------------------------------
# OUTPUT
# ------------------------------------------------------------

result <- list(
  
  origin = origin,
  
  destination = destination,
  
  observations = length(price_ts),
  
  mean_price = mean(price_ts),
  
  minimum_price = min(price_ts),
  
  maximum_price = max(price_ts),
  
  adf_statistic = as.numeric(
    adf_result$statistic
  ),
  
  adf_p_value = as.numeric(
    adf_result$p.value
  ),
  
  stationary = (
    adf_result$p.value < 0.05
  ),
  
  arima_model = paste(
    model$arma[1],
    model$arma[6],
    model$arma[2],
    sep = ","
  ),
  
  aic = AIC(model),
  
  forecast = forecast_values,
  
  lower_80 = lower_values,
  
  upper_80 = upper_values
)

cat(
  toJSON(
    result,
    auto_unbox = TRUE,
    pretty = TRUE
  )
)