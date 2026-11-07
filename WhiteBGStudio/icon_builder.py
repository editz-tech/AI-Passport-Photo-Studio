import cairosvg
from PIL import Image

# Render the clean silver monitor-and-gear mark from the SVG source.
cairosvg.svg2png(url="e-pix-icon.svg", write_to="e-pix-icon.png", output_width=256, output_height=256)
Image.open("e-pix-icon.png").convert("RGBA").save(
    "e-pix-icon.ico", format="ICO", sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)]
)
