from PIL import Image, ImageDraw

SIZE = 256
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Latar belakang bulat gradasi sederhana (cyan -> magenta)
cx, cy, r = SIZE // 2, SIZE // 2, SIZE // 2 - 6
for i in range(r, 0, -1):
    t = i / r
    color = (
        int(34 + (214 - 34) * (1 - t)),
        int(211 + (64 - 211) * (1 - t)),
        int(238 + (176 - 238) * (1 - t)),
        255,
    )
    draw.ellipse([cx - i, cy - i, cx + i, cy + i], fill=color)

# Segitiga play di tengah
tri_w, tri_h = 78, 96
p1 = (cx - tri_w * 0.35, cy - tri_h / 2)
p2 = (cx - tri_w * 0.35, cy + tri_h / 2)
p3 = (cx + tri_w * 0.65, cy)
draw.polygon([p1, p2, p3], fill=(255, 255, 255, 255))

# Garis kecil melambangkan "trim"
draw.rectangle([cx - 60, cy + 78, cx - 20, cy + 90], fill=(255, 255, 255, 230))
draw.rectangle([cx + 20, cy + 78, cx + 60, cy + 90], fill=(255, 255, 255, 230))

img.save("icon.png")
img.save("icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon dibuat")
