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


def scheduler(interval_minutes=5, second=4):
    """
    Scheduler fleksibel:
    - interval_minutes: eksekusi setiap kelipatan menit tertentu
    - selalu mengeksekusi pada detik tertentu (default detik ke-4)
    """
    write_log(f"Service aktif. Menunggu jadwal setiap {interval_minutes} menit, detik ke-{second}...")

    try:
        while True:
            now = datetime.now()
            delete_log()

            # Tentukan kelipatan berikutnya
            next_minute = ((now.minute // interval_minutes + 1) * interval_minutes) % 60
            hour_increment = ((now.minute // interval_minutes + 1) * interval_minutes) // 60

            next_run = now.replace(
                hour=(now.hour + hour_increment) % 24,
                minute=next_minute,
                second=second,
                microsecond=0
            )

            # Hitung waktu tidur
            sleep_seconds = (next_run - now).total_seconds()
            if sleep_seconds < 0:
                # jika sudah lewat target, langsung ke interval berikutnya
                next_run += timedelta(minutes=interval_minutes)
                sleep_seconds = (next_run - now).total_seconds()

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
