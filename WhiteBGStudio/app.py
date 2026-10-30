import os, sys, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageOps, ImageFilter
import numpy as np

# Use the bundled model when packaged, enabling offline processing after installation.
def resource_path(relative):
    return os.path.join(getattr(sys, "_MEIPASS", os.path.abspath(".")), relative)

bundled_model = resource_path(".u2net")
if os.path.isdir(bundled_model):
    os.environ["U2NET_HOME"] = bundled_model

from rembg import remove, new_session

APP_NAME = "WhiteBG Studio"
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

def clean_mask_and_defringe(result):
    """Reduce background-colored edge halos before compositing onto white."""
    rgba = result.convert("RGBA")
    alpha = rgba.getchannel("A")
    # Remove faint semi-transparent shadow/fringe pixels and contract the
    # segmentation by a tiny amount, then keep a slight antialias transition.
    alpha = alpha.point(lambda a: 0 if a < 90 else (255 if a > 210 else int((a - 90) * 255 / 120)))
    # Contract the mask more decisively so broad ear/neck/shoulder halos are
    # excluded instead of being carried onto the white canvas.
    alpha = alpha.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(0.35))
    arr = np.asarray(rgba).astype(np.float32)
    a = np.asarray(alpha).astype(np.float32) / 255.0
    rgb = arr[:, :, :3]
    # Brighten only boundary pixels to neutralize brown/grey contamination
    # left by the old background; keep fully opaque face/clothing pixels intact.
    edge = (a > 0.01) & (a < 0.98)
    if np.any(edge):
        strength = ((0.98 - a) / 0.98 * 0.72)
        rgb[edge] = rgb[edge] * (1.0 - strength[edge, None]) + 255.0 * strength[edge, None]
    arr[:, :, :3] = np.clip(rgb, 0, 255)
    arr[:, :, 3] = a * 255.0
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_NAME)
        root.geometry("1000x700")
        root.minsize(820, 580)
        root.configure(bg="#111214")
        self.source = tk.StringVar()
        self.output = tk.StringVar()
        self.status = tk.StringVar(value="Choose photos or a source folder to begin.")
        self.selected = []
        self.busy = False
        self.build()

    def build(self):
        # E-PIX BG STUDIO dashboard inspired by the supplied reference.
        bg = "#111214"
        panel = "#202226"
        silver = "#c9cbd0"
        accent = "#6f91b7"
        self.root.configure(bg=bg)

        shell = tk.Frame(self.root, bg=bg)
        shell.pack(fill="both", expand=True)

        sidebar = tk.Frame(shell, bg=panel, width=205, highlightthickness=1,
                           highlightbackground="#59606b")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        def nav_button(icon, title, command):
            item = tk.Frame(sidebar, bg=panel, cursor="hand2")
            item.pack(fill="x", padx=8, pady=(24, 8))
            ico = tk.Label(item, text=icon, font=("Segoe UI Symbol", 38),
                           fg="#d5d7dc", bg=panel, cursor="hand2")
            ico.pack(pady=(3, 0))
            txt = tk.Label(item, text=title, font=("Segoe UI", 13),
                           fg="#e1e2e5", bg=panel, cursor="hand2")
            txt.pack(pady=(0, 4))
            for widget in (item, ico, txt):
                widget.bind("<Button-1>", lambda _e, fn=command: fn())
                widget.bind("<Enter>", lambda _e, w=item: w.configure(bg="#30343b"))
                widget.bind("<Leave>", lambda _e, w=item: w.configure(bg=panel))
            return item

        nav_button("▰", "Choose Folder", self.pick_folder)
        nav_button("▣", "Choose Photo", self.pick_files)
        nav_button("⇧", "Output Folder", self.pick_output)

        main = tk.Frame(shell, bg=bg)
        main.pack(side="left", fill="both", expand=True)

        # Center branding
        brand = tk.Frame(main, bg=bg)
        brand.place(relx=0.5, rely=0.43, anchor="center")
        logo = tk.Label(brand, text="▣", font=("Segoe UI Symbol", 58, "bold"),
                        fg="#d5d7dc", bg="#33363b", width=3, height=1,
                        relief="ridge", bd=4)
        logo.pack(pady=(0, 18))
        tk.Label(brand, text="E - PIX", font=("Segoe UI", 42, "bold"),
                 fg="#e4e4e6", bg=bg).pack()
        tk.Label(brand, text="B G   S T U D I O", font=("Segoe UI Light", 20),
                 fg="#c6c7ca", bg=bg).pack(pady=(0, 14))

        self.selection_label = tk.Label(main, text="Choose a folder or individual photos",
                 font=("Segoe UI", 10), fg="#9da3ad", bg=bg)
        self.selection_label.place(relx=0.5, rely=0.68, anchor="center")

        self.go = tk.Button(main, text="START", command=self.start,
                 font=("Segoe UI", 20, "bold"), fg="#e6e7e9", bg="#45484e",
                 activebackground="#5a6069", activeforeground="white",
                 relief="ridge", bd=4, padx=28, pady=8, cursor="hand2")
        self.go.place(relx=0.5, rely=0.79, anchor="center")

        footer = tk.Frame(main, bg=bg)
        footer.pack(side="bottom", fill="x", padx=22, pady=16)
        self.progress = ttk.Progressbar(footer, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 7))
        self.status_label = tk.Label(footer, textvariable=self.status,
                 font=("Segoe UI", 9), fg="#c4c7cc", bg=bg, anchor="w")
        self.status_label.pack(fill="x")
        self.log = tk.Text(main, height=4, state="disabled", wrap="word",
                 bg="#191b1f", fg="#d5d8de", insertbackground="white",
                 relief="flat", font=("Consolas", 9))
        self.log.pack(side="bottom", fill="x", padx=22, pady=(0, 4))

        self.recursive = tk.BooleanVar(value=False)
        # Keep the advanced option accessible without cluttering the main design.
        tk.Checkbutton(main, text="Include subfolders", variable=self.recursive,
                 bg=bg, fg="#aeb4bd", selectcolor="#25282d", activebackground=bg,
                 activeforeground="white", font=("Segoe UI", 9)).place(
                 relx=0.5, rely=0.73, anchor="center")

    def pick_folder(self):
        p = filedialog.askdirectory(title="Select source photo folder")
        if p:
            self.source.set(p); self.selected = []
            self.selection_label.configure(text="Source folder: " + p)

    def pick_files(self):
        p = filedialog.askopenfilenames(title="Select photos", filetypes=[("Images","*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff")])
        if p:
            self.selected = list(p); self.source.set(f"{len(p)} photos selected")
            self.selection_label.configure(text=f"{len(p)} photo(s) selected")

    def pick_output(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p:
            self.output.set(p)
            self.say("Output folder: " + p)
            self.status.set("Output folder selected.")

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
                # Alpha matting improves fine hair and removes more of the original
                # background fringe than the default binary-ish mask.
                result = remove(
                    im,
                    session=session,
                    alpha_matting=True,
                    alpha_matting_foreground_threshold=250,
                    alpha_matting_background_threshold=20,
                    alpha_matting_erode_size=20,
                ).convert("RGBA")
                result = clean_mask_and_defringe(result)
                # Ensure the final canvas is genuinely pure white.
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
