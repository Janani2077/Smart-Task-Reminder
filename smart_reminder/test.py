from win10toast import ToastNotifier

toaster = ToastNotifier()
toaster.show_toast(
    "🔔 Test Reminder",
    "This is a real Windows popup!",
    duration=10,
    threaded=True
)

print("Popup sent — check the bottom right corner of your screen!")
