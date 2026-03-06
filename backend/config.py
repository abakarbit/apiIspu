import mysql.connector
import os
import time
from datetime import datetime as dt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def write_log(message):
    """Log message with timestamp"""
    timestamp = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def mysqlConfig():
    HOST = os.getenv('MYSQL_HOST')
    USER = os.getenv('MYSQL_USER')
    PASSWORD = os.getenv('MYSQL_PASSWORD')
    DATABASE = os.getenv('MYSQL_DATABASE')
    PORT = int(os.getenv('MYSQL_PORT'))
    
    
    # MySQL connection configuration
    MYSQL_CONFIG = {
        'host': HOST,
        'user': USER,
        'password': PASSWORD,
        'database': DATABASE,
        'port': PORT
    }

    return MYSQL_CONFIG


def check_duplicate_data(datetime, device, parameter):
    """
    Cek apakah data dengan device dan date yang sama sudah ada di database.

    Returns:
        True jika data sudah ada, False jika belum ada
    """
    try:
        MYSQL_CONFIG = mysqlConfig()
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # Cek di tabel tmp dan data
        query = f"""
                SELECT COUNT(*) FROM tbl_data
                WHERE recorded_at = %s AND device_id = %s AND parameter_name = %s
            """
        cursor.execute(query, (datetime, device, parameter))
        result = cursor.fetchone()
        if result and result[0] > 0:
            return True
        else:
            return False
        
    except Exception as e:
        write_log(f"Gagal mengecek duplicate data: {e}")
        return False


def insert_data(datetime,timestamp,device_id,parameter,value):
    # Simpan data ke database dengan tambahan kolom created_at dan updated_at
    create_at = dt.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    update_at = create_at
    # Cek apakah data dengan device dan date yang sama sudah ada
    if check_duplicate_data(datetime, device_id, parameter):
        write_log(f"Data dengan device '{device_id}' datetime '{datetime}' parameter '{parameter}' sudah ada di database. Tidak Disimpan.")
        return False
    
    query = """
        INSERT INTO tbl_data (recorded_at, timestamp, device_id, parameter_name, value, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
        
    try:
        MYSQL_CONFIG = mysqlConfig()
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        values = (
            datetime, timestamp, device_id, parameter, value, create_at, update_at
        )
        
        cursor.execute(query, values)
        conn.commit()

        write_log(f"Data berhasil disimpan kedatabase: device='{device_id}', datetime='{datetime}', parameter='{parameter}', value='{value}'")
        return True
        
    except Exception as e:
        write_log(f"Gagal memasukkan data ke database: {e}")
        return False
        
    finally:
        # Tutup koneksi
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

