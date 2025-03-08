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