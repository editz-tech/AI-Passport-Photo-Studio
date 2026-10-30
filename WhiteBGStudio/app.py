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
        root.geometry("1510x900")
        root.minsize(1200, 760)
        root.configure(bg="#08090b")
        self.source = tk.StringVar()
        self.output = tk.StringVar()
        self.status = tk.StringVar(value="Choose photos or a source folder to begin.")
        self.selected = []
        self.busy = False
        self.build()

    def build(self):
        # Fixed-proportion E-PIX layout: supplied design language on the left,
        # with a dedicated live processing/status area on the right.
        self.bg = "#090a0c"
        self.panel = "#202226"
        self.canvas = tk.Canvas(self.root, bg=self.bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.draw_dashboard)
        self.canvas.bind("<Button-1>", self.dashboard_click)
        self.source_display = ""
        self.output_display = "Not selected"
        self.recursive = tk.BooleanVar(value=False)
        self.log = tk.Text(self.root, height=8, state="disabled", wrap="word",
                 bg="#17191d", fg="#d7d9dd", insertbackground="white",
                 relief="flat", font=("Consolas", 9))
        self.progress = ttk.Progressbar(self.root, mode="determinate")
        self.progress_value = 0
        self.start_enabled = True
        self.draw_dashboard()

    def draw_dashboard(self, event=None):
        c = self.canvas
        c.delete("all")
        w = max(c.winfo_width(), 1200)
        h = max(c.winfo_height(), 760)
        # Keep the design canvas proportional and place processing panel on right.
        side_w = 205
        right_w = max(280, int(w * 0.235))
        design_w = w - right_w
        # Background and brushed-metal sidebar.
        c.create_rectangle(0, 0, w, h, fill="#090a0c", outline="")
        c.create_rectangle(0, 0, side_w, h, fill="#191b1f", outline="#56606c", width=2)
        for y in range(0, h, 4):
            shade = 27 + (y % 19)
            col = f"#{shade:02x}{shade:02x}{shade+2:02x}"
            c.create_line(3, y, side_w-3, y, fill=col, width=1)
        # Main charcoal vignette effect.
        c.create_rectangle(side_w+2, 0, design_w, h, fill="#101113", outline="")
        # Sidebar action icons and labels at the same positions as the reference.
        self._draw_folder_icon(c, 100, int(h*.22))
        c.create_text(100, int(h*.305), text="Choose Folder", fill="#d8d6d7",
                      font=("Segoe UI", 16))
        self._draw_camera_icon(c, 100, int(h*.49))
        c.create_text(100, int(h*.585), text="Choose Photo", fill="#d8d6d7",
                      font=("Segoe UI", 16))
        self._draw_output_icon(c, 100, int(h*.75))
        c.create_text(100, int(h*.835), text="Output Folder", fill="#d8d6d7",
                      font=("Segoe UI", 16))
        # Center brand panel, metallic badge and typography.
        cx = side_w + (design_w-side_w)//2
        self._metal_button(c, cx-68, int(h*.28)-68, cx+68, int(h*.28)+68)
        c.create_text(cx, int(h*.28), text="▣", fill="#15171a",
                      font=("Segoe UI Symbol", 48, "bold"))
        c.create_text(cx, int(h*.47), text="E - PIX", fill="#d7d3d0",
                      font=("Segoe UI", 46, "bold"))
        c.create_text(cx, int(h*.535), text="B G   S T U D I O", fill="#c6c2c4",
                      font=("Segoe UI Light", 21))
        self._metal_button(c, cx-92, int(h*.855)-44, cx+92, int(h*.855)+44)
        c.create_text(cx, int(h*.855), text=("START" if self.start_enabled else "PROCESSING..."),
                      fill="#e0dfe0", font=("Segoe UI Light", 23 if not self.start_enabled else 27))
        # Separate right-side live processing area.
        px = design_w + 20
        c.create_rectangle(design_w, 0, w, h, fill="#17191d", outline="#555b64", width=2)
        c.create_text(px+12, 42, text="PROCESSING", anchor="w",
                      fill="#dedfe2", font=("Segoe UI", 18, "bold"))
        c.create_line(px+12, 68, w-18, 68, fill="#777d86", width=1)
        c.create_text(px+12, 100, text="Source folder", anchor="w",
                      fill="#aeb4bd", font=("Segoe UI", 10, "bold"))
        c.create_text(px+12, 124, text=self.source_display or "Not selected",
                      anchor="w", width=right_w-48, fill="#e2e4e8",
                      font=("Segoe UI", 9))
        c.create_text(px+12, 170, text="Output folder", anchor="w",
                      fill="#aeb4bd", font=("Segoe UI", 10, "bold"))
        c.create_text(px+12, 194, text=self.output_display,
                      anchor="w", width=right_w-48, fill="#e2e4e8",
                      font=("Segoe UI", 9))
        c.create_text(px+12, 248, text="Progress", anchor="w",
                      fill="#aeb4bd", font=("Segoe UI", 10, "bold"))
        c.create_rectangle(px+12, 270, w-20, 286, fill="#33373d", outline="#737983")
        prog_w = max(0, (w-32-px-12) * self.progress_value / 100)
        if prog_w:
            c.create_rectangle(px+12, 270, px+12+prog_w, 286,
                               fill="#18b83e", outline="")
        c.create_text(px+12, 310, text=self.status.get(), anchor="w",
                      width=right_w-48, fill="#d1d4da", font=("Segoe UI", 9))
        c.create_text(px+12, 365, text="Activity log", anchor="w",
                      fill="#aeb4bd", font=("Segoe UI", 10, "bold"))
        # Log and progress widgets are embedded in the right-side panel.
        self.log.place(x=px+12, y=390, width=right_w-34, height=max(120,h-490))
        self.progress.place(x=px+12, y=h-75, width=right_w-34, height=20)

    def _metal_button(self, c, x1, y1, x2, y2):
        c.create_rectangle(x1, y1, x2, y2, fill="#42464c", outline="#9ba0a7", width=3)
        for k in range(1, 9):
            yy = y1 + k * (y2-y1) / 9
            c.create_line(x1+5, yy, x2-5, yy, fill="#555a61", width=1)
        c.create_rectangle(x1+8, y1+8, x2-8, y2-8, outline="#b0b3b8", width=1)

    def _draw_folder_icon(self, c, x, y):
        c.create_polygon(x-45,y-28,x-12,y-28,x,y-15,x+45,y-15,x+45,y+28,x-45,y+28,
                         fill="#353940", outline="#9ba0aa", width=3)
        c.create_polygon(x-36,y-12,x+38,y-12,x+30,y+23,x-42,y+23,
                         fill="#25292f", outline="#707783", width=2)
        c.create_rectangle(x-27,y-43,x-5,y-28,fill="#343941",outline="#9096a0",width=2)

    def _draw_camera_icon(self, c, x, y):
        c.create_rectangle(x-56,y-25,x+56,y+27,fill="#30343b",outline="#a0a5ae",width=3)
        c.create_rectangle(x-24,y-39,x+18,y-25,fill="#343941",outline="#9096a0",width=2)
        c.create_oval(x-30,y-20,x+30,y+30,fill="#171a1f",outline="#aeb3bc",width=4)
        c.create_oval(x-18,y-8,x+18,y+18,fill="#30343b",outline="#6f7782",width=3)
        c.create_oval(x-7,y-1,x+7,y+13,fill="#101216",outline="#a0a5ae",width=1)

    def _draw_output_icon(self, c, x, y):
        c.create_rectangle(x-42,y-22,x+31,y+31,fill="#25292f",outline="#a0a5ae",width=3)
        c.create_polygon(x-42,y-22,x-12,y-22,x,y-10,x+31,y-10,
                         fill="#333840",outline="#9096a0",width=2)
        c.create_line(x+12,y-47,x+12,y-5,fill="#aeb4bc",width=5)
        c.create_polygon(x-4,y-34,x+12,y-49,x+28,y-34,fill="#383d45",outline="#aeb4bc",width=2)

    def dashboard_click(self, event):
        w = max(self.canvas.winfo_width(), 1200)
        h = max(self.canvas.winfo_height(), 760)
        design_w = w - max(280, int(w * 0.235))
        if event.x < 205:
            if event.y < h*0.39:
                self.pick_folder()
            elif event.y < h*0.66:
                self.pick_files()
            else:
                self.pick_output()
        elif event.x < design_w and h*0.79 < event.y < h*0.93:
            self.start()

    def pick_folder(self):
        p = filedialog.askdirectory(title="Select source photo folder")
        if p:
            self.source.set(p); self.selected = []
            self.source_display = p
            self.draw_dashboard()

    def pick_files(self):
        p = filedialog.askopenfilenames(title="Select photos", filetypes=[("Images","*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff")])
        if p:
            self.selected = list(p); self.source.set(f"{len(p)} photos selected")
            self.source_display = f"{len(p)} photo(s) selected"
            self.draw_dashboard()

    def pick_output(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p:
            self.output.set(p)
            self.output_display = p
            self.say("Output folder: " + p)
            self.status.set("Output folder selected.")
            self.draw_dashboard()

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
        if self.busy:
            return
        if not self.output.get().strip():
            messagebox.showerror(APP_NAME, "Choose an output folder first.")
            self.say("START cancelled: select an output folder.")
            return
        paths = self.inputs()
        if not paths:
            messagebox.showwarning(APP_NAME, "Choose a source folder or image files.")
            self.say("START cancelled: no supported photos found in the selected source.")
            return
        try:
            out = Path(self.output.get())
            out.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Cannot create output folder: {e}")
            self.say(f"Output folder error: {e}")
            return

        self.busy = True
        self.start_enabled = False
        self.status.set(f"Starting AI model for {len(paths)} photo(s)...")
        self.say(f"START clicked. Queued {len(paths)} photo(s). Loading AI model...")
        self.progress.configure(maximum=len(paths), value=0)
        self.progress_value = 0
        self.draw_dashboard()
        threading.Thread(target=self.process, args=(paths, out), daemon=True).start()

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
            self.root.after(0, setattr, self, "progress_value", int(i * 100 / len(paths)))
            self.root.after(0, self.draw_dashboard)
            self.root.after(0, self.status.set, f"Processed {i} of {len(paths)}")
        self.root.after(0, self.done, good, bad)

    def done(self, good, bad):
        self.busy = False
        self.start_enabled = True
        self.status.set(f"Finished • Successful: {good} • Errors: {bad}")
        self.progress_value = 100 if bad == 0 else self.progress_value
        self.draw_dashboard()
        (messagebox.showinfo if bad == 0 else messagebox.showwarning)(
            APP_NAME, f"Processing finished.\nSuccessful: {good}\nErrors: {bad}")

if __name__ == "__main__":
    root = tk.Tk()
    try: ttk.Style().theme_use("vista")
    except tk.TclError: pass
    App(root); root.mainloop()
