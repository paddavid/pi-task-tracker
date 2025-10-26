import tkinter as tk
import json, os, threading, time, datetime, csv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

TASK_FILE = "tasks.json"
LOG_FILE = "pomodoro_log.csv"

# ---------- Helpers ----------
def load_tasks():
    if not os.path.exists(TASK_FILE):
        save_tasks(["Task 1", "Task 2", "Task 3"])
    with open(TASK_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def log_pomodoro(minutes):
    today = datetime.date.today()
    year, week, _ = today.isocalendar()
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([year, week, str(today), minutes])

def get_week_minutes():
    if not os.path.exists(LOG_FILE): 
        return 0
    today = datetime.date.today()
    year, week, _ = today.isocalendar()
    total = 0
    with open(LOG_FILE, "r") as f:
        for row in csv.reader(f):
            if len(row) >= 4 and row[0]==str(year) and row[1]==str(week):
                total += int(row[3])
    return total

def fmt_mins(mins):
    h, m = divmod(mins, 60)
    return f"{h:02d}h {m:02d}m"

# ---------- File Watcher ----------
class TaskWatcher(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
    def on_modified(self, event):
        if event.src_path.endswith(TASK_FILE):
            self.callback()

# ---------- App ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Discipline Tracker V3")
        self.configure(bg="black")
        self.geometry("1024x600")
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # Start watchdog for tasks.json
        self.observer = Observer()
        self.observer.schedule(TaskWatcher(self.reload_tasks), ".", recursive=False)
        self.observer.start()

        self.tasks = []
        self.done = []
        self.frame_tasks = None
        self.week_label = None
        self.header = None

        self.show_home()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def show_home(self):
        self.clear()

        # --- Header Bar ---
        self.header = tk.Frame(self, bg="#111")
        self.header.pack(fill="x")
        tk.Button(self.header, text="↻ Reload", bg="#333", fg="white",
                  font=("Arial",16), command=self.reload_tasks).pack(side="left", padx=10, pady=5)
        tk.Label(self.header, text="Discipline Tracker", bg="#111", fg="white",
                 font=("Arial",18,"bold")).pack(side="left", expand=True)
        tk.Button(self.header, text="× Close", bg="red", fg="white",
                  font=("Arial",16,"bold"), command=self.destroy).pack(side="right", padx=10, pady=5)

        # --- Tasks Frame ---
        self.frame_tasks = tk.Frame(self, bg="black")
        self.frame_tasks.pack(side="left", fill="both", expand=True)

        self.tasks = load_tasks()
        self.done = [False]*len(self.tasks)

        for i, task in enumerate(self.tasks):
            b = tk.Button(self.frame_tasks, text=task, fg="white", bg="black",
                          font=("Arial", 26, "bold"), relief="flat")
            b.pack(expand=True, pady=10)
            def toggle(i=i, btn=b):
                self.done[i]=not self.done[i]
                btn.config(fg="green" if self.done[i] else "white")
            b.config(command=toggle)

        # --- Right Side ---
        right = tk.Frame(self, bg="black")
        right.pack(side="right", fill="both", expand=True)

        week_mins = get_week_minutes()
        self.week_label = tk.Label(right, text=f"Pomodoro time this week: {fmt_mins(week_mins)}",
                                   fg="yellow", bg="black", font=("Arial",20))
        self.week_label.pack(pady=20)

        def confirm_session(minutes):
            popup = tk.Toplevel(self)
            popup.configure(bg="black")
            popup.geometry("400x200+300+200")
            tk.Label(popup, text="Mit Pomodoro Session beginnen?",
                     fg="white", bg="black", font=("Arial",18)).pack(pady=20)
            def start():
                popup.destroy()
                self.show_pomodoro(minutes)
            tk.Button(popup, text="Ja", font=("Arial",16),
                      command=start).pack(side="left", expand=True, padx=30)
            tk.Button(popup, text="Nein", font=("Arial",16),
                      command=popup.destroy).pack(side="right", expand=True, padx=30)

        tk.Button(right, text="45 min", font=("Arial",20),
                  command=lambda: confirm_session(45)).pack(pady=10)
        tk.Button(right, text="90 min", font=("Arial",20),
                  command=lambda: confirm_session(90)).pack(pady=10)

    def reload_tasks(self):
        self.show_home()

    # ---- Pomodoro Screen ----
    def show_pomodoro(self, minutes):
        self.clear()
        timer_lbl = tk.Label(self, text=f"{minutes:02}:00",
                             fg="red", bg="black",
                             font=("Arial",120,"bold"))
        timer_lbl.pack(expand=True)
        running = {"flag":True, "remaining":minutes*60}

        def tick():
            while running["flag"] and running["remaining"]>0:
                mins, secs = divmod(running["remaining"],60)
                timer_lbl.config(text=f"{mins:02}:{secs:02}")
                time.sleep(1)
                running["remaining"]-=1
            if running["remaining"]<=0:
                log_pomodoro(minutes)
                self.show_home()

        threading.Thread(target=tick, daemon=True).start()

        def pause():
            running["flag"]=not running["flag"]
            if running["flag"]:
                threading.Thread(target=tick, daemon=True).start()

        btn_frame = tk.Frame(self,bg="black")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame,text="Pause",font=("Arial",24),
                  command=pause).pack(side="left",padx=20)
        tk.Button(btn_frame,text="Abbrechen",font=("Arial",24),
                  command=self.show_home).pack(side="right",padx=20)

# ---------- Run ----------
if __name__=="__main__":
    try:
        App().mainloop()
    finally:
        try: App().observer.stop()
        except: pass
