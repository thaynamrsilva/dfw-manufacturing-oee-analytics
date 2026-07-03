"""
generate_dataset.py

Generates a synthetic production dataset for Meridian Precision Manufacturing,
a fictional manufacturing facility located in the Dallas-Fort Worth (DFW)
industrial corridor, Texas.

The dataset simulates 12 months of daily production records across multiple
production lines and shifts, including downtime events and their causes,
following realistic manufacturing business rules (OEE methodology:
Availability x Performance x Quality).

Author: Thayná Menezes
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Reproducibility: same "random" data every time the script runs
np.random.seed(42)

# ---------------------------------------------------------------------------
# 1. CONFIGURATION — business rules and reference values
# ---------------------------------------------------------------------------

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 12, 31)

PRODUCTION_LINES = [
    {"line_id": "L1", "line_name": "Line 1 - CNC Machining", "ideal_cycle_time_sec": 45, "cost_per_downtime_hour": 850},
    {"line_id": "L2", "line_name": "Line 2 - Precision Assembly", "ideal_cycle_time_sec": 30, "cost_per_downtime_hour": 620},
    {"line_id": "L3", "line_name": "Line 3 - Surface Treatment", "ideal_cycle_time_sec": 60, "cost_per_downtime_hour": 710},
    {"line_id": "L4", "line_name": "Line 4 - Final Inspection & Packaging", "ideal_cycle_time_sec": 20, "cost_per_downtime_hour": 480},
]

SHIFTS = [
    {"shift_id": "S1", "shift_name": "Morning", "planned_minutes": 480},   # 8h
    {"shift_id": "S2", "shift_name": "Afternoon", "planned_minutes": 480}, # 8h
    {"shift_id": "S3", "shift_name": "Night", "planned_minutes": 480},     # 8h
]

# Downtime reasons with realistic relative likelihood and typical severity (minutes)
DOWNTIME_REASONS = [
    {"category": "Equipment Failure", "subcategory": "Mechanical Breakdown", "weight": 0.22, "avg_minutes": 85, "std_minutes": 35},
    {"category": "Equipment Failure", "subcategory": "Electrical Fault", "weight": 0.10, "avg_minutes": 65, "std_minutes": 25},
    {"category": "Changeover", "subcategory": "Product Setup / Changeover", "weight": 0.20, "avg_minutes": 45, "std_minutes": 15},
    {"category": "Material Issue", "subcategory": "Material Shortage", "weight": 0.14, "avg_minutes": 55, "std_minutes": 20},
    {"category": "Material Issue", "subcategory": "Material Quality Reject", "weight": 0.08, "avg_minutes": 30, "std_minutes": 10},
    {"category": "Planned Maintenance", "subcategory": "Scheduled Preventive Maintenance", "weight": 0.10, "avg_minutes": 90, "std_minutes": 20},
    {"category": "Unplanned Maintenance", "subcategory": "Unscheduled Repair", "weight": 0.10, "avg_minutes": 75, "std_minutes": 30},
    {"category": "Operator", "subcategory": "Operator Availability / Training", "weight": 0.06, "avg_minutes": 25, "std_minutes": 10},
]

# Night shift and Mondays have a higher probability of downtime (realistic pattern:
# fatigue on night shift, restart issues after the weekend)
SHIFT_DOWNTIME_MULTIPLIER = {"S1": 1.0, "S2": 1.1, "S3": 1.45}

# Probability that a given line/shift/day has at least one downtime event
BASE_DOWNTIME_PROBABILITY = 0.72

# Some lines are less reliable than others (older equipment, more complex process).
# Line 3 (Surface Treatment) is intentionally the least reliable line — this creates
# a realistic "problem line" for the analysis to surface.
LINE_DOWNTIME_MULTIPLIER = {"L1": 0.90, "L2": 0.85, "L3": 1.35, "L4": 0.95}

# Quality: baseline defect rate, with some lines being less consistent than others
LINE_BASE_DEFECT_RATE = {"L1": 0.015, "L2": 0.010, "L3": 0.022, "L4": 0.008}


# ---------------------------------------------------------------------------
# 2. GENERATION LOGIC
# ---------------------------------------------------------------------------

def daterange(start, end):
    days = (end - start).days + 1
    for i in range(days):
        yield start + timedelta(days=i)


def pick_downtime_reason():
    weights = [r["weight"] for r in DOWNTIME_REASONS]
    idx = np.random.choice(len(DOWNTIME_REASONS), p=weights)
    return DOWNTIME_REASONS[idx]


def generate_records():
    records = []

    for current_date in daterange(START_DATE, END_DATE):
        is_monday = current_date.weekday() == 0
        is_weekend = current_date.weekday() >= 5

        for line in PRODUCTION_LINES:
            for shift in SHIFTS:

                # Weekend night/afternoon shifts run at reduced or no capacity
                # for some lines (realistic: not all lines run 7 days a week)
                if is_weekend and line["line_id"] in ("L3", "L4") and shift["shift_id"] == "S3":
                    continue  # line not operating this shift

                planned_minutes = shift["planned_minutes"]

                # --- Downtime simulation ---
                downtime_minutes = 0
                reason_category = "No Downtime"
                reason_subcategory = "No Downtime"

                prob = (
                    BASE_DOWNTIME_PROBABILITY
                    * SHIFT_DOWNTIME_MULTIPLIER[shift["shift_id"]]
                    * LINE_DOWNTIME_MULTIPLIER[line["line_id"]]
                )
                if is_monday:
                    prob *= 1.15
                prob = min(prob, 0.95)

                if np.random.random() < prob:
                    reason = pick_downtime_reason()
                    reason_category = reason["category"]
                    reason_subcategory = reason["subcategory"]
                    downtime_minutes = max(
                        5,
                        np.random.normal(reason["avg_minutes"], reason["std_minutes"])
                    )
                    downtime_minutes = round(min(downtime_minutes, planned_minutes * 0.6), 1)

                run_time_minutes = planned_minutes - downtime_minutes

                # --- Performance simulation ---
                ideal_cycle_time_min = line["ideal_cycle_time_sec"] / 60
                # Small random efficiency variation around 90% of theoretical max output
                efficiency_factor = np.clip(np.random.normal(0.90, 0.06), 0.55, 1.0)
                theoretical_max_units = run_time_minutes / ideal_cycle_time_min if ideal_cycle_time_min > 0 else 0
                units_produced = int(theoretical_max_units * efficiency_factor)

                # --- Quality simulation ---
                base_defect_rate = LINE_BASE_DEFECT_RATE[line["line_id"]]
                # Defect rate increases slightly after high-downtime shifts (restart quality issues)
                defect_rate = base_defect_rate * (1 + (downtime_minutes / planned_minutes))
                defective_units = int(units_produced * np.clip(np.random.normal(defect_rate, defect_rate * 0.3), 0, 1))
                good_units = max(units_produced - defective_units, 0)

                units_planned = int(planned_minutes / ideal_cycle_time_min) if ideal_cycle_time_min > 0 else 0

                downtime_cost = round((downtime_minutes / 60) * line["cost_per_downtime_hour"], 2)

                records.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "line_id": line["line_id"],
                    "line_name": line["line_name"],
                    "shift_id": shift["shift_id"],
                    "shift_name": shift["shift_name"],
                    "planned_minutes": planned_minutes,
                    "downtime_minutes": downtime_minutes,
                    "run_time_minutes": round(run_time_minutes, 1),
                    "downtime_reason_category": reason_category,
                    "downtime_reason_subcategory": reason_subcategory,
                    "downtime_cost_usd": downtime_cost,
                    "ideal_cycle_time_sec": line["ideal_cycle_time_sec"],
                    "units_planned": units_planned,
                    "units_produced": units_produced,
                    "units_good": good_units,
                    "units_defective": units_produced - good_units,
                })

    return pd.DataFrame(records)


if __name__ == "__main__":
    print("Generating synthetic production dataset for Meridian Precision Manufacturing...")
    df = generate_records()

    output_path = "fact_production.csv"
    df.to_csv(output_path, index=False)

    print(f"Done. {len(df):,} records generated.")
    print(f"Saved to: {output_path}")
    print("\nPreview:")
    print(df.head(10).to_string(index=False))

    # Quick sanity check: overall OEE
    total_planned = df["planned_minutes"].sum()
    total_runtime = df["run_time_minutes"].sum()
    total_units = df["units_produced"].sum()
    total_good = df["units_good"].sum()

    availability = total_runtime / total_planned
    quality = total_good / total_units if total_units > 0 else 0

    print(f"\nSanity check — Overall Availability: {availability:.1%}")
    print(f"Sanity check — Overall Quality: {quality:.1%}")