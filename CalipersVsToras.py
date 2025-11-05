"""
Human vs Automated Measurement Agreement
========================================
This script compares human annotator measurements against
an automated tool (e.g., algorithmic or instrument-based)
for continuous trait estimation.

Metrics computed:
- RMSE (Root Mean Square Error)
- R² Score
- Average Bias

"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score


# ---------------------------------------------------------
# === Configuration ===
# ---------------------------------------------------------

# Input CSV path (anonymized)
DATA_PATH = "data/traits.csv"

# Output file
OUTPUT_FIG = "CalipersVsToras.pdf"

# Annotator-to-system pairs (anonymized)
ANNOTATOR_PAIRS = [
    ('AnnotatorA_length', 'System_length', 'Annotator A vs Automated System', 'Annotator A'),
    ('AnnotatorB_length', 'System_length', 'Annotator B vs Automated System', 'Annotator B'),
    ('AnnotatorC_length', 'System_length', 'Annotator C vs Automated System', 'Annotator C')
]

# Axis limits for consistent visual comparison
LIM_MIN, LIM_MAX = 0.15, 0.65


# ---------------------------------------------------------
# === Load Data ===
# ---------------------------------------------------------
df = pd.read_csv(DATA_PATH)

# Check expected columns
required_cols = [x[0] for x in ANNOTATOR_PAIRS] + ['System_length']
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")


# ---------------------------------------------------------
# === Helper Function: Compute Metrics ===
# ---------------------------------------------------------
def compute_agreement_metrics(x, y):
    """Compute RMSE, R², and bias between two numeric arrays."""
    rmse = np.sqrt(mean_squared_error(y, x))
    r2 = r2_score(y, x)
    bias = np.mean(x - y)
    return rmse, r2, bias


# ---------------------------------------------------------
# === Plot Comparison: Human vs System ===
# ---------------------------------------------------------
plt.style.use('seaborn-v0_8-whitegrid')
fig, axes = plt.subplots(1, 3, figsize=(24, 6))

metrics_summary = []

for ax, (human_col, sys_col, title, human_label) in zip(axes, ANNOTATOR_PAIRS):
    df_sub = df[[human_col, sys_col]].dropna()
    x = df_sub[human_col].values
    y = df_sub[sys_col].values

    # Compute metrics
    rmse, r2, bias = compute_agreement_metrics(x, y)
    metrics_summary.append((title, rmse, r2, bias))

    # Scatter plot
    ax.scatter(x, y, color='steelblue', s=60, edgecolor='black', linewidth=0.3)

    # Perfect agreement line
    ax.plot([LIM_MIN, LIM_MAX], [LIM_MIN, LIM_MAX],
            linestyle='--', color='orange', linewidth=2, label='Perfect agreement')

    # Formatting
    ax.set_xlabel(human_label, fontsize=22, labelpad=12, fontweight='bold')
    ax.set_ylabel("Automated System", fontsize=22, fontweight='bold', labelpad=12)
    ax.set_title(title, fontsize=24, fontweight='bold', pad=12)
    ax.set_xlim(LIM_MIN, LIM_MAX)
    ax.set_ylim(LIM_MIN, LIM_MAX)
    ax.tick_params(axis='both', labelsize=18)

# Layout
plt.subplots_adjust(wspace=0.3, right=0.88)
axes[0].legend(loc='upper left', fontsize=18, frameon=True)


# ---------------------------------------------------------
# === Average of Human Annotators vs System ===
# ---------------------------------------------------------
human_cols = [pair[0] for pair in ANNOTATOR_PAIRS]
df["HumanAvg_length"] = df[human_cols].mean(axis=1)
df_sub = df[["HumanAvg_length", "System_length"]].dropna()

x_avg = df_sub["HumanAvg_length"].values
y_sys = df_sub["System_length"].values

rmse_avg, r2_avg, bias_avg = compute_agreement_metrics(x_avg, y_sys)
metrics_summary.append(("Average Human vs Automated System", rmse_avg, r2_avg, bias_avg))


# ---------------------------------------------------------
# === Save & Display Results ===
# ---------------------------------------------------------
os.makedirs("figures", exist_ok=True)
output_path = os.path.join("figures", OUTPUT_FIG)
plt.savefig(output_path, format='pdf', bbox_inches='tight', dpi=600)
plt.show()

print(f"✅ Final plot saved at: {output_path}\n")

print("📊 === Human vs Automated System Metrics ===")
for title, rmse, r2, bias in metrics_summary:
    print(f"{title}:")
    print(f"   RMSE       = {rmse:.4f}")
    print(f"   R² Score   = {r2:.4f}")
    print(f"   Avg. Bias  = {bias:.4f}\n")
