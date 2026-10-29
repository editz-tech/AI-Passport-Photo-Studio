from PIL import Image, ImageDraw, ImageFont
import math

S = 3
im = Image.new("RGB", (300*S, 300*S), "black")
d = ImageDraw.Draw(im)

def xy(box):
    return tuple(int(v*S) for v in box)

# Silver rounded-square monitor tile
tile = Image.new("RGB", (124*S, 126*S))
pix = tile.load()
for x in range(tile.width):
    t = x / max(1, tile.width-1)
    shade = int(17 + 238*t)
    for y in range(tile.height):
        pix[x,y] = (shade, shade, shade)
mask = Image.new("L", tile.size, 0)
ImageDraw.Draw(mask).rounded_rectangle((0,0,tile.width-1,tile.height-1), radius=15*S, fill=255)
im.paste(tile, (88*S,39*S), mask)
d = ImageDraw.Draw(im)
# Monitor / photo controls pictogram
line = lambda coords, fill="#050505", width=4*S: d.line([(int(x*S),int(y*S)) for x,y in coords], fill=fill, width=width, joint="curve")
d.rounded_rectangle(xy((123,78,174,117)), radius=2*S, outline="#050505", width=4*S)
line([(130,126),(167,126)])
line([(148,117),(148,126)])
# Gear / lens
d.ellipse(xy((151,89,173,111)), outline="#050505", width=4*S)
d.ellipse(xy((157,95,167,105)), outline="#050505", width=3*S)
for a in range(8):
    ang = a*math.pi/4
    x1,y1 = 162+12*math.cos(ang),100+12*math.sin(ang)
    x2,y2 = 162+15*math.cos(ang),100+15*math.sin(ang)
    line([(x1,y1),(x2,y2)], width=4*S)
for x in (133,140):
    line([(x,88),(x,95)], width=2*S)
line([(133,102),(133,108)], width=2*S)
line([(140,100),(140,108)], width=2*S)

try:
    bold = ImageFont.truetype("arialbd.ttf", 66*S)
    regular = ImageFont.truetype("arial.ttf", 29*S)
except OSError:
    bold = ImageFont.load_default(size=66*S)
    regular = ImageFont.load_default(size=29*S)
d.text((49*S, 183*S), "E-PIX", font=bold, fill="white", stroke_width=0)
d.text((50*S, 258*S), "BG STUDIO", font=regular, fill="white", stroke_width=0)
im = im.resize((300,300), Image.Resampling.LANCZOS)
im.save("e-pix-icon.png")
im.save("e-pix-icon.ico", format="ICO", sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])
