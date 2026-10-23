from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "reference" / "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
OUTPUT_PATH = ROOT / "task4-attendance" / "docs" / "HEADCOUNT_RECONSTRUCTED_BACKTEST.csv"

TRAIN_MONTHS = 36
FORECAST_HORIZON = 6
SEASONAL_STRENGTH = 0.5


def forecast_values(history, future_dates):
    """Reconstructed linear trend with half-strength monthly seasonality."""
    history = history.dropna().astype(float).reset_index(drop=True)

    if len(history) < TRAIN_MONTHS:
        return np.full(len(future_dates), np.nan)

    y = history.iloc[-TRAIN_MONTHS:].to_numpy()
    x = np.arange(TRAIN_MONTHS, dtype=float)

    slope, intercept = np.polyfit(x, y, 1)
    fitted = intercept + slope * x
    residuals = y - fitted

    # Estimate month-of-year seasonality from detrended residuals.
    months = np.arange(len(y)) % 12
    seasonal = np.zeros(12, dtype=float)

    for month in range(12):
        values = residuals[months == month]
        seasonal[month] = values.mean() if len(values) else 0.0

    # Center seasonal adjustments to avoid shifting the overall trend.
    seasonal -= seasonal.mean()

    future_x = np.arange(TRAIN_MONTHS, TRAIN_MONTHS + len(future_dates))
    predictions = intercept + slope * future_x

    for i, date in enumerate(future_dates):
        predictions[i] += SEASONAL_STRENGTH * seasonal[date.month - 1]

    return np.maximum(predictions, 0)


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Workbook not found: {DATA_PATH}")

    df = pd.read_excel(
        DATA_PATH,
        sheet_name="fact_headcount_monthly",
    )

    df["month_start_date"] = pd.to_datetime(df["month_start_date"])
    df = df.sort_values(["department_id", "month_start_date"])

    results = []

    for department, group in df.groupby("department_id"):
        group = group.sort_values("month_start_date").reset_index(drop=True)

        # Six-month-ahead rolling-origin forecasts.
        for origin in range(TRAIN_MONTHS, len(group) - FORECAST_HORIZON + 1):
            history = group.loc[: origin - 1, "headcount_end"]
            future = group.loc[
                origin : origin + FORECAST_HORIZON - 1,
                "month_start_date",
            ].tolist()

            actual = group.loc[
                origin : origin + FORECAST_HORIZON - 1,
                "headcount_end",
            ].to_numpy(dtype=float)

            predicted = forecast_values(history, future)

            for date, actual_value, forecast_value in zip(
                future, actual, predicted
            ):
                absolute_error = abs(actual_value - forecast_value)
                percentage_error = (
                    absolute_error / abs(actual_value) * 100
                    if actual_value != 0
                    else np.nan
                )

                results.append(
                    {
                        "department_id": department,
                        "forecast_month": date,
                        "actual_headcount": actual_value,
                        "reconstructed_forecast": round(float(forecast_value), 4),
                        "absolute_error": round(float(absolute_error), 4),
                        "absolute_percentage_error": (
                            round(float(percentage_error), 4)
                            if pd.notna(percentage_error)
                            else np.nan
                        ),
                        "training_months": TRAIN_MONTHS,
                        "forecast_horizon_months": FORECAST_HORIZON,
                        "seasonal_strength": SEASONAL_STRENGTH,
                        "model_status": "RECONSTRUCTED_NOT_OFFICIAL",
                    }
                )

    output = pd.DataFrame(results)
    if output.empty:
        raise ValueError("No backtest rows generated. Check historical data coverage.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False)

    valid = output["absolute_percentage_error"].dropna()

    print("RECONSTRUCTED HEADCOUNT BACKTEST")
    print("--------------------------------")
    print(f"Rows evaluated: {len(output)}")
    print(f"Departments: {output['department_id'].nunique()}")
    print(f"Period: {output['forecast_month'].min():%Y-%m} to "
          f"{output['forecast_month'].max():%Y-%m}")
    print(f"MAE (employees): {output['absolute_error'].mean():.4f}")
    print(f"MAPE (%): {valid.mean():.4f}" if not valid.empty else "MAPE: N/A")
    print(f"Results saved to: {OUTPUT_PATH}")
    print("WARNING: This is a reconstructed approximation, not official model accuracy.")


if __name__ == "__main__":
    main()