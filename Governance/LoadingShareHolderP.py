import os
import pandas as pd
from sqlalchemy import create_engine
import traceback

# --- 1. Configuration ---
# TODO: Replace with your actual PostgreSQL connection details
DB_CONFIG = {
    "user": "mageshboopathi",
    "password": "jesus",
    "host": "localhost",  # or your DB host
    "port": "5432",
    "database": "Environment"
}

# The folder containing your CSV files
CSV_FOLDER_PATH = "data/ShareHolderPattern"
TABLE_NAME = "share_holder_pattern"

# --- 2. Database Connection ---
# Create the database connection URL
db_url = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Create a SQLAlchemy engine
engine = None
try:
    engine = create_engine(db_url)
    print("Successfully connected to the PostgreSQL database.")

    # --- 3. Data Ingestion Loop ---
    # Walk through all files in the specified directory
    for filename in os.listdir(CSV_FOLDER_PATH):
        if filename.endswith('.csv'):
            file_path = os.path.join(CSV_FOLDER_PATH, filename)
            print(f"Processing file: {filename}...")

            try:
                # Read the CSV file into a pandas DataFrame.
                # pandas automatically handles missing values by reading them as NaN.
                df = pd.read_csv(file_path)

                # Append the DataFrame to the SQL table.
                # 'if_exists='append'' adds the data to the table if it exists.
                # 'index=False' prevents pandas from writing the DataFrame index as a column.
                df.to_sql(
                    TABLE_NAME,
                    con=engine,
                    if_exists='append',
                    index=False
                )
                print(f"Data from {filename} appended successfully to '{TABLE_NAME}'.")

            except Exception as e:
                print(f"Error processing file {filename}: {e}")
                traceback.print_exc()

except Exception as e:
    print(f"An error occurred during database connection or processing: {e}")
    traceback.print_exc()

finally:
    # --- 4. Close Connection ---
    if engine:
        engine.dispose()
        print("Database connection closed.")