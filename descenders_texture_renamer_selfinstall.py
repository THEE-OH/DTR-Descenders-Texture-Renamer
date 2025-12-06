import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image

# ----------------------------
# Ensure tkinterdnd2 is installed
# ----------------------------
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
        sys.exit(1)

# ----------------------------
# Sorting + Processing Helpers
# ----------------------------
def sort_file_into_slot(filename):
    """Return the entry key for a given filename (bike-relevant)."""
    name = filename.lower()
    if "frame" in name:
        return "frame_metal" if "metal" in name or "ms" in name else "frame_base"
    elif "gear" in name:
        return "gear_metal" if "metal" in name or "ms" in name else "gear_base"
    elif "handle" in name or "bar" in name:
        return "handle_metal" if "metal" in name or "ms" in name else "handle_base"
    elif "wheel" in name or "wheels" in name:
        return "wheels_metal" if "metal" in name or "ms" in name else "wheels_base"
    return None

def apply_metallic_transparency(input_file, output_file):
    img = Image.open(input_file).convert("RGBA")
    new_data = []
    for r, g, b, *_ in img.getdata():
        gray = (r + g + b) / 3
        alpha = int((gray / 255) * 255)
        new_data.append((r, g, b, alpha))
    img.putdata(new_data)
    img.save(output_file)

# ----------------------------
# Browse + Drop helpers
# ----------------------------
def browse_file(entry):
    file = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.tga")])
    if file:
        entry.delete(0, tk.END)
        entry.insert(0, file)

def bind_drop(entry):
    entry.drop_target_register(DND_FILES)
    entry.dnd_bind("<<Drop>>", lambda e: entry.delete(0, tk.END) or entry.insert(0, e.data.strip("{}")))

# ----------------------------
# GUI
# ----------------------------
root = TkinterDnD.Tk()
root.title("Descenders Texture Renamer - Made by THEE OH")
root.geometry("650x700")
root.resizable(False, False)

# Icon
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

icon_path = os.path.join(base_path, "theicon.png")
if os.path.exists(icon_path):
    try:
        root.iconphoto(True, tk.PhotoImage(file=icon_path))
    except Exception:
        pass  # ignore icon load errors

# Notebook Tabs
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

tab_bikes = ttk.Frame(notebook)
tab_clothes = ttk.Frame(notebook)
tab_helmets = ttk.Frame(notebook)

notebook.add(tab_bikes, text="Bikes")
notebook.add(tab_clothes, text="Clothes")
notebook.add(tab_helmets, text="Helmets / Goggles")

# ----------------------------
# BIKE TAB
# ----------------------------
bike_entries = {}

def bike_row(label, key, parent):
    row = tk.Frame(parent)
    row.pack(pady=4, padx=20, fill="x")
    tk.Label(row, text=label, width=20, anchor="w").pack(side="left")
    entry = tk.Entry(row, width=40)
    entry.pack(side="left", padx=5)
    btn = tk.Button(row, text="Browse", command=lambda: browse_file(entry))
    btn.pack(side="left")
    bind_drop(entry)
    bike_entries[key] = entry

# Create the 8 entry rows
bike_row("Frame Base", "frame_base", tab_bikes)
bike_row("Frame Metallic", "frame_metal", tab_bikes)
bike_row("Gear Base", "gear_base", tab_bikes)
bike_row("Gear Metallic", "gear_metal", tab_bikes)
bike_row("Handlebar Base", "handle_base", tab_bikes)
bike_row("Handlebar Metallic", "handle_metal", tab_bikes)
bike_row("Wheels Base", "wheels_base", tab_bikes)
bike_row("Wheels Metallic", "wheels_metal", tab_bikes)

# Bulk drag & drop area for bikes (restores the feature)
bulk_frame = tk.LabelFrame(tab_bikes, text="Bulk Drag & Drop (Bikes)", padx=10, pady=8)
bulk_frame.pack(padx=20, pady=(10, 6), fill="x")

bulk_label = tk.Label(bulk_frame, text="Drop multiple bike textures here — up to 8 files. Files are auto-sorted by name.", bg="#f0f0f0", height=3)
bulk_label.pack(fill="x", padx=6, pady=4)

def handle_bike_bulk_drop(event):
    raw = event.data.strip()
    # Windows drop format often like: {C:\path\file.png} {C:\path\file2.png}
    parts = raw.replace("}{", "} {").split()
    cleaned = []
    for p in parts:
        p = p.strip()
        if p.startswith("{") and p.endswith("}"):
            p = p[1:-1]
        cleaned.append(p)
    assigned = []
    for path in cleaned:
        name = os.path.basename(path)
        slot = sort_file_into_slot(name)
        if slot and slot in bike_entries:
            bike_entries[slot].delete(0, tk.END)
            bike_entries[slot].insert(0, path)
            assigned.append(slot)
    if assigned:
        messagebox.showinfo("Files Assigned", f"Assigned: {', '.join(assigned)}")
    else:
        messagebox.showwarning("No Match", "No valid bike texture names detected in dropped files.")

bulk_label.drop_target_register(DND_FILES)
bulk_label.dnd_bind("<<Drop>>", handle_bike_bulk_drop)

# Bike bottom controls
bike_bottom = tk.Frame(tab_bikes)
bike_bottom.pack(pady=12)

# Bike number and controls arranged horizontally for clarity
bike_controls = tk.Frame(bike_bottom)
bike_controls.pack()

tk.Label(bike_controls, text="Bike Number:").grid(row=0, column=0, padx=6)
bike_num = tk.Entry(bike_controls, width=10)
bike_num.grid(row=0, column=1, padx=6)

rename_bikes = tk.BooleanVar(value=True)
tk.Checkbutton(bike_controls, text="Enable Renaming Mode", variable=rename_bikes).grid(row=0, column=2, padx=6)

metal_toggle = tk.BooleanVar(value=True)
tk.Checkbutton(bike_controls, text="Enable adding transparency to metallic maps", variable=metal_toggle).grid(row=0, column=3, padx=6)

# Export function for bikes
def export_bikes():
    num = bike_num.get().strip()
    if rename_bikes.get() and not num.isdigit():
        messagebox.showerror("Invalid Input", "Bike number must be numeric")
        return

    outdir = filedialog.askdirectory()
    if not outdir:
        return

    pairs = {
        "frame": ("frame_base", "frame_metal"),
        "gear": ("gear_base", "gear_metal"),
        "handlebar": ("handle_base", "handle_metal"),
        "wheels": ("wheels_base", "wheels_metal")
    }

    exported = []
    for part, (base, metal) in pairs.items():
        base_in = bike_entries[base].get().strip()
        metal_in = bike_entries[metal].get().strip()

        if rename_bikes.get():
            base_out = os.path.join(outdir, f"{num}_{part}_{num}_D.png")
            metal_out = os.path.join(outdir, f"{num}_{part}_{num}_MS.png")
        else:
            base_out = os.path.join(outdir, os.path.basename(base_in)) if base_in else None
            metal_out = os.path.join(outdir, os.path.basename(metal_in)) if metal_in else None

        if base_in:
            try:
                shutil.copy2(base_in, base_out)
                exported.append(f"{part} base")
            except Exception as e:
                messagebox.showwarning("Copy failed", f"Failed to copy base for {part}: {e}")

        if metal_in:
            try:
                if metal_toggle.get():
                    apply_metallic_transparency(metal_in, metal_out)
                else:
                    shutil.copy2(metal_in, metal_out)
                exported.append(f"{part} metallic")
            except Exception as e:
                messagebox.showwarning("Processing failed", f"Failed handling metallic for {part}: {e}")

    if exported:
        messagebox.showinfo("Done", "Exported: " + ", ".join(exported))
    else:
        messagebox.showwarning("No files", "No bike textures were exported.")

tk.Button(
    bike_bottom,
    text="Export Bikes",
    bg="#0078D7",
    fg="white",
    font=("Segoe UI", 11, "bold"),
    width=22,
    height=2,
    command=export_bikes
).pack(pady=10)

# ----------------------------
# CLOTHES TAB
# ----------------------------
clo_frame = tk.Frame(tab_clothes, pady=20)
clo_frame.pack()

tk.Label(clo_frame, text="Clothes Base Colour Map").pack()

clo_entry = tk.Entry(clo_frame, width=45)
clo_entry.pack(pady=5)
bind_drop(clo_entry)

tk.Button(clo_frame, text="Browse", command=lambda: browse_file(clo_entry)).pack(pady=4)

clo_number = tk.Entry(clo_frame, width=10)
tk.Label(clo_frame, text="Clothes Number:").pack(pady=5)
clo_number.pack()

def export_clothes():
    num = clo_number.get().strip()
    file = clo_entry.get().strip()
    if not num.isdigit() or not file:
        messagebox.showerror("Error", "Invalid input")
        return

    out = filedialog.askdirectory()
    if not out:
        return

    try:
        shutil.copy2(file, os.path.join(out, f"{num}_{num}_D.png"))
        messagebox.showinfo("Done", "Clothes exported!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export clothes: {e}")

tk.Button(tab_clothes, text="Export Clothes", bg="#0078D7", fg="white", height=2, width=20,
          command=export_clothes).pack(pady=15)

# ----------------------------
# HELMET / GOGGLES TAB
# ----------------------------
hel_entries = {}

def hel_row(text, key):
    row = tk.Frame(tab_helmets)
    row.pack(pady=5)
    tk.Label(row, text=text, width=18, anchor="w").pack(side="left")
    e = tk.Entry(row, width=40)
    e.pack(side="left", padx=4)
    bind_drop(e)
    hel_entries[key] = e
    tk.Button(row, text="Browse", command=lambda: browse_file(e)).pack(side="left")

hel_row("Base Colour", "base")
hel_row("Metallic Map", "metal")

hel_number = tk.Entry(tab_helmets, width=10)
tk.Label(tab_helmets, text="Helmet/Goggle Number:").pack(pady=5)
hel_number.pack()

def export_helmet():
    num = hel_number.get().strip()
    base = hel_entries["base"].get().strip()
    metal = hel_entries["metal"].get().strip()

    if not num.isdigit():
        messagebox.showerror("Error", "Number required")
        return

    out = filedialog.askdirectory()
    if not out:
        return

    try:
        if base:
            shutil.copy2(base, os.path.join(out, f"{num}_{num}_D.png"))
        if metal:
            apply_metallic_transparency(metal, os.path.join(out, f"{num}_{num}_MS.png"))
        messagebox.showinfo("Done", "Helmet / goggles exported!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export helmet/goggles: {e}")

tk.Button(
    tab_helmets,
    text="Export Helmets / Goggles",
    bg="#0078D7",
    fg="white",
    height=2,
    width=24,
    command=export_helmet
).pack(pady=10)

# ----------------------------
# FOOTER
# ----------------------------
footer = tk.Label(bike_bottom, text="Made by THEE OH", fg="gray")
footer.pack(pady=(0,10))

root.mainloop()
