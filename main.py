import os.path
import tkinter as tk
from tkinter import simpledialog, ttk
from PIL import ImageGrab, ImageTk
import time
import datetime
import threading


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Screenshot App")

        self.rect = None
        self.start_x = None
        self.start_y = None
        self.region_selected = False

        self.select_region_button = ttk.Button(root, text="Select Region", command=self.select_region)
        self.select_region_button.pack(pady=10)

        self.freq_label = ttk.Label(root, text="Frequency:")
        self.freq_label.pack(pady=10)
        self.freq_entry = ttk.Entry(root)
        self.freq_entry.pack(pady=10)
        self.freq_entry.insert(0, "5")

        self.unit_combobox = ttk.Combobox(root, values=["seconds", "minutes", "hours"])
        self.unit_combobox.pack(pady=10)
        self.unit_combobox.set("seconds")

        self.start_button = ttk.Button(root, text="Start", command=self.start_screenshot)
        self.start_button.pack(pady=10)
        self.stop_button = ttk.Button(root, text="Stop", command=self.stop_screenshot)
        self.stop_button.pack(pady=10)

        self.countdown_var = tk.StringVar()
        self.countdown_var.set("Next screenshot in: --")
        self.countdown_label = ttk.Label(root, textvariable=self.countdown_var)
        self.countdown_label.pack(pady=10)

        self.screenshot_thread = None
        self.is_running = False

    def select_region(self):
        self.region_win = tk.Toplevel(self.root)
        self.region_win.attributes('-fullscreen', True, '-alpha', 0.5)
        self.canvas = tk.Canvas(self.region_win, cursor="cross", bg='grey75')
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

        # Setting default values for end_x and end_y
        self.end_x = self.start_x
        self.end_y = self.start_y

        if not self.rect:
            self.rect = None

    def on_drag(self, event):
        if self.rect:
            self.canvas.delete(self.rect)

        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)

        # Sort the coordinates to allow dragging in any direction
        top_left_x = min(self.start_x, self.end_x)
        top_left_y = min(self.start_y, self.end_y)
        bottom_right_x = max(self.start_x, self.end_x)
        bottom_right_y = max(self.start_y, self.end_y)

        self.rect = self.canvas.create_rectangle(top_left_x, top_left_y, bottom_right_x, bottom_right_y, outline='red')

    def on_release(self, event):
        self.region_selected = True
        self.region_win.destroy()

        # Ensure we capture using sorted coordinates
        top_left_x = min(self.start_x, self.end_x)
        top_left_y = min(self.start_y, self.end_y)
        bottom_right_x = max(self.start_x, self.end_x)
        bottom_right_y = max(self.start_y, self.end_y)

        bbox = (top_left_x, top_left_y, bottom_right_x, bottom_right_y)
        screenshot = ImageGrab.grab(bbox)

        # Convert to thumbnail and display in main window
        screenshot.thumbnail((150, 150))
        self.thumbnail_image = ImageTk.PhotoImage(screenshot)

        if hasattr(self, 'thumbnail_label'):
            self.thumbnail_label.destroy()

        self.thumbnail_label = ttk.Label(self.root, image=self.thumbnail_image)
        self.thumbnail_label.pack(pady=10)

    def start_screenshot(self):
        if not self.region_selected:
            print("Please select a region first!")
            return

        self.is_running = True
        freq = float(self.freq_entry.get())
        unit = self.unit_combobox.get()

        if unit == "minutes":
            freq *= 60
        elif unit == "hours":
            freq *= 3600

        if not self.screenshot_thread:
            self.screenshot_thread = threading.Thread(target=self.take_screenshot, args=(freq,))
            self.screenshot_thread.start()

    def take_screenshot(self, freq):
        count = 0
        if not os.path.exists("out"):
            os.makedirs("out")
        while self.is_running:
            self.update_countdown(freq)
            count += 1
            bbox = (self.start_x, self.start_y, self.end_x, self.end_y)
            screenshot = ImageGrab.grab(bbox)
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot.save(f"out/{count}_{current_time}.png", "PNG")
            self.countdown_var.set(f"Next screenshot in: --")
            time.sleep(freq)

    def stop_screenshot(self):
        self.is_running = False
        self.screenshot_thread = None
        self.countdown_var.set("Next screenshot in: --")

    def update_countdown(self, freq):
        if not self.is_running:
            return

        total_seconds = int(freq)
        hours = total_seconds // 3600
        total_seconds %= 3600
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        while hours > 0 or minutes > 0 or seconds > 0:
            if not self.is_running:
                break

            # Update countdown label
            self.countdown_var.set(f"Next screenshot in: {hours:02}:{minutes:02}:{seconds:02}")

            # Decrement the countdown
            time.sleep(1)
            seconds -= 1

            if seconds < 0:
                seconds = 59
                minutes -= 1
                if minutes < 0:
                    minutes = 59
                    hours -= 1


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
