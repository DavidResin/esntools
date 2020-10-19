import argparse, math, os, random, shutil, sys, textwrap
from PIL import Image, ImageColor, ImageDraw, ExifTags

# Define image exporting routine
def export_image(img, wm, pos, color, dist, file_out, circle, radius, suff=""):
    p = "".join([x[0] for x in pos.split("-")])
    iW, iH = img.size
    wW, wH = wm.size

    # Computing logo position
    sH = wH / 2 + min(wH, wW) * dist
    sH = int(sH if "t" in p else iH / 2 if p == "c" else iH - sH)
    
    sW = wW / 2 + min(wH, wW) * dist
    sW = int(sW if "l" in p else iW / 2 if p == "c" else iW - sW)
        
    # Supersampling the image to draw a smooth circle
    if circle:
        factor = 8
        r = int(max(wW, wH) * radius / 2)
        img_big = img.resize([factor * x for x in img.size])
        ImageDraw.Draw(img_big).ellipse(tuple(factor * x for x in (sW - r, sH - r, sW + r, sH + r)), fill=color)
        img = img_big.resize(img.size)

    # Pasting the logo
    img.paste(wm, (sW - int(wW / 2), sH - int(wH / 2)), wm)
    
    # Saving
    fst, snd = file_out
    img.save(fst + "_" + p + str(suff) + "." + snd)

# Define default data
d_size = 0.025
d_dist = .3
d_radius = 1.55
d_input = "input"
d_output = "output"
d_format = "png"
fn_color = "logo_color.png"
fn_white = "logo_white.png"
prefix = "wm_"
pos_choices = ["bottom-right", "bottom-left", "top-right", "top-left", "center", "random", "random-plus", "all"]
color_choices = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "magenta": (236, 0, 140),
    "orange": (244, 123, 32),
    "green": (122, 193, 67),
    "cyan": (0, 174, 239),
    "purple": (46, 49, 146),
}

# Setup argument parser
ap = argparse.ArgumentParser(description="ESN Watermark Inserter", formatter_class=argparse.RawTextHelpFormatter)
ap.add_argument("-q",	"--quiet",		action="store_true",							help="silent running")
ap.add_argument("-f",	"--flush",		action="store_true",							help="flush output folder")
ap.add_argument("-k",	"--keep",		action="store_true",							help=f"keep original file format (if omitted, will default to { d_format.upper() } format)")
ap.add_argument("-np",	"--no-prefix",	action="store_true",							help=f"do not add a '{ prefix }' prefix to outputs")
ap.add_argument("-nr",	"--no-rotate",	action="store_true",							help=f"do not rotate images if they are not upright")
ap.add_argument("-nc",	"--no-circle",	action="store_true",							help="do not add a colored circle behind the logo (not recommended)")
ap.add_argument("-i",	"--input",		action="store", type=str,	default=d_input,	help=f"set a custom input directory path (default is '{ d_input }')")
ap.add_argument("-o",	"--output",		action="store", type=str,	default=d_output,	help=f"set a custom output directory path (default is '{ d_output }')")
ap.add_argument("-s",	"--size",		action="store", type=float,	default=d_size,		help=f"set the ratio of the watermark's size compared to the image's size (default is { d_size })")
ap.add_argument("-d",	"--distance",	action="store", type=float,	default=d_dist,		help=f"set the ratio of the watermark's padding to the size of the watermark (default is { d_dist })")
ap.add_argument("-r",	"--radius",		action="store", type=float,	default=d_radius,	help=f"set the ratio of the circle's size compared to the logo's size (default is { d_radius })")
ap.add_argument("-c",	"--color",		action="store",
                                        type=str,
                                        default=list(color_choices.keys())[0],
                                        help=textwrap.dedent("set the color of the circle, options are the following:\n"
                                                            + "> official ESN colors:\n"
                                                                + "\t'white' [Default value]\n"
                                                                + "\t'black'\n"
                                                                + "\t'magenta'\n"
                                                                + "\t'orange'\n"
                                                                + "\t'green'\n"
                                                                + "\t'cyan'\n"
                                                                + "\t'purple'\n"
                                                            + "> 'random' [Random color for each image]\n"
                                                            + "> 'all' [All versions of each image with suffixes]\n"
                                                            + "> '#rrggbb' [Any other HEX RGB color, not recommended]"))
ap.add_argument("-p",	"--position",	type=str,
                                        metavar="POSITION",
                                        default=pos_choices[0],
                                        choices=pos_choices,
                                        help=textwrap.dedent("set the position of the watermark, options are the following:\n"
                                                            + "> 'bottom-right' [Default value]\n"
                                                            + "> 'bottom-left'\n"
                                                            + "> 'top-right'\n"
                                                            + "> 'top-left'\n"
                                                            + "> 'center'\n"
                                                            + "> 'random' [Random edge for each image]\n"
                                                            + "> 'random-plus' [Random edge or center for each image]\n"
                                                            + "> 'all' [All versions of each image with suffixes]"))

# Parse arguments
args = vars(ap.parse_args())

quiet = args["quiet"]
flush = args["flush"]
keep = args["keep"]
prefix = prefix * (not args["no_prefix"])
rotate = not args["no_rotate"]
circle = not args["no_circle"]
path_in = args["input"]
path_out = args["output"]
path_inv = "invalid"
ratio = args["size"]
dist = args["distance"]
radius = args["radius"]
color = args["color"]
pos = args["position"]

# Parse color
try:
    if color == "random":
        this_color = []
    elif color == "all":
        this_color = list(color_choices.values())
    else:
        this_color = [color_choices.get(color) or ImageColor.getrgb(color)]
except:
    sys.exit("Wrong color format. Official ESN color or #rrggbb hexadecimal format expected.")

# Define work variables
try:
    fns = os.listdir(path_in)
    this_pos = pos
    count, total, invalid = 0, len(fns), 0
except:
    if not os.path.exists(d_input):
        os.makedirs(d_input)
        
    sys.exit("Input folder not found. Make sure you arguments are correct or use the default '" + d_input + "' folder.")
    
# Create missing folders
if not os.path.exists(path_out):
    os.makedirs(path_out)
    
if not os.path.exists(path_inv):
    os.makedirs(path_inv)

exts = ('.jpg', '.png', '.jpeg', '.ico', '.webp')
proc_str = "Processing image {} of {} (invalid: {})"
end_str = "Processed {} images successfully!"
inv_str = " ({} image(s) failed and moved to 'invalid')"

# Load watermark
wm_color = Image.open(fn_color)
wm_white = Image.open(fn_white)
wm = wm_color
wW, wH = wm.size

# Flush all valid images in output directory if asked to
if flush:
    for old in os.listdir(path_out):
        if any([old.lower().endswith(ext) for ext in exts]):
            os.remove(os.path.join(path_out, old))

# Apply to all images
for fn in fns:
    count += 1
    print(proc_str.format(count, total, invalid), end="\r")
    
    # Generate paths
    file_in = os.path.join(path_in, fn)
    file_out = os.path.join(path_out, prefix + fn).rsplit(".", 1)
    
    # Move picture to 'invalid' if it doesn't have the right file format
    if not any([fn.lower().endswith(ext) for ext in exts]):
        invalid += 1
        shutil.move(file_in, os.path.join(path_inv, fn))
        continue
        
    # Try to load image
    try:
        img = Image.open(file_in)
        iW, iH = img.size
        wm_ratio = (wW * wH) / (iW * iH)
    except:
        invalid += 1
        shutil.move(file_in, os.path.join(path_inv, fn))
        continue
    
    # Unify format if asked to
    if keep:
        file_out[1] = d_format

    # Try to re-orient the picture if it is allowed and orientation data is available 
    if rotate and img._getexif():
        tilt = dict((ExifTags.TAGS[k], v) for k, v in img._getexif().items() if k in ExifTags.TAGS)['Orientation']
        
        try:  
            if tilt in [3, 4]:
                img = img.rotate(180, expand=True)
            elif tilt in [5, 6]:
                img = img.rotate(270, expand=True)
            elif tilt in [7, 8]:
                img = img.rotate(90, expand=True)
        except:
            pass
    
    # Choose a color for the 'random' case
    if color == "random":
        this_color = [random.choice(list(color_choices.values()))]
        
    # Randomize position if asked
    if pos == "random":
        this_pos = [pos_choices[random.randint(0, 3)]]
    elif pos == "random-plus":
        this_pos = [pos_choices[random.randint(0, 4)]]
    elif pos == "all":
        this_pos = pos_choices[:5]
    else:
        this_pos = [pos]
        
    for p in this_pos:
        for suff, c in enumerate(this_color):
            # Use white logo is background not white
            this_wm = wm_color if c == (255, 255, 255) else wm_white
            
            # No need for color suffix if only one color
            if len(this_color) == 1:
                suff = ""    
                
            # Resize watermark only if it doesn't exceed its own resolution
            if wm_ratio > ratio:
                this_w = int(wW * math.sqrt(ratio / wm_ratio))
                this_h = int(wH * math.sqrt(ratio / wm_ratio))
                this_wm = this_wm.resize((this_w, this_h), Image.ANTIALIAS)
            
            export_image(img.copy(), this_wm, p, c, dist, file_out, circle=circle, radius=radius, suff=suff)

print()
print(end_str.format(total) + (inv_str.format(invalid) if invalid else ""))