from io import BytesIO
from PIL import Image
import requests 
import math
from typing import Tuple, List

#DEFAULT_IMAGE_SIZE = (146, 204)  # Size of each image in the grid
DEFAULT_IMAGE_SIZE = (223, 310)

def generate_grid(card_images:List[str])->BytesIO:
    image_count = len(card_images)
    
    if image_count > 16:
        print("Warning: More than 16 images provided, only the first 16 will be used.")
        card_images = card_images[:16]  # Limit to 16 images for a 4x4 grid

    (grid_height, grid_width) = _calculate_grid_size(image_count)
   
    # Create a new blank image for the grid
    
    image_size = (223, 310)  # Size of each image in the grid
    grid_image = Image.new('RGB', (grid_width * image_size[0], grid_height * image_size[1]))

    for index, image_path in enumerate(card_images):
        try:
            img_response = requests.get(image_path, stream=True)
            img = Image.open(BytesIO(img_response.content))
            img = img.resize(image_size)  # Resize image to fit in the grid
            x = (index % grid_width) * image_size[0]
            y = (index // grid_width) * image_size[1]
    
            grid_image.paste(img, (x, y))
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            raise e

    grid_bytes = BytesIO()
    grid_image.save(grid_bytes, format='PNG')
    grid_bytes.seek(0)
    
    return grid_bytes

def _calculate_grid_size(image_count:int)->Tuple[int, int]:
    if image_count < 3:
        grid_width = image_count # 1x1 or 1x2 grid
    elif image_count < 10:
        grid_width = 3  # 3x3 grid
    else:
        grid_width = 4  # 4x4 grid
    
    grid_height = math.ceil(image_count / grid_width)
    return (grid_width, grid_height)
    
    