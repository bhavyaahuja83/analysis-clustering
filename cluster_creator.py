from time_analysis import analyze_time_slots
from itertools import combinations
from tqdm import tqdm

CLUSTER_FIELDS = [
    ('AgeGroup', 'AgeGroup'),
    ('Gender', 'Gender'),
    ('IncomeGroup', 'IncomeGroup'),
    ('ProfessionType', 'Profession'),
    ('CityId', 'City'),
    ('Brandname', 'Brand'),
]

MIN_CLUSTER_SIZE = 6000

def generate_clusters(df):
    if 'Age' in df.columns:
        df = df[(df['Age'] >= 18) & (df['Age'] <= 87)].copy()

    df = df.copy()
    df["assigned"] = False
    clusters = []

    available_fields = [(col, out) for col, out in CLUSTER_FIELDS if col in df.columns]
    if not available_fields:
        raise ValueError("No valid fields for clustering.")

    for level in range(len(available_fields), 0, -1):
        combos = list(combinations(available_fields, level))
        total_groups = 0
        for field_combo in combos:
            groupby_fields = [col for col, _ in field_combo]
            sub_df = df[~df["assigned"]].copy()
            grouped = sub_df.groupby(groupby_fields)
            total_groups += len(grouped)

        with tqdm(total=total_groups, desc=f"Clustering (level {level})", unit="group") as pbar:
            for field_combo in combos:
                groupby_fields = [col for col, _ in field_combo]
                output_keys = [out for _, out in field_combo]
                sub_df = df[~df["assigned"]].copy()
                grouped = sub_df.groupby(groupby_fields)
                for keys, group in grouped:
                    if len(group) >= MIN_CLUSTER_SIZE:
                        cluster = {}
                        for i, out_key in enumerate(['AgeGroup', 'IncomeGroup', 'Gender', 'Profession', 'City', 'Brand']):
                            source_col = next((col for col, out in CLUSTER_FIELDS if out == out_key), None)
                            if source_col in groupby_fields:
                                val = group[source_col].dropna().unique()
                                if out_key in ['AgeGroup', 'IncomeGroup']:
                                    if len(val) == 1:
                                        cluster[out_key] = str(val[0])
                                    else:
                                        continue  # skip cluster if multiple AgeGroup or IncomeGroup
                                else:
                                    cluster[out_key] = ", ".join(sorted(map(str, val))) if len(val) > 0 else 'any'
                            else:
                                cluster[out_key] = 'any'

                        cluster["LeadCount"] = len(group)
                        cluster["PickupPattern"] = analyze_time_slots(group)
                        clusters.append(cluster)
                        df.loc[group.index, "assigned"] = True
                    pbar.update(1)

        remaining = len(df[~df["assigned"]])
        print(f"✅ Clusters formed with {level} fields: {len(clusters)} | Unassigned rows: {remaining}")
        if remaining == 0:
            break

    leftover_df = df[~df["assigned"]]
    if not leftover_df.empty:
        cluster = {"MergedFrom": "Leftovers", "LeadCount": len(leftover_df)}
        for out_key in ['AgeGroup', 'IncomeGroup', 'Gender', 'Profession', 'City', 'Brand']:
            source_col = next((col for col, out in CLUSTER_FIELDS if out == out_key), None)
            if source_col in leftover_df.columns:
                vals = leftover_df[source_col].dropna().unique()
                if out_key in ['AgeGroup', 'IncomeGroup']:
                    cluster[out_key] = str(vals[0]) if len(vals) == 1 else 'any'
                else:
                    cluster[out_key] = ", ".join(sorted(map(str, vals))) if len(vals) > 0 else 'any'
            else:
                cluster[out_key] = 'any'
        cluster["PickupPattern"] = analyze_time_slots(leftover_df)
        clusters.append(cluster)

    return clusters
