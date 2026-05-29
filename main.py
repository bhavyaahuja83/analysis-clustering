import time
from data_loader import stream_json_chunks
from cluster_creator import generate_clusters
from export_excel import export_to_excel
from config import DATA_PATH
import pandas as pd

def main():
    print("\U0001F4CA Generating Micro-Clusters and Time Slot Insights...\n")
    total_rows = 1320000
    chunk_size = 500000
    dfs = []
    start_time = time.time()
    load_start = time.time()

    try:
        for i, df_chunk in enumerate(stream_json_chunks(DATA_PATH, chunk_size=chunk_size, total_rows=total_rows)):
            print(f"✅ Loaded chunk {i+1} with {len(df_chunk):,} rows")
            dfs.append(df_chunk)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted! Proceeding with loaded data so far...")

    if not dfs:
        print("❌ No data loaded. Exiting.")
        return

    df = pd.concat(dfs, ignore_index=True)
    print(f"\nℹ️ Total rows loaded: {len(df):,}")
    print(f"⏱️ Loading Time: {round(time.time() - load_start, 2)} seconds")

    cluster_start = time.time()
    print(f"\n🔍 Clustering in progress...")
    clusters = generate_clusters(df)
    print(f"⏱️ Clustering Time: {round(time.time() - cluster_start, 2)} seconds")

    export_start = time.time()
    export_to_excel(clusters)
    print(f"⏱️ Export Time: {round(time.time() - export_start, 2)} seconds")

    print(f"\n✅ Clustering Complete. Output saved to './output_clusters.xlsx'")
    print(f"\n⏱️ Total Runtime: {round(time.time() - start_time, 2)} seconds")

if __name__ == "__main__":
    main()
