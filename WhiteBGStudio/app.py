import os, sys, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageOps

# Use the bundled model when packaged, enabling offline processing after installation.
def resource_path(relative):
    return os.path.join(getattr(sys, "_MEIPASS", os.path.abspath(".")), relative)

bundled_model = resource_path(".u2net")
if os.path.isdir(bundled_model):
    os.environ["U2NET_HOME"] = bundled_model

from rembg import remove, new_session

APP_NAME = "WhiteBG Studio"
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_NAME)
        root.geometry("760x540")
        root.minsize(650, 460)
        self.source = tk.StringVar()
        self.output = tk.StringVar()
        self.status = tk.StringVar(value="Choose photos or a source folder to begin.")
        self.selected = []
        self.busy = False
        self.build()

    def build(self):
        frame = ttk.Frame(self.root, padding=18); frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="WhiteBG Studio", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Automatic AI background replacement • Pure white #FFFFFF").pack(anchor="w", pady=(2,16))
        a = ttk.LabelFrame(frame, text="Input photos", padding=10); a.pack(fill="x", pady=5)
        ttk.Entry(a, textvariable=self.source).pack(side="left", fill="x", expand=True, padx=(0,8))
        ttk.Button(a, text="Choose folder", command=self.pick_folder).pack(side="left")
        ttk.Button(a, text="Choose files", command=self.pick_files).pack(side="left", padx=(6,0))
        b = ttk.LabelFrame(frame, text="Output folder", padding=10); b.pack(fill="x", pady=5)
        ttk.Entry(b, textvariable=self.output).pack(side="left", fill="x", expand=True, padx=(0,8))
        ttk.Button(b, text="Browse", command=self.pick_output).pack(side="left")
        self.recursive = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Include subfolders", variable=self.recursive).pack(anchor="w", pady=(8,2))
        ttk.Label(frame, text="Originals are never changed. Existing output files are never overwritten.",
                  foreground="#555").pack(anchor="w", pady=(2,10))
        self.progress = ttk.Progressbar(frame, mode="determinate"); self.progress.pack(fill="x", pady=4)
        ttk.Label(frame, textvariable=self.status).pack(anchor="w")
        self.log = tk.Text(frame, height=8, state="disabled", wrap="word"); self.log.pack(fill="both", expand=True, pady=8)
        self.go = ttk.Button(frame, text="Start background removal", command=self.start); self.go.pack(anchor="e")

    def pick_folder(self):
        p = filedialog.askdirectory(title="Select source photo folder")
        if p: self.source.set(p); self.selected = []

    def pick_files(self):
        p = filedialog.askopenfilenames(title="Select photos", filetypes=[("Images","*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff")])
        if p: self.selected = list(p); self.source.set(f"{len(p)} photos selected")

    def pick_output(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p: self.output.set(p)

    def say(self, message):
        self.log.configure(state="normal"); self.log.insert("end", message + "\n")
        self.log.see("end"); self.log.configure(state="disabled")

    def inputs(self):
        if self.selected: return [Path(p) for p in self.selected]
        p = Path(self.source.get())
        if not p.is_dir(): return []
        it = p.rglob("*") if self.recursive.get() else p.iterdir()
        return [x for x in it if x.is_file() and x.suffix.lower() in EXTS]

    def start(self):
        if self.busy: return
        if not self.output.get().strip():
            messagebox.showerror(APP_NAME, "Choose an output folder first."); return
        paths = self.inputs()
        if not paths:
            messagebox.showwarning(APP_NAME, "Choose a source folder or image files."); return
        out = Path(self.output.get()); out.mkdir(parents=True, exist_ok=True)
        self.busy = True; self.go.configure(state="disabled")
        self.progress.configure(maximum=len(paths), value=0)
        threading.Thread(target=self.process, args=(paths,out), daemon=True).start()

    def process(self, paths, out):
        good = bad = 0
        try:
            session = new_session("u2net")
        except Exception as e:
            self.root.after(0, self.say, "AI model error: " + str(e))
            self.root.after(0, self.done, 0, len(paths)); return
        for i, src in enumerate(paths, 1):
            try:
                with Image.open(src) as im:
                    im = ImageOps.exif_transpose(im).convert("RGBA")
                result = remove(im, session=session).convert("RGBA")
                white = Image.new("RGBA", result.size, (255,255,255,255))
                white.alpha_composite(result)
                dest = out / (src.stem + ".jpg")
                n = 1
                while dest.exists():
                    dest = out / f"{src.stem}_{n}.jpg"; n += 1
                white.convert("RGB").save(dest, "JPEG", quality=95, optimize=True)
                good += 1; self.root.after(0, self.say, "Saved: " + dest.name)
            except Exception as e:
                bad += 1; self.root.after(0, self.say, f"ERROR {src.name}: {e}")
            self.root.after(0, self.progress.configure, {"value": i})
            self.root.after(0, self.status.set, f"Processed {i} of {len(paths)}")
        self.root.after(0, self.done, good, bad)

    def done(self, good, bad):
        self.busy = False; self.go.configure(state="normal")
        self.status.set(f"Finished • Successful: {good} • Errors: {bad}")
        (messagebox.showinfo if bad == 0 else messagebox.showwarning)(
            APP_NAME, f"Processing finished.\nSuccessful: {good}\nErrors: {bad}")

if __name__ == "__main__":
    root = tk.Tk()
    try: ttk.Style().theme_use("vista")
    except tk.TclError: pass
    App(root); root.mainloop()
