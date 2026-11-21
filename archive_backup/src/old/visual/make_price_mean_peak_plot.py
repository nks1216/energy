from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def main():
    # Project root: energy/
    root_dir = Path(__file__).resolve().parents[2]

    input_path = root_dir / "data" / "interim" / "price_merge.csv"
    output_dir = root_dir / "report" / "graph"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    df = pd.read_csv(input_path)

    df["delivery_date"] = pd.to_datetime(
        df["delivery_date"], errors="raise"
    )
    df["price_rt_hubavg"] = pd.to_numeric(
        df["price_rt_hubavg"], errors="raise"
    )

    if df.empty or df[["delivery_date", "price_rt_hubavg"]].isna().any().any():
        raise ValueError(
            "Input data is empty or contains missing dates or prices."
        )

    # 2. Calculate daily mean and peak prices
    daily = (
        df.groupby("delivery_date")["price_rt_hubavg"]
        .agg(mean_price="mean", peak_price="max")
        .sort_index()
    )

    # Leave gaps in the plotted lines for missing dates
    daily = daily.asfreq("D")

    # 3. Create plots
    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(14, 8),
        sharex=True,
        constrained_layout=True,
    )

    plot_settings = [
        ("mean_price", "Daily Mean Price", "tab:blue"),
        ("peak_price", "Daily Peak Price", "tab:orange"),
    ]

    for ax, (column, title, color) in zip(axes, plot_settings):
        ax.plot(
            daily.index,
            daily[column],
            color=color,
            linewidth=0.8,
        )
        ax.set_title(title)
        ax.set_ylabel("Price ($/MWh)")
        ax.grid(True, alpha=0.3)
        ax.margins(x=0)

    locator = mdates.AutoDateLocator()
    axes[-1].xaxis.set_major_locator(locator)
    axes[-1].xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(locator)
    )
    axes[-1].set_xlabel("Delivery Date")

    fig.suptitle("ERCOT Real-Time Hub Average Price", fontsize=15)

    # 4. Save as PNG
    output_path = output_dir / "price_daily_mean_peak.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()