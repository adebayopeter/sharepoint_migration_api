import pyodbc
import pandas as pd
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


# Spool records to push into sharepoint
def get_images_and_metadata():
    conn_str = (
        f"DRIVER={os.getenv('DB_DRIVER')};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_DATABASE')};"
        f"UID={os.getenv('DB_USERNAME')};"
        f"PWD={os.getenv('DB_PASSWORD')}"
    )

    conn = pyodbc.connect(conn_str)
    query_table = os.getenv('DB_TABLE_1')

    query = f"SELECT * FROM {query_table}"
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def update_image_status(ref_id, image_link, status, filename):
    conn_str = (
        f"DRIVER={os.getenv('DB_DRIVER')};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_DATABASE')};"
        f"UID={os.getenv('DB_USERNAME')};"
        f"PWD={os.getenv('DB_PASSWORD')}"
    )

    conn = pyodbc.connect(conn_str)
    query_table = os.getenv('DB_TABLE_1')
    cursor = conn.cursor()

    query = (
        f"UPDATE {query_table} SET image_link = ?, "
        f"status = ?, filename = ? WHERE id = ?"
    )

    cursor.execute(query, (image_link, status, filename, ref_id))
    conn.commit()
    conn.close()




