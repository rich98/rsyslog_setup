import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import re

LOG_PATTERN = re.compile(
    r'^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[\+\-]\d{2}:\d{2})) (?P<host>\S+) (?P<process>\S+?): (?P<message>.+)$'
)

class LogEntry:
    def __init__(self, timestamp, host, process, message):
        self.timestamp = timestamp
        self.host = host
        self.process = process
        self.message = message

    def __repr__(self):
        return f"{self.timestamp} {self.host} {self.process}: {self.message}"

def parse_log_line(line, year=None):  # year no longer needed
    match = LOG_PATTERN.match(line)
    if not match:
        return None
    try:
        timestamp = datetime.fromisoformat(match.group('timestamp'))
        return LogEntry(timestamp, match.group('host'), match.group('process'), match.group('message'))
    except ValueError:
        return None

def read_logs(file_path, year):
    entries = []
    with open(file_path, 'r') as f:
        for line in f:
            entry = parse_log_line(line, year)
            if entry:
                entries.append(entry)
    return sorted(entries, key=lambda e: e.timestamp)

def filter_logs(entries, process=None, keyword=None, start_time=None, end_time=None):
    filtered = []
    for entry in entries:
        if process and process.lower() not in entry.process.lower():
            continue
        if keyword and keyword.lower() not in entry.message.lower():
            continue
        if start_time and entry.timestamp < start_time:
            continue
        if end_time and entry.timestamp > end_time:
            continue
        filtered.append(entry)
    return filtered

class LogViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("rsyslog Viewer")
        self.log_entries = []
        self.year = datetime.now().year

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
            try:
                self.log_entries = read_logs(file_path, self.year)
                self.display_logs(self.log_entries)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read log file:\n{e}")

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
        filtered = filter_logs(self.log_entries, process, keyword, start_time, end_time)
        self.display_logs(filtered)

    def display_logs(self, logs):
        self.tree.delete(*self.tree.get_children())
        for entry in logs:
            self.tree.insert("", "end", values=(entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"), entry.host, entry.process, entry.message))

if __name__ == "__main__":
    root = tk.Tk()
    app = LogViewerApp(root)
    root.mainloop()
