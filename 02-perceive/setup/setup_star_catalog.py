"""One-time setup: the star catalog the Astronomer queries — a REAL BigQuery table.

The astronomer can't classify a biome from the sky alone; it extracts star features from
the image, then looks them up here (via the Google-MANAGED BigQuery MCP — no SQL driver,
no server of ours).

Run:   uv run python setup/setup_star_catalog.py
"""
import os

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
DATASET = "multimodal_levels"
TABLE = "star_catalog"

# The controlled vocabulary — extraction is enum-constrained to exactly these values,
# so the SQL lookup can be an exact match. (Vector search is the WRONG tool here: you
# want THE row, not something similar to it.)
ROWS = [
    # CRYO · NW — sharp cold stars, pale-blue aurora
    {"star_color": "blue_white", "sky_condition": "pale_blue_aurora", "quadrant": "NW", "biome": "CRYO"},
    {"star_color": "blue_white", "sky_condition": "crystal_clear",    "quadrant": "NW", "biome": "CRYO"},
    {"star_color": "cyan",       "sky_condition": "pale_blue_aurora", "quadrant": "NW", "biome": "CRYO"},
    # VOLCANIC · NE — stars dimmed by ash, orange horizon glow
    {"star_color": "red_orange", "sky_condition": "ash_dimmed",       "quadrant": "NE", "biome": "VOLCANIC"},
    {"star_color": "deep_red",   "sky_condition": "ash_dimmed",       "quadrant": "NE", "biome": "VOLCANIC"},
    {"star_color": "red_orange", "sky_condition": "orange_glow",      "quadrant": "NE", "biome": "VOLCANIC"},
    # VERDANT · SW — warm stars through canopy, green airglow
    {"star_color": "warm_yellow", "sky_condition": "green_airglow",   "quadrant": "SW", "biome": "VERDANT"},
    {"star_color": "warm_yellow", "sky_condition": "humid_haze",      "quadrant": "SW", "biome": "VERDANT"},
    {"star_color": "golden",      "sky_condition": "green_airglow",   "quadrant": "SW", "biome": "VERDANT"},
    # ARID · SE — brilliant dense field, bone-dry clear sky
    {"star_color": "white",  "sky_condition": "crystal_clear_dense",  "quadrant": "SE", "biome": "ARID"},
    {"star_color": "white",  "sky_condition": "no_haze",              "quadrant": "SE", "biome": "ARID"},
    {"star_color": "silver", "sky_condition": "crystal_clear_dense",  "quadrant": "SE", "biome": "ARID"},
]

SCHEMA = [
    bigquery.SchemaField("star_color", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("sky_condition", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("quadrant", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("biome", "STRING", mode="REQUIRED"),
]


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)

    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET}")
    dataset_ref.location = "US"
    client.create_dataset(dataset_ref, exists_ok=True)
    print(f"  ✓ dataset {PROJECT_ID}.{DATASET}")

    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    client.delete_table(table_id, not_found_ok=True)  # idempotent re-seed
    client.create_table(bigquery.Table(table_id, schema=SCHEMA))
    errors = client.insert_rows_json(table_id, ROWS)
    if errors:
        raise SystemExit(f"  ✗ insert failed: {errors}")
    print(f"  ✓ table {table_id} seeded with {len(ROWS)} rows")

    for row in client.query(
        f"SELECT biome, quadrant, COUNT(*) n FROM `{table_id}` GROUP BY biome, quadrant ORDER BY biome"
    ).result():
        print(f"    {row.biome:<9} {row.quadrant}  ×{row.n}")


if __name__ == "__main__":
    main()
