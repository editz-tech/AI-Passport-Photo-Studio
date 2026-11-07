from PIL import Image

# Use the exact silver monitor-and-gear mark supplied for the window icon.
source = Image.open("e-pix-window-icon.png").convert("RGBA")
source = source.resize((256, 256), Image.Resampling.LANCZOS)
source.save("e-pix-icon.png")
source.save("e-pix-icon.ico", format="ICO", sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])
