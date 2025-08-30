# post_images_instagram.py
from instagrapi import Client
from typing import List
import os

def post_images_to_instagram(image_paths: List[str], caption: str):
    """
    Posts a list of images to Instagram with the same caption.
    If multiple images are provided, posts them as a carousel.

    Args:
        image_paths: List of file paths to images.
        caption: Caption for the post.
    """
    # Initialize client and login
    cl = Client()
    cl.login("", "")

    # Filter out invalid paths
    valid_images = [img for img in image_paths if os.path.isfile(img)]
    if not valid_images:
        print("No valid images found.")
        return

    # Post single image or carousel
    if len(valid_images) == 1:
        print(f"Posting single image: {valid_images[0]}")
        cl.photo_upload(valid_images[0], caption)
    else:
        print(f"Posting carousel with {len(valid_images)} images.")
        cl.album_upload(valid_images, caption)
    
    print("Done posting images!")

# Example usage
if __name__ == "__main__":
    IMAGES = ["../img.jpg"]
    CAPTION = "Check out these photos! #example #instagrapi"

    post_images_to_instagram(IMAGES, CAPTION)
