"""Draw the Backdrop app icon: two tilted photo frames with a landscape.

usage: python tools/draw_icon.py app/icon.png 304
"""
import sys
from PIL import Image, ImageDraw, ImageFilter

W, H = 512, 512
S = 4  # supersample for smooth edges
w, h = W * S, H * S


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgradient(size, top, bottom):
    g = Image.new("RGB", size)
    d = ImageDraw.Draw(g)
    for y in range(size[1]):
        d.line([(0, y), (size[0], y)], fill=lerp(top, bottom, y / max(1, size[1] - 1)))
    return g


# background: deep navy -> near black
img = vgradient((w, h), (30, 36, 64), (10, 11, 20)).convert("RGBA")


def frame_layer(box, angle, inner_fn, shadow=True):
    """Draw a white-bordered photo at box, rotated by angle, onto a transparent layer."""
    x0, y0, x1, y1 = box
    fw, fh = x1 - x0, y1 - y0
    pad = int(fw * 0.055)
    radius = int(fw * 0.035)

    photo = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    pd = ImageDraw.Draw(photo)
    pd.rounded_rectangle([0, 0, fw - 1, fh - 1], radius=radius, fill=(246, 244, 238, 255))
    inner = inner_fn((fw - 2 * pad, fh - 2 * pad))
    mask = Image.new("L", inner.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, inner.size[0] - 1, inner.size[1] - 1],
                                           radius=int(radius * 0.6), fill=255)
    photo.paste(inner, (pad, pad), mask)

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([0, 0, fw - 1, fh - 1], radius=radius, fill=(0, 0, 0, 150))
        sh = sh.rotate(angle, expand=True, resample=Image.BICUBIC)
        sl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        sl.paste(sh, (cx - sh.size[0] // 2 + 6 * S, cy - sh.size[1] // 2 + 14 * S), sh)
        sl = sl.filter(ImageFilter.GaussianBlur(14 * S))
        layer = Image.alpha_composite(layer, sl)
    rot = photo.rotate(angle, expand=True, resample=Image.BICUBIC)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    layer.paste(rot, (cx - rot.size[0] // 2, cy - rot.size[1] // 2), rot)
    return layer


def back_photo(size):
    # muted teal/blue abstract for the back frame
    return vgradient(size, (92, 150, 170), (46, 78, 112)).convert("RGBA")


def landscape(size):
    iw, ih = size
    sky = vgradient(size, (255, 186, 120), (255, 122, 110)).convert("RGBA")
    d = ImageDraw.Draw(sky)
    # sun
    r = int(iw * 0.11)
    sx, sy = int(iw * 0.68), int(ih * 0.36)
    d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 238, 180, 255))
    # far mountains
    d.polygon([(0, int(ih * .72)), (int(iw * .22), int(ih * .44)), (int(iw * .42), int(ih * .66)),
               (int(iw * .62), int(ih * .40)), (iw, int(ih * .70)), (iw, ih), (0, ih)],
              fill=(122, 82, 140, 255))
    # near hills
    d.polygon([(0, int(ih * .84)), (int(iw * .30), int(ih * .62)), (int(iw * .58), int(ih * .82)),
               (int(iw * .80), int(ih * .66)), (iw, int(ih * .80)), (iw, ih), (0, ih)],
              fill=(58, 48, 96, 255))
    return sky


# back frame (tilted left), front frame (slight right tilt)
fw, fh = int(w * 0.50), int(w * 0.41)
cx, cy = w // 2, int(h * 0.50)
back = frame_layer((cx - fw // 2 - 34 * S, cy - fh // 2 - 18 * S, cx + fw // 2 - 34 * S, cy + fh // 2 - 18 * S),
                   9, back_photo)
front = frame_layer((cx - fw // 2 + 26 * S, cy - fh // 2 + 14 * S, cx + fw // 2 + 26 * S, cy + fh // 2 + 14 * S),
                    -4, landscape)
img = Image.alpha_composite(img, back)
img = Image.alpha_composite(img, front)

# Final size: the TV scales the icon to its app tile with a cheap filter, which makes
# tilted edges wavy if it has to shrink a lot. Shipping it close to tile size (the
# repo's original icon was 304px) means we do the big, high-quality downscale here.
OUT = int(sys.argv[2]) if len(sys.argv) > 2 else W
out = img.resize((OUT, OUT * H // W), Image.LANCZOS).convert("RGB")
out.save(sys.argv[1], optimize=True)
print("saved", sys.argv[1], out.size)
