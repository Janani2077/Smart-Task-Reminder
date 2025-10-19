import threading
import time
import datetime
import json
import os
from flask import Flask, render_template_string, request, jsonify
import pyttsx3
import speech_recognition as sr
from win10toast import ToastNotifier
import re

app = Flask(__name__)
toaster = ToastNotifier()
tasks_file = "tasks.json"

# ------------------ Load existing tasks ------------------
if os.path.exists(tasks_file):
    with open(tasks_file, "r") as f:
        tasks = json.load(f)
else:
    tasks = []

# ------------------ Utility Functions ------------------
def speak(text):
    """Speak text asynchronously."""
    def _speak():
        try:
            e = pyttsx3.init()
            e.setProperty("rate", 180)
            e.say(text)
            e.runAndWait()
            e.stop()
        except Exception as ex:
            print("Speech error:", ex)
    threading.Thread(target=_speak, daemon=True).start()

def listen():
    """Listen to user voice and return recognized text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Listening...")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        print("✅ Recognized:", text)
        return text.lower()
    except Exception as e:
        print("❌ Speech not recognized:", e)
        return ""

def parse_time(text):
    """Parse natural language time phrases like '5 pm', '18 30', '6:45', etc."""
    text = text.strip().lower()
    match = re.search(r"(\d{1,2})([:\s]?)(\d{0,2})(\s*)(am|pm)?", text)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(3)) if match.group(3) else 0
    ampm = match.group(5)
    if ampm == "pm" and hour < 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0
    if 0 <= hour < 24 and 0 <= minute < 60:
        return f"{hour:02d}:{minute:02d}"
    return None

def save_tasks():
    with open(tasks_file, "w") as f:
        json.dump(tasks, f, indent=4)

def check_reminders():
    """Constantly checks for due reminders."""
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        for t in tasks[:]:
            if t["time"] == now:
                toaster.show_toast("⏰ Reminder", t["task"], duration=10, threaded=True)
                speak(f"Reminder! {t['task']}")
                tasks.remove(t)
                save_tasks()
        time.sleep(60)

# ------------------ HTML Template ------------------
html = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Task Reminder</title>
    <style>
        html, body { height:100%; width:100%; margin:0; padding:0; font-family:'Roboto Mono', monospace; background:#1e1e2f; color:#fff; }
        .container { display:grid; grid-template-columns:1fr 2fr; gap:20px; max-width:1200px; margin:0 auto; height:100vh; padding:30px; box-sizing:border-box; }
        .panel { background:#2c2f3a; padding:25px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.5); display:flex; flex-direction:column; }
        h1 { margin-top:0; text-align:center; color:#0abde3; font-size:2em; }
        h2 { color:#0abde3; margin-bottom:10px; }
        input, button { width:100%; padding:12px; margin:8px 0; border-radius:6px; border:1px solid #0abde3; background:#1e1e2f; color:#fff; font-family:'Roboto Mono', monospace; font-size:1em; }
        button:hover { background:#0abde3; color:#000; cursor:pointer; }
        .voice-btn { background-color:#10ac84; border:none; }
        .delete-btn { background-color:#ff6b6b; border:none; }
        #taskList { display:none; overflow-y:auto; flex-grow:1; margin-top:10px; }
        .task { background:#3a3d4e; padding:15px; margin:8px 0; border-left:4px solid #10ac84; border-radius:6px; display:flex; justify-content:space-between; align-items:center; transition: all 0.3s ease; }
        .task:hover { transform:scale(1.02); box-shadow:0 4px 12px rgba(0,0,0,0.4); }
        .task .time { color:#ccc; font-size:0.9em; }
        .listening { text-align:center; color:#10ac84; font-weight:bold; animation:pulse 1s infinite; }
        @keyframes pulse { 0% {opacity:0.4;} 50% {opacity:1;} 100% {opacity:0.4;} }
        #status { text-align:center; font-size:16px; margin-top:10px; color:#ccc; }
        #showBtn { background-color:#0abde3; color:#000; margin-bottom:10px; font-weight:bold; }
    </style>
</head>
<body>
    <div class="container">

        <!-- Left Panel -->
        <div class="panel">
            <h1>🧠 Smart Reminder</h1>
            <form id="taskForm">
                <input type="text" name="task" placeholder="Enter your task" required>
                <input type="time" name="time" required>
                <button type="submit">Add Task</button>
            </form>
            <button class="voice-btn" id="voiceBtn">🎤 Add Task via Voice</button>
            <div id="status"></div>
            <button id="showBtn">📋 Show Tasks</button>
        </div>

        <!-- Right Panel -->
        <div class="panel" id="taskList">
            <h2>Scheduled Tasks</h2>
            <div id="tasksContainer">
                {% for t in tasks %}
                    <div class="task" data-index="{{ loop.index0 }}">
                        <div><b>{{ loop.index }}. {{ t.task }}</b><br><span class="time">{{ t.time }}</span></div>
                        <button class="delete-btn" onclick="deleteTask({{ loop.index0 }})">Delete</button>
                    </div>
                {% endfor %}
            </div>
        </div>

    </div>

<script>
const voiceBtn = document.getElementById("voiceBtn");
const statusDiv = document.getElementById("status");
const taskList = document.getElementById("taskList");
const showBtn = document.getElementById("showBtn");
const taskForm = document.getElementById("taskForm");

// Voice input
voiceBtn.addEventListener("click", async () => {
    statusDiv.innerHTML = '<div class="listening">🎙️ Listening...</div>';
    voiceBtn.disabled = true;
    const response = await fetch("/voice", { method:"POST" });
    const result = await response.json();
    if(result.success){
        statusDiv.innerHTML = "✅ Task added: "+result.task+" at "+result.time;
        addTaskCard(result.task, result.time, result.index);
    } else {
        statusDiv.innerHTML = "❌ "+result.message;
    }
    voiceBtn.disabled = false;
});

// Show/Hide tasks
showBtn.addEventListener("click", () => {
    if(taskList.style.display==="none"){ taskList.style.display="flex"; showBtn.innerText="🔽 Hide Tasks"; }
    else { taskList.style.display="none"; showBtn.innerText="📋 Show Tasks"; }
});

// AJAX delete
function deleteTask(index){
    fetch(`/delete/${index}`, { method:"POST" })
    .then(res=>res.json())
    .then(data=>{
        if(data.success){
            const card = document.querySelector(`.task[data-index='${index}']`);
            if(card) card.remove();
        }
    });
}

// AJAX add task via form
taskForm.addEventListener("submit", async (e)=>{
    e.preventDefault();
    const formData = new FormData(taskForm);
    const response = await fetch("/add_ajax", { method:"POST", body:formData });
    const result = await response.json();
    if(result.success){
        addTaskCard(result.task, result.time, result.index);
        taskForm.reset();
    }
});

// Add a task card dynamically
function addTaskCard(task, time, index){
    const container = document.getElementById("tasksContainer");
    const card = document.createElement("div");
    card.className = "task";
    card.setAttribute("data-index", index);
    card.innerHTML = `<div><b>${task}</b><br><span class="time">${time}</span></div>
                      <button class="delete-btn" onclick="deleteTask(${index})">Delete</button>`;
    container.appendChild(card);
    if(taskList.style.display==="none") { taskList.style.display="flex"; showBtn.innerText="🔽 Hide Tasks"; }
}
</script>
</body>
</html>
"""

# ------------------ Flask Routes ------------------
@app.route("/")
def index():
    return render_template_string(html, tasks=tasks)

@app.route("/add_ajax", methods=["POST"])
def add_ajax():
    task_text = request.form["task"]
    time_str = request.form["time"]
    tasks.append({"task":task_text, "time":time_str})
    save_tasks()
    toaster.show_toast("✅ Task Added", f"{task_text} at {time_str}", duration=5, threaded=True)
    speak(f"Task added: {task_text} at {time_str}")
    return jsonify(success=True, task=task_text, time=time_str, index=len(tasks)-1)

@app.route("/delete/<int:index>", methods=["POST"])
def delete_task(index):
    if 0<=index<len(tasks):
        removed = tasks.pop(index)
        save_tasks()
        toaster.show_toast("🗑️ Deleted", removed["task"], duration=5, threaded=True)
        speak(f"Deleted {removed['task']}")
        return jsonify(success=True)
    return jsonify(success=False)

@app.route("/voice", methods=["POST"])
def voice():
    try:
        speak("What task would you like to add?")
        task_text = listen()
        if not task_text:
            return jsonify(success=False, message="Task not understood")
        speak("At what time should I remind you?")
        time_text = listen()
        time_str = parse_time(time_text)
        if not time_str:
            now = datetime.datetime.now() + datetime.timedelta(minutes=1)
            time_str = now.strftime("%H:%M")
        tasks.append({"task":task_text, "time":time_str})
        save_tasks()
        toaster.show_toast("✅ Task Added (Voice)", f"{task_text} at {time_str}", duration=5, threaded=True)
        speak(f"Task added: {task_text} at {time_str}")
        return jsonify(success=True, task=task_text, time=time_str, index=len(tasks)-1)
    except Exception as e:
        print("Voice error:", e)
        return jsonify(success=False, message="Voice input failed.")

# ------------------ Run ------------------
if __name__=="__main__":
    threading.Thread(target=check_reminders, daemon=True).start()
    speak("Smart Task Reminder web version started successfully.")
    print("✅ Running at http://127.0.0.1:5000")
    app.run(debug=False)
