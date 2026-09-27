import colorsys
from PIL import Image

def invert_bw_keep_color(img_path: str, out_path: str) -> None:
    img = Image.open(img_path).convert("RGBA")
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]

            # Convert RGB (0-1 range) to HSV
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

            # If saturation is low, it's part of the black/white/gray body or background
            if s < 0.15:
                v = 1.0 - v  # Invert the brightness

                # Convert back to RGB
                nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
                pixels[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)

    img.save(out_path)
    print(f"Inverted logo saved to {out_path}")

if __name__ == "__main__":
    invert_bw_keep_color("icon.png", "icon_dark.png")
