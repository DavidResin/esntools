# Default libraries
import argparse
import random
import sys
import textwrap

# External libraries
from PIL import ImageColor

# Color parsing
def parse_color(args, color_choices):
	color = args["color"]

	try:
		if color == "random":
			ret = []
		elif color == "all":
			ret = list(color_choices.values())
		else:
			ret = [color_choices.get(color) or ImageColor.getrgb(color)]
	except ValueError:
		sys.exit("Wrong color format. Official ESN color or #rrggbb hexadecimal format expected.")

	return ret

# Generate list of positions based on arguments
def get_pos_list(position, position_options):
	if position == "random":
		ret = [position_options[random.randint(0, 3)]]
	elif position == "all":
		ret = position_options[:4]
	else:
		ret = [position]

	return ret

# Setup argument parser
def setup_argparser(default_vals, color_choices, pos_choices):
	ap = argparse.ArgumentParser(description="ESN Lausanne Watermark Inserter", formatter_class=argparse.RawTextHelpFormatter)
	ap.add_argument("-f",	"--flush",				action="store_true",														help="flush output folder")
	ap.add_argument("-np",	"--no-prefix",			action="store_true",														help="do not add a '{}' prefix to outputs".format(default_vals["wm_prefix"]))
	ap.add_argument("-nr",	"--no-rotate",			action="store_true",														help="do not rotate images if they are not upright")
	ap.add_argument("-nc",	"--no-circle",			action="store_true",														help="do not add a colored circle behind the logo (not recommended)")
	ap.add_argument("-cc",	"--center-circle",		action="store_true",														help="center the circle around the logo (not recommended)")
	ap.add_argument("-i",	"--input",				action="store", type=str,	default=default_vals["input"],					help="set a custom input directory path (default is '{}')".format(default_vals["input"]))
	ap.add_argument("-o",	"--output",				action="store", type=str,	default=default_vals["output"],					help="set a custom output directory path (default is '{}')".format(default_vals["output"]))
	ap.add_argument("-wms",	"--watermark-size",		action="store", type=float,	default=default_vals["wm_size"],				help="set the size of the watermark compared to the image's size (default is {})".format(default_vals["wm_size"]))
	ap.add_argument("-wmr",	"--watermark-ratio",	action="store", type=float,	default=default_vals["wm_ratio"],				help="set the size ratio between the logo's width and the circle's diameter, (default is {})".format(default_vals["wm_ratio"]))
	ap.add_argument("-wmp",	"--watermark-padding",	action="store", type=float,	default=default_vals["wm_pad"],					help="set the padding between the logo and the edge of the picture, as a ratio of the logo's height (default is {})".format(default_vals["wm_pad"]))
	ap.add_argument("-ss",  "--supersampling",		action="store", type=int,	default=default_vals["ss"], metavar="FACTOR",	help="set the supersampling factor for smoothing the circle (default is {}, smaller means faster execution but less smoothing)".format(default_vals["ss"]))
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