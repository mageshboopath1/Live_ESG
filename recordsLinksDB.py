import os
import json
import psycopg2
from psycopg2 import sql

def create_table_and_insert_data(folder_path, db_name, db_user, db_password, db_host, table_name):
    """
    Reads all JSON files from a folder and inserts the data into a PostgreSQL table.

    Args:
        folder_path (str): Path to the folder containing JSON files.
        db_name (str): The name of the PostgreSQL database.
        db_user (str): The PostgreSQL username.
        db_password (str): The PostgreSQL password.
        db_host (str): The PostgreSQL host.
        table_name (str): The name of the table to create and insert data into.
    """
    conn = None
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host
        )
        cursor = conn.cursor()

        # Create the table with the new 'company_name' column
        create_table_query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {table} (
                id SERIAL PRIMARY KEY,
                company_name TEXT,
                industry_name TEXT,
                address TEXT,
                city TEXT,
                state_name TEXT,
                category_name TEXT,
                has_clickable_action BOOLEAN,
                source_name TEXT,
                detail_page_url TEXT
            )
        """).format(table=sql.Identifier(table_name))
        cursor.execute(create_table_query)
        conn.commit()
        print(f"Table '{table_name}' created or already exists.")

        # Iterate over JSON files in the folder
        json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        
        for filename in json_files:
            file_path = os.path.join(folder_path, filename)
            # Extract company name from the filename by removing the extension
            company_name_from_file = os.path.splitext(filename)[0]
            
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    
                    if not data:
                        print(f"Skipping empty file: {filename}")
                        continue
                    
                    # Prepare data for insertion
                    insert_query = sql.SQL("""
                        INSERT INTO {table} (
                            company_name, industry_name, address, city, state_name, category_name,
                            has_clickable_action, source_name, detail_page_url
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """).format(table=sql.Identifier(table_name))

                    for record in data:
                        # Use .get() to handle potentially missing keys
                        record_values = (
                            company_name_from_file,
                            record.get('industry_name'),
                            record.get('address'),
                            record.get('city'),
                            record.get('state_name'),
                            record.get('category_name'),
                            record.get('has_clickable_action'),
                            record.get('source_name'),
                            record.get('detail_page_url')
                        )
                        cursor.execute(insert_query, record_values)
                    
                    conn.commit()
                    print(f"Data from '{filename}' successfully inserted.")
                
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from '{filename}'. Skipping.")
                except Exception as e:
                    print(f"An error occurred while processing '{filename}': {e}")

    except Exception as e:
        print(f"Database connection or operation failed: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

# --- How to use the code ---
DB_HOST = 'localhost'
DB_NAME = 'Environment'
DB_USER = 'mageshboopathi'
DB_PASSWORD = 'jesus'
TABLE_NAME = 'nift50_pollution'
FOLDER_PATH = 'data/recordLinks'

# Call the function to perform the task
create_table_and_insert_data(FOLDER_PATH, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, TABLE_NAME)