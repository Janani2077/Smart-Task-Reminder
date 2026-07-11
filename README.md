# Smart-Task-Reminder# 🎯 Smart Task Reminder

A Python-based **Smart Task Reminder** application that allows users to create and manage reminders efficiently. The application supports voice-enabled interactions and automatically alerts users when a task is due.

---

## 📖 Overview

Smart Task Reminder is designed to help users organize their daily tasks without missing important events. It combines task scheduling with voice interaction to provide a simple and user-friendly reminder system.

---

## ✨ Features

- 📝 Add new reminders
- 📋 View saved tasks
- ⏰ Automatic reminder notifications
- 🎤 Voice-enabled reminder support
- 💾 Stores tasks in JSON format
- ⚡ Lightweight and easy to use

---

## 🛠️ Technologies Used

- Python 3
- SpeechRecognition
- pyttsx3 (Text-to-Speech)
- JSON
- datetime
- threading
- Webbrowser module

---

## 📁 Project Structure

```
SMART-TASK-REMINDER/
│
├── smart_reminder.py         # Main reminder application
├── smart_remider_web.py      # Web/voice functionality
├── tasks.json                # Stores reminder data
├── test.py                   # Testing file
└── README.md
```

---

## 🚀 Getting Started

### Clone the Repository

```bash
git clone https://github.com/your-username/SMART-TASK-REMINDER.git
```

### Navigate to the Project

```bash
cd SMART-TASK-REMINDER
```

### Install Required Libraries

```bash
pip install SpeechRecognition pyttsx3
```

If your project also uses other libraries, install them as required.

### Run the Application

```bash
python smart_reminder.py
```

---

## 💡 How It Works

1. Start the application.
2. Add a task with its reminder time.
3. The task is saved in `tasks.json`.
4. The application continuously checks pending reminders.
5. When the scheduled time arrives, it notifies the user using voice and/or notifications.

---

## 📂 Data Storage

All reminders are stored in:

```
tasks.json
```

This makes the application lightweight and easy to manage without requiring a database.

---

## 🔮 Future Enhancements

- 📅 Google Calendar Integration
- 📧 Email Notifications
- 📱 Android Application
- ☁️ Cloud Storage
- 🤖 AI-based Smart Reminder Suggestions
- 🌙 Dark Mode
- 🌍 Multi-language Support

---

## 👩‍💻 Author

**Janani P**

Computer Science Engineering Student

Interested in AI, Machine Learning, and Software Development.

---

## ⭐ Support

If you like this project, consider giving it a **⭐ Star** on GitHub.

It motivates me to build more useful projects.