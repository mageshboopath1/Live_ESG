import pandas as pd
import psycopg2
from psycopg2 import sql
import os

def csv_to_psql(csv_file_path, db_name, db_user, db_password, db_host, table_name):
    """
    Converts a CSV file to a PostgreSQL table.

    Args:
        csv_file_path (str): The path to the CSV file.
        db_name (str): The name of the PostgreSQL database.
        db_user (str): The PostgreSQL username.
        db_password (str): The PostgreSQL password.
        db_host (str): The PostgreSQL host.
        table_name (str): The name of the table to create.
    """
    if not os.path.exists(csv_file_path):
        print(f"Error: The file '{csv_file_path}' does not exist.")
        return

    conn = None
    try:
        df = pd.read_csv(csv_file_path)
        print(f"Successfully read data from '{csv_file_path}'.")

        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host
        )
        cursor = conn.cursor()

        column_types = {
            'int64': 'INTEGER',
            'float64': 'DOUBLE PRECISION',
            'object': 'TEXT',
            'bool': 'BOOLEAN'
        }
        columns = [
            sql.SQL("{} {}").format(sql.Identifier(col), sql.SQL(column_types.get(str(df.dtypes[col]), 'TEXT')))
            for col in df.columns
        ]

        create_table_query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(columns)
        )
        cursor.execute(create_table_query)
        conn.commit()
        print(f"Table '{table_name}' created or already exists.")

        insert_query = sql.SQL("INSERT INTO {} VALUES ({})").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(sql.Placeholder() * len(df.columns))
        )

        for _, row in df.iterrows():
            cursor.execute(insert_query, tuple(row))

        conn.commit()
        print("Data successfully inserted into the table.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

# --- Example Usage ---
# Replace these with your actual database credentials and file path
DB_HOST = 'localhost'
DB_NAME = 'Environment'
DB_USER = 'mageshboopathi'
DB_PASSWORD = 'jesus'
TABLE_NAME = 'nift50_companies'
CSV_FILE_PATH = 'data/ind_nifty50list.csv'

csv_to_psql(CSV_FILE_PATH, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, TABLE_NAME)