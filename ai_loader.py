import pandas as pd
import subprocess
import tempfile
from tqdm import tqdm
from io import StringIO

INPUT_FILE = 'output_clusters.xlsx'
OUTPUT_FILE = 'output_refined.xlsx'
OLLAMA_MODEL = 'phi3:medium'

def call_ollama_deepseek(prompt, chunk_df):
    try:
        input_text = prompt + '\n\n' + chunk_df.to_csv(index=False)

        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as f:
            f.write(input_text)
            f.flush()
            temp_filename = f.name

        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            stdin=open(temp_filename, 'rb'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300  # 5 minutes per chunk
        )

        if result.returncode != 0:
            print("[ERROR] Ollama returned non-zero exit code:")
            print(result.stderr.decode())
            return None

        return result.stdout.decode()

    except subprocess.TimeoutExpired:
        print("[ERROR] Ollama call timed out.")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error during Ollama call: {e}")
        return None


def main():
    df = pd.read_excel(INPUT_FILE)
    print(f"[AI Refinement] Loaded {len(df)} rows from {INPUT_FILE}.")

    prompt = (
        "You are an expert data analyst. Review the following tele-calling cluster data. "
        "Suggest any refinements, corrections, or improvements to the clusters. "
        "If you can, return a refined table in the same format. "
        "If not, return a list of suggestions. "
        "Make sure city, age, and income merged ranges are clearly mentioned, like: CityId - 3,2."
    )

    all_outputs = []

    cluster_groups = df.groupby("ClusterIndex")

    with tqdm(total=len(cluster_groups), desc="Refining Clusters", unit="cluster") as pbar:
        for cluster_index, cluster_df in cluster_groups:
            print(f"\n[INFO] Processing Cluster {cluster_index} with {len(cluster_df)} rows...")
            ai_response = call_ollama_deepseek(prompt, cluster_df)

            if ai_response is None:
                cluster_df['AI_Suggestions'] = "Error: No response"
                all_outputs.append(cluster_df)
                pbar.update(1)
                continue

            try:
                refined_df = pd.read_csv(StringIO(ai_response))
                all_outputs.append(refined_df)
            except Exception:
                cluster_df['AI_Suggestions'] = ai_response
                all_outputs.append(cluster_df)

            pbar.update(1)

    final_df = pd.concat(all_outputs, ignore_index=True)
    final_df.to_excel(OUTPUT_FILE, index=False)
    print(f"\n✅ All clusters refined. Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
