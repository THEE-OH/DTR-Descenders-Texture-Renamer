import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from pypresence import Presence
import time
import threading

# -----------------------------
# Discord Rich Presence setup
# -----------------------------
DISCORD_CLIENT_ID = '1435987709603741859'  # Your Discord App ID

def start_discord_presence():
    try:
        rpc = Presence(DISCORD_CLIENT_ID)
        rpc.connect()
        rpc.update(
            details="Descenders Texture Renamer",
            large_image="theicon_1_",  # icon uploaded in Discord Dev Portal
            state="DTR-Descenders-Texture-Renamer on GitHub",
            buttons=[{"label": "GitHub", "url": "https://github.com/THEE-OH/DTR-Descenders-Texture-Renamer/tree/main"}]
        )
        while True:
            time.sleep(15)  # refresh every 15 seconds
    except Exception as e:
        print("Discord Rich Presence failed:", e)

# Start Discord presence in background thread
threading.Thread(target=start_discord_presence, daemon=True).start()

# -----------------------------
# Ensure tkinterdnd2 is installed
# -----------------------------
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    root_temp = tk.Tk()
    root_temp.withdraw()
    install = messagebox.askyesno(
        "Install Library", "The 'tkinterdnd2' library is not installed.\nInstall it now?"
    )
    root_temp.destroy()
    if install:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tkinterdnd2"])
        from tkinterdnd2 import DND_FILES, TkinterDnD
    else:
        tk.messagebox.showerror("Missing Library", "Cannot continue without 'tkinterdnd2'. Exiting.")
        sys.exit(1)

# -----------------------------
# Texture Sorting Logic
# -----------------------------
def sort_file_into_slot(filename):
    name = filename.lower()
    if "frame" in name:
        return "frame_metal" if "metal" in name or "ms" in name else "frame_base"
    elif "gear" in name:
        return "gear_metal" if "metal" in name or "ms" in name else "gear_base"
    elif "handle" in name or "bar" in name:
        return "handlebar_metal" if "metal" in name or "ms" in name else "handlebar_base"
    elif "wheel" in name:
        return "wheels_metal" if "metal" in name or "ms" in name else "wheels_base"
    return None

# -----------------------------
# GUI Functions
# -----------------------------
def browse_file(entry_field):
    file_path = filedialog.askopenfilename(
        title="Select texture file",
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.tga"), ("All files", "*.*")]
    )
    if file_path:
        entry_field.delete(0, tk.END)
        entry_field.insert(0, file_path)

def handle_bulk_drop(event):
    dropped = event.data.strip("{}").split("}")
    dropped = [f.strip().replace("{", "") for f in dropped if f.strip()]
    assigned = []

    for path in dropped:
        slot = sort_file_into_slot(os.path.basename(path))
        if slot and slot in entry_fields:
            entry_fields[slot].delete(0, tk.END)
            entry_fields[slot].insert(0, path)
            assigned.append(slot)

    if assigned:
        messagebox.showinfo("Files Assigned", f"Assigned: {', '.join(assigned)}")
    else:
        messagebox.showwarning("No Match", "No valid texture names detected in dropped files.")

def export_textures():
    bike_num = bike_number_entry.get().strip()
    rename_enabled = rename_var.get()
    transparency_enabled = transparency_var.get()

    if rename_enabled and not bike_num.isdigit():
        messagebox.showerror("Invalid Input", "Please enter a valid bike number (numbers only).")
        return

    input_files = {key: field.get().strip() for key, field in entry_fields.items()}
    output_dir = filedialog.askdirectory(title="Select Output Folder")
    if not output_dir:
        return

    processed = []
    parts = {
        "frame": ("frame_base", "frame_metal"),
        "gear": ("gear_base", "gear_metal"),
        "handlebar": ("handlebar_base", "handlebar_metal"),
        "wheels": ("wheels_base", "wheels_metal"),
    }

    for part, (base_key, metal_key) in parts.items():
        base_in = input_files[base_key]
        metal_in = input_files[metal_key]

        if not base_in and not metal_in:
            continue

        if rename_enabled:
            base_out = os.path.join(output_dir, f"{bike_num}_{part}_{bike_num}_D.png")
            metal_out = os.path.join(output_dir, f"{bike_num}_{part}_{bike_num}_MS.png")
        else:
            base_out = os.path.join(output_dir, os.path.basename(base_in)) if base_in else None
            metal_out = os.path.join(output_dir, os.path.basename(metal_in)) if metal_in else None

        if base_in and os.path.isfile(base_in):
            shutil.copy2(base_in, base_out)
            processed.append(f"{part} base")

        if metal_in and os.path.isfile(metal_in):
            metal_img = Image.open(metal_in).convert("RGBA")
            if transparency_enabled:
                new_data = []
                for r, g, b, *_ in metal_img.getdata():
                    gray = (r + g + b) / 3
                    alpha = int((gray / 255) * 255)
                    new_data.append((r, g, b, alpha))
                metal_img.putdata(new_data)
            metal_img.save(metal_out)
            processed.append(f"{part} metallic")

    if processed:
        mode = "Renamed" if rename_enabled else "Transparency Only"
        messagebox.showinfo("Success", f"Mode: {mode}\nExported: {', '.join(processed)}\n\nSaved to:\n{output_dir}")
    else:
        messagebox.showwarning("No Files", "No valid textures were selected.")

# -----------------------------
# GUI Setup
# -----------------------------
root = TkinterDnD.Tk()
root.title("Descenders Texture Renamer - Made by THEE OH")
root.geometry("600x700")
root.resizable(False, False)

# Load icon
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, "theicon.png")
if os.path.exists(icon_path):
    icon = tk.PhotoImage(file=icon_path)
    root.iconphoto(True, icon)

# Title label
tk.Label(root, text="Descenders Texture Renamer - Made by THEE OH", font=("Segoe UI", 16, "bold")).pack(pady=10)

# Bulk drag & drop
bulk_frame = tk.LabelFrame(root, text="Drag & Drop All Textures Here", padx=10, pady=10)
bulk_frame.pack(padx=20, pady=10, fill="x")
bulk_label = tk.Label(bulk_frame, text="Drop up to 8 textures here (auto-sorted)", bg="#f0f0f0", height=4)
bulk_label.pack(fill="x", padx=10, pady=5)
bulk_label.drop_target_register(DND_FILES)
bulk_label.dnd_bind("<<Drop>>", handle_bulk_drop)

# Individual file entries
frame = tk.Frame(root)
frame.pack(pady=5)
entry_fields = {}

def make_file_row(parent, label_text, key):
    row = tk.Frame(parent)
    row.pack(fill="x", padx=20, pady=4)
    label = tk.Label(row, text=label_text, width=20, anchor="w")
    label.pack(side="left")
    entry = tk.Entry(row, width=45)
    entry.pack(side="left", padx=5)
    browse = tk.Button(row, text="Browse", bg="white", command=lambda: browse_file(entry))
    browse.pack(side="left")
    entry.drop_target_register(DND_FILES)
    entry.dnd_bind("<<Drop>>", lambda e: entry.delete(0, tk.END) or entry.insert(0, e.data.strip("{}")))
    entry_fields[key] = entry

make_file_row(frame, "Frame Base Colour:", "frame_base")
make_file_row(frame, "Frame Metallic:", "frame_metal")
make_file_row(frame, "Gear Base Colour:", "gear_base")
make_file_row(frame, "Gear Metallic:", "gear_metal")
make_file_row(frame, "Handlebar Base Colour:", "handlebar_base")
make_file_row(frame, "Handlebar Metallic:", "handlebar_metal")
make_file_row(frame, "Wheels Base Colour:", "wheels_base")
make_file_row(frame, "Wheels Metallic:", "wheels_metal")

# Bottom controls
bottom_frame = tk.Frame(root)
bottom_frame.pack(pady=20)

# Bike number
bike_frame = tk.Frame(bottom_frame)
bike_frame.pack(pady=5)
tk.Label(bike_frame, text="Bike Number:").pack(side="left", padx=5)
bike_number_entry = tk.Entry(bike_frame, width=10)
bike_number_entry.pack(side="left")

# Rename toggle
rename_var = tk.BooleanVar(value=True)
rename_checkbox = tk.Checkbutton(bottom_frame, text="Enable Renaming Mode", variable=rename_var)
rename_checkbox.pack(pady=5)

# Metallic transparency toggle
transparency_var = tk.BooleanVar(value=True)
transparency_checkbox = tk.Checkbutton(
    bottom_frame, text="Enable adding transparency to metallic maps", variable=transparency_var
)
transparency_checkbox.pack(pady=5)

# Export button
export_button = tk.Button(
    bottom_frame, text="Export Textures",
    font=("Segoe UI", 12, "bold"), bg="#0078D7", fg="white",
    width=20, height=2, command=export_textures
)
export_button.pack(pady=10)

# Footer label below export button
footer_label = tk.Label(bottom_frame, text="Made by THEE OH", font=("Segoe UI", 9), fg="gray")
footer_label.pack(pady=(0,10))

root.mainloop()
