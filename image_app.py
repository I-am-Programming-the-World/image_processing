import cv2import numpy as npimport matplotlib.pyplot as pltfrom tkinter import Tk, filedialog, Button, Label, Frame, Canvas, messagebox, ttk, Menu, PhotoImage, Toplevel, StringVarfrom PIL import Image, ImageTkfrom scipy.fft import fft2, fftshiftfrom scipy.stats import skew, kurtosisimport loggingimport osfrom matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

