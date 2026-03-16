"""
WHOISXMLAPI.COM - March 2026   Version 1.0

This utility creates a upper-left and lower-right boundry from the centerpoint specified by a longitude/latitude coorinate. The miles value is the 
distance from the center point to each edge (not each corner), so the total rectangle is 2× miles on each side.

Latitude offset is straightforward — 1 degree of latitude is always ~69 miles, so: delta_lat = miles / 3958.8 × (180/π)

Longitude offset must account for the fact that longitude degrees get narrower as you move away from the equator, so it's scaled by 
    
    cos(latitude): delta_lon = miles / (3958.8 × cos(lat)) × (180/π)

Input validation handles invalid numbers (letters, symbols) with a re-prompt, and checks that lat/lon are in valid ranges and distance is positive.

Example input and output from downtown San Francisco, CA, USA at 0.25 miles:

$ python latlong.py
=======================================================
   Bounding Rectangle Calculator
=======================================================
Enter a center point and a distance (in miles).
The script will compute the upper-left and lower-right
corners of the bounding rectangle.

  Center Latitude   (-90  to  90 ): 37.79002270288523
  Center Longitude  (-180 to 180 ): -122.39721443415249
  Distance in miles (e.g. 1.5    ): 0.25

=======================================================
  Center Point   : (37.79002270288523, -122.39721443415249)
  Distance       : 0.25 mile(s) from center to each edge
-------------------------------------------------------
  Upper-Left     : (37.793641, -122.401793)
  Upper-Right    : (37.793641, -122.392636)
  Lower-Left     : (37.786404, -122.401793)
  Lower-Right    : (37.786404, -122.392636)
=======================================================

  Rectangle size : ~0.5 mi (N-S) × ~0.5 mi (E-W)

"""

import math

def calculate_bounding_rectangle(latitude, longitude, miles):
    """
    Given a center point (lat/lon) and a distance in miles,
    calculate the upper-left and lower-right corners of a
    bounding rectangle where each edge is 'miles' away from center.

    Returns:
        upper_left  (lat, lon)
        lower_right (lat, lon)
    """
    # Earth's radius in miles
    EARTH_RADIUS_MILES = 3958.8

    # Convert latitude to radians for longitude scaling
    lat_rad = math.radians(latitude)

    # Degrees of latitude per mile (constant everywhere)
    delta_lat = (miles / EARTH_RADIUS_MILES) * (180 / math.pi)

    # Degrees of longitude per mile (shrinks as you move away from equator)
    delta_lon = (miles / (EARTH_RADIUS_MILES * math.cos(lat_rad))) * (180 / math.pi)

    upper_left  = (latitude + delta_lat, longitude - delta_lon)
    lower_right = (latitude - delta_lat, longitude + delta_lon)

    return upper_left, lower_right


def get_float_input(prompt):
    """Prompt the user for a float value, re-asking on invalid input."""
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print(f"  ✗  '{raw}' is not a valid number. Please try again.")


def main():
    print("=" * 55)
    print("   Bounding Rectangle Calculator")
    print("=" * 55)
    print("Enter a center point and a distance (in miles).")
    print("The script will compute the upper-left and lower-right")
    print("corners of the bounding rectangle.\n")

    latitude  = get_float_input("  Center Latitude   (-90  to  90 ): ")
    longitude = get_float_input("  Center Longitude  (-180 to 180 ): ")
    miles     = get_float_input("  Distance in miles (e.g. 1.5    ): ")

    # Basic validation
    if not (-90 <= latitude <= 90):
        print("\n  ✗  Latitude must be between -90 and 90.")
        return
    if not (-180 <= longitude <= 180):
        print("\n  ✗  Longitude must be between -180 and 180.")
        return
    if miles <= 0:
        print("\n  ✗  Distance must be a positive number.")
        return

    upper_left, lower_right = calculate_bounding_rectangle(latitude, longitude, miles)

    print("\n" + "=" * 55)
    print(f"  Center Point   : ({latitude}, {longitude})")
    print(f"  Distance       : {miles} mile(s) from center to each edge")
    print("-" * 55)
    print(f"  Upper-Left     : ({upper_left[0]:.6f}, {upper_left[1]:.6f})")
    print(f"  Upper-Right    : ({upper_left[0]:.6f}, {lower_right[1]:.6f})")
    print(f"  Lower-Left     : ({lower_right[0]:.6f}, {upper_left[1]:.6f})")
    print(f"  Lower-Right    : ({lower_right[0]:.6f}, {lower_right[1]:.6f})")
    print("=" * 55)

    # Total dimensions
    lat_span_miles = miles * 2
    lon_span_miles = miles * 2
    print(f"\n  Rectangle size : ~{lat_span_miles} mi (N-S) × ~{lon_span_miles} mi (E-W)")
    print()


if __name__ == "__main__":
    main()
