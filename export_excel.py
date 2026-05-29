import pandas as pd

def export_to_excel(clusters, filename="output_clusters.xlsx"):
    rows = []

    for idx, cluster in enumerate(clusters, start=1):
        cluster_base = {
            'ClusterIndex': idx,
            'AgeGroup': cluster.get('AgeGroup', ''),
            'Gender': cluster.get('Gender', ''),
            'IncomeGroup': cluster.get('IncomeGroup', ''),
            'Profession': cluster.get('Profession', ''),
            'City': cluster.get('City', ''),
            'Brand': cluster.get('Brand', ''),
            'LeadCount': cluster.get('LeadCount', 0),
        }

        pattern = cluster.get("PickupPattern", [])

        if not pattern:
            row = cluster_base.copy()
            row.update({
                'Day': '',
                'Time': '',
                'PickupRate': '',
                'AvgDuration': '',
                'BestTime': False
            })
            rows.append(row)
        else:
            for p in pattern:
                row = cluster_base.copy()
                row.update({
                    'Day': p.get('Day', ''),
                    'Time': p.get('Time', ''),
                    'PickupRate': p.get('PickupRate', ''),  # Per time slot
                    'AvgDuration': p.get('AvgDuration', ''),  # Per time slot
                    'BestTime': p.get('BestTime', False)
                })
                rows.append(row)

    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)
