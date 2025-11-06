"""
Inter-Annotator Agreement Visualization
=======================================
This script compares continuous trait measurements between
multiple human annotators and computes agreement metrics:
- RMSE
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

# Input file (replace with your dataset)
DATA_PATH = "data/traits.csv"                       # anonymized path
OUTPUT_FIG = "InterAnnotatorAgreement.pdf"          # output figure name


# Define inter-annotator pairs (anonymized)
ANNOTATOR_PAIRS = [
    ('AnnotatorA_length', 'AnnotatorB_length', 'Annotator A vs Annotator B', 'Annotator A', 'Annotator B'),
    ('AnnotatorB_length', 'AnnotatorC_length', 'Annotator B vs Annotator C', 'Annotator B', 'Annotator C'),
    ('AnnotatorC_length', 'AnnotatorA_length', 'Annotator C vs Annotator A', 'Annotator C', 'Annotator A')
]

# Axis limits for plotting
LIM_MIN, LIM_MAX = 0.15, 0.65


# ---------------------------------------------------------
# === Load Data ===
# ---------------------------------------------------------
df = pd.read_csv(DATA_PATH)

# Optional: check columns
required_cols = [x[0] for x in ANNOTATOR_PAIRS] + [x[1] for x in ANNOTATOR_PAIRS]
missing = [col for col in required_cols if col not in df.columns]
if missing:
    raise ValueError(f"Missing columns in input CSV: {missing}")


# ---------------------------------------------------------
# === Create Plots ===
# ---------------------------------------------------------
plt.style.use('seaborn-v0_8-whitegrid')
fig, axes = plt.subplots(1, 3, figsize=(24, 6))

results = []

for ax, (x_col, y_col, title, x_label, y_label) in zip(axes, ANNOTATOR_PAIRS):
    df_sub = df[[x_col, y_col]].dropna()
    x = df_sub[x_col].values
    y = df_sub[y_col].values

    # --- Compute metrics ---
    rmse = np.sqrt(mean_squared_error(y, x))
    r2 = r2_score(y, x)
    bias = np.mean(x - y)
    results.append((title, rmse, r2, bias))

    # --- Plot scatter ---
    ax.scatter(x, y, color='steelblue', s=60, edgecolor='black', linewidth=0.3)

    # Perfect agreement line
    ax.plot([LIM_MIN, LIM_MAX], [LIM_MIN, LIM_MAX],
            linestyle='--', color='orange', linewidth=2, label='Perfect agreement')

    # Formatting
    ax.set_xlabel(x_label, fontsize=22, labelpad=12, fontweight='bold')
    ax.set_ylabel(y_label, fontsize=22, labelpad=12, fontweight='bold')
    ax.set_title(title, fontsize=24, fontweight='bold', pad=12)
    ax.set_xlim(LIM_MIN, LIM_MAX)
    ax.set_ylim(LIM_MIN, LIM_MAX)
    ax.tick_params(axis='both', labelsize=18)

# Adjust layout
plt.subplots_adjust(wspace=0.3, right=0.88)
axes[0].legend(loc='upper left', fontsize=18, frameon=True)

# Save output
os.makedirs("figures", exist_ok=True)
output_path = os.path.join("figures", OUTPUT_FIG)
plt.savefig(output_path, format='pdf', bbox_inches='tight', dpi=600)
plt.show()



# ---------------------------------------------------------
# === Display Summary ===
# ---------------------------------------------------------
print(f"✅ Inter-Annotator Agreement figure saved at: {output_path}\n")

print("📊 === Inter-Annotator Agreement Metrics ===")
for title, rmse, r2, bias in results:
    print(f"{title}:")
    print(f"   RMSE       = {rmse:.4f}")
    print(f"   R² Score   = {r2:.4f}")
    print(f"   Avg. Bias  = {bias:.4f}\n")

# Overall averages
avg_rmse = np.mean([r[1] for r in results])
avg_r2   = np.mean([r[2] for r in results])
avg_bias = np.mean([r[3] for r in results])

print("📈 === Average Across All Annotator Pairs ===")
print(f"   RMSE (mean)  = {avg_rmse:.4f}")
print(f"   R² (mean)    = {avg_r2:.4f}")
print(f"   Bias (mean)  = {avg_bias:.4f}")
