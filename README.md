# Ultimate Image Processing Studio

## Description

The **Ultimate Image Processing Studio** is an advanced GUI-based application for processing grayscale and color images. It features a wide range of transformations, enhancements, analysis tools, and the ability to apply various filters and effects to images. The application supports various file operations such as loading, saving, and undo/redo functionality. 

With an intuitive interface designed using Tkinter, this tool offers options for users to work with both grayscale and color images, apply complex transformations, and analyze image statistics. The app also includes a batch processing feature for applying selected operations to multiple images simultaneously.

## Features

### 1. **File Operations**
   - **Load**: Load image files from the local file system.
   - **Save**: Save the current processed image in various formats.
   - **Undo**: Undo the last action taken (with support for multiple undo operations).
   - **Redo**: Redo the last undone action.
   - **Color Mode**: Switch between grayscale and color modes.

### 2. **Image Transformations**
   - **Halve Resolution**: Reduce image resolution by half.
   - **Negative Transformation**: Invert the colors of the image.
   - **Rotate 90°**: Rotate the image 90 degrees clockwise.
   - **Flip Horizontal**: Flip the image horizontally.
   - **Log Transform**: Apply a logarithmic transformation to the image.
   - **Gamma Transform**: Apply gamma correction to adjust image brightness.

### 3. **Image Enhancements**
   - **Histogram Equalization**: Enhance the contrast of grayscale images using histogram equalization.
   - **Sharpen Image**: Apply a sharpening filter to enhance edges.
   - **Contrast Stretch**: Stretch the contrast in the image for better clarity.
   - **Gaussian Blur**: Apply a Gaussian blur filter to smooth the image.
   - **Median Filter**: Use a median filter for noise reduction.
   - **Bilateral Filter**: Apply bilateral filtering for edge-preserving smoothing.

### 4. **Color Adjustments** (Only in Color Mode)
   - **Saturation**: Adjust the saturation of the image.
   - **Brightness**: Adjust the brightness of the image.

### 5. **Image Analysis Tools**
   - **Histogram**: Display the image histogram (for both grayscale and color images).
   - **Gradient Magnitude**: Apply a gradient magnitude filter for edge detection.
   - **Edge Detection**: Detect edges in the image using the Canny edge detector.
   - **Image Statistics**: Display image statistics such as mean, standard deviation, skewness, and kurtosis.
   - **FFT (Fast Fourier Transform)**: Visualize the frequency spectrum of the image.

### 6. **Batch Processing**
   - Apply selected transformations and enhancements to multiple images at once.

### 7. **Region of Interest (ROI) Selection**
   - Select a specific area of the image for processing by drawing a rectangle on the canvas.

### 8. **Theme Customization**
   - Toggle between light and dark themes for a more personalized user experience.

### 9. **Tooltips and Keyboard Shortcuts**
   - Tooltips provide helpful descriptions of each button and control.
   - Common operations have associated keyboard shortcuts for quicker access (e.g., `Ctrl+Z` for undo, `Ctrl+Y` for redo).

## Requirements

To run this application, you need the following Python libraries:

- OpenCV
- NumPy
- Tkinter (usually pre-installed)
- Matplotlib
- Pillow
- SciPy
- Multiprocessing (for batch processing)

You can install the necessary packages using pip:

```bash
pip install opencv-python numpy matplotlib pillow scipy
