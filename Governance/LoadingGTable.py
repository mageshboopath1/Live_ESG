import os
import csv
import re
import psycopg2
from psycopg2 import extras

# --- Configuration ---
# Replace with your PostgreSQL database connection details
DB_CONFIG = {
    "dbname": "Environment",
    "user": "mageshboopathi",
    "password": "jesus",
    "host": "localhost",
    "port": "5432"
}

# The folder where your CSV files are located
CSV_FOLDER_PATH = "data"

# The name of the table you want to create and insert data into
TABLE_NAME = "corporate_announcements"

# --- Development Setting ---
# WARNING: Setting this to True will delete all data in the table on every run.
# This is useful for development to ensure a clean slate.
# Set to False in a production environment to avoid data loss.
DROP_TABLE_ON_RUN = True


def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connection established successfully.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Could not connect to the database: {e}")
        return None

def clean_column_name(header_name):
    """Cleans a string to be a valid SQL column name."""
    # Convert to lowercase
    name = header_name.lower()
    # Replace spaces, slashes, and other non-alphanumeric chars with an underscore
    name = re.sub(r'[^a-z0-9]+', '_', name)
    # Remove leading/trailing underscores
    return name.strip('_')

def create_table_if_not_exists(cursor):
    """Creates the target table if it doesn't already exist."""
    # Note: Column names are lowercase and cleaned.
    # Data types are chosen based on the sample CSV. Adjust if necessary.
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(50),
        company_name VARCHAR(255),
        subject TEXT,
        details TEXT,
        broadcast_date_time TIMESTAMP,
        receipt TIMESTAMP,
        dissemination TIMESTAMP,
        difference VARCHAR(50),
        attachment TEXT
    );
    """
    try:
        cursor.execute(create_table_query)
        print(f"✅ Table '{TABLE_NAME}' is ready.")
    except psycopg2.Error as e:
        print(f"❌ Error creating table: {e}")
        raise

def process_csv_files(conn, folder_path):
    """
    Finds all CSV files in a folder, reads their data, handles empty values,
    and inserts the data into the PostgreSQL table.
    """
    cursor = conn.cursor()
    
    try:
        csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
        if not csv_files:
            print(f"⚠️ No CSV files found in '{folder_path}'.")
            return

        print(f"Found {len(csv_files)} CSV files to process...")

        for file_name in csv_files:
            file_path = os.path.join(folder_path, file_name)
            print(f"\nProcessing '{file_name}'...")
            
            # Use 'utf-8-sig' to handle the Byte Order Mark (BOM) at the start of the file
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader) # Read the header row
                
                # Prepare data for batch insertion
                data_to_insert = []
                for row in reader:
                    # Replace empty strings or placeholder hyphens with None for NULL insertion
                    processed_row = [None if val.strip() in ('', '-') else val for val in row]
                    data_to_insert.append(tuple(processed_row))

                if not data_to_insert:
                    print(f"  - No data rows found in '{file_name}'. Skipping.")
                    continue
                
                # Clean column names from the CSV header for the INSERT statement
                columns_cleaned = [clean_column_name(h) for h in header]
                
                # Construct the INSERT statement for batch execution
                insert_query = f"""
                    INSERT INTO {TABLE_NAME} ({', '.join(columns_cleaned)}) 
                    VALUES %s
                """
                
                # Use execute_values for efficient batch insertion
                extras.execute_values(
                    cursor,
                    insert_query,
                    data_to_insert,
                    template=None,
                    page_size=100
                )
                print(f"  - Successfully inserted {len(data_to_insert)} rows from '{file_name}'.")

        conn.commit()
        print("\n✅ All data has been committed to the database.")

    except (IOError, psycopg2.Error, csv.Error) as e:
        print(f"❌ An error occurred: {e}")
        conn.rollback() # Rollback changes on error
    finally:
        cursor.close()


def main():
    """Main function to run the ETL process."""
    print("--- Starting CSV to PostgreSQL Importer ---")
    
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                if DROP_TABLE_ON_RUN:
                    print(f"⚠️ Dropping table '{TABLE_NAME}' as per configuration.")
                    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
                
                create_table_if_not_exists(cursor)
            
            process_csv_files(conn, CSV_FOLDER_PATH)

        finally:
            conn.close()
            print("🔌 Database connection closed.")
    
    print("--- Process Finished ---")


if __name__ == "__main__":
    main()

