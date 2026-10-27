from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

# Set file and directory paths based on the current script location
BASE_DIR = Path(__file__).resolve().parent.parent.parent  
DATA_PATH = BASE_DIR / "data" / "interim" / "ercot_merge.csv"
OUTPUT_DIR = BASE_DIR / "report" / "graph"

# Automatically create the output directory if it does not exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def plot_ercot_trend():
    # Load the dataset
    df = pd.read_csv(DATA_PATH)

    # Parse the date/time column into datetime objects and sort chronologically
    df["Hour Ending"] = pd.to_datetime(df["Hour Ending"])
    df = df.sort_values("Hour Ending")

    # Generate the visualization plot
    plt.figure(figsize=(14, 6))

    # Check if 'ERCOT' total column exists; if not, calculate the sum of regional columns
    if "ERCOT" in df.columns:
        plt.plot(
            df["Hour Ending"],
            df["ERCOT"],
            label="ERCOT Total",
            color="#1f77b4",
            linewidth=1.2,
        )
    else:
        # Exclude metadata columns and sum up the remaining load columns
        exclude_cols = {"Hour Ending", "hour", "day", "dayofweek", "month", "year"}
        region_cols = [col for col in df.columns if col not in exclude_cols]
        df["ERCOT_Total"] = df[region_cols].sum(axis=1)
        
        plt.plot(
            df["Hour Ending"],
            df["ERCOT_Total"],
            label="ERCOT Total (Calculated)",
            color="#1f77b4",
            linewidth=1.2,
        )

    plt.title("ERCOT Electricity Load Over Time", fontsize=14, pad=12)
    plt.xlabel("Date / Time", fontsize=11)
    plt.ylabel("Demand (MW)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper right")
    plt.tight_layout()

    # Save the plot as an image file
    save_path = OUTPUT_DIR / "ercot_trend.png"
    plt.savefig(save_path, dpi=300)
    plt.close()

    print(f"Plot successfully saved to: {save_path}")


if __name__ == "__main__":
    plot_ercot_trend()