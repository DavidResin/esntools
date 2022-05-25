##################################################
##												##
##	File :		functions.py					##
##	Author :	David Resin, ESN EPFL			##
##	Date :		24.05.2022						##
##	Email :		davidresin@citycable.ch			##
##	Repo :		github.com/DavidResin/esntools	##
##												##
## ============================================ ##
##												##
##	THIS IS A HELPER FILE AND IS NOT MEANT		##
##	TO BE RUN ON ITS OWN.						##
##												##
##################################################

# Default libraries
import argparse
import os
import random
import shutil
import sys
import textwrap

# External library
from PIL import ImageColor, ImageDraw, ExifTags

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
	
# Create a directory if it is missing
def create_dir_if_missing(path):
	if not os.path.exists(path):
		os.makedirs(path)

# Auromatically tilt an image based on its EXIF data
def tilt_img(img, tilt_map):
	tilt = dict((ExifTags.TAGS[k], v) for k, v in img._getexif().items() if k in ExifTags.TAGS).get('Orientation')
	tilt_idx = tilt_map[(tilt - 1) // 2]
	return img.rotate(tilt_idx, expand=True)

# Flush the output directory
def flush_output(path_out, exts):
	for old in os.listdir(path_out):
		if any([old.lower().endswith(ext) for ext in exts]):
			os.remove(os.path.join(path_out, old))

# Move an invalid picture out
def invalidate(fn, img_path, path_inv, invalid_count):
	shutil.move(img_path, os.path.join(path_inv, fn))
	return invalid_count + 1

# Generate list of positions based on arguments
def get_pos_list(pos):
	if pos == "random":
		ret = [pos_choices[random.randint(0, 3)]]
	elif pos == "all":
		ret = pos_choices[:4]
	else:
		ret = [pos]

	return ret

# Watermark an image with a given position and color
def watermark_image_pos_color(img, sub_img, big_sub_img, file_out, pos, logo, crop_edges, circle_edges, circle_center, circle_radius, logo_dims, logo_center, color, shifts, ss_factor, draw_circle=True, suffix=""):
	# Drawing the circle if requested
	if draw_circle:
		ImageDraw.Draw(big_sub_img).ellipse([ss_factor * elem for elem in circle_edges], fill=color)

	# Pasting the logo
	big_sub_img.paste(logo, [int(ss_factor * (edges + circle_radius - shift) - dim / 2) for edges, shift, dim in zip(circle_edges[:2], shifts, logo.size)], logo)

	# Downscale the watermark area back to its normal size then paste it on the full image
	sub_img = big_sub_img.resize(sub_img.size)
	img_out = img.copy()
	img_out.paste(sub_img, crop_edges[:2])

	# Format suffix
	if len(suffix):
		suffix = "_" + suffix

	# Save the image
	fst, snd = file_out
	img_out.save(fst + "_" + pos + str(suffix) + "." + snd)

# Watermark an image with a given position and a list of colors
def watermark_image_pos(img, file_out, pos, logos, logo_dims, logo_center, circle_center, circle_radius, shifts, color_list, ss_factor, draw_circle=True):
	# Compute circle bounding box from the center and radius
	circle_edges_x = circle_center[0] - circle_radius, circle_center[0] + circle_radius
	circle_edges_y = circle_center[1] - circle_radius, circle_center[1] + circle_radius

	# Compute real bounding box by removing out-of-bounds parts
	crop_edges_x = max(0, circle_edges_x[0]), min(img.size[0], circle_edges_x[1])
	crop_edges_y = max(0, circle_edges_y[0]), min(img.size[1], circle_edges_y[1])
	crop_edges = tuple([int(elem) for elem in [crop_edges_x[0], crop_edges_y[0], crop_edges_x[1], crop_edges_y[1]]])

	# Compute circle edges relative to the cropped area
	padded_circle_edges_x = [elem - crop_edges_x[0] for elem in circle_edges_x]
	padded_circle_edges_y = [elem - crop_edges_y[0] for elem in circle_edges_y]
	padded_circle_edges = tuple([int(elem) for elem in [padded_circle_edges_x[0], padded_circle_edges_y[0], padded_circle_edges_x[1], padded_circle_edges_y[1]]])

	# Crop out the area of the watermark and upscale it
	sub_img = img.crop(box=crop_edges)
	big_sub_img = sub_img.resize([ss_factor * dim for dim in sub_img.size])
		
	# Loop through the selected colors
	for suffix, color in enumerate(color_list):
		#variation_count += 1
		logo = logos["color"] if color == (255, 255, 255) else logos["white"]	
			
		# No need for color suffix if only one color
		if len(color_list) == 1:
			suffix = ""

		# Watermark picture
		watermark_image_pos_color(	img=img, \
									sub_img=sub_img, \
									big_sub_img=big_sub_img, \
									file_out=file_out, \
									pos=pos, \
									logo=logo, \
									crop_edges=crop_edges, \
									circle_edges=padded_circle_edges, \
									circle_center=circle_center, \
									circle_radius=circle_radius, \
									logo_dims=logo_dims, \
									logo_center=logo_center, \
									color=color, \
									shifts=shifts, \
									ss_factor=ss_factor, \
									draw_circle=draw_circle, \
									suffix=str(suffix))

# Watermark an image with a list of positions and a list of colors
def watermark_image(img, file_out, logos, ratios, pos_list, color_list, draw_circle=True, center_circle=False):
	image_width, image_height = img.size
	src_logo_width, src_logo_height = logos["color"].size

	# Compute logo dimensions from image dimensions and image-watermark ratio
	tgt_logo_height = ratios["img_wm_ratio"] * image_height
	tgt_logo_width = tgt_logo_height / src_logo_height * src_logo_width

	# Rescale the logos for the current picture
	logos_scaled = dict([(key, logo.resize([int(ratios["ss_factor"] * elem) for elem in [tgt_logo_width, tgt_logo_height]])) for key, logo in logos.items()])

	# Compute logo padding from padding ratio and logo height
	logo_padding = ratios["logo_padding_ratio"] * tgt_logo_height

	# Compute logo center from padding and logo dimensions
	logo_center_x = logo_padding + tgt_logo_width / 2
	logo_center_y = logo_padding + tgt_logo_height / 2

	# Iterate through positions
	for pos in pos_list:
		# Set logo center depending on the chosen position
		curr_logo_center_x = logo_center_x if "left" in pos else image_width - logo_center_x
		curr_logo_center_y = logo_center_y if "top" in pos else image_height - logo_center_y

		# Set circle position
		ratio_x = .5 if center_circle else ratios["circle_shift_ratio_x"]
		ratio_y = .5 if center_circle else ratios["circle_shift_ratio_y"]

		# Compute shifts
		sX = tgt_logo_width * (ratio_x - .5) * ((-1) ** ("left" in pos))
		sY = tgt_logo_height * (ratio_y - .5) * ((-1) ** ("top" in pos))

		# Compute circle center from logo center and offset factors
		curr_circle_center_x = curr_logo_center_x + sX
		curr_circle_center_y = curr_logo_center_y + sY

		# Compute circle radius from logo width and logo-circle ratio
		circle_radius = tgt_logo_width * ratios["logo_circle_ratio"] / 2

		watermark_image_pos(img=img, \
							file_out=file_out, \
							pos=pos, \
							logos=logos_scaled, \
							logo_dims=[tgt_logo_width, tgt_logo_height], \
							logo_center=[curr_logo_center_x, curr_logo_center_y], \
							circle_center=[curr_circle_center_x, curr_circle_center_y], \
							circle_radius=circle_radius, \
							shifts=[sX, sY], \
							color_list=color_list, \
							ss_factor=ratios["ss_factor"], \
							draw_circle=draw_circle)

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