import os
import mysql.connector
from dotenv import load_dotenv

def test_database_connection():
    """
    Loads database credentials from a .env file and attempts to connect.
    Prints a detailed success or failure message.
    """
    # 1. Load environment variables from the .env file
    load_dotenv()

    # 2. Retrieve credentials using os.getenv()
    db_host = os.getenv("DATABASE_HOST")
    db_name = os.getenv("DATABASE_NAME")
    db_user = os.getenv("DATABASE_USERNAME")
    db_pass = os.getenv("DATABASE_PASSWORD")

    print("Attempting to connect to the database...")
    print(f"Host: {db_host}")
    print(f"Database: {db_name}")
    print(f"User: {db_user}")

    # Check if any variable is missing
    if not all([db_host, db_name, db_user, db_pass]):
        print("\n❌ ERROR: One or more database environment variables are missing.")
        print("Please check your .env file for DATABASE_HOST, DATABASE_NAME, DATABASE_USERNAME, and DATABASE_PASSWORD.")
        return

    connection = None
    try:
        # 3. Attempt to establish the connection
        connection = mysql.connector.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass,
            connection_timeout=10 # Set a timeout of 10 seconds
        )

        # 4. Check if the connection is successful
        if connection.is_connected():
            db_info = connection.get_server_info()
            print("\n✅ SUCCESS: Database connection established successfully!")
            print(f"MySQL Server Version: {db_info}")
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            print(f"You're connected to database: {record[0]}")

    except mysql.connector.Error as err:
        # 5. Print a detailed error message on failure
        print(f"\n❌ FAILED: Could not connect to the database.")
        print(f"Error Code: {err.errno}")
        print(f"SQLSTATE: {err.sqlstate}")
        print(f"Message: {err.msg}")
        print("\nCommon reasons for failure:")
        print("  - Incorrect credentials in the .env file.")
        print("  - The IP address of this machine is not whitelisted in cPanel's 'Remote MySQL'.")
        print("  - The database server is down or there is a network issue.")

    finally:
        # 6. Ensure the connection is closed
        if connection and connection.is_connected():
            connection.close()
            print("\nConnection closed.")

if __name__ == "__main__":
    test_database_connection()
