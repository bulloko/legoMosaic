import numpy
if not hasattr(numpy, "asscalar"):
    numpy.asscalar = lambda a: a.item()
import streamlit as st
from PIL import Image
from io import BytesIO
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

# LEGO color palette (accurate RGB values)
LEGO_COLORS = [
    {"name": "Brick Yellow", "rgb": (236, 217, 185)},
    {"name": "Nougat", "rgb": (204, 142, 105)},
    {"name": "Bright Red", "rgb": (180, 0, 0)},
    {"name": "Bright Blue", "rgb": (0, 85, 191)},
    {"name": "Bright Yellow", "rgb": (255, 205, 0)},
    {"name": "Black", "rgb": (27, 42, 52)},
    {"name": "Dark Green", "rgb": (0, 69, 26)},
    {"name": "Bright Green", "rgb": (75, 151, 75)},
    {"name": "Dark Orange", "rgb": (160, 80, 0)},
    {"name": "Medium Blue", "rgb": (73, 138, 199)},
    {"name": "Bright Orange", "rgb": (255, 127, 0)},
    {"name": "Bright Bluish Green", "rgb": (0, 158, 143)},
    {"name": "Bright Yellowish-Green", "rgb": (193, 223, 0)},
    {"name": "Bright Reddish Violet", "rgb": (160, 0, 128)},
    {"name": "Sand Blue", "rgb": (100, 124, 162)},
    {"name": "Sand Yellow", "rgb": (170, 153, 114)},
    {"name": "Earth Blue", "rgb": (0, 32, 96)},
    {"name": "Earth Green", "rgb": (0, 50, 40)},
    {"name": "Sand Green", "rgb": (120, 144, 130)},
    {"name": "Dark Red", "rgb": (123, 0, 27)},
    {"name": "Flame Yellowish Orange", "rgb": (255, 176, 0)},
    {"name": "Reddish Brown", "rgb": (105, 64, 40)},
    {"name": "Medium Stone Grey", "rgb": (163, 162, 165)},
    {"name": "Dark Stone Grey", "rgb": (99, 95, 98)},
    {"name": "Light Stone Grey", "rgb": (229, 228, 223)},
    {"name": "Light Royal Blue", "rgb": (180, 210, 228)},
    {"name": "Bright Purple", "rgb": (123, 0, 123)},
    {"name": "Light Purple", "rgb": (220, 178, 229)},
    {"name": "Cool Yellow", "rgb": (255, 236, 108)},
    {"name": "Dark Purple", "rgb": (85, 0, 85)},
    {"name": "Light Nougat", "rgb": (255, 223, 196)},
    {"name": "Dark Brown", "rgb": (62, 32, 10)},
    {"name": "Medium Nougat", "rgb": (174, 122, 89)},
    {"name": "Dark Azur", "rgb": (32, 108, 137)},
    {"name": "Medium Azur", "rgb": (104, 195, 226)},
    {"name": "Aqua", "rgb": (175, 232, 225)},
    {"name": "Medium Lavender", "rgb": (180, 140, 200)},
    {"name": "Lavender", "rgb": (203, 153, 201)},
    {"name": "White Glow", "rgb": (247, 247, 247)},
    {"name": "Spring Yellowish Green", "rgb": (234, 255, 99)},
    {"name": "Olive Green", "rgb": (91, 110, 53)},
    {"name": "Medium Yellowish Green", "rgb": (170, 210, 60)},
    {"name": "Vibrant Coral", "rgb": (255, 115, 119)},
    {"name": "Vibrant Yellow", "rgb": (255, 239, 0)},
]

# RGB → LAB
def rgb_to_lab(rgb):
    srgb = sRGBColor(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    return convert_color(srgb, LabColor)

# High accuracy color matching
def closest_lego_color_lab(pixel_rgb):
    target = rgb_to_lab(pixel_rgb)
    closest = LEGO_COLORS[0]
    min_dist = float('inf')

    for color in LEGO_COLORS:
        lego_lab = rgb_to_lab(color["rgb"])
        raw_delta = delta_e_cie2000(target, lego_lab)
        delta = raw_delta.item() if hasattr(raw_delta, "item") else float(raw_delta)

        if delta < min_dist:
            min_dist = delta
            closest = color

    return closest["rgb"]

# Fast RGB match
def closest_lego_color(pixel_rgb):
    def distance(c1, c2):
        return sum((a - b) ** 2 for a, b in zip(c1, c2))
    return min(LEGO_COLORS, key=lambda c: distance(pixel_rgb, c["rgb"]))["rgb"]

# Main pixelation function
def lego_pixelate(img, pixel_size, grid_size, use_lego_palette=True, high_accuracy=True):
    small = img.resize(grid_size, resample=Image.BILINEAR)
    result = Image.new("RGB", (grid_size[0] * pixel_size, grid_size[1] * pixel_size))

    for y in range(grid_size[1]):
        for x in range(grid_size[0]):
            orig_color = small.getpixel((x, y))
            if use_lego_palette:
                color = closest_lego_color_lab(orig_color) if high_accuracy else closest_lego_color(orig_color)
            else:
                color = orig_color

            for dy in range(pixel_size):
                for dx in range(pixel_size):
                    result.putpixel((x * pixel_size + dx, y * pixel_size + dy), color)
    return result

def img_to_bytes(img):
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ---- Streamlit UI ----
st.set_page_config(page_title="Lego Photo App", layout="centered")
st.title("🧱 Lego-style Photo Editor")

uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded:
    original = Image.open(uploaded).convert("RGB")
    st.subheader("Original Image")
    st.image(original, use_column_width=True)

    st.subheader("Tweak Lego Settings")
    col1, col2 = st.columns(2)
    with col1:
        brick_size = st.slider("Brick Size (px)", 5, 50, 20)
    with col2:
        width_blocks = st.slider("Grid Width (blocks)", 10, 100, 48)

    aspect_ratio = original.height / original.width
    height_blocks = int(width_blocks * aspect_ratio)

    use_lego = st.checkbox("Use Real LEGO Colors", value=True)
    high_accuracy = st.checkbox("High Accuracy Color Matching (slower)", value=True)

    lego_img = lego_pixelate(
        original,
        brick_size,
        (width_blocks, height_blocks),
        use_lego_palette=use_lego,
        high_accuracy=high_accuracy
    )

    st.image(lego_img, caption=f"Lego-Style ({width_blocks}x{height_blocks} bricks)", use_column_width=True)
    st.download_button(
        "📥 Download Lego Image",
        data=img_to_bytes(lego_img),
        file_name="lego_style.png",
        mime="image/png"
    )