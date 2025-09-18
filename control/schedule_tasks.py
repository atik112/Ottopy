import schedule
import time

def task_example():
    print("Zamanlı görev çalıştı.")

def start_scheduler():
    schedule.every().day.at("09:00").do(task_example)
    while True:
        schedule.run_pending()
        time.sleep(1)
