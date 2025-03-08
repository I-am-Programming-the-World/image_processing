import cv2
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog, Button, Label, Frame, Canvas, messagebox, ttk, Menu, PhotoImage, Toplevel, StringVar
from PIL import Image, ImageTk
from scipy.fft import fft2, fftshift
from scipy.stats import skew, kurtosis
import logging
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Logging setup
logging.basicConfig(filename='image_app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x, y = self.widget.winfo_pointerxy()
        self.tooltip = Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x + 10}+{y + 10}")
        label = Label(self.tooltip, text=self.text, bg="#ffffe0", fg="black", relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class SectionFrame(Frame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="#ecf0f1", bd=1, relief="solid")
        self.title_label = Label(self, text=title, font=("Arial", 12, "bold"), bg="#ecf0f1", fg="#2c3e50")
        self.title_label.pack(fill='x', padx=5, pady=5)
        self.content_frame = Frame(self, bg="#ecf0f1")
        self.content_frame.pack(fill='x', padx=5, pady=5)

class ImageProcessingApp:
    def __init__(self):
        self.original_image = None
        self.processed_image = None
        self.history = []
        self.future_history = []
        self.history_limit = 50
        self.color_mode = 'grayscale'
        self.selected_roi = None
        self.zoom_factor = 1.0
        self.setup_gui()

    def setup_gui(self):
        self.root = Tk()
        self.root.title("Ultimate Image Processing Studio")
        self.root.geometry("1200x1000")
        self.root.resizable(True, True)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1, minsize=300)
        self.root.grid_columnconfigure(1, weight=3)import cv2
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog, Button, Label, Frame, Canvas, messagebox, ttk, Menu, PhotoImage, Toplevel, StringVar
from PIL import Image, ImageTk
from scipy.fft import fft2, fftshift
from scipy.stats import skew, kurtosis
import logging
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Logging setup
logging.basicConfig(
    filename='image_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

