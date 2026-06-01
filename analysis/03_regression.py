"""
Phase 7 — Regression Analysis
Builds sales volume prediction models: OLS multiple regression + Random Forest.
Evaluates both and saves the RF model for the prediction API.

Output:
  - analysis/ols_summary.txt
  - backend/models/rf_model.pkl, label_encoder.pkl
  - analysis/charts/10–11_*.png
"""

import pandas as pd
import numpy as np
import joblib
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import statsmodels.api as sm

# ---- Language toggle ----
LANG = "en"
T = {
    "zh": {"feat_imp": "特征重要性", "actual_pred": "实际销量 vs 预测销量"},
    "en": {"feat_imp": "Feature Importance", "actual_pred": "Actual vs Predicted Sales"},
}[LANG]

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = pd.read_csv("data/cleaned/cleaned_data.csv").dropna(
    subset=["price", "sales_volume", "review_count", "rating", "is_promoted", "category"]
)
print(f"Records for regression: {len(df)}")

# ---------------------------------------------------------------------------
# Encode category
# ---------------------------------------------------------------------------
le = LabelEncoder()
df["category_enc"] = le.fit_transform(df["category"])
print(f"Category encoding: {dict(zip(le.classes_, le.transform(le.classes_)))}")

# ---------------------------------------------------------------------------
# Feature set
# ---------------------------------------------------------------------------
features = ["price", "rating", "review_count", "is_promoted", "category_enc"]
X = df[features]
y = df["sales_volume"]

print(f"\nFeatures: {features}")
print(f"Target: sales_volume")

# ---------------------------------------------------------------------------
# OLS Regression (statsmodels)
# ---------------------------------------------------------------------------
X_ols = sm.add_constant(X)
model_ols = sm.OLS(y, X_ols).fit()
print(f"\n{'=' * 60}")
print("OLS Regression Summary")
print(f"{'=' * 60}")
print(model_ols.summary())

os.makedirs("analysis", exist_ok=True)
with open("analysis/ols_summary.txt", "w", encoding="utf-8") as f:
    f.write(str(model_ols.summary()))
print("\nSaved: analysis/ols_summary.txt")

# ---------------------------------------------------------------------------
# Random Forest Regression
# ---------------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print(f"\n{'=' * 60}")
print("Random Forest — Test Set Performance")
print(f"{'=' * 60}")
print(f"  MAE:  {mae:.2f}")
print(f"  RMSE: {rmse:.2f}")
print(f"  R²:   {r2:.4f}")

# OLS R² for comparison
ols_r2 = model_ols.rsquared
print(f"\n  OLS R² (full data):  {ols_r2:.4f}")
print(f"  RF R² (test set):    {r2:.4f}")
print(f"  Improvement:         +{r2 - ols_r2:.4f}")

# ---------------------------------------------------------------------------
# Save model and encoder
# ---------------------------------------------------------------------------
os.makedirs("backend/models", exist_ok=True)
joblib.dump(rf, "backend/models/rf_model.pkl")
joblib.dump(le, "backend/models/label_encoder.pkl")
print("\nSaved: backend/models/rf_model.pkl, label_encoder.pkl")

# ---------------------------------------------------------------------------
# Chart 10: Feature importance
# ---------------------------------------------------------------------------
charts_dir = "analysis/charts"
os.makedirs(charts_dir, exist_ok=True)

fig, ax = plt.subplots(figsize=(8, 5))
importance = pd.Series(rf.feature_importances_, index=features)
# Map to readable names
name_map = {
    "price": "Price", "rating": "Rating", "review_count": "Review Count",
    "is_promoted": "Is Promoted", "category_enc": "Category",
}
importance.index = [name_map.get(f, f) for f in features]
importance.sort_values().plot(kind="barh", ax=ax, color="steelblue", edgecolor="white")
ax.set_title(T["feat_imp"], fontsize=14, fontweight="bold")
ax.set_xlabel("Importance")
plt.tight_layout()
plt.savefig(f"{charts_dir}/10_feature_importance.png", dpi=150)
plt.close()
print("  Chart 10: Feature importance")

# ---------------------------------------------------------------------------
# Chart 11: Actual vs Predicted
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 7))
ax.scatter(y_test, y_pred, alpha=0.25, s=8, color="steelblue", edgecolors="none")
lims = [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())]
ax.plot(lims, lims, "r--", linewidth=1.5, alpha=0.7, label="Perfect prediction")
ax.set_xlabel("Actual Sales")
ax.set_ylabel("Predicted Sales")
ax.set_title(T["actual_pred"], fontsize=14, fontweight="bold")
ax.text(0.05, 0.95, f"R² = {r2:.3f}\nMAE = {mae:.0f}\nRMSE = {rmse:.0f}",
        transform=ax.transAxes, fontsize=10, va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig(f"{charts_dir}/11_actual_vs_predicted.png", dpi=150)
plt.close()
print("  Chart 11: Actual vs predicted")

# ---------------------------------------------------------------------------
# Interpret results
# ---------------------------------------------------------------------------
print(f"\n{'=' * 60}")
print("Regression Analysis — Key Interpretations")
print(f"{'=' * 60}")

# Which features matter most
print(f"\n  Feature importance (Random Forest):")
for feat, imp in importance.sort_values(ascending=False).items():
    pct = imp * 100
    bar = "█" * int(pct / 2)
    print(f"    {feat:20s}: {pct:5.1f}% {bar}")

# OLS p-values
print(f"\n  OLS p-values (significance):")
for feat in ["const"] + features:
    pval = model_ols.pvalues[feat]
    sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "(ns)"
    print(f"    {feat:20s}: p = {pval:.4f} {sig}")

print(f"\n  Charts saved to {charts_dir}/")
