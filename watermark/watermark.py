# Default libraries
import random
import sys
from pathlib import Path

# External libraries
from PIL import Image
from pillow_heif import register_heif_opener

# Custom libraries
from helpers.image_manipulation import watermark_image
from helpers.file_operations import create_dir_if_missing, glob_all_except, flush_output, attempt_open_image, EXTS
from helpers.others import setup_argparser, get_pos_list

# Main code
if __name__ == "__main__":

	root_path = Path()
	logo_path = root_path / "logos"

	# Define default values
	default_values = {
		"ss": 			2,
		"wm_size": 		0.07,
		"wm_ratio": 	1.6,
		"wm_pad": 		0.15,
		"wm_prefix":	"wm_",
		"input": 		"input",
		"output": 		"output",
		"format": 		"png",
	}

	# Other parameters
	proc_str = "Processing image {} of {} \t({} of {} variations, \tinvalid: {})"
	end_str = "Processed {} images successfully!"
	inv_str = " ({} image(s) failed and moved to 'invalid')"
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
		"color": Image.open(logo_path / fn_color),
		"white": Image.open(logo_path / fn_white)
	}

	# Setup argparser and parse arguments
	ap = setup_argparser(default_vals=default_values, color_choices=color_choices, pos_choices=pos_choices)
	args = vars(ap.parse_args())

	prefix = 	default_values["wm_prefix"] * (not args["no_prefix"])
	path_in = 	root_path / args["input"]
	path_out = 	root_path / args["output"]
	path_inv = 	root_path / "invalid"
	pos = 		args["position"]
	
	circle_offset_ratio_x = 3 / 5
	circle_offset_ratio_y = 1
	
	ratios = {
		"image_watermark_ratio": 	args["watermark_size"],
		"logo_padding_ratio": 		args["watermark_padding"],
		"logo_circle_ratio": 		args["watermark_ratio"],
		"circle_offset_ratio_x": 	.5 if args["center_circle"] else circle_offset_ratio_x,
		"circle_offset_ratio_y": 	.5 if args["center_circle"] else circle_offset_ratio_y,
		"ss_factor": 				args["supersampling"],
		"draw_circle":				not args["no_circle"],
	}

	# Create missing folders if needed
	create_dir_if_missing(path_out)
	create_dir_if_missing(path_inv)

	# Process filenames
	if path_in.is_dir():
		paths_imgs = glob_all_except(path_in, excluded_patterns=["*.gitkeep"])
	else:
		create_dir_if_missing(default_values["input"])
		sys.exit("Input folder not found. Make sure you arguments are correct or use the default '" + default_values["input"] + "' folder.")

	# Flush all images in the output directory if asked to
	if args["flush"]:
		flush_output(path_out, EXTS)
		
	# Apply to all images
	invalid_count = 0

	# TODO : Condition this
	# Enable the HEIF/HEIC Pillow plugin
	register_heif_opener()

	# Loop through images
	for processed_count, curr_path_in in enumerate(paths_imgs):
		image = attempt_open_image(curr_path_in, path_inv, attempt_rotate=not args["no_rotate"])

		if image is None:
			continue
		
		# Choose a color for the 'random' case
		if args["color"] == "random":
			color_list = [random.choice(list(color_choices.values()))]
			
		# Randomize position if asked
		pos_list = get_pos_list(pos, pos_choices)

		print("Processing image", processed_count, "of", len(paths_imgs), "| Colors:", len(color_list), "| Variations:", len(pos_list), "| Invalid:", invalid_count, end="\r")

		# Watermark picture
		watermark_image(image, curr_path_in, logos, ratios, pos_list, color_list)

	print()
	print("Done")