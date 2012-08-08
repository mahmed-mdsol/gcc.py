## {{{ http://code.activestate.com/recipes/362879/ (r1)
import Image, ImageDraw, ImageEnhance, ImageFont

def reduce_opacity(im, opacity):
    """Returns an image with reduced opacity."""
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im

def watermark(im, mark, position, opacity=1):
    """Adds a watermark to an image."""
    if opacity < 1:
        mark = reduce_opacity(mark, opacity)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    # create a transparent layer the size of the image and draw the
    # watermark in that layer.
    layer = Image.new('RGBA', im.size, (0,0,0,0))
    if position == 'tile':
        for y in range(0, im.size[1], mark.size[1]):
            for x in range(0, im.size[0], mark.size[0]):
                layer.paste(mark, (x, y))
    elif position == 'scale':
        # scale, but preserve the aspect ratio
        ratio = min(
            float(im.size[0]) / mark.size[0], float(im.size[1]) / mark.size[1])
        w = int(mark.size[0] * ratio)
        h = int(mark.size[1] * ratio)
        mark = mark.resize((w, h))
        layer.paste(mark, ((im.size[0] - w) / 2, (im.size[1] - h) / 2))
    else:
        layer.paste(mark, position)
    # composite the watermark with the layer
    return Image.composite(layer, im, layer)

def test():
    im = Image.open('test.png')
    mark = Image.open('overlay.png')
    watermark(im, mark, 'tile', 0.5).show()
    watermark(im, mark, 'scale', 1.0).show()
    watermark(im, mark, (100, 100), 0.5).show()

## end of http://code.activestate.com/recipes/362879/ }}}

def round_corner(radius, fill):
    """Draw a round corner"""
    corner = Image.new('RGBA', (radius, radius), (0, 0, 0, 0))
    draw = ImageDraw.Draw(corner)
    draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=fill)
    return corner
 
def round_rectangle(size, radius, fill):
    """Draw a rounded rectangle"""
    width, height = size
    rectangle = Image.new('RGBA', size, fill)
    corner = round_corner(radius, fill)
    rectangle.paste(corner, (0, 0))
    rectangle.paste(corner.rotate(90), (0, height - radius)) # Rotate the corner and paste it
    rectangle.paste(corner.rotate(180), (width - radius, height - radius))
    rectangle.paste(corner.rotate(270), (width - radius, 0))
    return rectangle

## end of http://nadiana.com/pil-tutorial-basic-advanced-drawing

def write_centered_text(img, text, color='black', font=None):
  '''Write the given text centered vertically and horizontally on the given image'''
  draw = ImageDraw.Draw(img)
  text_size = draw.textsize(text, font=font)
  y = img.size[1]/2 - text_size[1]/2
  x = img.size[0]/2 - text_size[0]/2
  draw.text((x,y), text, fill=color, font=font)
  return img

## Adapted above from http://forums.devshed.com/python-programming-11/centering-graphical-text-with-pil-409129.html

if __name__ == '__main__':
  rect_size = (200,50)
  text = "Sunday, August 5, 2012"
  font = ImageFont.truetype("HannaHandwriting.ttf", 14)
  mark = write_centered_text(round_rectangle(rect_size, 10, "grey"), text, color='white', font=font)
  im = Image.open('test.png')
  watermark(im, mark, (im.size[0] - mark.size[0], im.size[1] - mark.size[1]), 0.5).show()




#if __name__ == '__main__':
#    test()



