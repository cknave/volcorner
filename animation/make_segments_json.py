#!/usr/bin/env python3

import json

from PIL import Image, ImageChops, ImageDraw

IMAGE_PAIRS = [tuple(s.format(i) for s in ('segment_empty{}.png', 'segment_full{}.png'))
               for i in range(1, 5)]

OUTPUT_FILE = 'segments.json'


def main():
    # Build the segment JSON.
    result = \
        {
            'segments': [
                {
                    'empty': empty,
                    'full': full,
                    'travel': find_max_travel(full),
                    'bbox': find_bbox(full)
                }
                for empty, full in IMAGE_PAIRS
            ]
        }
    # Write it to the output file.
    with open(OUTPUT_FILE, 'w') as output:
        json.dump(result, output, indent=2)


def find_max_travel(full_filename):
    # Open the full segment and extract its alpha channel.
    full = Image.open(full_filename)
    mask = full.split()[-1]
    # Offset the image further towards the origin until the canvas is empty.
    canvas = Image.new('RGBA', full.size)
    draw = ImageDraw.Draw(canvas)
    for offset in range(1, full.size[0]):
        # Clear the canvas
        draw.rectangle([(0, 0), full.size], fill=0)
        # Paste in the full segment in its new position
        canvas.paste(full, (-offset, -offset), mask)
        # Mask with the alpha channel at its original position
        alpha = canvas.split()[-1]
        result = ImageChops.multiply(alpha, mask)
        if image_is_empty(result):
            return offset
    # No other offset worked, so travel the entire width of the image.
    return full.size[0]


def image_is_empty(image):
    alpha = image.split()[-1]
    return alpha.getbbox() is None


def find_bbox(full_filename):
    full = Image.open(full_filename)
    alpha = full.split()[-1]
    return alpha.getbbox()


if __name__ == '__main__':
    main()
