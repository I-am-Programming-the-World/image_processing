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
logging.basicConfig(filename='image_app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ToolTip Class for user guidance
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

# SectionFrame Class for consistent section styling
class SectionFrame(Frame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="#ecf0f1", bd=1, relief="solid")
        self.title_label = Label(self, text=title, font=("Arial", 12, "bold"), bg="#ecf0f1", fg="#2c3e50")
        self.title_label.pack(fill='x', padx=5, pady=5)
        self.content_frame = Frame(self, bg="#ecf0f1")
        self.content_frame.pack(fill='x', padx=5, pady=5)

# Main Application Class
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
        self.root.grid_columnconfigure(0, weight=1, minsize=300)  # Left panel with min width 300px
        self.root.grid_columnconfigure(1, weight=3)  # Workspace prioritized

        # Menu bar
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)
        help_menu = Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        settings_menu = Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

        # Title
        self.title_label = Label(self.root, text="Ultimate Image Processing Studio", font=("Arial", 22, "bold"), pady=15, bg="#ecf0f1", fg="#2980b9")
        self.title_label.grid(row=0, column=0, columnspan=2, sticky='ew')

        # Left panel with scrollable controls
        left_panel = Frame(self.root, bg="#ecf0f1")
        left_panel.grid(row=1, column=0, sticky='nsew')
        self.left_canvas = Canvas(left_panel, bg="#ecf0f1")
        self.left_canvas.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=self.left_canvas.yview)
        scrollbar.pack(side='right', fill='y')
        self.left_canvas.configure(yscrollcommand=scrollbar.set)
        left_frame = Frame(self.left_canvas, bg="#ecf0f1")
        self.left_canvas.create_window((0, 0), window=left_frame, anchor='nw')
        left_frame.bind("<Configure>", lambda e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all")))
        def _on_mousewheel(event):
            self.left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.left_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Setup sections
        self._setup_frames(left_frame)

        # Right canvas for image
        self._setup_canvas()

        # Status elements
        self._setup_status_elements()

        # Bind shortcuts
        self._bind_shortcuts()

        # Apply theme
        self.apply_theme()

        # Update color widgets state initially
        self.update_color_widgets_state()

        self.root.mainloop()

    def _setup_frames(self, left_frame):
        file_frame = SectionFrame(left_frame, "File Controls")
        self._setup_file_frame(file_frame.content_frame)
        file_frame.pack(fill='x', padx=5, pady=15)

        transform_frame = SectionFrame(left_frame, "Transformations")
        self._setup_transform_frame(transform_frame.content_frame)
        transform_frame.pack(fill='x', padx=5, pady=15)

        enhancement_frame = SectionFrame(left_frame, "Enhancements")
        self._setup_enhancement_frame(enhancement_frame.content_frame)
        enhancement_frame.pack(fill='x', padx=5, pady=15)

        color_frame = SectionFrame(left_frame, "Color Adjustments")
        self._setup_color_frame(color_frame.content_frame)
        color_frame.pack(fill='x', padx=5, pady=15)

        analysis_frame = SectionFrame(left_frame, "Analysis Tools")
        self._setup_analysis_frame(analysis_frame.content_frame)
        analysis_frame.pack(fill='x', padx=5, pady=15)

    def _setup_file_frame(self, frame):
        # Row 1: Load, Save, Undo, Redo, Reset
        file_row1 = Frame(frame, bg="#ecf0f1")
        file_row1.pack(fill='x', padx=5, pady=5)
        btn_load = Button(file_row1, text="Load", command=self.load_image, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_load.pack(side='left', padx=(15,5))
        self.add_hover_effect(btn_load)
        ToolTip(btn_load, "Load an image from your device")

        btn_save = Button(file_row1, text="Save", command=self.save_image, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_save.pack(side='left', padx=5)
        self.add_hover_effect(btn_save)
        ToolTip(btn_save, "Save the current image (Ctrl+S)")

        btn_undo = Button(file_row1, text="Undo", command=self.undo, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_undo.pack(side='left', padx=5)
        self.add_hover_effect(btn_undo)
        ToolTip(btn_undo, "Undo last action (Ctrl+Z)")

        btn_redo = Button(file_row1, text="Redo", command=self.redo, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_redo.pack(side='left', padx=5)
        self.add_hover_effect(btn_redo)
        ToolTip(btn_redo, "Redo last undone action (Ctrl+Y)")

        btn_reset = Button(file_row1, text="Reset", command=self.reset_app, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_reset.pack(side='left', padx=5)
        self.add_hover_effect(btn_reset)
        ToolTip(btn_reset, "Reset the application to initial state")

        # Row 2: Mode and Zoom
        file_row2 = Frame(frame, bg="#ecf0f1")
        file_row2.pack(fill='x', padx=5, pady=5)
        mode_label = Label(file_row2, text="Mode:", bg="#ecf0f1", fg="#2c3e50")
        mode_label.pack(side='left', padx=(15,5))
        self.color_mode_var = StringVar(value='grayscale')
        color_mode_combo = ttk.Combobox(file_row2, textvariable=self.color_mode_var, values=['grayscale', 'color'], state='readonly', width=10)
        color_mode_combo.pack(side='left', padx=5)
        color_mode_combo.bind("<<ComboboxSelected>>", self.switch_color_mode)
        ToolTip(color_mode_combo, "Switch between grayscale and color modes")

        btn_zoom_in = Button(file_row2, text="Zoom In", command=self.zoom_in, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_zoom_in.pack(side='left', padx=5)
        self.add_hover_effect(btn_zoom_in)
        ToolTip(btn_zoom_in, "Zoom in on the image")

        btn_zoom_out = Button(file_row2, text="Zoom Out", command=self.zoom_out, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_zoom_out.pack(side='left', padx=5)
        self.add_hover_effect(btn_zoom_out)
        ToolTip(btn_zoom_out, "Zoom out on the image")

    def _setup_transform_frame(self, frame):
        # Row 1: Halve Resolution, Negative, Rotate 90°, Flip Horizontal
        transform_row1 = Frame(frame, bg="#ecf0f1")
        transform_row1.pack(fill='x', padx=5, pady=5)
        btn_halve = Button(transform_row1, text="Halve Resolution", command=self.halve_resolution, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_halve.pack(side='left', padx=(15,5))
        self.add_hover_effect(btn_halve)
        btn_negative = Button(transform_row1, text="Negative", command=self.negative_transform, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_negative.pack(side='left', padx=5)
        self.add_hover_effect(btn_negative)
        btn_rotate_90 = Button(transform_row1, text="Rotate 90°", command=self.rotate_90, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_rotate_90.pack(side='left', padx=5)
        self.add_hover_effect(btn_rotate_90)
        btn_flip = Button(transform_row1, text="Flip Horizontal", command=self.flip_horizontal, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_flip.pack(side='left', padx=5)
        self.add_hover_effect(btn_flip)

        # Row 2: Log Transform
        log_row = Frame(frame, bg="#ecf0f1")
        log_row.pack(fill='x', padx=5, pady=5)
        log_label = Label(log_row, text="Log c:", bg="#ecf0f1", fg="#2c3e50")
        log_label.pack(side='left', padx=(15,5))
        self.log_c_entry = ttk.Entry(log_row, width=8)
        self.log_c_entry.insert(0, "1.0")
        self.log_c_entry.pack(side='left', padx=5)
        ToolTip(self.log_c_entry, "Scaling factor for log transform")
        btn_log = Button(log_row, text="Log", command=self.log_transform, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_log.pack(side='left', padx=5)
        self.add_hover_effect(btn_log)

        # Row 3: Gamma Transform
        gamma_row = Frame(frame, bg="#ecf0f1")
        gamma_row.pack(fill='x', padx=5, pady=5)
        gamma_label = Label(gamma_row, text="Gamma:", bg="#ecf0f1", fg="#2c3e50")
        gamma_label.pack(side='left', padx=(15,5))
        self.gamma_entry = ttk.Entry(gamma_row, width=8)
        self.gamma_entry.insert(0, "1.0")
        self.gamma_entry.pack(side='left', padx=5)
        ToolTip(self.gamma_entry, "Gamma value for power-law transform")
        c_label = Label(gamma_row, text="c:", bg="#ecf0f1", fg="#2c3e50")
        c_label.pack(side='left', padx=5)
        self.c_entry = ttk.Entry(gamma_row, width=8)
        self.c_entry.insert(0, "1.0")
        self.c_entry.pack(side='left', padx=5)
        ToolTip(self.c_entry, "Scaling factor for gamma transform")
        btn_gamma = Button(gamma_row, text="Gamma", command=self.gamma_transform, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_gamma.pack(side='left', padx=5)
        self.add_hover_effect(btn_gamma)

        # Row 4: Arbitrary Rotation
        rotate_row = Frame(frame, bg="#ecf0f1")
        rotate_row.pack(fill='x', padx=5, pady=5)
        angle_label = Label(rotate_row, text="Angle:", bg="#ecf0f1", fg="#2c3e50")
        angle_label.pack(side='left', padx=(15,5))
        self.rotate_angle_entry = ttk.Entry(rotate_row, width=8)
        self.rotate_angle_entry.insert(0, "0")
        self.rotate_angle_entry.pack(side='left', padx=5)
        ToolTip(self.rotate_angle_entry, "Rotation angle in degrees")
        btn_rotate_any = Button(rotate_row, text="Rotate", command=self.rotate_any, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_rotate_any.pack(side='left', padx=5)
        self.add_hover_effect(btn_rotate_any)

    def _setup_enhancement_frame(self, frame):
        # Row 1: Hist Equalize, Sharpen, Contrast Stretch, Gaussian Blur
        enhance_row1 = Frame(frame, bg="#ecf0f1")
        enhance_row1.pack(fill='x', padx=5, pady=5)
        btn_hist = Button(enhance_row1, text="Hist Equalize", command=self.histogram_equalization, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_hist.pack(side='left', padx=(15,5))
        self.add_hover_effect(btn_hist)
        btn_sharpen = Button(enhance_row1, text="Sharpen", command=self.sharpen_image, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_sharpen.pack(side='left', padx=5)
        self.add_hover_effect(btn_sharpen)
        btn_contrast = Button(enhance_row1, text="Contrast Stretch", command=self.contrast_stretch, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_contrast.pack(side='left', padx=5)
        self.add_hover_effect(btn_contrast)
        btn_gauss = Button(enhance_row1, text="Gaussian Blur", command=self.gaussian_blur, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_gauss.pack(side='left', padx=5)
        self.add_hover_effect(btn_gauss)

        # Row 2: Median Filter, Bilateral Filter
        enhance_row2 = Frame(frame, bg="#ecf0f1")
        enhance_row2.pack(fill='x', padx=5, pady=5)
        btn_median = Button(enhance_row2, text="Median Filter", command=self.median_filter, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_median.pack(side='left', padx=(15,5))
        self.add_hover_effect(btn_median)
        btn_bilateral = Button(enhance_row2, text="Bilateral Filter", command=self.bilateral_filter, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_bilateral.pack(side='left', padx=5)
        self.add_hover_effect(btn_bilateral)

        # Row 3: Filter Size
        filter_row = Frame(frame, bg="#ecf0f1")
        filter_row.pack(fill='x', padx=5, pady=5)
        filter_label = Label(filter_row, text="Filter Size:", bg="#ecf0f1", fg="#2c3e50")
        filter_label.pack(side='left', padx=(15,5))
        self.mask_size_entry = ttk.Entry(filter_row, width=8)
        self.mask_size_entry.insert(0, "3")
        self.mask_size_entry.pack(side='left', padx=5)
        ToolTip(self.mask_size_entry, "Size of the filter kernel (positive integer)")

    def _setup_color_frame(self, frame):
        # Row 1: Saturation
        saturation_row = Frame(frame, bg="#ecf0f1")
        saturation_row.pack(fill='x', padx=5, pady=5)
        saturation_label = Label(saturation_row, text="Saturation:", bg="#ecf0f1", fg="#2c3e50")
        saturation_label.pack(side='left', padx=(15,5))
        self.saturation_entry = ttk.Entry(saturation_row, width=8)
        self.saturation_entry.insert(0, "1.0")
        self.saturation_entry.pack(side='left', padx=5)
        ToolTip(self.saturation_entry, "Saturation factor (0.0 to 2.0)")

        # Row 2: Brightness
        brightness_row = Frame(frame, bg="#ecf0f1")
        brightness_row.pack(fill='x', padx=5, pady=5)
        brightness_label = Label(brightness_row, text="Brightness:", bg="#ecf0f1", fg="#2c3e50")
        brightness_label.pack(side='left', padx=(15,5))
        self.brightness_entry = ttk.Entry(brightness_row, width=8)
        self.brightness_entry.insert(0, "0")
        self.brightness_entry.pack(side='left', padx=5)
        ToolTip(self.brightness_entry, "Brightness offset (-255 to 255)")

        # Row 3: Apply Button
        color_apply_row = Frame(frame, bg="#ecf0f1")
        color_apply_row.pack(fill='x', padx=5, pady=5)
        self.color_apply_btn = Button(color_apply_row, text="Apply", command=self.adjust_color, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        self.color_apply_btn.pack(side='left', padx=(15,5))
        self.add_hover_effect(self.color_apply_btn)

    def _setup_analysis_frame(self, frame):
        # Row 1: Histogram, Gradient Mag, Edge Detection
        analysis_row1 = Frame(frame, bg="#ecf0f1")
        analysis_row1.pack(fill='x', padx=5, pady=5)
        btn_histogram = Button(analysis_row1, text="Histogram", command=self.show_histogram, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_histogram.pack(side='left', padx=(15,5))
        self.add_hover_effect(btn_histogram)
        btn_gradient = Button(analysis_row1, text="Gradient Mag", command=self.gradient_magnitude, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_gradient.pack(side='left', padx=5)
        self.add_hover_effect(btn_gradient)
        btn_edge = Button(analysis_row1, text="Edge Detection", command=self.edge_detection, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_edge.pack(side='left', padx=5)
        self.add_hover_effect(btn_edge)

        # Row 2: Stats, Batch Process, FFT
        analysis_row2 = Frame(frame, bg="#ecf0f1")
        analysis_row2.pack(fill='x', padx=5, pady=5)
        btn_stats = Button(analysis_row2, text="Stats", command=self.show_image_stats, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_stats.pack(side='left', padx=(15,5))
        self.add_hover_effect(btn_stats)
        btn_batch = Button(analysis_row2, text="Batch Process", command=self.batch_process, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_batch.pack(side='left', padx=5)
        self.add_hover_effect(btn_batch)
        btn_fft = Button(analysis_row2, text="FFT", command=self.show_fft, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_fft.pack(side='left', padx=5)
        self.add_hover_effect(btn_fft)

    def _setup_canvas(self):
        self.image_canvas = Canvas(self.root, bd=0, relief="flat", highlightthickness=0, bg="#ffffff")
        self.image_canvas.grid(row=1, column=1, sticky='nsew', padx=10, pady=5)
        self.image_canvas.bind("<Configure>", lambda event: self.update_image_display())
        self.image_canvas.bind("<Motion>", self.show_pixel_info)
        self.image_canvas.bind("<Button-1>", self.start_roi)
        self.image_canvas.bind("<B1-Motion>", self.update_roi)
        self.image_canvas.bind("<ButtonRelease-1>", self.end_roi)

    def _setup_status_elements(self):
        self.status_label = Label(self.root, text="Ready", font=("Arial", 10, "bold"), bd=1, relief="flat", anchor="w", padx=10, bg="#ecf0f1", fg="#2c3e50")
        self.status_label.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        self.pixel_info_label = Label(self.root, text="", font=("Arial", 10), bd=1, relief="flat", anchor="w", padx=10, bg="#ecf0f1", fg="#2c3e50")
        self.pixel_info_label.grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

    def _bind_shortcuts(self):
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-s>", lambda e: self.save_image())
        self.root.bind("<Control-o>", lambda e: self.load_image())

    def apply_theme(self):
        bg = "#ecf0f1"
        fg = "#2c3e50"
        self.root.configure(bg=bg)
        self.title_label.configure(bg=bg, fg="#2980b9")
        self.status_label.configure(bg=bg, fg=fg)
        self.pixel_info_label.configure(bg=bg, fg=fg)
        def set_widget_theme(widget):
            if isinstance(widget, Frame): widget.configure(bg=bg)
            elif isinstance(widget, Label): widget.configure(bg=bg, fg=fg)
            elif isinstance(widget, Canvas): widget.configure(bg="#ffffff")
            for child in widget.winfo_children(): set_widget_theme(child)
        for widget in self.root.winfo_children(): set_widget_theme(widget)

    def add_hover_effect(self, button):
        button.bind("<Enter>", lambda e: button.config(bg="#2980b9"))
        button.bind("<Leave>", lambda e: button.config(bg="#3498db"))

    def toggle_theme(self):
        messagebox.showinfo("Theme", "Theme switching is not yet implemented.")

    def show_user_guide(self):
        guide = (
            "Welcome to Ultimate Image Processing Studio!\n\n"
            "1. Load/Save: Ctrl+O to load, Ctrl+S to save.\n"
            "2. Transformations: Apply geometric/intensity changes.\n"
            "3. Enhancements: Improve quality with filters/adjustments.\n"
            "4. Color Adjustments: Modify saturation/brightness (color mode).\n"
            "5. Analysis: View histograms, stats, edges, FFT, etc.\n"
            "6. Undo/Redo: Ctrl+Z and Ctrl+Y.\n"
            "7. Zoom: Use zoom buttons to inspect details.\n"
            "8. ROI: Click and drag on the image to select a region.\n"
            "Hover for tooltips!"
        )
        messagebox.showinfo("User Guide", guide)

    def show_about(self):
        about = "Ultimate Image Processing Studio\nVersion 2.0\nDeveloped by @I_am_Programming_the_World\nMIT License"
        messagebox.showinfo("About", about)

    def load_image(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")])
            if not file_path:
                return
            self.original_image = cv2.cvtColor(cv2.imread(file_path, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            if self.original_image is None:
                raise ValueError("Invalid image file.")
            self.processed_image = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY) if self.color_mode == 'grayscale' else self.original_image.copy()
            self.history = [self.processed_image.copy()]
            self.future_history.clear()
            self.update_image_display()
            self.status_label.config(text="Image loaded")
            logging.info(f"Loaded image: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Load failed: {str(e)}")
            logging.error(f"Load failed: {str(e)}")

    def save_image(self):
        try:
            if self.processed_image is None:
                raise ValueError("No image to save.")
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")])
            if not file_path:
                return
            img = self.processed_image if self.color_mode == 'grayscale' else cv2.cvtColor(self.processed_image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(file_path, img)
            self.status_label.config(text=f"Saved to {os.path.basename(file_path)}")
            logging.info(f"Saved image: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {str(e)}")
            logging.error(f"Save failed: {str(e)}")

    def undo(self):
        if len(self.history) <= 1:
            messagebox.showinfo("Undo", "No more steps to undo!")
            return
        self.future_history.append(self.processed_image.copy())
        self.history.pop()
        self.processed_image = self.history[-1].copy()
        self.update_image_display()
        self.status_label.config(text="Undo successful")
        logging.info("Undo performed")

    def redo(self):
        if not self.future_history:
            messagebox.showinfo("Redo", "No more steps to redo!")
            return
        self.history.append(self.processed_image.copy())
        self.processed_image = self.future_history.pop()
        self.update_image_display()
        self.status_label.config(text="Redo successful")
        logging.info("Redo performed")

    def update_image_display(self):
        if self.processed_image is None:
            self.image_canvas.delete("all")
            self.image_canvas.create_text(self.image_canvas.winfo_width() // 2, self.image_canvas.winfo_height() // 2, text="No image loaded", fill="gray", font=("Arial", 14))
            return
        canvas_width, canvas_height = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()
        image_height, image_width = self.processed_image.shape[:2]
        display_width = int(image_width * self.zoom_factor)
        display_height = int(image_height * self.zoom_factor)
        img = Image.fromarray(self.processed_image).resize((display_width, display_height), Image.Resampling.LANCZOS)
        self.imgtk = ImageTk.PhotoImage(image=img)
        self.image_canvas.delete("all")
        self.image_canvas.create_image(canvas_width // 2, canvas_height // 2, anchor='center', image=self.imgtk)
        if self.selected_roi:
            x1, y1, x2, y2 = self.map_roi_to_canvas_coords()
            self.image_canvas.create_rectangle(x1, y1, x2, y2, outline="red")

    def save_to_history(self):
        self.future_history.clear()
        if len(self.history) >= self.history_limit:
            self.history.pop(0)
        self.history.append(self.processed_image.copy())

    def apply_to_image(self, func, *args, **kwargs):
        if self.processed_image is None:
            return
        try:
            if self.selected_roi:
                x1, y1, x2, y2 = self.map_roi_to_image_coords()
                roi = self.processed_image[y1:y2, x1:x2]
                self.processed_image[y1:y2, x1:x2] = func(roi, *args, **kwargs)
            else:
                self.processed_image = func(self.processed_image, *args, **kwargs)
            self.save_to_history()
            self.update_image_display()
        except Exception as e:
            messagebox.showerror("Error", f"Operation failed: {str(e)}")
            logging.error(f"Operation failed: {str(e)}")

    def halve_resolution(self):
        self.apply_to_image(lambda img: cv2.resize(img, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
        self.status_label.config(text="Resolution halved")

    def negative_transform(self):
        self.apply_to_image(lambda img: 255 - img)
        self.status_label.config(text="Negative transform applied")

    def rotate_90(self):
        self.apply_to_image(lambda img: cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE))
        self.status_label.config(text="Rotated 90° clockwise")

    def flip_horizontal(self):
        self.apply_to_image(cv2.flip, 1)
        self.status_label.config(text="Flipped horizontally")

    def log_transform(self):
        try:
            c = float(self.log_c_entry.get())
            if c <= 0:
                raise ValueError("'c' must be positive.")
            func = lambda img: np.uint8(np.clip(c * np.log1p(img), 0, 255)) if self.color_mode == 'grayscale' else \
                   np.stack([np.uint8(np.clip(c * np.log1p(img[:, :, i]), 0, 255)) for i in range(3)], axis=2)
            self.apply_to_image(func)
            self.status_label.config(text="Log transform applied")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def gamma_transform(self):
        try:
            gamma = float(self.gamma_entry.get())
            c = float(self.c_entry.get())
            if gamma <= 0 or c <= 0:
                raise ValueError("'gamma' and 'c' must be positive.")
            func = lambda img: np.uint8(np.clip(c * np.power(img / 255.0, gamma) * 255, 0, 255)) if self.color_mode == 'grayscale' else \
                   np.stack([np.uint8(np.clip(c * np.power(img[:, :, i] / 255.0, gamma) * 255, 0, 255)) for i in range(3)], axis=2)
            self.apply_to_image(func)
            self.status_label.config(text="Gamma transform applied")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def histogram_equalization(self):
        if self.processed_image is None:
            return
        if self.color_mode == 'grayscale':
            self.processed_image = cv2.equalizeHist(self.processed_image)
        else:
            ycrcb = cv2.cvtColor(self.processed_image, cv2.COLOR_RGB2YCrCb)
            ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
            self.processed_image = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2RGB)
        self.save_to_history()
        self.update_image_display()
        self.status_label.config(text="Histogram equalization applied")

    def sharpen_image(self):
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        self.apply_to_image(cv2.filter2D, -1, kernel)
        self.status_label.config(text="Image sharpened")

    def contrast_stretch(self):
        def stretch(img):
            if self.color_mode == 'grayscale':
                min_val, max_val = np.min(img), np.max(img)
                return np.uint8(255 * (img - min_val) / (max_val - min_val)) if max_val > min_val else img
            else:
                for i in range(3):
                    min_val, max_val = np.min(img[:, :, i]), np.max(img[:, :, i])
                    if max_val > min_val:
                        img[:, :, i] = np.uint8(255 * (img[:, :, i] - min_val) / (max_val - min_val))
                return img
        self.apply_to_image(stretch)
        self.status_label.config(text="Contrast stretched")

    def gaussian_blur(self):
        try:
            n = int(self.mask_size_entry.get())
            if n <= 0 or n % 2 == 0:
                raise ValueError("Filter size must be a positive odd integer.")
            self.apply_to_image(cv2.GaussianBlur, (n, n), 0)
            self.status_label.config(text=f"Gaussian blur applied with filter size {n}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def median_filter(self):
        try:
            n = int(self.mask_size_entry.get())
            if n <= 0 or n % 2 == 0:
                raise ValueError("Filter size must be a positive odd integer.")
            self.apply_to_image(cv2.medianBlur, n)
            self.status_label.config(text=f"Median filter applied with filter size {n}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def bilateral_filter(self):
        try:
            n = int(self.mask_size_entry.get())
            if n <= 0:
                raise ValueError("Filter size must be a positive integer.")
            self.apply_to_image(cv2.bilateralFilter, n, 75, 75)
            self.status_label.config(text=f"Bilateral filter applied with filter size {n}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def adjust_color(self):
        if self.color_mode != 'color' or self.processed_image is None:
            messagebox.showerror("Error", "Color adjustments are only available in color mode.")
            return
        try:
            sat = float(self.saturation_entry.get())
            bright = int(self.brightness_entry.get())
            if not (0 <= sat <= 2) or not (-255 <= bright <= 255):
                raise ValueError("Saturation must be 0.0-2.0, brightness -255 to 255.")
            hsv = cv2.cvtColor(self.processed_image, cv2.COLOR_RGB2HSV)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat, 0, 255)
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] + bright, 0, 255)
            self.processed_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            self.save_to_history()
            self.update_image_display()
            self.status_label.config(text="Color adjusted")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_histogram(self):
        if self.processed_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        hist_window = Toplevel(self.root)
        hist_window.title("Histogram")
        fig = plt.Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        if self.color_mode == 'grayscale':
            ax.hist(self.processed_image.ravel(), bins=256, color='gray')
            ax.set_title('Grayscale Histogram')
        else:
            colors = ['r', 'g', 'b']
            for i, color in enumerate(colors):
                ax.hist(self.processed_image[:, :, i].ravel(), bins=256, color=color, alpha=0.5, label=f'{color.upper()} Channel')
            ax.legend()
            ax.set_title('Color Histogram')
        canvas = FigureCanvasTkAgg(fig, master=hist_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def gradient_magnitude(self):
        if self.processed_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        if self.color_mode == 'grayscale':
            sobelx = cv2.Sobel(self.processed_image, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(self.processed_image, cv2.CV_64F, 0, 1, ksize=3)
            mag = np.sqrt(sobelx**2 + sobely**2)
            self.processed_image = np.uint8(255 * mag / np.max(mag))
        else:
            mags = []
            for i in range(3):
                sobelx = cv2.Sobel(self.processed_image[:, :, i], cv2.CV_64F, 1, 0, ksize=3)
                sobely = cv2.Sobel(self.processed_image[:, :, i], cv2.CV_64F, 0, 1, ksize=3)
                mag = np.sqrt(sobelx**2 + sobely**2)
                mags.append(np.uint8(255 * mag / np.max(mag)))
            self.processed_image = np.stack(mags, axis=2)
        self.save_to_history()
        self.update_image_display()
        self.status_label.config(text="Gradient magnitude computed")

    def edge_detection(self):
        if self.processed_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        if self.color_mode == 'grayscale':
            self.processed_image = cv2.Canny(self.processed_image, 100, 200)
        else:
            gray = cv2.cvtColor(self.processed_image, cv2.COLOR_RGB2GRAY)
            self.processed_image = cv2.cvtColor(cv2.Canny(gray, 100, 200), cv2.COLOR_GRAY2RGB)
        self.save_to_history()
        self.update_image_display()
        self.status_label.config(text="Edge detection applied")

    def show_image_stats(self):
        if self.processed_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        stats = ""
        if self.color_mode == 'grayscale':
            data = self.processed_image.ravel()
            stats = f"Mean: {np.mean(data):.2f}\nStd Dev: {np.std(data):.2f}\nMin: {np.min(data)}\nMax: {np.max(data)}\nSkewness: {skew(data):.2f}\nKurtosis: {kurtosis(data):.2f}"
        else:
            colors = ['Red', 'Green', 'Blue']
            for i, color in enumerate(colors):
                data = self.processed_image[:, :, i].ravel()
                stats += f"{color} - Mean: {np.mean(data):.2f}, Std Dev: {np.std(data):.2f}, Min: {np.min(data)}, Max: {np.max(data)}, Skew: {skew(data):.2f}, Kurt: {kurtosis(data):.2f}\n"
        messagebox.showinfo("Image Statistics", stats)

    def show_fft(self):
        if self.processed_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        fft_window = Toplevel(self.root)
        fft_window.title("Frequency Spectrum")
        fig = plt.figure(figsize=(12, 4))
        if self.color_mode == 'color':
            axes = fig.subplots(1, 3)
            colors = ['Red', 'Green', 'Blue']
            for i, ax in enumerate(axes):
                f = fftshift(fft2(self.processed_image[:, :, i]))
                magnitude_spectrum = 20 * np.log(np.abs(f) + 1)
                ax.imshow(magnitude_spectrum, cmap='gray')
                ax.set_title(f'{colors[i]} Channel')
            plt.tight_layout()
        else:
            f = fftshift(fft2(self.processed_image))
            magnitude_spectrum = 20 * np.log(np.abs(f) + 1)
            plt.imshow(magnitude_spectrum, cmap='gray')
            plt.title('Grayscale')
        canvas = FigureCanvasTkAgg(fig, master=fft_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def batch_process(self):
        files = filedialog.askopenfilenames(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if not files:
            return
        operations = [
            ("Negative Transform", self.negative_transform),
            ("Histogram Equalization", self.histogram_equalization),
            ("Gaussian Blur", self.gaussian_blur),
            ("Median Filter", self.median_filter)
        ]
        selected_ops = []
        dialog = Toplevel(self.root)
        dialog.title("Select Operations")
        for op_name, _ in operations:
            var = StringVar(value="0")
            chk = ttk.Checkbutton(dialog, text=op_name, variable=var, onvalue="1", offvalue="0")
            chk.pack(anchor='w', padx=5, pady=5)
            selected_ops.append((op_name, var))
        ttk.Button(dialog, text="Process", command=dialog.destroy).pack(pady=10)
        dialog.wait_window()
        selected_names = [name for name, var in selected_ops if var.get() == "1"]
        if not selected_names:
            return

        for i, file in enumerate(files):
            img = cv2.imread(file, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            for op_name in selected_names:
                for name, func in operations:
                    if name == op_name:
                        self.processed_image = img
                        func()
                        img = self.processed_image
                        break
            base, ext = os.path.splitext(file)
            output_path = f"{base}_processed{ext}"
            counter = 1
            while os.path.exists(output_path):
                output_path = f"{base}_processed_{counter}{ext}"
                counter += 1
            cv2.imwrite(output_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        messagebox.showinfo("Batch Process", f"Processed {len(files)} images.")
        self.status_label.config(text="Batch process completed")

    def switch_color_mode(self, event):
        new_mode = self.color_mode_var.get()
        if new_mode == self.color_mode or self.original_image is None:
            return
        if messagebox.askyesno("Confirm Mode Switch", "Switching color mode will reset the history. Proceed?"):
            self.color_mode = new_mode
            self.processed_image = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY) if new_mode == 'grayscale' else self.original_image.copy()
            self.history = [self.processed_image.copy()]
            self.future_history.clear()
            self.update_image_display()
            self.status_label.config(text=f"Switched to {self.color_mode} mode")
            self.update_color_widgets_state()
        else:
            self.color_mode_var.set(self.color_mode)

    def update_color_widgets_state(self):
        state = 'normal' if self.color_mode == 'color' else 'disabled'
        self.saturation_entry.config(state=state)
        self.brightness_entry.config(state=state)
        self.color_apply_btn.config(state=state)

    def reset_app(self):
        self.original_image = None
        self.processed_image = None
        self.history.clear()
        self.future_history.clear()
        self.selected_roi = None
        self.zoom_factor = 1.0
        self.update_image_display()
        self.status_label.config(text="Application reset")

    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.update_image_display()
        self.status_label.config(text=f"Zoomed in (factor: {self.zoom_factor:.2f})")

    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.update_image_display()
        self.status_label.config(text=f"Zoomed out (factor: {self.zoom_factor:.2f})")

    def show_pixel_info(self, event):
        if self.processed_image is None:
            self.pixel_info_label.config(text="")
            return
        canvas_w, canvas_h = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()
        img_h, img_w = self.processed_image.shape[:2]
        display_w = int(img_w * self.zoom_factor)
        display_h = int(img_h * self.zoom_factor)
        x = (event.x - (canvas_w - display_w) // 2) / self.zoom_factor
        y = (event.y - (canvas_h - display_h) // 2) / self.zoom_factor
        if 0 <= x < img_w and 0 <= y < img_h:
            pixel = self.processed_image[int(y), int(x)]
            text = f"({int(x)}, {int(y)}): {pixel}" if self.color_mode == 'color' else f"({int(x)}, {int(y)}): {pixel}"
            self.pixel_info_label.config(text=text)
        else:
            self.pixel_info_label.config(text="")

    def start_roi(self, event):
        self.roi_start = (event.x, event.y)
        self.roi_rect = None

    def update_roi(self, event):
        if self.roi_rect:
            self.image_canvas.delete(self.roi_rect)
        self.roi_rect = self.image_canvas.create_rectangle(self.roi_start[0], self.roi_start[1], event.x, event.y, outline="red")

    def end_roi(self, event):
        self.selected_roi = (self.roi_start[0], self.roi_start[1], event.x, event.y)
        self.status_label.config(text="ROI selected")
        self.update_image_display()

    def map_roi_to_image_coords(self):
        if not self.selected_roi:
            return (0, 0, self.processed_image.shape[1], self.processed_image.shape[0])
        x1, y1, x2, y2 = self.selected_roi
        canvas_w, canvas_h = self.image_canvas.winfo_width(), self.image_canvas.winfo_height()
        img_h, img_w = self.processed_image.shape[:2]
        display_w = int(img_w * self.zoom_factor)
        display_h = int(img_h * self.zoom_factor)
        offset_x = (canvas_w - display_w) // 2
        offset_y = (canvas_h - display_h) // 2
        img_x1 = int((x1 - offset_x) / self.zoom_factor)
        img_y1 = int((y1 - offset_y) / self.zoom_factor)
        img_x2 = int((x2 - offset_x) / self.zoom_factor)
        img_y2 = int((y2 - offset_y) / self.zoom_factor)
        img_x1, img_x2 = max(0, min(img_x1, img_x2)), min(img_w, max(img_x1, img_x2))
        img_y1, img_y2 = max(0, min(img_y1, img_y2)), min(img_h, max(img_y1, img_y2))
        return (img_x1, img_y1, img_x2, img_y2)

    def map_roi_to_canvas_coords(self):
        if not self.selected_roi:
            return (0, 0, self.image_canvas.winfo_width(), self.image_canvas.winfo_height())
        x1, y1, x2, y2 = self.selected_roi
        return (x1, y1, x2, y2)

    def rotate_any(self):
        try:
            angle = float(self.rotate_angle_entry.get())
            h, w = self.processed_image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            self.apply_to_image(cv2.warpAffine, M, (w, h))
            self.status_label.config(text=f"Rotated by {angle}°")
        except ValueError:
            messagebox.showerror("Error", "Invalid angle.")

if __name__ == "__main__":
    ImageProcessingApp()