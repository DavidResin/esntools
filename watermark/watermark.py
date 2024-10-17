# Default libraries
import sys
from pathlib import Path

# External libraries
from PIL import Image
from pillow_heif import register_heif_opener

# Custom libraries
from helpers.image_manipulation import watermark_image
from helpers.file_operations import (
    create_dir_if_missing,
    glob_all_except,
    flush_output,
    attempt_open_image,
    IMG_EXTS
)

from helpers.others import ( # Needs to become a * import
	setup_argparser,
	position_list_from_setting,
	color_mapping_from_setting,
	COLOR_OPTIONS,
	POSITION_OPTIONS
)

# Main code
if __name__ == "__main__":

	# TODO : Configure dry run

	print("Start")

	root_path = Path()
	logo_path = root_path / "logos"

	# Define default values
	default_values = {
		"ss_factor": 	2,
		"wm_size": 		0.07,
		"wm_ratio": 	1.6,
		"wm_pad": 		0.15,
		"wm_prefix":	"wm_",
		"input_dir": 	"input",
		"output_dir": 	"output",
		"format": 		"png",
	}

	# Other parameters
	str_process = "Processing image {} of {} \t({} of {} variations, \tinvalid: {})"
	str_end = "Processed {} images successfully!"
	str_invalid = " ({} image(s) failed and moved to 'invalid')"

	# Names of logo files
	fn_color = "logo_color.png"
	fn_white = "logo_white.png"

	# Open logo files
	logos = {
		"color": Image.open(logo_path / fn_color),
		"white": Image.open(logo_path / fn_white),
	}

	# Setup argparser and parse arguments
	ap = setup_argparser(default_vals=default_values, color_options=COLOR_OPTIONS, pos_choices=POSITION_OPTIONS)
	args = vars(ap.parse_args())

	prefix = 			"" if args["no_prefix"] else default_values["wm_prefix"]
	path_input =		root_path / args["input_dir"]
	path_output =		root_path / args["output_dir"]
	path_invalid =		root_path / "invalid"
	position_setting = 	args["position"]
	
	settings = {
		"image_watermark_ratio": 	args["watermark_size"],
		"logo_padding_ratio": 		args["watermark_padding"],
		"logo_circle_ratio": 		args["watermark_ratio"],
		"circle_offset_ratio_x": 	.5 if args["center_circle"] else 3 / 5,
		"circle_offset_ratio_y": 	.5 if args["center_circle"] else 1,
		"ss_factor": 				args["supersampling"],
		"draw_circle":				not args["no_circle"],
		"output_path":				path_output,
		"color_setting":			args["color"],
		"prefix":					prefix, # TODO : Offer option to customise the prefix
		"format":					default_values["format"] # TODO : Offer option to change output format
	}

	# Create missing folders if needed
	create_dir_if_missing(path_output)
	create_dir_if_missing(path_invalid)

	# Process filenames
	if path_input.is_dir():
		image_paths = glob_all_except(path_input, excluded_patterns=["*.gitkeep"])
	else:
		create_dir_if_missing(default_values["input"])
		sys.exit("Input folder not found. Make sure you arguments are correct or use the default '" + default_values["input_dir"] + "' folder.")

	# Flush all images in the output directory if asked to
	if args["flush"]:
		flush_output(path_output, EXTS)
	
	# Apply to all images
	invalid_count = 0

	# TODO : Condition this
	# Enable the HEIF/HEIC Pillow plugin
	register_heif_opener()

	# Loop through images
	for processed_count, image_path in enumerate(image_paths):
		image = attempt_open_image(	image_path=image_path,
							 		path_invalid=path_invalid,
									attempt_rotate=not args["no_rotate"])
		
		if image is None:
			continue
		
		# Randomize position if asked
		position_list = position_list_from_setting(position_setting)
		color_mapping = color_mapping_from_setting(settings["color_setting"])

		print("Processing image", processed_count + 1, "of", len(image_paths), "| Invalid:", invalid_count, end="\r")

		# Watermark picture
		watermark_image(image,
				  		path=image_path,
						logos=logos,
						position_list=position_list,
						settings=settings)
	
	print()
	print("Done")