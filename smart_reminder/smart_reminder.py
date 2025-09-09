import speech_recognition as sr
import pyttsx3
import datetime
import time
import json
import re
import threading
from plyer import notification


# --- Config ---
TASK_FILE = "tasks.json"
CHECK_INTERVAL_SECONDS = 15  # how often we check reminders
MIC_DEVICE_INDEX = None      # set to an integer if you need a specific mic

# --- TTS ---
engine = pyttsx3.init()

def speak(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("TTS error:", e)

# --- Speech recognition ---
recognizer = sr.Recognizer()

def listen(prompt=None, timeout=5, phrase_time_limit=7):
    """Listen and return recognized text, or None on failure."""
    if prompt:
        speak(prompt)
    try:
        with sr.Microphone(device_index=MIC_DEVICE_INDEX) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.6)
            print("Listening...", "(you can also type if recognition fails)")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        text = recognizer.recognize_google(audio)
        print("Heard:", text)
        return text
    except sr.WaitTimeoutError:
        print("No speech detected (timeout).")
        return None
    except sr.UnknownValueError:
        print("Speech unintelligible.")
        return None
    except sr.RequestError as e:
        print("Speech service error:", e)
        return None
    except Exception as e:
        print("Microphone/listen error:", e)
        return None

# --- Persistence ---
def load_tasks():
    try:
        with open(TASK_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

# --- Time parsing ---
WORD_NUM = {
    "one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,
    "eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,"eighteen":18,"nineteen":19,
    "twenty":20,"thirty":30,"forty":40,"fifty":50,"half":30,"quarter":15
}

def parse_time(text):
    if not text:
        return None
    t = text.lower().replace(".", " ").strip()
    ampm = None
    if "am" in t:
        ampm = "am"
        t = t.replace("am"," ")
    if "pm" in t:
        ampm = "pm"
        t = t.replace("pm"," ")

    digits = re.findall(r'\d+', t)
    if len(digits) >= 2:
        try:
            h = int(digits[0]) % 24
            m = int(digits[1]) % 60
            if ampm == "pm" and h < 12:
                h += 12
            if ampm == "am" and h == 12:
                h = 0
            return h, m
        except:
            return None
    elif len(digits) == 1:
        try:
            h = int(digits[0]) % 24
            m = 0
            if ampm == "pm" and h < 12:
                h += 12
            if ampm == "am" and h == 12:
                h = 0
            return h, m
        except:
            return None

    tokens = re.split(r'[\s\-]+', t)
    hour = None
    minute = 0
    for tok in tokens:
        if tok in WORD_NUM:
            val = WORD_NUM[tok]
            if hour is None and val <= 12:
                hour = val
            else:
                minute += val
    if hour is not None:
        if ampm == "pm" and hour < 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
        minute = minute % 60
        return hour, minute
    return None

# --- Task operations ---
def add_task(task_text, hour, minute):
    tasks = load_tasks()
    time_str = f"{hour:02d}:{minute:02d}"
    tasks.append({"task": task_text, "time": time_str})
    save_tasks(tasks)

    # Terminal feedback
    print(f"Added: '{task_text}' at {time_str}")

    # 🔔 Desktop popup confirmation
    notification.notify(
        title="✅ Task Added",
        message=f"{task_text} at {time_str}",
        timeout=10
    )

    # 🔊 Voice confirmation
    speak(f"Task added: {task_text} at {hour:02d}:{minute:02d}")

def show_tasks():
    tasks = load_tasks()
    if not tasks:
        print("No tasks scheduled.")
        speak("No tasks scheduled.")
        return
    print("Scheduled tasks:")
    for i, t in enumerate(tasks, start=1):
        print(f"{i}. {t['task']} — {t['time']}")
    # Popup summary
    try:
        notification.notify(
            title="📋 Scheduled Tasks",
            message=f"You have {len(tasks)} task(s).",
            timeout=5
        )
    except Exception as e:
        print("Notification error:", e)

def delete_task_by_index(index):
    tasks = load_tasks()
    if 0 <= index < len(tasks):
        removed = tasks.pop(index)
        save_tasks(tasks)
        print("Removed:", removed)
        speak("Task removed.")
        try:
            notification.notify(
                title="🗑️ Task Removed",
                message=f"{removed['task']} at {removed['time']}",
                timeout=5
            )
        except:
            pass
        return True
    return False

# --- Reminder checking loop ---
def check_tasks(stop_event):
    print("Reminder checker started (background).")
    while not stop_event.is_set():
        now = datetime.datetime.now().strftime("%H:%M")
        tasks = load_tasks()
        changed = False
        for t in tasks[:]:
            if t["time"] == now:
                try:
                    notification.notify(
                        title="⏰ Task Reminder",
                        message=t["task"],
                        timeout=10
                    )
                except Exception as e:
                    print("Notification error:", e)
                speak("Reminder: " + t["task"])
                print("REMINDER:", t["task"], "at", now)
                tasks.remove(t)
                changed = True
        if changed:
            save_tasks(tasks)
        for _ in range(int(CHECK_INTERVAL_SECONDS / 1)):
            if stop_event.is_set():
                break
            time.sleep(1)
    print("Reminder checker stopped.")

# --- Utility: list microphones ---
def list_mics():
    try:
        names = sr.Microphone.list_microphone_names()
        print("Available microphone devices:")
        for i, name in enumerate(names):
            print(i, name)
    except Exception as e:
        print("Could not list microphones:", e)

# --- Main interactive loop ---
def main():
    # Startup voice
    speak("Smart Task Reminder started.")

    # Startup popup + task count
    try:
        tasks = load_tasks()
        count = len(tasks)
        if count:
            msg = f"System is running. You have {count} task(s) scheduled."
            speak(f"You have {count} task scheduled." if count == 1 else f"You have {count} tasks scheduled.")
        else:
            msg = "System is running. No tasks yet."
            speak("No tasks yet.")
        notification.notify(
            title="🟢 Smart Task Reminder",
            message=msg,
            timeout=5
        )
    except Exception as e:
        print("Notification error:", e)

    # Start background reminder checker
    stop_event = threading.Event()
    checker_thread = threading.Thread(target=check_tasks, args=(stop_event,), daemon=False)
    checker_thread.start()

    try:
        while True:
            speak("Say 'add' to add a task, 'show' to list tasks, 'delete' to remove, or 'exit' to quit.")
            cmd = listen(prompt=None)
            if cmd is None:
                cmd = input("Command (add/show/delete/list/exit or 'mics'): ").strip().lower()
            else:
                cmd = cmd.lower()

            if "mics" in cmd:
                list_mics()
                continue

            if any(k in cmd for k in ["add", "new", "remind", "set"]):
                speak("Please say the task description.")
                task = listen()
                if not task:
                    task = input("Task text (type): ").strip()
                if not task:
                    speak("No task given. Cancelled.")
                    continue

                speak("Please say the time. Example: 18 30 or six thirty pm.")
                time_text = listen()
                if not time_text:
                    time_text = input("Time (e.g., 18 30 or 6:30 pm): ").strip()
                parsed = parse_time(time_text)
                if parsed:
                    hour, minute = parsed
                    add_task(task, hour, minute)
                else:
                    speak("Could not parse the time. Please add again.")
                    print("Failed to parse time from:", time_text)

            elif any(k in cmd for k in ["show", "list"]):
                show_tasks()
            elif "delete" in cmd or "remove" in cmd:
                show_tasks()
                idx = input("Enter number to delete (or blank to cancel): ").strip()
                if idx.isdigit():
                    delete_task_by_index(int(idx)-1)
                else:
                    speak("Cancelled delete.")
            elif any(k in cmd for k in ["exit", "quit", "stop"]):
                speak("Exiting smart reminder. Goodbye.")
                stop_event.set()
                break
            else:
                speak("Command not recognized. Please say add, show, delete, or exit.")
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Exiting.")
        stop_event.set()
    except Exception as e:
        print("Unexpected error:", e)
        stop_event.set()

    checker_thread.join()

if __name__ == "__main__":
    main()
