import time
import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from config import insert_data

# Load environment variables from .env file
load_dotenv()

APIENDPOINT = os.getenv('APIENDPOINT_ISPU_LATEST')
APIKEY = os.getenv('ISPU_APIKEY')
APISECRET = os.getenv('ISPU_APISECRET')

def write_log(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def getData():

    # Ambil data dari API
    try:
        response = requests.get(APIENDPOINT, headers={
            "apikey": APIKEY,
            "apisecret": APISECRET
        }, timeout=(5, 60))
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            write_log(f"Gagal mengambil data dari API. Status Code: {response.status_code}, Response: {response.text}")
            return None
    except requests.RequestException as e:
        write_log(f"Error saat mengambil data dari API: {e}")
        return None


def ispuLatest():
    """
    Parse JSON data dengan struktur rows dan insert setiap parameter ke database.
    
    Args:
        json_data: Dictionary atau JSON string dengan struktur rows
    
    Returns:
        Dictionary dengan statistik insert (success, failed, skipped)
    """
    try:
        # Jika input adalah string, parse ke dictionary
        json_data = getData()
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        
        if 'rows' not in data:
            write_log("JSON tidak memiliki key 'rows'")
            return None
        
        stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Iterasi setiap device
        for row in data['rows']:
            device_id = row.get('deviceId')
            
            if not device_id:
                write_log("Device ID tidak ditemukan, skip entry")
                stats['skipped'] += 1
                continue
            
            # Iterasi setiap value entry (datetime entry)
            for value_entry in row.get('values', []):
                datetime_str = value_entry.get('datetime')
                
                if not datetime_str:
                    write_log(f"Datetime tidak ditemukan untuk device {device_id}, skip entry")
                    stats['skipped'] += 1
                    continue
                
                # Convert datetime string ke timestamp
                try:
                    dt_object = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                    timestamp = int(dt_object.timestamp())
                except Exception as e:
                    write_log(f"Error parsing datetime '{datetime_str}': {e}")
                    stats['failed'] += 1
                    continue
                
                # Iterasi setiap parameter
                for param in value_entry.get('parameters', []):
                    param_name = param.get('label')
                    param_value = param.get('ispu')
                    
                    if param_name is None or param_value is None:
                        write_log(f"Parameter tidak lengkap untuk device {device_id}, skip")
                        stats['skipped'] += 1
                        continue
                    
                    # Mapping parameter ke nama yang diinginkan 
                    # Kiri parameter API, kanan nama parameter yang diinginkan di database
                    param_mapping = {
                        'pm10': 'ipm10',
                        'pm2.5': 'ipm25',
                        'o3': 'io3',
                        'so2': 'iso2',
                        'no2': 'ino2',
                        'co': 'ico',
                        'hc': 'ihc'
                    }
                    
                    # Cek apakah parameter ada dalam mapping
                    param_lower = param_name.lower()
                    if param_lower not in param_mapping:
                        # Parameter tidak ada dalam list yang ditentukan, skip
                        continue
                    
                    # Ambil nama parameter yang sudah di-mapping
                    param_name = param_mapping[param_lower]

                    # Insert ke database
                    try:
                        result = insert_data(
                            datetime_val=datetime_str,
                            timestamp_val=timestamp,
                            device_id=device_id,
                            parameter=param_name,
                            value=param_value
                        )
                        if result:
                            stats['success'] += 1
                        else:
                            stats['skipped'] += 1
                    except Exception as e:
                        write_log(f"Error insert data device={device_id}, param={param_name}: {e}")
                        stats['failed'] += 1
        
        write_log(f"Parsing selesai. Success: {stats['success']}, Skipped: {stats['skipped']}, Failed: {stats['failed']}")
        return stats
        
    except Exception as e:
        write_log(f"Error saat parsing JSON data: {e}")
        return None

ispuLatest()
