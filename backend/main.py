import time
import os
import sys
import json
import requests
from datetime import datetime, timedelta
from dataLatest import latest
from dataLatestWeather import latestWeather
from dataIspuLatest import ispuLatest

def write_log(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def delete_log():
    """Hapus Log Jika lebih dari 6000 baris"""
    log_file = "/app/logs/main.log"
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        if len(lines) > 6000:
            with open(log_file, 'w') as f:
                f.writelines(lines[-6000:])
            write_log("Log file dibersihkan, hanya menyimpan 6000 baris terakhir.")
        else:
            write_log("Log file masih dalam batas, tidak perlu dibersihkan.")
    else:
        write_log("Log file tidak ditemukan, tidak bisa dibersihkan.")

def scheduler():
    write_log("Service aktif. Menunggu jadwal pengambiland dari API...")

    try:
        while True:
            now = datetime.now()
            delete_log()
    
            # Tentukan target waktu: 4 menit berikutnya detik 4
            next_run = (now.replace(second=0, microsecond=0) + timedelta(minutes=4)).replace(second=4)

            # Hitung waktu tidur
            sleep_seconds = (next_run - now).total_seconds()
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

            # Jalankan task
            try:
                write_log("Menjalankan task pengambilan data dari API Ispu Latest...")
                ispuLatest()

                write_log("Menjalankan task pengambilan data dari API Latest Weather...")
                latestWeather()

                write_log("Menjalankan task pengambilan data dari API Latest...")
                latest()
            except Exception as e:
                write_log(f"Error saat menjalankan task: {e}")

    except KeyboardInterrupt:
        write_log("Service dihentikan manual.")

if __name__ == "__main__":
    scheduler()
