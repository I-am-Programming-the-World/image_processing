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
        self.setup_gui()

    def setup_gui(self):
        self.root = Tk()
        self.root.title("Ultimate Image Processing Studio")
        self.root.geometry("1200x1000")
        self.root.resizable(True, True)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=4)
        self.root.grid_columnconfigure(1, weight=2)

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
        btn_load = Button(frame, text="Load", command=self.load_image, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_load.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_load)
        ToolTip(btn_load, "Load an image from your device")

        btn_save = Button(frame, text="Save", command=self.save_image, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_save.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_save)
        ToolTip(btn_save, "Save the current image (Ctrl+S)")

        btn_undo = Button(frame, text="Undo", command=self.undo, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_undo.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_undo)
        ToolTip(btn_undo, "Undo last action (Ctrl+Z)")

        btn_redo = Button(frame, text="Redo", command=self.redo, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_redo.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_redo)
        ToolTip(btn_redo, "Redo last undone action (Ctrl+Y)")

        btn_reset = Button(frame, text="Reset", command=self.reset_app, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_reset.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_reset)
        ToolTip(btn_reset, "Reset the application to initial state")

        btn_clear_roi = Button(frame, text="Clear ROI", command=self.clear_roi, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_clear_roi.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_clear_roi)
        ToolTip(btn_clear_roi, "Clear the current ROI selection")

        self.color_mode_var = StringVar(value='grayscale')
        color_mode_combo = ttk.Combobox(frame, textvariable=self.color_mode_var, values=['grayscale', 'color'], state='readonly', width=10)
        color_mode_combo.pack(side='left', padx=5, pady=5)
        color_mode_combo.bind("<<ComboboxSelected>>", self.switch_color_mode)
        ToolTip(color_mode_combo, "Switch between grayscale and color modes")

    def _setup_transform_frame(self, frame):
        button_frame = Frame(frame, bg="#ecf0f1")
        button_frame.pack(fill='x', padx=5, pady=5)
        btn_halve = Button(button_frame, text="Halve Resolution", command=self.halve_resolution, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_halve.pack(side='left', padx=5)
        self.add_hover_effect(btn_halve)
        btn_negative = Button(button_frame, text="Negative", command=self.negative_transform, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_negative.pack(side='left', padx=5)
        self.add_hover_effect(btn_negative)
        btn_rotate = Button(button_frame, text="Rotate 90°", command=self.rotate_90, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_rotate.pack(side='left', padx=5)
        self.add_hover_effect(btn_rotate)
        btn_flip = Button(button_frame, text="Flip Horizontal", command=self.flip_horizontal, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_flip.pack(side='left', padx=5)
        self.add_hover_effect(btn_flip)

        log_frame = Frame(frame, bg="#ecf0f1")
        log_frame.pack(fill='x', padx=5, pady=5)
        Label(log_frame, text="Log c:", bg="#ecf0f1", fg="#2c3e50").grid(row=0, column=0, sticky='e', padx=5)
        self.log_c_entry = ttk.Entry(log_frame, width=8)
        self.log_c_entry.insert(0, "1.0")
        self.log_c_entry.grid(row=0, column=1, padx=5)
        ToolTip(self.log_c_entry, "Scaling factor for log transform")
        btn_log = Button(log_frame, text="Log", command=self.log_transform, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_log.grid(row=0, column=2, padx=5)
        self.add_hover_effect(btn_log)

        gamma_frame = Frame(frame, bg="#ecf0f1")
        gamma_frame.pack(fill='x', padx=5, pady=5)
        Label(gamma_frame, text="Gamma:", bg="#ecf0f1", fg="#2c3e50").grid(row=0, column=0, sticky='e', padx=5)
        self.gamma_entry = ttk.Entry(gamma_frame, width=8)
        self.gamma_entry.insert(0, "1.0")
        self.gamma_entry.grid(row=0, column=1, padx=5)
        ToolTip(self.gamma_entry, "Gamma value for power-law transform")
        Label(gamma_frame, text="c:", bg="#ecf0f1", fg="#2c3e50").grid(row=0, column=2, sticky='e', padx=5)
        self.c_entry = ttk.Entry(gamma_frame, width=8)
        self.c_entry.insert(0, "1.0")
        self.c_entry.grid(row=0, column=3, padx=5)
        ToolTip(self.c_entry, "Scaling factor for gamma transform")
        btn_gamma = Button(gamma_frame, text="Gamma", command=self.gamma_transform, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_gamma.grid(row=0, column=4, padx=5)
        self.add_hover_effect(btn_gamma)

    def _setup_enhancement_frame(self, frame):
        button_frame = Frame(frame, bg="#ecf0f1")
        button_frame.pack(fill='x', padx=5, pady=5)
        btn_hist = Button(button_frame, text="Hist Equalize", command=self.histogram_equalization, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_hist.pack(side='left', padx=5)
        self.add_hover_effect(btn_hist)
        btn_sharpen = Button(button_frame, text="Sharpen", command=self.sharpen_image, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_sharpen.pack(side='left', padx=5)
        self.add_hover_effect(btn_sharpen)
        btn_contrast = Button(button_frame, text="Contrast Stretch", command=self.contrast_stretch, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_contrast.pack(side='left', padx=5)
        self.add_hover_effect(btn_contrast)
        btn_gauss = Button(button_frame, text="Gaussian Blur", command=self.gaussian_blur, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_gauss.pack(side='left', padx=5)
        self.add_hover_effect(btn_gauss)
        btn_median = Button(button_frame, text="Median Filter", command=self.median_filter, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_median.pack(side='left', padx=5)
        self.add_hover_effect(btn_median)
        btn_bilateral = Button(button_frame, text="Bilateral Filter", command=self.bilateral_filter, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_bilateral.pack(side='left', padx=5)
        self.add_hover_effect(btn_bilateral)

        filter_frame = Frame(frame, bg="#ecf0f1")
        filter_frame.pack(fill='x', padx=5, pady=5)
        Label(filter_frame, text="Filter Size:", bg="#ecf0f1", fg="#2c3e50").grid(row=0, column=0, sticky='e', padx=5)
        self.mask_size_entry = ttk.Entry(filter_frame, width=8)
        self.mask_size_entry.insert(0, "3")
        self.mask_size_entry.grid(row=0, column=1, padx=5)
        ToolTip(self.mask_size_entry, "Size of the filter kernel (odd number)")

    def _setup_color_frame(self, frame):
        saturation_frame = Frame(frame, bg="#ecf0f1")
        saturation_frame.pack(fill='x', padx=5, pady=5)
        Label(saturation_frame, text="Saturation:", bg="#ecf0f1", fg="#2c3e50").grid(row=0, column=0, sticky='e', padx=5)
        self.saturation_entry = ttk.Entry(saturation_frame, width=8)
        self.saturation_entry.insert(0, "1.0")
        self.saturation_entry.grid(row=0, column=1, padx=5)
        ToolTip(self.saturation_entry, "Saturation factor (0.0 to 2.0)")

        brightness_frame = Frame(frame, bg="#ecf0f1")
        brightness_frame.pack(fill='x', padx=5, pady=5)
        Label(brightness_frame, text="Brightness:", bg="#ecf0f1", fg="#2c3e50").grid(row=0, column=0, sticky='e', padx=5)
        self.brightness_entry = ttk.Entry(brightness_frame, width=8)
        self.brightness_entry.insert(0, "0")
        self.brightness_entry.grid(row=0, column=1, padx=5)
        ToolTip(self.brightness_entry, "Brightness offset (-255 to 255)")

        btn_apply = Button(frame, text="Apply", command=self.adjust_color, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_apply.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_apply)

    def _setup_analysis_frame(self, frame):
        btn_histogram = Button(frame, text="Histogram", command=self.show_histogram, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_histogram.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_histogram)
        btn_gradient = Button(frame, text="Gradient Mag", command=self.gradient_magnitude, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_gradient.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_gradient)
        btn_edge = Button(frame, text="Edge Detection", command=self.edge_detection, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_edge.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_edge)
        btn_stats = Button(frame, text="Stats", command=self.show_image_stats, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_stats.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_stats)
        btn_batch = Button(frame, text="Batch Process", command=self.batch_process, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_batch.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_batch)
        btn_fft = Button(frame, text="FFT", command=self.show_fft, bg="#3498db", fg="white", font=("Arial", 10), relief="flat")
        btn_fft.pack(side='left', padx=5, pady=5)
        self.add_hover_effect(btn_fft)

    def _setup_canvas(self):
        self.image_canvas = Canvas(self.root, bd=0, relief="flat", highlightthickness=0, bg="#ffffff")
        self.image_canvas.grid(row=1, column=1, sticky='nsew', padx=10, pady=5)
        self.image_canvas.bind("<Configure>", lambda event: self.update_image_display())

    def _setup_status_elements(self):
        self.progress = ttk.Progressbar(self.root, length=400, mode='determinate')
        self.progress.grid(row=2, column=0, columnspan=2, pady=5)
        self.status_label = Label(self.root, text="Ready", font=("Arial", 10, "bold"), bd=1, relief="flat", anchor="w", padx=10, bg="#ecf0f1", fg="#2c3e50")
        self.status_label.grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

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
        pass  # Placeholder for future theme support

    def show_user_guide(self):
        guide = (
            "Welcome to Ultimate Image Processing Studio!\n\n"
            "1. Load/Save: Ctrl+O to load, Ctrl+S to save.\n"
            "2. Transformations: Apply geometric/intensity changes.\n"
            "3. Enhancements: Improve quality with filters/adjustments.\n"
            "4. Color Adjustments: Modify saturation/brightness (color mode).\n"
            "5. Analysis: View histograms, stats, edges, FFT, etc.\n"
            "6. Undo/Redo: Ctrl+Z and Ctrl+Y.\n"
            "Hover for tooltips!"
        )
        messagebox.showinfo("User Guide", guide)

    def show_about(self):
        about = "Ultimate Image Processing Studio\nVersion 2.0\nDeveloped by @I_am_Progamming_the_World\nMIT License"
        messagebox.showinfo("About", about)

    def load_image(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")])
            if not file_path:
                return
            # Load original image in color mode (3 channels)
            self.original_image = cv2.cvtColor(cv2.imread(file_path, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            if self.original_image is None:
                raise ValueError("Invalid image file.")
            # Set processed_image based on current color mode
            if self.color_mode == 'grayscale':
                self.processed_image = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY)
            else:
                self.processed_image = self.original_image.copy()
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
        canvas_aspect = canvas_width / canvas_height
        image_aspect = image_width / image_height
        if image_aspect > canvas_aspect:
            display_width = canvas_width
            display_height = int(canvas_width / image_aspect)
        else:
            display_height = canvas_height
            display_width = int(canvas_height * image_aspect)
        img = Image.fromarray(self.processed_image).resize((display_width, display_height), Image.Resampling.LANCZOS)
        self.imgtk = ImageTk.PhotoImage(image=img)
        self.image_canvas.delete("all")
        self.image_canvas.create_image((canvas_width - display_width) // 2, (canvas_height - display_height) // 2, anchor='nw', image=self.imgtk)

    def save_to_history(self):
        self.future_history.clear()
        if len(self.history) >= self.history_limit:
            self.history.pop(0)
        self.history.append(self.processed_image.copy())

    def apply_to_image(self, func, *args, **kwargs):
        if self.processed_image is None:
            return
        self.processed_image = func(self.processed_image, *args, **kwargs)
        self.save_to_history()
        self.update_image_display()

    def halve_resolution(self):
        if self.processed_image is None:
            return
        self.processed_image = cv2.resize(self.processed_image, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        self.save_to_history()
        self.update_image_display()
        self.status_label.config(text="Resolution halved")

    def negative_transform(self):
        self.apply_to_image(lambda img: 255 - img)
        self.status_label.config(text="Negative transform applied")

    def rotate_90(self):
        if self.processed_image is None:
            return
        self.processed_image = cv2.rotate(self.processed_image, cv2.ROTATE_90_CLOCKWISE)
        self.save_to_history()
        self.update_image_display()
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
            # Convert to YCrCb, equalize Y channel, convert back to RGB
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
            if n % 2 == 0 or n <= 0:
                raise ValueError("Filter size must be a positive odd integer.")
            self.apply_to_image(cv2.GaussianBlur, (n, n), 0)
            self.status_label.config(text=f"Gaussian blur applied with filter size {n}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def median_filter(self):
        try:
            n = int(self.mask_size_entry.get())
            if n % 2 == 0 or n <= 0:
                raise ValueError("Filter size must be a positive odd integer.")
            self.apply_to_image(cv2.medianBlur, n)
            self.status_label.config(text=f"Median filter applied with filter size {n}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def bilateral_filter(self):
        try:
            n = int(self.mask_size_entry.get())
            if n % 2 == 0 or n <= 0:
                raise ValueError("Filter size must be a positive odd integer.")
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
        fig = plt.figure(figsize=(6, 4))
        if self.color_mode == 'grayscale':
            f = fftshift(fft2(self.processed_image))
            magnitude_spectrum = 20 * np.log(np.abs(f) + 1)
            plt.imshow(magnitude_spectrum, cmap='gray')
        else:
            magnitude_spectrum = np.zeros(self.processed_image.shape[:2])
            for i in range(3):
                f = fftshift(fft2(self.processed_image[:, :, i]))
                magnitude_spectrum += 20 * np.log(np.abs(f) + 1)
            plt.imshow(magnitude_spectrum / 3, cmap='gray')
        plt.colorbar()
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

        def process_file(file):
            img = cv2.imread(file, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            for op_name in selected_names:
                for name, func in operations:
                    if name == op_name:
                        self.processed_image = img
                        func()
                        img = self.processed_image
                        break
            output_path = f"{os.path.splitext(file)[0]}_processed.png"
            cv2.imwrite(output_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            return output_path

        for file in files:
            process_file(file)
        messagebox.showinfo("Batch Process", f"Processed {len(files)} images.")
        self.status_label.config(text="Batch process completed")

    def switch_color_mode(self, event):
        new_mode = self.color_mode_var.get()
        if new_mode == self.color_mode or self.original_image is None:
            return
        self.color_mode = new_mode
        if self.color_mode == 'grayscale':
            self.processed_image = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY)
        else:
            self.processed_image = self.original_image.copy()
        self.history = [self.processed_image.copy()]
        self.future_history.clear()
        self.update_image_display()
        self.status_label.config(text=f"Switched to {self.color_mode} mode")

    def reset_app(self):
        self.original_image = None
        self.processed_image = None
        self.history.clear()
        self.future_history.clear()
        self.update_image_display()
        self.status_label.config(text="Application reset")

    def clear_roi(self):
        self.update_image_display()
        self.status_label.config(text="ROI cleared")

