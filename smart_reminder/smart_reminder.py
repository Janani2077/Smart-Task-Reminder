import speech_recognition as sr
import pyttsx3
import datetime
import time
import json
import re
from threading import Thread,Lock,Event
from win11toast import toast  # ✅ for Windows 10/11 popup notifications
tts_lock = Lock()            # Prevent overlapping pyttsx3 calls
resume_listening = Event()   # Control when main loop listens
resume_listening.set()       # Initially allow listening

# --- Config ---
TASK_FILE = "tasks.json"
CHECK_INTERVAL_SECONDS = 15
MIC_DEVICE_INDEX = None

# --- Speak Function ---
def speak(text):
    try:
        print(f"[Speaking]: {text}")
        engine = pyttsx3.init()
        engine.setProperty('rate', 175)
        engine.setProperty('volume', 1.0)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        time.sleep(0.2)
    except Exception as e:
        print("TTS error:", e)

# --- Speech Recognition ---
recognizer = sr.Recognizer()

def listen(prompt=None, timeout=5, phrase_time_limit=7):
    if prompt:
        speak(prompt)
    try:
        with sr.Microphone(device_index=MIC_DEVICE_INDEX) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🎤 Listening once...")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        text = recognizer.recognize_google(audio)
        print("🗣 Heard:", text)
        return text.strip()
    except sr.WaitTimeoutError:
        print("⏳ Timeout: No speech detected.")
    except sr.UnknownValueError:
        print("🤔 Could not understand speech.")
    except sr.RequestError:
        print("⚠ Speech service unavailable.")
    except Exception as e:
        print("Error while listening:", e)
    return None

# --- Load/Save Tasks ---
def load_tasks():
    try:
        with open(TASK_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

# --- Time Parsing ---
WORD_NUM = {
    "one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,
    "eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,"sixteen":16,
    "seventeen":17,"eighteen":18,"nineteen":19,"twenty":20,"thirty":30,"forty":40,"fifty":50,
    "half":30,"quarter":15
}

def parse_time(text):
    if not text:
        return None
    t = text.lower().replace(".", "").replace(" ", "")
    
    ampm = None
    if "am" in t:
        ampm = "am"
        t = t.replace("am", "")
    elif "pm" in t:
        ampm = "pm"
        t = t.replace("pm", "")

    # Handle colon-separated format hh:mm
    if ":" in t:
        try:
            h_str, m_str = t.split(":")
            h, m = int(h_str) % 24, int(m_str) % 60
            if ampm == "pm" and h < 12: h += 12
            if ampm == "am" and h == 12: h = 0
            return h, m
        except:
            return None

    # Fallback: word-based numbers like "six thirty"
    tokens = re.split(r'[\s\-]+', text.lower())
    hour, minute = None, 0
    for tok in tokens:
        if tok in WORD_NUM:
            val = WORD_NUM[tok]
            if hour is None and val <= 12:
                hour = val
            else:
                minute += val
    if hour is not None:
        if ampm == "pm" and hour < 12: hour += 12
        if ampm == "am" and hour == 12: hour = 0
        return hour, minute % 60
    return None

# --- Task Operations ---
def add_task(task_text, hour, minute):
    tasks = load_tasks()
    time_str = f"{hour:02d}:{minute:02d}"
    tasks.append({"task": task_text, "time": time_str})
    save_tasks(tasks)
    print(f"✅ Added: '{task_text}' at {time_str}")
    toast("✅ Task Added", f"{task_text} at {time_str}")
    speak(f"Task added: {task_text} at {hour:02d}:{minute:02d}")

def show_tasks():
    tasks = load_tasks()
    if not tasks:
        speak("No tasks scheduled.")
        print("No tasks scheduled.")
        return
    print("Scheduled tasks:")
    for i, t in enumerate(tasks, start=1):
        print(f"{i}. {t['task']} — {t['time']}")
    speak(f"You have {len(tasks)} tasks scheduled.")

def delete_task_by_index(index):
    tasks = load_tasks()
    if 0 <= index < len(tasks):
        removed = tasks.pop(index)
        save_tasks(tasks)
        speak("Task removed.")
        toast("🗑 Task Removed", f"{removed['task']} at {removed['time']}")
        print("Removed:", removed)
        return True
    return False

# --- Check Task Once ---
def check_and_remind():
    now = datetime.datetime.now().strftime("%H:%M")
    tasks = load_tasks()
    for t in tasks[:]:
        if t["time"] == now:
            toast("⏰ Task Reminder", t["task"])
            speak("Reminder: " + t["task"])
            print("REMINDER:", t["task"], "at", now)
            tasks.remove(t)
            save_tasks(tasks)
            resume_listening.set()

# --- Background Reminder Thread ---
def reminder_loop():
    while True:
        check_and_remind()
        time.sleep(CHECK_INTERVAL_SECONDS)

# --- Main Function ---
def main():
    speak("Smart Task Reminder started.")
    print("🎯 Smart Task Reminder ready.")

    # Start reminder loop in background
    reminder_thread = Thread(target=reminder_loop, daemon=True)
    reminder_thread.start()

    while True:
        resume_listening.wait()   # Wait until allowed
        resume_listening.clear()  # Pause again until next reminder
        cmd = listen("Say add, show, delete or exit.")
        if not cmd:
            speak("No command detected.")
            continue

        cmd = cmd.lower()

        if any(word in cmd for word in ["add", "new", "remind", "set"]):
            speak("Please say the task description.")
            task = listen()
            if not task:
                speak("No task detected.")
                resume_listening.set()
                continue
            speak("Please say the time. Example: six thirty pm or sixteen thirty.")
            time_text = listen()
            parsed = parse_time(time_text)
            if parsed:
                h, m = parsed
                add_task(task, h, m)
                speak("Task added. Pausing until next reminder.")
            else:
                speak("Could not understand the time.")

        elif any(word in cmd for word in ["show", "list"]):
            show_tasks()

        elif any(word in cmd for word in ["delete", "remove"]):
            show_tasks()
            speak("Say the number of the task to delete.")
            idx_text = listen()
            if idx_text and idx_text.isdigit():
                delete_task_by_index(int(idx_text) - 1)
            else:
                speak("Invalid input. Cancelled.")

        elif any(word in cmd for word in ["exit", "quit", "stop"]):
            speak("Goodbye! Exiting Smart Reminder.")
            print("👋 Exiting...")
            break

        else:
            speak("Command not recognized. Please try again.")

if __name__ == "__main__":
    main()