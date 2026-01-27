from io import BytesIO
from scryfall import scryfall_query
from PIL import Image
import requests 
import math
def generate_grid(images)->BytesIO:
    image_count = len(images)
    
    if image_count > 16:
        print("Warning: More than 16 images provided, only the first 16 will be used.")
        images = images[:16]  # Limit to 16 images for a 4x4 grid

    if image_count < 3:
        grid_width = image_count
    elif image_count < 10:
        grid_width = 3  # 3x3 grid
    else:
        grid_width = 4  # 4x4 grid
    
    grid_height = math.ceil(len(images) / grid_width)
        
    # Create a new blank image for the grid
    #image_size = (146, 204)  # Size of each image in the grid
    image_size = (223, 310)  # Size of each image in the grid
    grid_image = Image.new('RGB', (grid_width * image_size[0], grid_height * image_size[1]))

    for index, image_path in enumerate(images):
        try:
            img_response = requests.get(image_path, stream=True)
            img = Image.open(BytesIO(img_response.content))
            img = img.resize(image_size)  # Resize image to fit in the grid
            x = (index % grid_width) * image_size[0]
            y = (index // grid_width) * image_size[1]
    
            grid_image.paste(img, (x, y))
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")

    grid_bytes = BytesIO()
    grid_image.save(grid_bytes, format='PNG')
    grid_bytes.seek(0)
    
    return grid_bytes



    
    