import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import threading
import re

RSYSLOG_PATTERN = re.compile(
    r'^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[\+\-]\d{2}:\d{2})) (?P<host>\S+) (?P<process>\S+?): (?P<message>.+)$'
)

WINDOWS_LOG_PATTERN = re.compile(
    r'^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[\+\-]\d{2}:\d{2}))\s+(?P<host>\S+)\s+(?P<source>\S+)\s+(?P<fields>.+)$'
)

class LogEntry:
    def __init__(self, timestamp, host, process, message):
        self.timestamp = timestamp
        self.host = host
        self.process = process
        self.message = message

def parse_rsyslog_line(line):
    match = RSYSLOG_PATTERN.match(line)
    if not match:
        return None
    try:
        timestamp = datetime.fromisoformat(match.group('timestamp'))
        return LogEntry(timestamp, match.group('host'), match.group('process'), match.group('message'))
    except ValueError:
        return None

def parse_windows_log_line(line):
    match = WINDOWS_LOG_PATTERN.match(line)
    if not match:
        return None
    try:
        timestamp = datetime.fromisoformat(match.group('timestamp'))
        host = match.group('host')
        process = match.group('source')
        fields = match.group('fields').replace("#011", "\t").split("\t")
        message = " ".join(fields[11:]).strip() if len(fields) > 11 else " ".join(fields)
        return LogEntry(timestamp, host, process, message)
    except Exception:
        return None

def read_logs_generator(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            entry = parse_rsyslog_line(line) or parse_windows_log_line(line)
            if entry:
                yield entry

class LogViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Log Viewer")
        self.log_entries = []
        self.create_widgets()

    def create_widgets(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(fill="x")

        tk.Button(frame, text="Open Log File", command=self.open_file).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(frame, text="Process:").grid(row=0, column=1)
        self.process_entry = tk.Entry(frame, width=15)
        self.process_entry.grid(row=0, column=2)

        tk.Label(frame, text="Keyword:").grid(row=0, column=3)
        self.keyword_entry = tk.Entry(frame, width=15)
        self.keyword_entry.grid(row=0, column=4)

        tk.Label(frame, text="Start (YYYY-MM-DD HH:MM:SS):").grid(row=1, column=0)
        self.start_entry = tk.Entry(frame, width=20)
        self.start_entry.grid(row=1, column=1)

        tk.Label(frame, text="End (YYYY-MM-DD HH:MM:SS):").grid(row=1, column=2)
        self.end_entry = tk.Entry(frame, width=20)
        self.end_entry.grid(row=1, column=3)

        tk.Button(frame, text="Filter Logs", command=self.filter_and_display).grid(row=1, column=4)

        self.status_label = tk.Label(self.root, text="", anchor="w")
        self.status_label.pack(fill="x")

        self.tree = ttk.Treeview(self.root, columns=("Time", "Host", "Process", "Message"), show='headings')
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="w", width=150 if col != "Message" else 500)
        self.tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Log Files", "*.log *.txt"), ("All Files", "*.*")])
        if file_path:
            self.status_label.config(text="Loading in background...")
            self.tree.delete(*self.tree.get_children())
            thread = threading.Thread(target=self.load_logs_thread, args=(file_path,))
            thread.start()

    def load_logs_thread(self, file_path):
        entries = []
        count = 0
        for entry in read_logs_generator(file_path):
            entries.append(entry)
            count += 1

        entries.sort(key=lambda e: e.timestamp)
        self.log_entries = entries

        # Schedule GUI update in main thread
        self.root.after(0, self.display_logs, entries)
        self.root.after(0, lambda: self.status_label.config(text=f"Loaded {count} entries."))

    def parse_time(self, timestr):
        try:
            return datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S") if timestr else None
        except ValueError:
            messagebox.showerror("Invalid Time", f"Invalid time format:\n{timestr}")
            return None

    def filter_and_display(self):
        start_time = self.parse_time(self.start_entry.get())
        end_time = self.parse_time(self.end_entry.get())
        process = self.process_entry.get().strip()
        keyword = self.keyword_entry.get().strip()

        filtered = []
        for entry in self.log_entries:
            if process and process.lower() not in entry.process.lower():
                continue
            if keyword and keyword.lower() not in entry.message.lower():
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            filtered.append(entry)

        self.display_logs(filtered)
        self.status_label.config(text=f"{len(filtered)} entries matched filter.")

    def display_logs(self, logs):
        self.tree.delete(*self.tree.get_children())

        def batch_insert(index):
            BATCH_SIZE = 500
            end = min(index + BATCH_SIZE, len(logs))
            for entry in logs[index:end]:
                self.tree.insert("", "end", values=(
                    entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    entry.host,
                    entry.process,
                    entry.message
                ))
            if end < len(logs):
                self.root.after(1, batch_insert, end)

        batch_insert(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = LogViewerApp(root)
    root.mainloop()
