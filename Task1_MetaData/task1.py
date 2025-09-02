from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import sys

def get_exif_data(image_path):
    image = Image.open(image_path)
    exif_data = {}
    info = image._getexif()
    
    if info:
        for tag, value in info.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_tag = GPSTAGS.get(t, t)
                    gps_data[sub_tag] = value[t]
                exif_data["GPSInfo"] = gps_data
            else:
                exif_data[tag_name] = value
    return exif_data

def get_decimal_from_dms(dms, ref):
    degrees = float(dms[0])
    minutes = float(dms[1])
    seconds = float(dms[2])

    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ["S", "W"]:
        decimal = -decimal
    return decimal


def get_gps_coords(exif_data):
    if "GPSInfo" not in exif_data:
        return None

    gps_info = exif_data["GPSInfo"]
    lat = lon = None

    if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info:
        lat = get_decimal_from_dms(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])
    if "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
        lon = get_decimal_from_dms(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])

    return (lat, lon)

if __name__ == "__main__":
    # if len(sys.argv) < 2:
    #     print("Usage: python image_metadata.py ")
    #     sys.exit(1)

    image_path = "../Task1_MetaData/assets/image0.jpeg"
    exif = get_exif_data(image_path)

    print("=== Extracted Metadata ===")
    for key, value in exif.items():
        print(f"{key}: {value}")

    gps_coords = get_gps_coords(exif)
    if gps_coords:
        print("\nGPS Coordinates:", gps_coords)
