#!/usr/bin/env python3
"""
Generate an icon for the Screenshot Utility
"""
import os
import tempfile
import subprocess
from PIL import Image, ImageDraw

def create_icon():
    """Create a simple camera icon for the app"""
    # Create a 1024x1024 image (Apple's recommended size for icons)
    img = Image.new('RGBA', (1024, 1024), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Define colors
    main_color = (80, 120, 255)
    highlight_color = (100, 150, 255)
    shadow_color = (40, 80, 220)
    
    # Draw a camera body
    # Main body rectangle
    draw.rectangle(
        [(200, 300), (824, 724)],
        fill=main_color,
        outline=shadow_color,
        width=10
    )
    
    # Camera lens (circle)
    center_x, center_y = 512, 512
    radius = 150
    draw.ellipse(
        [(center_x - radius, center_y - radius),
         (center_x + radius, center_y + radius)],
        fill=highlight_color,
        outline=shadow_color,
        width=10
    )
    
    # Inner lens
    inner_radius = 100
    draw.ellipse(
        [(center_x - inner_radius, center_y - inner_radius),
         (center_x + inner_radius, center_y + inner_radius)],
        fill=shadow_color,
        outline=(0, 0, 0),
        width=5
    )
    
    # Camera top (viewfinder)
    draw.rectangle(
        [(412, 230), (612, 300)],
        fill=main_color,
        outline=shadow_color,
        width=8
    )
    
    # Save as PNG
    png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app_icon.png")
    img.save(png_path)
    print(f"Icon saved as {png_path}")
    
    # Convert to ICNS if on macOS
    if os.path.exists("/usr/bin/sips") and os.path.exists("/usr/bin/iconutil"):
        try:
            icns_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "appicon.icns")
            
            # Create temporary iconset directory
            iconset_dir = tempfile.mkdtemp(suffix='.iconset')
            
            # Generate different size icons
            sizes = [16, 32, 64, 128, 256, 512, 1024]
            for size in sizes:
                # Standard resolution
                output_path = os.path.join(iconset_dir, f"icon_{size}x{size}.png")
                subprocess.run([
                    "sips",
                    "-z", str(size), str(size),
                    png_path,
                    "--out", output_path
                ], check=True, capture_output=True)
                
                # High resolution (retina)
                if size <= 512:  # No 2048x2048 icon needed
                    output_path = os.path.join(iconset_dir, f"icon_{size}x{size}@2x.png")
                    subprocess.run([
                        "sips",
                        "-z", str(size*2), str(size*2),
                        png_path,
                        "--out", output_path
                    ], check=True, capture_output=True)
            
            # Convert iconset to icns
            subprocess.run([
                "iconutil",
                "-c", "icns",
                iconset_dir,
                "-o", icns_path
            ], check=True, capture_output=True)
            
            print(f"ICNS icon created at {icns_path}")
            
            # Clean up temporary directory
            import shutil
            shutil.rmtree(iconset_dir)
            
            return icns_path
        except Exception as e:
            print(f"Error creating ICNS icon: {e}")
    
    return png_path

if __name__ == "__main__":
    create_icon()