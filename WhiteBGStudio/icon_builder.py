from PIL import Image, ImageDraw

# Build the silver monitor-and-gear app icon using Pillow only.
# This avoids Cairo/native DLL dependencies on Windows GitHub runners.
S = 512
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
pix = im.load()
for y in range(S):
    for x in range(S):
        t = (x + y) / (2 * (S - 1))
        v = int(246 - 42 * t + 10 * (1 - abs(0.5 - t) * 2))
        pix[x, y] = (max(0, min(255, v)),) * 3 + (255,)

mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle((8, 8, S-8, S-8), radius=82, fill=255)
im.putalpha(mask)
d = ImageDraw.Draw(im)
ink = (12, 12, 12, 255)
# Monitor body and stand
d.rounded_rectangle((128, 142, 384, 340), radius=12, outline=ink, width=17)
d.line((171, 377, 341, 377), fill=ink, width=17)
d.line((256, 340, 256, 377), fill=ink, width=17)
d.line((211, 405, 301, 405), fill=ink, width=17)
# Left-side control marks
d.line((171, 180, 171, 247), fill=ink, width=15)
d.line((204, 180, 204, 224), fill=ink, width=15)
d.line((171, 277, 171, 301), fill=ink, width=15)
d.line((204, 264, 204, 301), fill=ink, width=15)
# Gear on the right
cx, cy = 311, 242
d.ellipse((cx-54, cy-54, cx+54, cy+54), outline=ink, width=19)
d.ellipse((cx-21, cy-21, cx+21, cy+21), outline=ink, width=17)
for angle in range(0, 360, 45):
    import math
    a = math.radians(angle)
    x1, y1 = cx + int(57*math.cos(a)), cy + int(57*math.sin(a))
    x2, y2 = cx + int(77*math.cos(a)), cy + int(77*math.sin(a))
    d.line((x1, y1, x2, y2), fill=ink, width=17)
# Downsample for smooth rounded edges and save multi-size Windows icon.
im = im.resize((256, 256), Image.Resampling.LANCZOS)
im.save("e-pix-icon.png")
im.save("e-pix-icon.ico", format="ICO", sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])
