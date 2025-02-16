# Prediction interface for Cog ⚙️
# https://cog.run/python
from cog import BasePredictor, Input, Path
from PIL import Image

class Predictor(BasePredictor):
    def setup(self):
        """Load the model into memory to make running multiple predictions efficient"""
        # No model to load for this simple image processing task
        pass

    def calculate_scale_factor(self, foreground, background, max_scale=1.0):
        """Calculate the scale factor to fit the foreground within the background."""
        fg_width, fg_height = foreground.size
        bg_width, bg_height = background.size
        
        # Calculate the maximum scale that fits within the background
        scale_width = bg_width / fg_width
        scale_height = bg_height / fg_height
        scale = min(scale_width, scale_height, max_scale)
        
        return scale

    def predict(
        self,
        foreground: Path = Input(
            description="PNG image with transparency to be used as foreground",
            default=None,
        ),
        background: Path = Input(
            description="JPG image to be used as background",
            default=None,
        ),
        position_x: int = Input(
            description="X coordinate for foreground image position (optional, defaults to center)",
            default=None,
        ),
        position_y: int = Input(
            description="Y coordinate for foreground image position (optional, defaults to center)",
            default=None,
        ),
        max_scale: float = Input(
            description="Maximum scale factor for foreground image (optional, defaults to 1.0)",
            default=1.0,
            ge=0.1,  # minimum scale
            le=5.0,   # maximum scale
        ),
    ) -> Path:
        """Run a single prediction on the model"""
        # Open the images
        foreground_img = Image.open(str(foreground)).convert('RGBA')
        background_img = Image.open(str(background)).convert('RGBA')
        
        # Calculate the optimal scale factor
        scale_factor = self.calculate_scale_factor(foreground_img, background_img, max_scale)
        
        # Scale the foreground image
        new_width = int(foreground_img.width * scale_factor)
        new_height = int(foreground_img.height * scale_factor)
        foreground_img = foreground_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Ensure background is in correct mode
        if background_img.mode != 'RGBA':
            background_img = background_img.convert('RGBA')
        
        # Calculate position
        if position_x is None or position_y is None:
            position = (
                (background_img.width - foreground_img.width) // 2,
                (background_img.height - foreground_img.height) // 2
            )
        else:
            position = (position_x, position_y)
        
        # Create a new image with the same size as background
        merged_image = Image.new('RGBA', background_img.size)
        # Paste background onto the new image
        merged_image.paste(background_img, (0, 0))
        # Paste foreground onto the new image, using its alpha channel as mask
        merged_image.paste(foreground_img, position, foreground_img)
        # Convert to RGB before saving as JPG
        merged_image = merged_image.convert('RGB')
        output_path = Path("/tmp/output.jpg")
        merged_image.save(str(output_path), 'JPEG', quality=95)
        return output_path