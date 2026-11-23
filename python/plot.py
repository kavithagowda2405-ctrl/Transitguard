import os
import pandas as pd
import matplotlib.pyplot as plt

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(DOCS, exist_ok=True)

for name in ["normal", "door", "ajar", "failure", "freeze"]:
    df = pd.read_csv(os.path.join(DATA, f"log_{name}_0.csv"))
    t = (df["epoch"] - df["epoch"].iloc[0]) / 60
    plt.figure(figsize=(9, 4))
    plt.plot(t, df["t_air"], label="Air", alpha=0.6)
    plt.plot(t, df["t_pay"], label="Payload (true)")
    plt.plot(t, df["t_est"], "--", label="Estimate")
    plt.axhline(2, color="gray", ls=":")
    plt.axhline(8, color="gray", ls=":")
    plt.xlabel("Time (min)")
    plt.ylabel("Temperature (°C)")
    plt.title(name)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS, f"plot_{name}.png"), dpi=150)
    plt.close()
print("Plots saved in docs/")