# Data Dictionary — fact_production.csv

| Column                      | Type    | Description                                                            |
|-----------------------------|---------|------------------------------------------------------------------------|
| date                        | Date    | Production date                                                        |
| line_id                     | Text    | Production line identifier (L1-L4)                                     |
| line_name                   | Text    | Production line name and process type                                  |
| shift_id                    | Text    | Shift identifier (S1-S3)                                               |
| shift_name                  | Text    | Shift name (Morning / Afternoon / Night)                               |
| planned_minutes             | Number  | Scheduled production time for the shift, in minutes                    |
| downtime_minutes            | Number  | Minutes lost to downtime during the shift                              |
| run_time_minutes            | Number  | Actual production time (planned - downtime)                            |
| downtime_reason_category    | Text    | High-level downtime cause category                                     |
| downtime_reason_subcategory | Text    | Specific downtime cause                                                |
| downtime_cost_usd           | Number  | Estimated cost of downtime for that shift, in USD                      |
| ideal_cycle_time_sec        | Number  | Theoretical time to produce one unit on this line, in seconds          |
| units_planned               | Number  | Theoretical maximum units for the shift at full capacity               |
| units_produced              | Number  | Actual units produced during the shift                                 |
| units_good                  | Number  | Units produced without defects                                         |
| units_defective             | Number  | Units produced with defects                                            |

## Data Source

This dataset is synthetically generated (see `scripts/generate_dataset.py`)
to simulate 12 months of realistic manufacturing operations data, since real
production data is confidential. Downtime patterns follow realistic
manufacturing business rules (higher risk on night shifts and Mondays,
line-specific reliability differences).