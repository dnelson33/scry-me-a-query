from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from io import BytesIO
from PIL import Image
import requests 
import math
from typing import Tuple, List

DEFAULT_IMAGE_SIZE = (223, 310)
MAX_PARALLEL_DOWNLOADS = 8
IMAGE_CACHE_SIZE = 128
REQUEST_TIMEOUT = (5, 20)

def generate_grid(card_images:List[str])->BytesIO:
    image_count = len(card_images)
    
    if image_count > 16:
        print("Warning: More than 16 images provided, only the first 16 will be used.")
        card_images = card_images[:16]  # Limit to 16 images for a 4x4 grid
        image_count = len(card_images)

    if image_count == 0:
        raise ValueError("No card images provided")
    
    (grid_width, grid_height) = _calculate_grid_size(image_count)
    image_size = DEFAULT_IMAGE_SIZE

    # Card art is immutable, so fetch in parallel and keep the decoded tiles in
    # order before building the grid.
    with ThreadPoolExecutor(max_workers=min(MAX_PARALLEL_DOWNLOADS, image_count)) as executor:
        images = list(executor.map(_load_card_image, card_images))

    grid_image = Image.new('RGB', (grid_width * image_size[0], grid_height * image_size[1]))
    for index, img in enumerate(images):
        x = (index % grid_width) * image_size[0]
        y = (index // grid_width) * image_size[1]
        grid_image.paste(img, (x, y))

    grid_bytes = BytesIO()
    grid_image.save(grid_bytes, format='PNG')
    grid_bytes.seek(0)
    
    return grid_bytes

def _load_card_image(url:str)->Image.Image:
    if not url:
        raise ValueError("Card image URL is missing")

    try:
        with Image.open(get_card_image(url)) as img:
            return img.convert('RGB').resize(DEFAULT_IMAGE_SIZE, Image.LANCZOS)
    except Exception as e:
        print(f"Error loading image {url}: {e}")
        raise

@lru_cache(maxsize=IMAGE_CACHE_SIZE)
def _download_image(url:str)->bytes:
    img_response = requests.get(url, headers={'User-Agent': 'ScryQueryBot/1.0'}, timeout=REQUEST_TIMEOUT)
    img_response.raise_for_status()
    return img_response.content

def get_card_image(url:str)->BytesIO:
    return BytesIO(_download_image(url))
    
def _calculate_grid_size(image_count:int)->Tuple[int, int]:
    if image_count < 3:
        grid_width = image_count # 1x1 or 1x2 grid
    elif image_count < 10:
        grid_width = 3  # 3x3 grid
    else:
        grid_width = 4  # 4x4 grid
    
    grid_height = math.ceil(image_count / grid_width)
    return (grid_width, grid_height)
