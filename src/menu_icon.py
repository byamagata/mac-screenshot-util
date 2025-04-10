#!/usr/bin/env python3
"""
Generate a menu bar icon for the Screenshot Utility
"""
import os
from PIL import Image, ImageDraw

def create_menu_icon():
    """Create a simple camera icon for the menu bar"""
    # Create a smaller image for menu bar (22x22 is a good size for menu bar)
    img = Image.new('RGBA', (22, 22), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Define colors - using darker colors for menu bar visibility
    main_color = (40, 80, 220)
    
    # Draw a simple camera outline - smaller for menu bar
    # Main body rectangle
    draw.rectangle(
        [(2, 5), (20, 17)],
        fill=main_color,
        outline=(10, 30, 160),
        width=1
    )
    
    # Camera lens (circle)
    center_x, center_y = 11, 11
    radius = 4
    draw.ellipse(
        [(center_x - radius, center_y - radius),
         (center_x + radius, center_y + radius)],
        fill=(60, 100, 240),
        outline=(10, 30, 160),
        width=1
    )
    
    # Camera top (viewfinder)
    draw.rectangle(
        [(8, 2), (14, 5)],
        fill=main_color,
        outline=(10, 30, 160),
        width=1
    )
    
    # Save as PNG
    menu_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "menu_icon.png")
    img.save(menu_icon_path)
    print(f"Menu icon saved as {menu_icon_path}")
    
    return menu_icon_path

if __name__ == "__main__":
    create_menu_icon()