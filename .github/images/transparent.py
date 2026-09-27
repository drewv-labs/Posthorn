from PIL import Image

def remove_black_background(img_path: str, out_path: str) -> None:
    img = Image.open(img_path).convert("RGBA")
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]

            # The brightest color channel determines how opaque the pixel should be
            alpha = max(r, g, b)

            if alpha > 0:
                # Un-premultiply the RGB values to remove the black fringing
                # (e.g., a 50% dark gray edge becomes a 100% white edge at 50% opacity)
                nr = int((r / alpha) * 255)
                ng = int((g / alpha) * 255)
                nb = int((b / alpha) * 255)

                pixels[x, y] = (nr, ng, nb, alpha)
            else:
                # Pure black becomes completely transparent
                pixels[x, y] = (0, 0, 0, 0)

    img.save(out_path)
    print(f"Transparent logo saved to {out_path}")

if __name__ == "__main__":
    # Point this at the dark mode icon we generated in the last step
    remove_black_background("icon.png", "icon_transparent.png")
