from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def main():
    # Project root: energy/
    root_dir = Path(__file__).resolve().parents[2]

    input_path = root_dir / "data" / "interim" / "texas_merge.csv"
    output_dir = root_dir / "report" / "graph"
    output_dir.mkdir(parents=True, exist_ok=True)

    temp_column = "HourlyDryBulbTemperature"

    # 1. Load data
    df = pd.read_csv(input_path)

    df["DATE"] = pd.to_datetime(df["DATE"], errors="raise")
    df[temp_column] = pd.to_numeric(
        df[temp_column], errors="raise"
    )

    if df.empty or df["DATE"].isna().any():
        raise ValueError("Input data is empty or contains missing dates.")

    if df[temp_column].notna().sum() == 0:
        raise ValueError("No valid temperature observations were found.")

    if df["DATE"].duplicated().any():
        raise ValueError("Duplicate timestamps were found.")

    # 2. Calculate daily mean, maximum, and minimum temperatures
    daily = (
        df.set_index("DATE")[temp_column]
        .sort_index()
        .resample("D")
        .agg(
            mean_temp="mean",
            max_temp="max",
            min_temp="min",
            n_observations="count",
        )
    )

    # Check daily observation counts
    print("\nDaily valid temperature observation counts:")
    print(daily["n_observations"].value_counts().sort_index())

    print("\nDates with fewer than 20 valid observations:")
    print(daily.loc[daily["n_observations"] < 20, ["n_observations"]])

    # Mask daily statistics with fewer than 20 valid observations
    temp_columns = ["mean_temp", "max_temp", "min_temp"]
    daily.loc[daily["n_observations"] < 20, temp_columns] = float("nan")

    # Report missing observations without filling them
    missing_count = df[temp_column].isna().sum()
    if missing_count:
        print(
            f"Warning: {missing_count} missing temperature observations. "
            "Daily statistics use available observations."
        )

    # 3. Create plots
    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(14, 8),
        sharex=True,
        sharey=True,
        constrained_layout=True,
    )

    axes[0].plot(
        daily.index,
        daily["mean_temp"],
        color="tab:blue",
        linewidth=0.8,
        label="Daily Mean Temperature",
    )
    axes[0].set_title("Daily Mean Temperature")

    axes[1].plot(
        daily.index,
        daily["max_temp"],
        color="tab:red",
        linewidth=0.8,
        label="Daily Maximum Temperature",
    )
    axes[1].plot(
        daily.index,
        daily["min_temp"],
        color="tab:blue",
        linewidth=0.8,
        label="Daily Minimum Temperature",
    )
    axes[1].set_title("Daily Maximum and Minimum Temperatures")

    for ax in axes:
        ax.set_ylabel("Temperature (°C)")
        ax.axhline(
            0,
            color="gray",
            linestyle="--",
            linewidth=0.7,
        )
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper left")
        ax.margins(x=0)

    locator = mdates.AutoDateLocator()
    axes[-1].xaxis.set_major_locator(locator)
    axes[-1].xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(locator)
    )
    axes[-1].set_xlabel("Date")

    fig.suptitle(
        "Texas Four-City Weighted Average Temperature",
        fontsize=15,
    )

    # 4. Save as PNG
    output_path = output_dir / "temp_daily_mean_peak.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()