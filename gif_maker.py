#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import threading
import shutil


def check_ffmpeg():
    """Check if FFmpeg is available in PATH."""
    return shutil.which("ffmpeg") is not None


def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)


def validate_inputs(folder, extension, framerate):
    """Validate user inputs and return error message or None if valid."""
    if not folder:
        return "Please select a folder"

    if not extension.strip():
        return "Please enter a file extension"

    if not framerate.strip():
        return "Please enter a frame rate"

    try:
        rate = float(framerate)
        if rate <= 0:
            return "Frame rate must be a positive number"
    except ValueError:
        return "Frame rate must be a valid number"

    return None


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
        root.after(0, lambda: messagebox.showerror("Error", f"No .{extension} files found in folder"))
        root.after(0, lambda: set_ui_state(True))
        return

    palette_path = os.path.join(folder, "palette.png")
    output_path = os.path.join(folder, output)

    try:
        # Generate palette
        result = subprocess.run([
            "ffmpeg", "-y", "-framerate", framerate,
            "-pattern_type", "glob", "-i", input_pattern,
            "-vf", f"scale={scale},palettegen=stats_mode=diff",
            palette_path
        ], check=True, capture_output=True, text=True)

        # Create GIF
        subprocess.run([
            "ffmpeg", "-y", "-framerate", framerate,
            "-pattern_type", "glob", "-i", input_pattern,
            "-i", palette_path,
            "-lavfi", f"scale={scale}[s];[s][1:v]paletteuse=dither=floyd_steinberg",
            "-loop", "0", output_path
        ], check=True, capture_output=True, text=True)

        root.after(0, lambda: messagebox.showinfo("Success", f"Created {output_path}"))
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        root.after(0, lambda: messagebox.showerror("Error", f"FFmpeg failed: {error_msg}"))
    finally:
        # Always clean up palette file
        try:
            if os.path.exists(palette_path):
                os.remove(palette_path)
        except OSError:
            pass  # Ignore cleanup errors

        # Re-enable UI
        root.after(0, lambda: set_ui_state(True))


def set_ui_state(enabled):
    """Enable or disable UI elements."""
    state = "normal" if enabled else "disabled"
    create_button.config(state=state, text="Create GIF" if enabled else "Creating...")
    browse_button.config(state=state)


def create_gif():
    folder = folder_var.get()
    extension = extension_var.get()
    framerate = framerate_var.get()
    scale = scale_var.get()
    output = output_var.get()

    # Check FFmpeg availability
    if not check_ffmpeg():
        messagebox.showerror("Error", "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
        return

    # Validate inputs
    error = validate_inputs(folder, extension, framerate)
    if error:
        messagebox.showerror("Error", error)
        return

    if not output.endswith('.gif'):
        output += '.gif'

    # Disable UI and run in thread
    set_ui_state(False)
    thread = threading.Thread(target=create_gif_thread, args=(folder, extension, framerate, scale, output))
    thread.daemon = True
    thread.start()


# Create window
root = tk.Tk()
root.title("GIF Maker")
root.geometry("400x250")

# Variables
folder_var = tk.StringVar()
extension_var = tk.StringVar(value="JPG")
framerate_var = tk.StringVar(value="4")
scale_var = tk.StringVar(value="iw/2:ih/2")
output_var = tk.StringVar(value="output.gif")

# Layout
tk.Label(root, text="Folder:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
tk.Entry(root, textvariable=folder_var, width=30).grid(row=0, column=1, padx=5, pady=5)
browse_button = tk.Button(root, text="Browse", command=select_folder)
browse_button.grid(row=0, column=2, padx=5, pady=5)

tk.Label(root, text="Extension:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
tk.Entry(root, textvariable=extension_var, width=30).grid(row=1, column=1, padx=5, pady=5)

tk.Label(root, text="Frame Rate:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
tk.Entry(root, textvariable=framerate_var, width=30).grid(row=2, column=1, padx=5, pady=5)

tk.Label(root, text="Scale:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
tk.Entry(root, textvariable=scale_var, width=30).grid(row=3, column=1, padx=5, pady=5)

tk.Label(root, text="Output Name:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
tk.Entry(root, textvariable=output_var, width=30).grid(row=4, column=1, padx=5, pady=5)

create_button = tk.Button(root, text="Create GIF", command=create_gif)
create_button.grid(row=5, column=1, pady=20)

root.mainloop()
