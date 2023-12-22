# Default libraries
import argparse
import random
import sys
import textwrap

# External libraries
from PIL import ImageColor

COLOR_OPTIONS = {
	"white": 	(255, 255, 255),
	"black": 	(  0,   0,   0),
	"magenta": 	(236,   0, 140),
	"orange": 	(244, 123,  32),
	"green": 	(122, 193,  67),
	"cyan": 	(  0, 174, 239),
	"purple": 	( 46,  49, 146),
}

POSITION_OPTIONS = [
	"bottom_right",
	"bottom_left",
	"top_right",
	"top_left",
	"random",
	"all",
]

# Color parsing
def color_names_list_from_setting(color_setting):
	if color_setting == "random":
		return [random.choice(list(COLOR_OPTIONS.keys()))]
	elif color_setting == "all":
		return list(COLOR_OPTIONS.keys())
	else:
		return [color_setting]

def color_mapping_from_setting(color_setting):
	ret = dict()

	for color_name in color_names_list_from_setting(color_setting):
		color = COLOR_OPTIONS.get(color_name)

		if color is None:
			try:
				print(color_name, color)
				color = ImageColor.getrgb(color_name)				
			except ValueError:
				sys.exit("Wrong color format. Official ESN color or #rrggbb hexadecimal format expected.")

		ret[color_name] = color
	
	return ret	

# Generate list of positions based on arguments
def position_list_from_setting(position):
	if position == "random":
		ret = [POSITION_OPTIONS[random.randint(0, 3)]]
	elif position == "all":
		ret = POSITION_OPTIONS[:4]
	else:
		ret = [position]

	return ret

def get_any_dict_value(dictionary):
	return next(iter(dictionary.values()))

def get_dict_value_or_none_value(dictionary: dict, key):
	return dictionary.get(key, dictionary[None])

# Setup argument parser
def setup_argparser(default_vals, color_options, pos_choices):
	ap = argparse.ArgumentParser(description="ESN Lausanne Watermark Inserter", formatter_class=argparse.RawTextHelpFormatter)
	ap.add_argument("-f",	"--flush",				action="store_true",																help="flush output folder")
	ap.add_argument("-np",	"--no-prefix",			action="store_true",																help="do not add a '{}' prefix to outputs".format(default_vals["wm_prefix"]))
	ap.add_argument("-nr",	"--no-rotate",			action="store_true",																help="do not rotate images if they are not upright")
	ap.add_argument("-nc",	"--no-circle",			action="store_true",																help="do not add a colored circle behind the logo (not recommended)")
	ap.add_argument("-cc",	"--center-circle",		action="store_true",																help="center the circle around the logo (not recommended)")
	ap.add_argument("-i",	"--input-dir",			action="store", type=str,	default=default_vals["input_dir"],						help="set a custom input directory path (default is '{}')".format(default_vals["input_dir"]))
	ap.add_argument("-o",	"--output-dir",			action="store", type=str,	default=default_vals["output_dir"],						help="set a custom output directory path (default is '{}')".format(default_vals["output_dir"]))
	ap.add_argument("-wms",	"--watermark-size",		action="store", type=float,	default=default_vals["wm_size"],						help="set the size of the watermark compared to the image's size (default is {})".format(default_vals["wm_size"]))
	ap.add_argument("-wmr",	"--watermark-ratio",	action="store", type=float,	default=default_vals["wm_ratio"],						help="set the size ratio between the logo's width and the circle's diameter, (default is {})".format(default_vals["wm_ratio"]))
	ap.add_argument("-wmp",	"--watermark-padding",	action="store", type=float,	default=default_vals["wm_pad"],							help="set the padding between the logo and the edge of the picture, as a ratio of the logo's height (default is {})".format(default_vals["wm_pad"]))
	ap.add_argument("-ss",  "--supersampling",		action="store", type=int,	default=default_vals["ss_factor"], metavar="FACTOR",	help="set the supersampling factor for smoothing the circle (default is {}, smaller means faster execution but less smoothing)".format(default_vals["ss_factor"]))
	ap.add_argument("-c",	"--color",				action="store",
													type=str,
													default="random",
													help=textwrap.dedent("set the color of the circle, options are the following:\n"
																		+ "> 'random' [Random color for each image, default value]\n"
																		+ "> official ESN colors:\n"
																			+ "\t'white'\n"
																			+ "\t'black'\n"
																			+ "\t'magenta'\n"
																			+ "\t'orange'\n"
																			+ "\t'green'\n"
																			+ "\t'cyan'\n"
																			+ "\t'purple'\n"
																		+ "> 'all' [All versions of each image with suffixes]\n"
																		+ "> '#rrggbb' [Any other HEX RGB color, not recommended]"))
	ap.add_argument("-p",	"--position",			type=str,
													metavar="POSITION",
													default=pos_choices[0],
													choices=pos_choices,
													help=textwrap.dedent("set the position of the watermark, options are the following:\n"
																		+ "> 'bottom_right' [Default value]\n"
																		+ "> 'bottom_left'\n"
																		+ "> 'top_right'\n"
																		+ "> 'top_left'\n"
																		+ "> 'random' [Random edge for each image]\n"
																		+ "> 'all' [All versions of each image with suffixes]"))

	return ap