#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import threading
import shutil
from datetime import datetime


def check_ffmpeg():
    """Check if FFmpeg is available in PATH."""
    return shutil.which("ffmpeg") is not None


def get_image_date(filepath):
    """Get image creation date from EXIF or file metadata."""
    try:
        # Try to read EXIF data using exiftool if available
        if shutil.which("exiftool"):
            result = subprocess.run(
                ["exiftool", "-DateTimeOriginal", "-s3", filepath],
                capture_output=True, text=True
            )
            if result.stdout.strip():
                # Parse EXIF date format: "2026:01:04 12:30:45"
                date_str = result.stdout.strip().split()[0]
                return date_str.replace(":", "")
    except Exception:
        pass

    # Fall back to file modification time
    try:
        mtime = os.path.getmtime(filepath)
        return datetime.fromtimestamp(mtime).strftime("%Y%m%d")
    except Exception:
        return datetime.now().strftime("%Y%m%d")


def select_files():
    """Open file dialog to select multiple image files."""
    filetypes = [
        ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.JPG *.JPEG *.PNG *.BMP *.TIFF *.TIF"),
        ("All files", "*.*")
    ]
    files = filedialog.askopenfilenames(filetypes=filetypes)
    if files:
        selected_files.clear()
        selected_files.extend(files)

        # Update display
        files_label_var.set(f"{len(files)} files selected")

        # Get folder and extension from first file
        first_file = files[0]
        folder = os.path.dirname(first_file)
        ext = os.path.splitext(first_file)[1].lstrip(".")

        folder_var.set(folder)
        extension_var.set(ext)

        # Generate default output name
        base_name = os.path.splitext(os.path.basename(first_file))[0]
        date_stamp = get_image_date(first_file)
        output_var.set(f"{base_name}_{date_stamp}.gif")

        # Clear status
        update_status("")


def update_scale_ui(*args):
    """Show/hide scale inputs based on mode selection."""
    mode = scale_mode_var.get()
    if mode == "factor":
        factor_frame.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        pixel_frame.grid_remove()
    else:
        pixel_frame.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        factor_frame.grid_remove()


def get_scale_string():
    """Build FFmpeg scale string based on current settings."""
    mode = scale_mode_var.get()
    if mode == "factor":
        factor = scale_factor_var.get()
        try:
            f = float(factor)
            return f"iw*{f}:ih*{f}"
        except ValueError:
            return "iw/2:ih/2"
    else:
        width = pixel_width_var.get()
        height = pixel_height_var.get()
        return f"{width}:{height}"


def validate_inputs():
    """Validate user inputs and return error message or None if valid."""
    if not selected_files:
        return "Please select image files"

    framerate = framerate_var.get()
    if not framerate.strip():
        return "Please enter a frame rate"

    try:
        rate = float(framerate)
        if rate <= 0:
            return "Frame rate must be a positive number"
    except ValueError:
        return "Frame rate must be a valid number"

    mode = scale_mode_var.get()
    if mode == "factor":
        try:
            f = float(scale_factor_var.get())
            if f <= 0:
                return "Scale factor must be positive"
        except ValueError:
            return "Scale factor must be a valid number"
    else:
        try:
            w = int(pixel_width_var.get())
            h = int(pixel_height_var.get())
            if w <= 0 or h <= 0:
                return "Width and height must be positive"
        except ValueError:
            return "Width and height must be valid integers"

    return None


def update_status(message, is_error=False):
    """Update the status label."""
    status_var.set(message)
    status_label.config(fg="red" if is_error else "green")


def append_ffmpeg_output(text):
    """Append text to the FFmpeg output window."""
    if show_ffmpeg_var.get():
        ffmpeg_text.config(state="normal")
        ffmpeg_text.insert("end", text)
        ffmpeg_text.see("end")
        ffmpeg_text.config(state="disabled")


def clear_ffmpeg_output():
    """Clear the FFmpeg output window."""
    ffmpeg_text.config(state="normal")
    ffmpeg_text.delete("1.0", "end")
    ffmpeg_text.config(state="disabled")


def toggle_ffmpeg_output(*args):
    """Show/hide the FFmpeg output frame."""
    if show_ffmpeg_var.get():
        ffmpeg_frame.grid(row=8, column=0, columnspan=3, sticky="nsew", padx=10, pady=(0, 10))
        root.geometry("800x600")
    else:
        ffmpeg_frame.grid_remove()
        root.geometry("800x375")


def run_ffmpeg_with_output(cmd, step_name):
    """Run FFmpeg command and capture output."""
    show_output = show_ffmpeg_var.get()

    root.after(0, lambda: append_ffmpeg_output(f"\n{'='*50}\n{step_name}\n{'='*50}\n"))
    root.after(0, lambda: append_ffmpeg_output(f"$ {' '.join(cmd)}\n\n"))

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # FFmpeg outputs to stderr
    output_lines = []
    for line in process.stderr:
        output_lines.append(line)
        if show_output:
            root.after(0, lambda l=line: append_ffmpeg_output(l))

    process.wait()

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd, stderr=''.join(output_lines))

    return ''.join(output_lines)


def create_gif_thread(folder, extension, framerate, scale, output):
    """Run GIF creation in a separate thread to prevent UI freeze."""
    # Handle case-insensitive extension matching
    ext_lower = extension.lower()
    ext_upper = extension.upper()

    # Try to find files with either case
    input_pattern_lower = os.path.join(folder, f"*.{ext_lower}")
    input_pattern_upper = os.path.join(folder, f"*.{ext_upper}")

    # Check which pattern has files
    import glob
    files_lower = glob.glob(input_pattern_lower)
    files_upper = glob.glob(input_pattern_upper)

    if files_upper:
        input_pattern = input_pattern_upper
    elif files_lower:
        input_pattern = input_pattern_lower
    else:
        root.after(0, lambda: update_status(f"Error: No .{extension} files found in folder", is_error=True))
        root.after(0, lambda: set_ui_state(True))
        return

    palette_path = os.path.join(folder, "palette.png")
    output_path = os.path.join(folder, output)

    try:
        # Clear previous output
        root.after(0, clear_ffmpeg_output)

        # Update progress - Step 1
        root.after(0, lambda: progress_var.set(0))
        root.after(0, lambda: update_status("Generating color palette..."))

        # Generate palette
        run_ffmpeg_with_output([
            "ffmpeg", "-y", "-framerate", framerate,
            "-pattern_type", "glob", "-i", input_pattern,
            "-vf", f"scale={scale},palettegen=stats_mode=diff",
            palette_path
        ], "Step 1: Generating palette")

        # Update progress - Step 2
        root.after(0, lambda: progress_var.set(50))
        root.after(0, lambda: update_status("Creating GIF..."))

        # Create GIF
        run_ffmpeg_with_output([
            "ffmpeg", "-y", "-framerate", framerate,
            "-pattern_type", "glob", "-i", input_pattern,
            "-i", palette_path,
            "-lavfi", f"scale={scale}[s];[s][1:v]paletteuse=dither=floyd_steinberg",
            "-loop", "0", output_path
        ], "Step 2: Creating GIF")

        # Complete
        root.after(0, lambda: progress_var.set(100))
        root.after(0, lambda: update_status(f"Saved: {output_path}"))
        root.after(0, lambda: append_ffmpeg_output(f"\n{'='*50}\nComplete!\n{'='*50}\n"))

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        root.after(0, lambda: update_status(f"Error: FFmpeg failed", is_error=True))
        root.after(0, lambda: append_ffmpeg_output(f"\nERROR: {error_msg}\n"))
    finally:
        # Always clean up palette file
        try:
            if os.path.exists(palette_path):
                os.remove(palette_path)
        except OSError:
            pass

        # Re-enable UI
        root.after(0, lambda: set_ui_state(True))


def set_ui_state(enabled):
    """Enable or disable UI elements."""
    state = "normal" if enabled else "disabled"
    create_button.config(state=state, text="Create GIF" if enabled else "Creating...")
    browse_button.config(state=state)
    if enabled:
        progress_var.set(0)


def create_gif():
    folder = folder_var.get()
    extension = extension_var.get()
    framerate = framerate_var.get()
    scale = get_scale_string()
    output = output_var.get()

    # Check FFmpeg availability
    if not check_ffmpeg():
        update_status("Error: FFmpeg not found. Please install FFmpeg.", is_error=True)
        return

    # Validate inputs
    error = validate_inputs()
    if error:
        update_status(f"Error: {error}", is_error=True)
        return

    if not output.endswith('.gif'):
        output += '.gif'

    # Clear status and start
    update_status("Starting...")

    # Disable UI and run in thread
    set_ui_state(False)
    thread = threading.Thread(target=create_gif_thread, args=(folder, extension, framerate, scale, output))
    thread.daemon = True
    thread.start()


# Create window
root = tk.Tk()
root.title("GIF Maker")
root.geometry("800x375")

# Storage for selected files
selected_files = []

# Variables
folder_var = tk.StringVar()
extension_var = tk.StringVar()
files_label_var = tk.StringVar(value="No files selected")
framerate_var = tk.StringVar(value="4")
scale_mode_var = tk.StringVar(value="factor")
scale_factor_var = tk.StringVar(value="0.5")
pixel_width_var = tk.StringVar(value="640")
pixel_height_var = tk.StringVar(value="480")
output_var = tk.StringVar(value="output.gif")
progress_var = tk.DoubleVar(value=0)
status_var = tk.StringVar(value="")
show_ffmpeg_var = tk.BooleanVar(value=False)

# Layout
row = 0

# File selection
tk.Label(root, text="Images:").grid(row=row, column=0, sticky="e", padx=10, pady=10)
tk.Label(root, textvariable=files_label_var, width=40, anchor="w").grid(row=row, column=1, sticky="w", padx=5, pady=10)
browse_button = tk.Button(root, text="Select Files...", command=select_files, width=15)
browse_button.grid(row=row, column=2, padx=10, pady=10)
row += 1

# Frame rate
tk.Label(root, text="Frame Rate:").grid(row=row, column=0, sticky="e", padx=10, pady=10)
tk.Entry(root, textvariable=framerate_var, width=50).grid(row=row, column=1, sticky="w", padx=5, pady=10)
tk.Label(root, text="fps").grid(row=row, column=2, sticky="w", padx=5, pady=10)
row += 1

# Scale mode selection
tk.Label(root, text="Scale Mode:").grid(row=row, column=0, sticky="e", padx=10, pady=10)
scale_mode_frame = tk.Frame(root)
scale_mode_frame.grid(row=row, column=1, sticky="w", padx=5, pady=10)
tk.Radiobutton(scale_mode_frame, text="By Factor", variable=scale_mode_var, value="factor", command=update_scale_ui).pack(side="left")
tk.Radiobutton(scale_mode_frame, text="By Pixels", variable=scale_mode_var, value="pixels", command=update_scale_ui).pack(side="left", padx=20)
row += 1

# Scale inputs (factor)
factor_frame = tk.Frame(root)
tk.Label(factor_frame, text="Scale factor:").pack(side="left")
tk.Entry(factor_frame, textvariable=scale_factor_var, width=10).pack(side="left", padx=5)
tk.Label(factor_frame, text="(e.g., 0.5 = half size, 2 = double size)").pack(side="left")
factor_frame.grid(row=row, column=1, sticky="w", padx=5, pady=10)

# Scale inputs (pixels)
pixel_frame = tk.Frame(root)
tk.Label(pixel_frame, text="Width:").pack(side="left")
tk.Entry(pixel_frame, textvariable=pixel_width_var, width=8).pack(side="left", padx=5)
tk.Label(pixel_frame, text="Height:").pack(side="left", padx=(15, 0))
tk.Entry(pixel_frame, textvariable=pixel_height_var, width=8).pack(side="left", padx=5)
tk.Label(pixel_frame, text="px").pack(side="left")
pixel_frame.grid(row=row, column=1, sticky="w", padx=5, pady=10)
pixel_frame.grid_remove()  # Hidden by default
row += 1

# Output name
tk.Label(root, text="Output Name:").grid(row=row, column=0, sticky="e", padx=10, pady=10)
tk.Entry(root, textvariable=output_var, width=50).grid(row=row, column=1, sticky="w", padx=5, pady=10)
row += 1

# FFmpeg output toggle
tk.Label(root, text="Options:").grid(row=row, column=0, sticky="e", padx=10, pady=10)
tk.Checkbutton(root, text="Show FFmpeg output", variable=show_ffmpeg_var, command=toggle_ffmpeg_output).grid(row=row, column=1, sticky="w", padx=5, pady=10)
row += 1

# Create button
create_button = tk.Button(root, text="Create GIF", command=create_gif, width=20, height=2)
create_button.grid(row=row, column=1, pady=20)
row += 1

# Progress bar
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=400)
progress_bar.grid(row=row, column=1, pady=(0, 5))
row += 1

# Status label
status_label = tk.Label(root, textvariable=status_var, wraplength=700, justify="left")
status_label.grid(row=row, column=0, columnspan=3, padx=10, pady=(0, 10))
row += 1

# FFmpeg output frame (hidden by default)
ffmpeg_frame = tk.Frame(root)
tk.Label(ffmpeg_frame, text="FFmpeg Output:").pack(anchor="w")
ffmpeg_text = tk.Text(ffmpeg_frame, height=12, width=95, state="disabled", bg="#1e1e1e", fg="#ffffff", font=("Courier", 10))
ffmpeg_scrollbar = tk.Scrollbar(ffmpeg_frame, command=ffmpeg_text.yview)
ffmpeg_text.config(yscrollcommand=ffmpeg_scrollbar.set)
ffmpeg_text.pack(side="left", fill="both", expand=True)
ffmpeg_scrollbar.pack(side="right", fill="y")

root.mainloop()
