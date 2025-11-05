import os
import shutil
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import PhotoImage
from PIL import Image

# -----------------------------
# Ensure tkinterdnd2 is installed
# -----------------------------
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    root_temp = tk.Tk()
    root_temp.withdraw()
    install = messagebox.askyesno(
        "Install Library",
        "The 'tkinterdnd2' library is not installed.\nInstall it now?"
    )
    root_temp.destroy()
    if install:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tkinterdnd2"])
        from tkinterdnd2 import DND_FILES, TkinterDnD
    else:
        tk.messagebox.showerror(
            "Missing Library", "Cannot continue without 'tkinterdnd2'. Exiting."
        )
        sys.exit(1)

# -----------------------------
# Texture renamer functions
# -----------------------------
def browse_file(entry_field):
    file_path = filedialog.askopenfilename(
        title="Select texture file",
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.tga"), ("All files", "*.*")]
    )
    if file_path:
        entry_field.delete(0, tk.END)
        entry_field.insert(0, file_path)

def export_textures():
    bike_num = bike_number_entry.get().strip()
    if not bike_num.isdigit():
        messagebox.showerror("Invalid Input", "Please enter a valid bike number (numbers only).")
        return

    input_files = {
        "frame_base": frame_base_entry.get(),
        "frame_metal": frame_metal_entry.get(),
        "gear_base": gear_base_entry.get(),
        "gear_metal": gear_metal_entry.get(),
        "handlebar_base": handlebar_base_entry.get(),
        "handlebar_metal": handlebar_metal_entry.get(),
        "wheels_base": wheels_base_entry.get(),
        "wheels_metal": wheels_metal_entry.get(),
    }

    # Ensure paths exist
    for key, path in input_files.items():
        if not os.path.isfile(path):
            messagebox.showerror("Missing File", f"Please select a valid file for {key.replace('_', ' ').title()}.")
            return

    output_dir = filedialog.askdirectory(title="Select Output Folder")
    if not output_dir:
        return

    parts = {
        "frame": ("frame_base", "frame_metal"),
        "gear": ("gear_base", "gear_metal"),
        "handlebar": ("handlebar_base", "handlebar_metal"),
        "wheels": ("wheels_base", "wheels_metal"),
    }

    for part, (base_key, metal_key) in parts.items():
        base_in = input_files[base_key]
        metal_in = input_files[metal_key]

        base_out = os.path.join(output_dir, f"{bike_num}_{part}_{bike_num}_D.png")
        metal_out = os.path.join(output_dir, f"{bike_num}_{part}_{bike_num}_MS.png")

        # Copy base color
        shutil.copy2(base_in, base_out)

        # Process metallic map: brightness → alpha
        metal_img = Image.open(metal_in).convert("RGBA")
        new_data = []

        for r, g, b, a in metal_img.getdata():
            brightness = int((r + g + b) / 3)  # 0=black, 255=white
            new_data.append((r, g, b, brightness))

        metal_img.putdata(new_data)
        metal_img.save(metal_out)

    messagebox.showinfo("Success", f"Textures exported successfully to:\n{output_dir}")

# -----------------------------
# GUI Setup
# -----------------------------
root = TkinterDnD.Tk()
root.title("Descenders Texture Renamer (Auto-Install & Drag & Drop)")

# Load icon
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

icon_path = os.path.join(base_path, "theicon.png")
if os.path.isfile(icon_path):
    icon = tk.PhotoImage(file=icon_path)
    root.iconphoto(True, icon)

# Footer
footer = tk.Label(root, text="Made by THEE OH", font=("Segoe UI", 9), fg="gray")
footer.pack(side="bottom", anchor="e", padx=10, pady=5)

root.geometry("600x550")
root.resizable(False, False)

title_label = tk.Label(root, text="Descenders Texture Renamer", font=("Segoe UI", 16, "bold"))
title_label.pack(pady=10)

frame = tk.Frame(root)
frame.pack(pady=10)

# Create drag & drop entry rows
def make_file_row(parent, label_text):
    row = tk.Frame(parent)
    row.pack(fill="x", padx=20, pady=5)
    label = tk.Label(row, text=label_text, width=20, anchor="w")
    label.pack(side="left")
    entry = tk.Entry(row, width=45)
    entry.pack(side="left", padx=5)
    browse = tk.Button(row, text="Browse", command=lambda: browse_file(entry))
    browse.pack(side="left")

    # Drag & drop with proper path stripping
    def handle_drop(event):
        path = event.data.strip().strip("{}").strip()
        entry.delete(0, tk.END)
        entry.insert(0, path)

    entry.drop_target_register(DND_FILES)
    entry.dnd_bind("<<Drop>>", handle_drop)

    return entry

frame_base_entry = make_file_row(frame, "Frame Base Colour:")
frame_metal_entry = make_file_row(frame, "Frame Metallic:")
gear_base_entry = make_file_row(frame, "Gear Base Colour:")
gear_metal_entry = make_file_row(frame, "Gear Metallic:")
handlebar_base_entry = make_file_row(frame, "Handlebar Base Colour:")
handlebar_metal_entry = make_file_row(frame, "Handlebar Metallic:")
wheels_base_entry = make_file_row(frame, "Wheels Base Colour:")
wheels_metal_entry = make_file_row(frame, "Wheels Metallic:")

# Bike number
bike_frame = tk.Frame(root)
bike_frame.pack(pady=20)
tk.Label(bike_frame, text="Bike Number:").pack(side="left", padx=5)
bike_number_entry = tk.Entry(bike_frame, width=10)
bike_number_entry.pack(side="left")

# Export button
export_button = tk.Button(
    root, text="Export Textures",
    font=("Segoe UI", 12, "bold"),
    bg="#4CAF50", fg="white",
    width=20, command=export_textures
)
export_button.pack(pady=20)

root.mainloop()
