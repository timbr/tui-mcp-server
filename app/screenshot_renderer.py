"""Render terminal output to PNG screenshots."""

from PIL import Image, ImageDraw, ImageFont
from typing import List
import os
import tempfile


class ScreenshotRenderer:
    """Renders terminal output to PNG images."""
    
    def __init__(self, cols: int = 80, rows: int = 24):
        self.cols = cols
        self.rows = rows
        
        # Font settings
        self.font_size = 14
        self.font_name = "DejaVuSansMono.ttf"
        self.char_width = 8
        self.char_height = 16
        self.line_spacing = 2
        
        # Colors
        self.bg_color = (0, 0, 0)  # Black
        self.fg_color = (0, 255, 0)  # Green
        self.cursor_color = (255, 255, 255)  # White
        
        # Try to load the font
        try:
            self.font = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{self.font_name}", self.font_size)
        except Exception:
            # Fallback to default font
            self.font = ImageFont.load_default()
    
    def render(self, buffer: List[str]) -> str:
        """Render the terminal buffer to a PNG image and return the path."""
        # Calculate image dimensions
        img_width = self.cols * self.char_width + 20  # Add padding
        img_height = self.rows * (self.char_height + self.line_spacing) + 20  # Add padding
        
        # Create a new image
        img = Image.new('RGB', (img_width, img_height), color=self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Draw each line of text
        for row, line in enumerate(buffer):
            y = 10 + row * (self.char_height + self.line_spacing)
            
            # Draw the line
            for col, char in enumerate(line):
                x = 10 + col * self.char_width
                
                # Draw character
                if char and char != ' ':
                    try:
                        draw.text((x, y), char, fill=self.fg_color, font=self.font)
                    except Exception:
                        # Fallback if font rendering fails
                        draw.text((x, y), char, fill=self.fg_color)
        
        # Save to a temporary file
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, "terminal_screenshot.png")
        img.save(temp_file)
        
        return temp_file
