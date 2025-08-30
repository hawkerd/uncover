import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point, Polygon
from io import BytesIO
from typing import Tuple, List, Optional

# Each marker: (lat, lon, optional color, optional label)
MarkerType = Tuple[float, float, Optional[str], Optional[str]]

def generate_map(
    output_filename: str,
    border: Tuple[Tuple[float, float], Tuple[float, float]],
    markers: List[MarkerType]
) -> str:
    # extend the border to fit all the markers
    if markers:
        lats = [m[0] for m in markers]
        lons = [m[1] for m in markers]
        border = (
            (min(border[0][0], min(lats)), min(border[0][1], min(lons))),
            (max(border[1][0], max(lats)), max(border[1][1], max(lons)))
        )

    # create bounding box polygon
    bbox_poly = Polygon([
        (border[0][1], border[0][0]),
        (border[0][1], border[1][0]),
        (border[1][1], border[1][0]),
        (border[1][1], border[0][0]),
        (border[0][1], border[0][0])
    ])
    bbox_gdf = gpd.GeoDataFrame(geometry=[bbox_poly], crs="EPSG:4326").to_crs(epsg=3857)

    # markers GeoDataFrame
    points = [Point(m[1], m[0]) for m in markers]
    colors = [m[2] if m[2] else "red" for m in markers]
    labels = [m[3] if m[3] else "" for m in markers]
    marker_gdf = gpd.GeoDataFrame(geometry=points, crs="EPSG:4326").to_crs(epsg=3857)

    # plot
    fig, ax = plt.subplots(figsize=(8, 8))
    bbox_gdf.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=2)
    for geom, color, label in zip(marker_gdf.geometry, colors, labels):
        ax.scatter(geom.x, geom.y, color=color, s=100)
        if label:
            ax.text(geom.x, geom.y, label, fontsize=10, ha="left", va="bottom", color=color)

    # clip
    minx, miny, maxx, maxy = bbox_gdf.total_bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    # add basemap
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.PositronNoLabels)

    ax.set_axis_off()
    plt.tight_layout()

    # save to file
    plt.savefig(output_filename, format="png", dpi=500)
    plt.close()
    return output_filename


if __name__ == "__main__":
    generate_map(
        output_filename="img.png",
        border=((44.90, -93.35), (45.00, -93.20)),
        markers=[
            (44.9778, -93.2650, "red", "Downtown"),
            (44.9500, -93.2800, "blue", "West Side"),
            (44.9900, -93.2300, "green", "Northeast")
        ]
    )
    print("Test map with colored markers and labels generated successfully.")
