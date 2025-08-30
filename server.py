from mcp.server.fastmcp import FastMCP
from typing import List, Tuple, Optional, Any, Dict
from service.generate_map import generate_map, MarkerType
from service.geocode import geocode_place
from service.instagram import post_images_to_instagram

# create MCP server instance (configured for stateless HTTP)
mcp = FastMCP(
    name="Dan's Server",
    host="0.0.0.0",
    port=8050,
    stateless_http=True,
)


# tools
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def create_map(
    output_filename: str,
    border: List[List[float]],
    markers: List[List[float | str]] = [],
) -> str:
    """
    Generate a map with a rectangle and markers.
    
    `output_filename`: desired output PNG file name
    `border`: [[lat1, lon1], [lat2, lon2]] bottom-left, top-right
    `markers`: [[lat, lon, optional color, optional label], ...]
    
    Returns the path to the generated PNG file.
    """

    print(f"Creating map with border: {border} and markers: {markers}")
    output_location: str = generate_map(output_filename=output_filename, border=border, markers=markers)
    print(f"Map generated at: {output_location}")
    return output_location


@mcp.tool()
def geocode_point(place: str) -> Dict[str, float]:
    """
    Returns the center point of a place.

    Example return:
    {
        "lat": 44.9778,
        "lon": -93.2650
    }
    """
    result = geocode_place(place)
    if not result:
        return {}

    return {"lat": float(result["lat"]), "lon": float(result["lon"])}


@mcp.tool()
def geocode_bbox(place: str) -> List[List[float]]:
    """
    Returns the bounding box of a place as two points: southwest and northeast.

    Example return:
    [[south_lat, west_lon], [north_lat, east_lon]]
    """
    result = geocode_place(place)
    if not result:
        return []

    southwest = result["southwest"]
    northeast = result["northeast"]
    return [southwest, northeast]

@mcp.tool()
def instagram_post_images(image_paths: List[str], caption: str) -> str:
    """
    Posts a list of images to Instagram with the same caption.
    If multiple images are provided, posts them as a carousel.

    Args:
        image_paths: List of file paths to images.
        caption: Caption for the post.

    Returns a status message.
    """

    post_images_to_instagram(image_paths, caption)
    return "Posted images to Instagram."

# run the server
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
    #mcp.run(transport="stdio")
    