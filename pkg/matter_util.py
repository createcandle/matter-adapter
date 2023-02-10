# helper functions for Matter adapter

import math
from collections import namedtuple



# Turns color names into HEX color values. Useful with voice control
def colorNameToHex(color):
    colors = {"alice blue":"#f0f8ff","antique white":"#faebd7","aqua":"#00ffff","aquamarine":"#7fffd4","azure":"#f0ffff",
    "beige":"#f5f5dc","bisque":"#ffe4c4","black":"#000000","blanched almond":"#ffebcd","blue":"#0000ff","blue violet":"#8a2be2","brown":"#a52a2a","burlywood":"#deb887",
    "cadet blue":"#5f9ea0","chartreuse":"#7fff00","chocolate":"#d2691e","coral":"#ff7f50","cornflower blue":"#6495ed","cornsilk":"#fff8dc","crimson":"#dc143c","cyan":"#00ffff",
    "dark blue":"#00008b","darkcyan":"#008b8b","dark golden rod":"#b8860b","darkgray":"#a9a9a9","dark green":"#006400","darkkhaki":"#bdb76b","dark magenta":"#8b008b","dark olive green":"#556b2f",
    "dark orange":"#ff8c00","dark orchid":"#9932cc","dark red":"#8b0000","dark salmon":"#e9967a","dark sea green":"#8fbc8f","dark slate blue":"#483d8b","dark slate gray":"#2f4f4f","dark turquoise":"#00ced1",
    "dark violet":"#9400d3","deep pink":"#ff1493","deep sky blue":"#00bfff","dim gray":"#696969","dodger blue":"#1e90ff",
    "firebrick":"#b22222","floral white":"#fffaf0","forest green":"#228b22","fuchsia":"#ff00ff",
    "gainsboro":"#dcdcdc","ghostwhite":"#f8f8ff","gold":"#ffd700","golden rod":"#daa520","gray":"#808080","green":"#008000","green yellow":"#adff2f",
    "honeydew":"#f0fff0","hot pink":"#ff69b4",
    "indian red ":"#cd5c5c","indigo":"#4b0082","ivory":"#fffff0","khaki":"#f0e68c",
    "lavender":"#e6e6fa","lavender blush":"#fff0f5","lawn green":"#7cfc00","lemon chiffon":"#fffacd","light blue":"#add8e6","light coral":"#f08080","light cyan":"#e0ffff","light goldenrod yellow":"#fafad2",
    "light grey":"#d3d3d3","light green":"#90ee90","light pink":"#ffb6c1","light salmon":"#ffa07a","light sea green":"#20b2aa","light sky blue":"#87cefa","light slate gray":"#778899","light steel blue":"#b0c4de",
    "light yellow":"#ffffe0","lime":"#00ff00","lime green":"#32cd32","linen":"#faf0e6",
    "magenta":"#ff00ff","maroon":"#800000","medium aquamarine":"#66cdaa","medium blue":"#0000cd","medium orchid":"#ba55d3","medium purple":"#9370d8","medium sea green":"#3cb371","medium slate blue":"#7b68ee",
    "medium spring green":"#00fa9a","mediumturquoise":"#48d1cc","medium violet red":"#c71585","midnight blue":"#191970","mintcream":"#f5fffa","mistyrose":"#ffe4e1","moccasin":"#ffe4b5",
    "navajo white":"#ffdead","navy":"#000080",
    "oldlace":"#fdf5e6","olive":"#808000","olive drab":"#6b8e23","orange":"#ffa500","orange red":"#ff4500","orchid":"#da70d6",
    "pale golden rod":"#eee8aa","pale green":"#98fb98","pale turquoise":"#afeeee","pale violet red":"#d87093","papayawhip":"#ffefd5","peachpuff":"#ffdab9","peru":"#cd853f","pink":"#ffc0cb","plum":"#dda0dd","powder blue":"#b0e0e6","purple":"#800080",
    "rebecca purple":"#663399","red":"#ff0000","rosy brown":"#bc8f8f","royal blue":"#4169e1",
    "saddlebrown":"#8b4513","salmon":"#fa8072","sandy brown":"#f4a460","sea green":"#2e8b57","seashell":"#fff5ee","sienna":"#a0522d","silver":"#c0c0c0","sky blue":"#87ceeb","slate blue":"#6a5acd","slategray":"#708090","snow":"#fffafa","spring green":"#00ff7f","steel blue":"#4682b4",
    "tan":"#d2b48c","teal":"#008080","thistle":"#d8bfd8","tomato":"#ff6347","turquoise":"#40e0d0",
    "violet":"#ee82ee",
    "wheat":"#f5deb3","white":"#ffffff","white smoke":"#f5f5f5",
    "yellow":"#ffff00","yellow green":"#9acd32"}

    if color.lower() in color: #(typeof colors[color.toLowerCase()] != 'undefined')
        return colors[color.lower()]
    else:
        return "#ffffff";



XYPoint = namedtuple('XYPoint', ['x', 'y'])

# from: https://github.com/benknight/hue-python-rgb-converter/blob/master/rgbxy/__init__.py
def hex_to_xy(hex):
    try:
        hex = hex.replace('#', '')
        print("hex_to_xy: parsing hex: " + str(hex))
        #self, red_i, green_i, blue_i
    
        red_i = hex_to_red(hex)
        green_i = hex_to_green(hex)
        blue_i = hex_to_blue(hex)
    
        red = red_i / 255.0
        green = green_i / 255.0
        blue = blue_i / 255.0

        r = ((red + 0.055) / (1.0 + 0.055))**2.4 if (red > 0.04045) else (red / 12.92)
        g = ((green + 0.055) / (1.0 + 0.055))**2.4 if (green > 0.04045) else (green / 12.92)
        b = ((blue + 0.055) / (1.0 + 0.055))**2.4 if (blue > 0.04045) else (blue / 12.92)

        X = r * 0.664511 + g * 0.154324 + b * 0.162028
        Y = r * 0.283881 + g * 0.668433 + b * 0.047685
        Z = r * 0.000088 + g * 0.072310 + b * 0.986039

        cx = X / (X + Y + Z)
        cy = Y / (X + Y + Z)

        # Check if the given XY value is within the colourreach of Hue lamps.
        xy_point = XYPoint(cx, cy)
    
        # TODO: how to deal with color reach?
        #in_reach = self.check_point_in_lamps_reach(xy_point)

        #if not in_reach:
        #    xy_point = self.get_closest_point_to_point(xy_point)

        return xy_point
    except Exception as ex:
        print("Util: error in hex_to_xy: " + str(ex))
        return XYPoint(0.5, 0.5) # Wild guess..
        

def hex_to_red(self, hex):
    """Parses a valid hex color string and returns the Red RGB integer value."""
    return int(hex[0:2], 16)

def hex_to_green(self, hex):
    """Parses a valid hex color string and returns the Green RGB integer value."""
    return int(hex[2:4], 16)

def hex_to_blue(self, hex):
    """Parses a valid hex color string and returns the Blue RGB integer value."""
    return int(hex[4:6], 16)

def hex_to_rgb(self, h):
    """Converts a valid hex color string to an RGB array."""
    rgb = (self.hex_to_red(h), self.hex_to_green(h), self.hex_to_blue(h))
    return rgb

def rgb_to_hex(self, r, g, b):
    """Converts RGB to hex."""
    return '%02x%02x%02x' % (r, g, b)


def xy_to_hex(self, x, y, bri=1):
    try:
        xy_point = XYPoint(x, y)
        #if not self.check_point_in_lamps_reach(xy_point):
            # Calculate the closest point on the color gamut triangle
            # and use that as xy value See step 6 of color to xy.
        #    xy_point = self.get_closest_point_to_point(xy_point)

        # Calculate XYZ values Convert using the following formulas:
        Y = bri
        X = (Y / xy_point.y) * xy_point.x
        Z = (Y / xy_point.y) * (1 - xy_point.x - xy_point.y)

        # Convert to RGB using Wide RGB D65 conversion
        r = X * 1.656492 - Y * 0.354851 - Z * 0.255038
        g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
        b = X * 0.051713 - Y * 0.121364 + Z * 1.011530

        # Apply reverse gamma correction
        r, g, b = map(
            lambda x: (12.92 * x) if (x <= 0.0031308) else ((1.0 + 0.055) * pow(x, (1.0 / 2.4)) - 0.055),
            [r, g, b]
        )

        # Bring all negative components to zero
        r, g, b = map(lambda x: max(0, x), [r, g, b])

        # If one component is greater than 1, weight components by that value.
        max_component = max(r, g, b)
        if max_component > 1:
            r, g, b = map(lambda x: x / max_component, [r, g, b])

        r, g, b = map(lambda x: int(x * 255), [r, g, b])

        # Convert the RGB values to your color object The rgb values from the above formulas are between 0.0 and 1.0.
        #return (r, g, b)
        return '%02x%02x%02x' % (r, g, b)
    
    except Exception as ex:
        print("Util: error in xy_to_hex: " + str(ex))
        return '#FFAA00' # orange












"""
From Zigbee2MQTT addon
        
# thanks to https://stackoverflow.com/questions/20283401/php-how-to-convert-rgb-color-to-cie-1931-color-specification
def HEXtoXY(hex) { 
	hex = hex.replace(/^#/, '')
	aRgbHex = hex.match(/.{1,2}/g)
	red = int(aRgbHex[0], 16);
	green = int(aRgbHex[1], 16);
	blue = int(aRgbHex[2], 16);

	red = (red > 0.04045) ? Math.pow((red + 0.055) / (1.0 + 0.055), 2.4) : (red / 12.92);
	green = (green > 0.04045) ? Math.pow((green + 0.055) / (1.0 + 0.055), 2.4) : (green / 12.92);
	blue = (blue > 0.04045) ? Math.pow((blue + 0.055) / (1.0 + 0.055), 2.4) : (blue / 12.92);
	var X = red * 0.664511 + green * 0.154324 + blue * 0.162028;
	var Y = red * 0.283881 + green * 0.668433 + blue * 0.047685;
	var Z = red * 0.000088 + green * 0.072310 + blue * 0.986039;
	var fx = X / (X + Y + Z);
	var fy = Y / (X + Y + Z);

	return [fx.toPrecision(2), fy.toPrecision(2)];
}



function XYtoHEX(x, y, bri) { // and needs brightness too
	const z = 1.0 - x - y;
	if (x == 0) {
		x = 0.00001
	};
	if (y == 0) {
		y = 0.00001
	};
	if (bri == 0) {
		bri = 1
	};
	const Y = bri / 255.0; // Brightness of lamp
	const X = (Y / y) * x;
	const Z = (Y / y) * z;
	var r = X * 1.612 - Y * 0.203 - Z * 0.302;
	var g = -X * 0.509 + Y * 1.412 + Z * 0.066;
	var b = X * 0.026 - Y * 0.072 + Z * 0.962;

	r = r <= 0.0031308 ? 12.92 * r : (1.0 + 0.055) * Math.pow(r, (1.0 / 2.4)) - 0.055;
	g = g <= 0.0031308 ? 12.92 * g : (1.0 + 0.055) * Math.pow(g, (1.0 / 2.4)) - 0.055;
	b = b <= 0.0031308 ? 12.92 * b : (1.0 + 0.055) * Math.pow(b, (1.0 / 2.4)) - 0.055;

	const maxValue = Math.max(r, g, b);
	r /= maxValue;
	g /= maxValue;
	b /= maxValue;
	r = r * 255;
	if (r < 0) {
		r = 0
	};
	if (r > 255) {
		r = 255
	};
	g = g * 255;
	if (g < 0) {
		g = 0
	};
	if (g > 255) {
		g = 255
	};
	b = b * 255;
	if (b < 0) {
		b = 0
	};
	if (b > 255) {
		b = 255
	};

	r = Math.floor(r).toString(16);
	g = Math.floor(g).toString(16);
	b = Math.floor(b).toString(16);

	if (r.length < 2)
		r = "0" + r;
	if (g.length < 2)
		g = "0" + g;
	if (b.length < 2)
		b = "0" + b;

	return "#" + r + g + b;
}
"""