import os
import shutil
import time
import datetime
import schedule
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

servers_dir = '/home/administrator/LPanel/servers'
backups_dir = '/home/administrator/LPanel/backups'

class Watcher:
    def __init__(self, path):
        self.path = path
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.path, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            self.backup_folder(event.src_path)

    def backup_folder(self, folder_path):
        folder_name = os.path.basename(folder_path)
        timestamp = datetime.datetime.now().strftime("%m-%d-%Y")
        backup_name = f"{folder_name}-{timestamp}"
        backup_path = os.path.join(backups_dir, backup_name)

        if not os.path.exists(backup_path):
            shutil.copytree(folder_path, backup_path)
            print(f"Backup created for {folder_name} at {backup_path}")

def backup_all_folders():
    for folder in os.listdir(servers_dir):
        folder_path = os.path.join(servers_dir, folder)
        if os.path.isdir(folder_path):
            backup_name = f"{folder}-{datetime.datetime.now().strftime('%m-%d-%Y')}"
            backup_path = os.path.join(backups_dir, backup_name)
            if not os.path.exists(backup_path):
                shutil.copytree(folder_path, backup_path)
                print(f"Backup created for {folder} at {backup_path}")

if __name__ == "__main__":
    backup_all_folders()
    
    watcher = Watcher(servers_dir)
    schedule.every(5).hours.do(backup_all_folders)

    print("Starting to watch the servers directory...")
    watcher.run()

    while True:
        schedule.run_pending()
        time.sleep(1)
