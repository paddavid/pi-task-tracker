import tkinter as tk
import json, os, threading, time, datetime, csv

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

# ---------- Pomodoro ----------
class Pomodoro:
    def __init__(self, label, counter_label):
        self.label = label
        self.counter_label = counter_label
        self.running = False
        self.remaining = 0
        self.thread = None
        self.duration = 0

    def start(self, minutes):
        if self.running: return
        self.duration = minutes
        self.remaining = minutes * 60
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        while self.running and self.remaining > 0:
            mins, secs = divmod(self.remaining, 60)
            self.label.config(text=f"{mins:02}:{secs:02}")
            time.sleep(1)
            self.remaining -= 1
        if self.running:
            self.finish()

    def pause(self):
        self.running = False

    def reset(self):
        self.running = False
        self.label.config(text="00:00")

    def finish(self):
        self.running = False
        self.label.config(text="DONE!")
        register_pomodoro(self.duration)

# ---------- Logging ----------
def register_pomodoro(duration):
    today = datetime.date.today()
    year, week, _ = today.isocalendar()

    # Write to CSV log
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([year, week, str(today),
                         datetime.datetime.now().strftime("%H:%M:%S"),
                         duration])

    # Count current week
    current_week_count = 0
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2 and row[0] == str(year) and row[1] == str(week):
                    current_week_count += 1
    stats_label.config(text=f"Pomodoros this week: {current_week_count}")

# ---------- GUI ----------
root = tk.Tk()
root.title("Discipline Dashboard")
root.attributes("-fullscreen", True)
root.configure(bg="black")

font_big = ("Arial", 28, "bold")
font_small = ("Arial", 20)

frame_tasks = tk.Frame(root, bg="black")
frame_tasks.pack(side="left", fill="both", expand=True)

tasks = load_tasks()
done = [False] * len(tasks)
buttons = []

def toggle_task(i):
    done[i] = not done[i]
    color = "green" if done[i] else "white"
    buttons[i].config(fg=color)

for i, task in enumerate(tasks):
    btn = tk.Button(frame_tasks, text=task, font=font_big,
                    bg="black", fg="white", relief="flat",
                    command=lambda i=i: toggle_task(i))
    btn.pack(pady=30)
    buttons.append(btn)

# Pomodoro frame
frame_pomo = tk.Frame(root, bg="black")
frame_pomo.pack(side="right", fill="both", expand=True)

label_timer = tk.Label(frame_pomo, text="00:00",
                       font=("Arial", 60, "bold"),
                       fg="red", bg="black")
label_timer.pack(pady=40)

pomo = Pomodoro(label_timer, None)

tk.Button(frame_pomo, text="45 min", font=font_small,
          command=lambda: pomo.start(45)).pack(pady=5)
tk.Button(frame_pomo, text="90 min", font=font_small,
          command=lambda: pomo.start(90)).pack(pady=5)
tk.Button(frame_pomo, text="Pause", font=font_small,
          command=pomo.pause).pack(pady=5)
tk.Button(frame_pomo, text="Reset", font=font_small,
          command=pomo.reset).pack(pady=5)

stats_label = tk.Label(frame_pomo, text="Pomodoros this week: 0",
                       font=font_small, fg="yellow", bg="black")
stats_label.pack(pady=30)

root.mainloop()