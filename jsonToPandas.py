import pandas as pd
import json
import os

pd.set_option('display.max_columns', None)

def unify_json_data(directory):
    """
    Reads all JSON files from a specified directory, unifies them into a single pandas
    DataFrame.
    """
    all_records = []
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return pd.DataFrame()

    json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
    
    if not json_files:
        print(f"No JSON files found in {directory}.")
        return pd.DataFrame()

    print(f"Found {len(json_files)} JSON files to process.")

    for filename in json_files:
        file_path = os.path.join(directory, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if data:
                    df = pd.DataFrame(data)
                    all_records.append(df)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {filename}: {e}. Skipping.")

    if not all_records:
        print("All JSON files were empty or invalid. Returning an empty DataFrame.")
        return pd.DataFrame()

    master_df = pd.concat(all_records, ignore_index=True)
    
    return master_df

# --- Main script execution ---
unified_data = unify_json_data('data/recordLinks')

if not unified_data.empty:
    for i, row in unified_data.iterrows():
        print(f"{i} {row['state_name']} {row['industry_name']}")