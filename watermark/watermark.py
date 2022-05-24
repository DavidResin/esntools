##################################################
##												##
##	File :		watermark.py					##
##	Author :	David Resin, ESN EPFL			##
##	Date :		24.05.2022						##
##	Email :		davidresin@citycable.ch			##
##	Repo :		github.com/DavidResin/esntools	##
##												##
## ============================================ ##
##												##
##	HOW TO RUN									##
##		1 - Install Python 3					##
##		2 - "cd path/to/the/watermark/folder"	##
##		3 - "pip install -r requirements.txt"	##
##		4 - "python watermark.py"				##
##												##
##################################################

# Default libraries
import os
import random
import sys

# External libraries
from PIL import Image, UnidentifiedImageError
import pillow_heif

# Custom library
from helpers import *

# Main code
if __name__ == "__main__":

	# Define default values
	default_vals = {
		"ss": 			2,
		"wm_size": 		1 / 8,
		"wm_ratio": 	1.6,
		"wm_pad": 		0.15,
		"wm_prefix":	"wm_",
		"input": 		"input",
		"output": 		"output",
		"format": 		"png"
	}

	# Other parameters
	exts = ('.jpg', '.png', '.jpeg', '.ico', '.webp', '.heic')
	preproc_exts = ('.heic')
	proc_str = "Processing image {} of {} \t({} of {} variations, \tinvalid: {})"
	end_str = "Processed {} images successfully!"
	inv_str = " ({} image(s) failed and moved to 'invalid')"
	path_inv = "invalid"
	tilt_map = {0: 0, 1: 180, 2: 270, 3: 90}
	pos_choices = ["bottom_right", "bottom_left", "top_right", "top_left", "random", "all"]
	color_choices = {
		"white": (255, 255, 255),
		"black": (0, 0, 0),
		"magenta": (236, 0, 140),
		"orange": (244, 123, 32),
		"green": (122, 193, 67),
		"cyan": (0, 174, 239),
		"purple": (46, 49, 146),
	}

	# Names of logo files
	fn_color = "logo_color.png"
	fn_white = "logo_white.png"

	# Open logo files
	logos = {
		"color": Image.open(os.path.join("logos", fn_color)),
		"white": Image.open(os.path.join("logos", fn_white))
	}

	# Setup argparser and parse arguments
	ap = setup_argparser(default_vals=default_vals, color_choices=color_choices, pos_choices=pos_choices)
	args = vars(ap.parse_args())

	prefix = 	default_vals["wm_prefix"] * (not args["no_prefix"])
	path_in = 	args["input"]
	path_out = 	args["output"]
	pos = 		args["position"]
	
	ratios = {
		"img_wm_ratio": 		args["watermark_size"],
		"logo_padding_ratio": 	args["watermark_padding"],
		"logo_circle_ratio": 	args["watermark_ratio"],
		"circle_shift_ratio_x": 3 / 5,
		"circle_shift_ratio_y": 1,
		"ss_factor": 			args["supersampling"]
	}

	# Create missing folders if needed
	create_dir_if_missing(path_out)
	create_dir_if_missing(path_inv)

	# Parse color
	color_list = parse_color(args, color_choices)

	# Process filenames
	try:
		fns = [el for el in os.listdir(path_in) if el != ".gitkeep"]
	except:
		create_dir_if_missing(default_input)
		sys.exit("Input folder not found. Make sure you arguments are correct or use the default '" + default_input + "' folder.")

	img_total = len(fns)

	# Flush all images in the output directory if asked to
	if args["flush"]:
		flush_output(path_out, exts)
		
	# Apply to all images
	processed_count = 0
	invalid_count = 0

	for fn in fns:
		processed_count += 1
		
		# Generate paths
		file_in = os.path.join(path_in, fn)
		file_out = os.path.join(path_out, prefix + fn).rsplit(".", 1)
		
		# Move picture to 'invalid' if it doesn't have the right file format
		if not any([fn.lower().endswith(ext) for ext in exts]):
			invalid_count = invalidate(fn, file_in, path_inv, invalid_count)
			continue
	
		# Try to load image
		if any([fn.lower().endswith(ext) for ext in preproc_exts]):
			# Special formats
			heif_file = pillow_heif.read_heif(file_in)
			img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw")
			fn = fn.rsplit(".", maxsplit=1)[0] + "." + default_format
		else:
			try:
				img = Image.open(file_in)
			except (FileNotFoundError, UnidentifiedImageError, ValueError) as e:
				invalid_count = invalidate(fn, file_in, path_inv, invalid_count)
				continue
		
		# Unify format if asked to
		if args["keep"]:
			file_out[1] = default_format

		# Try to re-orient the picture if it is allowed and orientation data is available 
		if not args["no_rotate"] and img._getexif():
			img = tilt_img(img, tilt_map)
		
		# Choose a color for the 'random' case
		if args["color"] == "random":
			color_list = [random.choice(list(color_choices.values()))]
			
		# Randomize position if asked
		pos_list = get_pos_list(pos)

		print("Processing image", processed_count, "of", len(fns), "| Colors:", len(color_list), "| Variations:", len(pos_list), "| Invalid:", invalid_count, end="\r")

		# Watermark picture
		watermark_image(img, file_out, logos, ratios, pos_list, color_list, draw_circle=not args["no_circle"], center_circle=args["center_circle"])

	print()
	print("Done")