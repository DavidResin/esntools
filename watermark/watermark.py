import os
import sys
from math import sqrt

from PIL import Image, ExifTags

EXTS = ('.jpg', '.png', '.jpeg')
WATERMARK_RATIO = 0.02

if len(sys.argv) < 3:
    print('Usage: watermark.py \'image folder path\' \'logo path\' [topleft, topright, bottomleft, bottomright, center]')
    sys.exit()
elif len(sys.argv) == 4:
    path = sys.argv[1]
    lgo = sys.argv[2]
    pos = sys.argv[3]
else:
    path = sys.argv[1]
    lgo = sys.argv[2]


for filename in os.listdir(path):
    if any([filename.lower().endswith(ext) for ext in EXTS]) and filename.split("\\")[-1] != lgo.split("\\")[-1]:

        print(filename + " " + lgo)
        logo = Image.open(lgo)
        logoWidth = logo.width
        logoHeight = logo.height
        image = Image.open(path + '/' + filename)

        if image._getexif():
            exif=dict((ExifTags.TAGS[k], v) for k, v in image._getexif().items() if k in ExifTags.TAGS)
            try:  
                print("Orientation:", exif['Orientation'])
                if exif['Orientation'] == 3: 
                    image=image.rotate(180, expand=True)
                elif exif['Orientation'] == 6: 
                    image=image.rotate(270, expand=True)
                elif exif['Orientation'] == 8: 
                    image=image.rotate(90, expand=True)
            except:
                pass

        imageWidth = image.width
        imageHeight = image.height
        print("Image Width:", imageWidth, "Image Height:", imageHeight)
        ratio = (logoWidth*logoHeight)/(imageWidth*imageHeight)
        print("Ratio:", ratio)
        
        if ratio > WATERMARK_RATIO:
            logoWidth = int(logoWidth*sqrt(WATERMARK_RATIO/ratio))
            logoHeight = int(logoHeight*sqrt(WATERMARK_RATIO/ratio))
            print("Logo Width:", logoWidth, "\tLogo Height:", logoHeight)
            print("New ratio:", (logoWidth*logoHeight)/(imageWidth*imageHeight))
            logo = logo.resize((logoWidth, logoHeight), Image.ANTIALIAS)

        try:
            if pos == 'topleft':
                image.paste(logo, (20, 20), logo)
            elif pos == 'topright':
                image.paste(logo, (imageWidth - logoWidth - 20, 20), logo)
            elif pos == 'bottomleft':
                image.paste(logo, (20, imageHeight - logoHeight - 20), logo)
            elif pos == 'bottomright':
                image.paste(logo, (imageWidth - logoWidth - 20, imageHeight - logoHeight - 20), logo)
            elif pos == 'center':
                image.paste(logo, ((imageWidth - logoWidth)/2, (imageHeight - logoHeight)/2), logo)
            else:
                print('Error: ' + pos + ' is not a valid position')
                print('Usage: watermark.py \'image path\' \'logo path\' [topleft, topright, bottomleft, bottomright, center]')

            image.save(path +  '/' + filename)
            print('Added watermark to ' + path + '/' + filename)

        except:
            image.paste(logo, ((imageWidth - logoWidth)/2, (imageHeight - logoHeight)/2), logo)
            image.save(path + '/' + filename)
            print('Added default watermark to ' + path + '/' + filename)
