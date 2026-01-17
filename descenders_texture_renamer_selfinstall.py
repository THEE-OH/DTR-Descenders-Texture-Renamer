import os
import sys
import shutil
import subprocess
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

# ----------------------------
# 1. Dependency Check
# ----------------------------
def install_libs():
    required = ["customtkinter", "tkinterdnd2", "Pillow"]
    missing = []
    
    import importlib.util
    if importlib.util.find_spec("customtkinter") is None: missing.append("customtkinter")
    if importlib.util.find_spec("tkinterdnd2") is None: missing.append("tkinterdnd2")
    if importlib.util.find_spec("PIL") is None: missing.append("Pillow")

    if missing:
        root_temp = tk.Tk()
        root_temp.withdraw()
        if messagebox.askyesno("Missing Libraries", f"Install required libraries?\n({', '.join(missing)})"):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            except Exception as e:
                messagebox.showerror("Error", f"Install failed: {e}")
                sys.exit(1)
        else:
            sys.exit(1)

install_libs()

import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES

# ----------------------------
# 2. Modern UI Config
# ----------------------------
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue") 

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

# ----------------------------
# 3. Logic Functions
# ----------------------------
def sort_file_into_slot(filename):
    name = filename.lower()
    if "frame" in name: return "frame_metal" if "metal" in name or "ms" in name else "frame_base"
    elif "gear" in name: return "gear_metal" if "metal" in name or "ms" in name else "gear_base"
    elif "handle" in name or "bar" in name: return "handle_metal" if "metal" in name or "ms" in name else "handle_base"
    elif "wheel" in name or "wheels" in name: return "wheels_metal" if "metal" in name or "ms" in name else "wheels_base"
    return None

def apply_metallic_transparency(input_file, output_file):
    try:
        img = Image.open(input_file).convert("RGBA")
        new_data = []
        for r, g, b, *_ in img.getdata():
            gray = (r + g + b) / 3
            alpha = int((gray / 255) * 255)
            new_data.append((r, g, b, alpha))
        img.putdata(new_data)
        img.save(output_file)
    except Exception as e:
        print(f"Error: {e}")

def browse_file(entry):
    f = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.tga")])
    if f: entry.delete(0, tk.END); entry.insert(0, f)

def bind_drop(entry):
    entry.drop_target_register(DND_FILES)
    entry.dnd_bind("<<Drop>>", lambda e: entry.delete(0, tk.END) or entry.insert(0, e.data.strip("{}")))

# ----------------------------
# 4. Main Application
# ----------------------------
app = App()
app.title("Descenders Texture Renamer")
app.geometry("720x880")
app.resizable(False, False)

# Icon
if getattr(sys, 'frozen', False): base_path = sys._MEIPASS
else: base_path = os.path.dirname(__file__)
if os.path.exists(os.path.join(base_path, "theicon.png")):
    try: app.iconphoto(True, tk.PhotoImage(file=os.path.join(base_path, "theicon.png")))
    except: pass

# Header
ctk.CTkLabel(app, text="Descenders Texture Renamer", font=("Roboto Medium", 22)).pack(pady=(20, 5))

# Tabs
tabview = ctk.CTkTabview(app, width=680, height=700, corner_radius=15, fg_color=("gray95", "gray10"))
tabview.pack(padx=20, pady=10, fill="both", expand=True)

tab_bikes = tabview.add("Bikes")
tab_clothes = tabview.add("Clothes")
tab_helmets = tabview.add("Helmets / Goggles")

# =============================================================================
# TAB 1: BIKES
# =============================================================================
bike_entries = {}

def create_input_row(parent, label_text, key, dictionary):
    # Distinct "Card" background for each row
    frame = ctk.CTkFrame(parent, fg_color=("white", "#212121"), corner_radius=8, border_width=1, border_color=("gray80", "#2b2b2b"))
    frame.pack(fill="x", pady=3, padx=5)
    
    lbl = ctk.CTkLabel(frame, text=label_text, width=130, anchor="w", font=("Roboto", 12))
    lbl.pack(side="left", padx=(15, 0))
    
    # Flat entry style
    entry = ctk.CTkEntry(frame, width=350, height=32, border_width=0, fg_color=("gray95", "#2b2b2b"), placeholder_text="Browse or Drop file...")
    entry.pack(side="left", padx=10, pady=5)
    bind_drop(entry)
    dictionary[key] = entry
    
    # Subtle browse button
    btn = ctk.CTkButton(frame, text="Browse", width=70, height=28, fg_color=("gray80", "#3a3a3a"), hover_color=("gray70", "#4a4a4a"), text_color=("black", "white"), command=lambda: browse_file(entry))
    btn.pack(side="left", padx=(0, 10))

# Inputs
create_input_row(tab_bikes, "Frame Base", "frame_base", bike_entries)
create_input_row(tab_bikes, "Frame Metallic", "frame_metal", bike_entries)
create_input_row(tab_bikes, "Gear Base", "gear_base", bike_entries)
create_input_row(tab_bikes, "Gear Metallic", "gear_metal", bike_entries)
create_input_row(tab_bikes, "Handlebar Base", "handle_base", bike_entries)
create_input_row(tab_bikes, "Handlebar Metallic", "handle_metal", bike_entries)
create_input_row(tab_bikes, "Wheels Base", "wheels_base", bike_entries)
create_input_row(tab_bikes, "Wheels Metallic", "wheels_metal", bike_entries)

# --- DRAG & DROP ZONE ---
bulk_frame = ctk.CTkFrame(
    tab_bikes, 
    fg_color=("#F0F0F0", "#181818"), 
    border_width=2, 
    border_color=("#BBBBBB", "#333333"), 
    corner_radius=12
)
bulk_frame.pack(fill="x", padx=10, pady=15)

bulk_lbl = ctk.CTkLabel(
    bulk_frame, 
    text="Drag and Drop\nAuto Sorts Textures", 
    font=("Roboto Medium", 15),
    text_color=("gray40", "gray70")
)
bulk_lbl.pack(pady=20)

def handle_bike_bulk(event):
    parts = event.data.strip().replace("}{", "} {").split()
    cleaned = [p.strip().strip("{}") for p in parts]
    found = 0
    for path in cleaned:
        slot = sort_file_into_slot(os.path.basename(path))
        if slot and slot in bike_entries:
            bike_entries[slot].delete(0, tk.END); bike_entries[slot].insert(0, path)
            found += 1
    
    if found:
        bulk_lbl.configure(text=f"✅ Sorted {found} files successfully!", text_color="#2CC985")
        app.after(3000, lambda: bulk_lbl.configure(text="Drag and Drop\nAuto Sorts Textures", text_color=("gray40", "gray70")))
    else:
        bulk_lbl.configure(text="⚠️ No matching filenames found.", text_color="orange")
        app.after(3000, lambda: bulk_lbl.configure(text="Drag and Drop\nAuto Sorts Textures", text_color=("gray40", "gray70")))

bulk_lbl.drop_target_register(DND_FILES)
bulk_lbl.dnd_bind("<<Drop>>", handle_bike_bulk)

# --- CONTROLS BAR ---
controls_frame = ctk.CTkFrame(tab_bikes, fg_color=("white", "#212121"), corner_radius=10)
controls_frame.pack(pady=5, padx=10, fill="x")

# Centered container inside the bar
c_inner = ctk.CTkFrame(controls_frame, fg_color="transparent")
c_inner.pack(pady=10)

ctk.CTkLabel(c_inner, text="Bike Number:", font=("Roboto", 12, "bold")).pack(side="left", padx=5)
bike_num_entry = ctk.CTkEntry(c_inner, width=60, justify="center", corner_radius=10)
bike_num_entry.pack(side="left", padx=10)

rename_bikes_var = ctk.BooleanVar(value=True)
ctk.CTkCheckBox(c_inner, text="Renaming Mode", variable=rename_bikes_var, font=("Roboto", 12)).pack(side="left", padx=15)

metal_bikes_var = ctk.BooleanVar(value=True)
ctk.CTkCheckBox(c_inner, text="Metallic Transparency", variable=metal_bikes_var, font=("Roboto", 12)).pack(side="left", padx=5)

def export_bikes():
    num = bike_num_entry.get().strip()
    if rename_bikes_var.get() and not num.isdigit(): return messagebox.showerror("Error", "Enter a valid bike number.")
    out = filedialog.askdirectory()
    if not out: return

    pairs = {"frame":("frame_base","frame_metal"), "gear":("gear_base","gear_metal"), 
             "handlebar":("handle_base","handle_metal"), "wheels":("wheels_base","wheels_metal")}
    count = 0
    for part, (b, m) in pairs.items():
        b_p, m_p = bike_entries[b].get().strip(), bike_entries[m].get().strip()
        if b_p:
            dst = os.path.join(out, f"{num}_{part}_{num}_D.png" if rename_bikes_var.get() else os.path.basename(b_p))
            try: shutil.copy2(b_p, dst); count+=1
            except: pass
        if m_p:
            dst = os.path.join(out, f"{num}_{part}_{num}_MS.png" if rename_bikes_var.get() else os.path.basename(m_p))
            try:
                if metal_bikes_var.get(): apply_metallic_transparency(m_p, dst)
                else: shutil.copy2(m_p, dst)
                count+=1
            except: pass
    messagebox.showinfo("Export", f"Processed {count} files.")

ctk.CTkButton(tab_bikes, text="EXPORT BIKE", height=45, width=200, font=("Roboto Medium", 15), fg_color="#2CC985", hover_color="#26ad72", corner_radius=22, command=export_bikes).pack(pady=20)


# =============================================================================
# TAB 2: CLOTHES
# =============================================================================
clo_frame = ctk.CTkFrame(tab_clothes, fg_color="transparent")
clo_frame.pack(expand=True)

ctk.CTkLabel(clo_frame, text="Clothes Base Colour Map", font=("Roboto Medium", 16)).pack(pady=(0, 15))

clo_entry = ctk.CTkEntry(clo_frame, width=400, height=40, placeholder_text="Drag file here...", justify="center", corner_radius=10)
clo_entry.pack(pady=5)
bind_drop(clo_entry)

ctk.CTkButton(clo_frame, text="Browse File", width=120, height=32, fg_color=("gray80", "#3a3a3a"), hover_color=("gray70", "#4a4a4a"), text_color=("black", "white"), command=lambda: browse_file(clo_entry)).pack(pady=10)

ctk.CTkLabel(clo_frame, text="Clothes Number", font=("Roboto", 12)).pack(pady=(20, 5))
clo_num_entry = ctk.CTkEntry(clo_frame, width=80, justify="center", corner_radius=10)
clo_num_entry.pack(pady=5)

def export_clothes():
    num, f = clo_num_entry.get().strip(), clo_entry.get().strip()
    if not num.isdigit() or not f: return messagebox.showerror("Error", "Invalid input")
    out = filedialog.askdirectory()
    if not out: return
    try: shutil.copy2(f, os.path.join(out, f"{num}_{num}_D.png")); messagebox.showinfo("Success", "Clothes exported.")
    except Exception as e: messagebox.showerror("Error", str(e))

ctk.CTkButton(tab_clothes, text="EXPORT CLOTHES", height=45, width=200, font=("Roboto Medium", 15), fg_color="#3B8ED0", corner_radius=22, command=export_clothes).pack(pady=30)


# =============================================================================
# TAB 3: HELMETS / GOGGLES
# =============================================================================
hel_entries = {}
hel_center = ctk.CTkFrame(tab_helmets, fg_color="transparent")
hel_center.pack(expand=True, fill="x", padx=20)

ctk.CTkLabel(hel_center, text="", height=20).pack() 
# Helper to reuse row style
def create_hel_row(label, key):
    frame = ctk.CTkFrame(hel_center, fg_color=("white", "#212121"), corner_radius=8, border_width=1, border_color=("gray80", "#2b2b2b"))
    frame.pack(fill="x", pady=5)
    ctk.CTkLabel(frame, text=label, width=120, anchor="w").pack(side="left", padx=15)
    e = ctk.CTkEntry(frame, width=350, height=32, border_width=0, fg_color=("gray95", "#2b2b2b"))
    e.pack(side="left", padx=10, pady=5)
    bind_drop(e)
    hel_entries[key] = e
    ctk.CTkButton(frame, text="Browse", width=70, height=28, fg_color=("gray80", "#3a3a3a"), text_color=("black", "white"), command=lambda: browse_file(e)).pack(side="left")

create_hel_row("Base Colour", "base")
create_hel_row("Metallic Map", "metal")

# Vertical Options Stack
opts = ctk.CTkFrame(hel_center, fg_color="transparent")
opts.pack(pady=30)

num_row = ctk.CTkFrame(opts, fg_color="transparent")
num_row.pack(pady=5)
ctk.CTkLabel(num_row, text="Helmet/Goggle #:", font=("Roboto", 12)).pack(side="left", padx=10)
hel_num_entry = ctk.CTkEntry(num_row, width=80, justify="center", corner_radius=10)
hel_num_entry.pack(side="left")

hel_rename_var = ctk.BooleanVar(value=True)
ctk.CTkCheckBox(opts, text="Enable Renaming Mode", variable=hel_rename_var).pack(pady=10)

hel_metal_var = ctk.BooleanVar(value=True)
ctk.CTkCheckBox(opts, text="Enable Metallic Transparency", variable=hel_metal_var).pack(pady=5)

def export_helmets():
    num, b, m = hel_num_entry.get().strip(), hel_entries['base'].get().strip(), hel_entries['metal'].get().strip()
    if hel_rename_var.get() and not num.isdigit(): return messagebox.showerror("Error", "Number required.")
    out = filedialog.askdirectory()
    if not out: return
    try:
        if b: shutil.copy2(b, os.path.join(out, f"{num}_{num}_D.png" if hel_rename_var.get() else os.path.basename(b)))
        if m:
            dst = os.path.join(out, f"{num}_{num}_MS.png" if hel_rename_var.get() else os.path.basename(m))
            if hel_metal_var.get(): apply_metallic_transparency(m, dst)
            else: shutil.copy2(m, dst)
        messagebox.showinfo("Success", "Files exported.")
    except Exception as e: messagebox.showerror("Error", str(e))

ctk.CTkButton(tab_helmets, text="EXPORT HELMET", height=45, width=200, font=("Roboto Medium", 15), fg_color="#E04F5F", hover_color="#C43343", corner_radius=22, command=export_helmets).pack(pady=20)


# =============================================================================
# FOOTER
# =============================================================================
footer_frame = ctk.CTkFrame(app, fg_color=("white", "#181818"), corner_radius=20, height=50)
footer_frame.pack(side="bottom", fill="x", padx=20, pady=20)

btn_gh = ctk.CTkButton(footer_frame, text="GitHub", width=90, height=28, fg_color="#24292e", hover_color="#444c56", corner_radius=14, command=lambda: webbrowser.open("https://github.com/THEE-OH"))
btn_gh.pack(side="left", padx=(15, 8), pady=10)

btn_ds = ctk.CTkButton(footer_frame, text="Discord", width=90, height=28, fg_color="#5865F2", hover_color="#4752C4", corner_radius=14, command=lambda: webbrowser.open("https://discord.gg/tfjRXa4BNx"))
btn_ds.pack(side="left", padx=0, pady=10)

ctk.CTkLabel(footer_frame, text="Made by THEE OH", text_color="gray50", font=("Roboto", 11)).pack(side="right", padx=20)

app.mainloop()
