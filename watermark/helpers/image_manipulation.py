# External libraries
from PIL import ImageDraw

# Custom libraries
from helpers.others import get_any_dict_value, get_dict_value_or_none_value, color_mapping_from_setting

TILT_MAP = {
	0: 0,
	1: 180,
	2: 270,
	3: 90,
}

EXIF_ORIENTATION_TAG = 274

ESN_CIRCLE_COLOR_MAP = {
	"white": "color",
	None:    "white",
}

# Auromatically tilt an image based on its EXIF data
def tilt_img(image):
	try:
		exif = image._getexif()
	except AttributeError:
		exif = image.getexif()

	tilt = exif.get(EXIF_ORIENTATION_TAG)

	# Don't tilt if exif orientation value is not between 1 and 8
	if tilt is None or tilt not in range(1, 9):
		return image
	
	tilt_idx = TILT_MAP[(tilt - 1) // 2]
	return image.rotate(tilt_idx, expand=True)

def logo_dims_from_image_and_ratio(logo_size, image_size, image_watermark_ratio):
	image_w, image_h = image_size
	src_logo_w, src_logo_h = logo_size

	# TODO : Make this configurable (h or w)
	tgt_logo_h = image_watermark_ratio * min(image_h, image_w)
	tgt_logo_w = tgt_logo_h / src_logo_h * src_logo_w

	return tgt_logo_w, tgt_logo_h

def scale_logos_with_supersampling(logos, target_dims, supersampling_factor):
	supersampled_dims = [int(supersampling_factor * dim) for dim in target_dims]
	return {key: logo.resize(supersampled_dims) for key, logo in logos.items()}

# Watermark an image with a given position and color
def watermark_image_pos_color(image, path, logo_ss, positioning_data, color, settings, suffix=""):
	# Crop out the area of the watermark and upscale it
	watermark_canvas = image.crop(box=positioning_data["watermark_bbox"])
	watermark_canvas_ss = watermark_canvas.resize([settings["ss_factor"] * dim for dim in watermark_canvas.size])
	
	# Drawing the circle if requested
	if settings["draw_circle"]:
		ImageDraw.Draw(watermark_canvas_ss).ellipse([settings["ss_factor"] * elem for elem in positioning_data["circle_bbox_in_watermark_bbox"]], fill=color)
	
	watermark_canvas_ss.paste(logo_ss, positioning_data["logo_pos_in_watermark_ss_bbox"], logo_ss)

	# Downscale the watermark area back to its normal size then paste it on the full image
	watermark_canvas = watermark_canvas_ss.resize(watermark_canvas.size)
	output_canvas = image.copy()
	output_canvas.paste(watermark_canvas, positioning_data["watermark_bbox"][:2])

	# Format suffix
	if len(suffix) > 0:
		suffix = "_" + suffix

	# Save the image
	path_out = settings["output_path"] / (settings["prefix"] + path.stem + suffix + "." + settings["format"])
	output_canvas.save(path_out)

# Watermark an image with a given position and a list of colors
def watermark_image_pos(image, path, position_str, logos_ss, settings, positioning_data):
	color_mapping = color_mapping_from_setting(settings["color_setting"])
	
	# Loop through the selected colors
	for suffix, (color_name, color) in enumerate(color_mapping.items()):
		# No need for color suffix if only one color
		if len(color_mapping) == 1:
			suffix = ""

		logo_ss = logos_ss[get_dict_value_or_none_value(ESN_CIRCLE_COLOR_MAP, color_name)]

		# Watermark picture
		watermark_image_pos_color(	image=image,
									path=path,
									logo_ss=logo_ss,
									positioning_data=positioning_data,
									color=color,
									settings=settings,
									suffix=str(suffix))
		
def compute_positioning_data(image_size, logo_ss_size, position_str, positioning_settings, settings):
	image_w, image_h = image_size
	logo_ss_w, logo_ss_h = logo_ss_size

	# Extract positioning settings for code readability
	logo_paddings = positioning_settings["logo_paddings"]
	circle_radius = positioning_settings["circle_radius"]
	circle_offset_abs = positioning_settings["circle_offset_abs"]

	# Set logo center depending on the chosen position
	logo_center_x = logo_paddings[0] if "left" in position_str else image_w - logo_paddings[0]
	logo_center_y = logo_paddings[1] if "top" in position_str else image_h - logo_paddings[1]

	# Set direction of offsets depending on the chosen position
	circle_offset_x = circle_offset_abs[0] * ((-1) ** ("left" in position_str))
	circle_offset_y = circle_offset_abs[1] * ((-1) ** ("top" in position_str))

	# Get circle center from logo center and offset
	circle_center_x = logo_center_x + circle_offset_x
	circle_center_y = logo_center_y + circle_offset_y

	# Get circle bounding box from the center and radius
	circle_bbox_xs = circle_center_x - circle_radius, circle_center_x + circle_radius
	circle_bbox_ys = circle_center_y - circle_radius, circle_center_y + circle_radius

	# Get watermark bounding box by excluding out-of-bounds parts of the circle
	watermark_bbox_xs = max(0, circle_bbox_xs[0]), min(image_size[0], circle_bbox_xs[1])
	watermark_bbox_ys = max(0, circle_bbox_ys[0]), min(image_size[1], circle_bbox_ys[1])

	# Assemble watermark bounding box
	watermark_bbox = tuple([int(elem) for elem in [
		watermark_bbox_xs[0],
		watermark_bbox_ys[0],
		watermark_bbox_xs[1],
		watermark_bbox_ys[1],
	]])

	# Get logo center relative to the watermark
	logo_center_in_watermark_x = logo_center_x - watermark_bbox_xs[0]
	logo_center_in_watermark_y = logo_center_y - watermark_bbox_ys[0]

	# Get logo top-left corner relative to supersampled watermark
	logo_pos_in_watermark_ss_x = int(settings["ss_factor"] * logo_center_in_watermark_x - logo_ss_w / 2)
	logo_pos_in_watermark_ss_y = int(settings["ss_factor"] * logo_center_in_watermark_y - logo_ss_h / 2)

	# Get circle sub-bounding box
	circle_bbox_in_watermark_xs = [x - watermark_bbox_xs[0] for x in circle_bbox_xs]
	circle_bbox_in_watermark_ys = [y - watermark_bbox_ys[0] for y in circle_bbox_ys]

	# Assemble circle sub-bounding box
	circle_bbox_in_watermark = tuple([int(elem) for elem in [
		circle_bbox_in_watermark_xs[0],
		circle_bbox_in_watermark_ys[0],
		circle_bbox_in_watermark_xs[1],
		circle_bbox_in_watermark_ys[1],
	]])

	return {
		"watermark_bbox": 					watermark_bbox,
		"circle_bbox_in_watermark_bbox": 	circle_bbox_in_watermark,
		"logo_pos_in_watermark_ss_bbox": 	(
			logo_pos_in_watermark_ss_x,
			logo_pos_in_watermark_ss_y,
		),
	}

# Watermark an image with a list of positions and a list of colors
def watermark_image(image, path, logos, position_list, settings):
	# Compute logo dimensions from image dimensions and image-watermark ratio
	target_logo_w, target_logo_h = logo_dims_from_image_and_ratio(	logo_size=logos["color"].size,
												 					image_size=image.size,
																	image_watermark_ratio=settings["image_watermark_ratio"])
	
	# Get scaled and supersampled logos
	logos_ss = scale_logos_with_supersampling(	logos=logos,
										   		target_dims=(target_logo_w, target_logo_h),
												supersampling_factor=settings["ss_factor"])

	# Get logo padding from padding ratio and logo height
	# TODO : Make this configurable (h or w)
	logo_padding = target_logo_h * settings["logo_padding_ratio"]

	# Get circle radius from logo width and logo-circle ratio
	# TODO : Make this configurable (h or w)
	circle_radius = target_logo_w * settings["logo_circle_ratio"] / 2

	# Get logo center
	logo_padding_x = logo_padding + target_logo_w / 2
	logo_padding_y = logo_padding + target_logo_h / 2

	# Get absolute circle offset
	circle_offset_abs_x = target_logo_w * (settings["circle_offset_ratio_x"] - .5)
	circle_offset_abs_y = target_logo_h * (settings["circle_offset_ratio_y"] - .5)

	positioning_settings = {
		"logo_paddings": (logo_padding_x, logo_padding_y),
		"circle_offset_abs": (circle_offset_abs_x, circle_offset_abs_y),
		"circle_radius": circle_radius,
	}

	# Iterate through the given positions
	for position_str in position_list:
		# Get positioning data
		positioning_data = compute_positioning_data(image_size=image.size,
											  		logo_ss_size=get_any_dict_value(logos_ss).size,
													position_str=position_str,
													positioning_settings=positioning_settings,
													settings=settings)

		watermark_image_pos(image=image,
							path=path,
							logos_ss=logos_ss,
							position_str=position_str,
							positioning_data=positioning_data,
							settings=settings)

# TODO : Code in a check that all logos have the same size