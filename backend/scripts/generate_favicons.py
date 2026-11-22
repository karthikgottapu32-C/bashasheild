from PIL import Image, ImageDraw

def create_shield_icon(size):
    img = Image.new("RGBA", (size, size), (9, 13, 28, 255)) # Deep Indigo #090D1C
    draw = ImageDraw.Draw(img)
    
    # Scale coordinates
    margin = size * 0.15
    w = size - 2 * margin
    h = size - 2 * margin
    
    # Shield polygon
    top = margin
    bottom = size - margin
    left = margin
    right = size - margin
    mid_x = size / 2.0
    mid_y = top + h * 0.65
    
    points = [
        (left + w * 0.1, top),
        (right - w * 0.1, top),
        (right, top + h * 0.4),
        (mid_x, bottom),
        (left, top + h * 0.4),
    ]
    
    # Shield fill (Ice cyan outline + glow)
    draw.polygon(points, fill=(15, 23, 42, 255), outline=(54, 228, 255, 255), width=max(1, int(size * 0.06)))
    
    # Inner neural core / checkmark / lightning symbol
    core_points = [
        (mid_x, top + h * 0.2),
        (right - w * 0.25, top + h * 0.45),
        (mid_x + w * 0.05, top + h * 0.5),
        (mid_x + w * 0.15, bottom - h * 0.2),
        (left + w * 0.25, top + h * 0.55),
        (mid_x - w * 0.05, top + h * 0.5)
    ]
    draw.polygon(core_points, fill=(54, 228, 255, 255))
    
    # Center dot in Ice White
    dot_r = max(2, int(size * 0.07))
    draw.ellipse([mid_x - dot_r, mid_y - dot_r, mid_x + dot_r, mid_y + dot_r], fill=(234, 244, 255, 255))
    
    return img

# Generate icons
icon_16 = create_shield_icon(16)
icon_32 = create_shield_icon(32)
icon_48 = create_shield_icon(48)
icon_180 = create_shield_icon(180)
icon_512 = create_shield_icon(512)

icon_16.save("frontend/public/favicon-16x16.png")
icon_32.save("frontend/public/favicon-32x32.png")
icon_180.save("frontend/public/apple-touch-icon.png")
icon_512.save("frontend/public/android-chrome-512x512.png")

# Save multi-resolution .ico
icon_48.save("frontend/public/favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
print("Generated favicon.ico, apple-touch-icon.png, and resolution variants in frontend/public/")
