# External libraries
from PIL import ImageDraw

# Custom libraries
from helpers.others import color_mapping_from_setting # Needs to disappear


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


def get_any_dict_value(dictionary):
	return next(iter(dictionary.values()))


def get_dict_value_or_none_value(dictionary: dict, key):
	return dictionary.get(key, dictionary[None])


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


def nearest_integer_scale(values, scale_factor):
	return [int(scale_factor * value) for value in values]


def scale_logos_with_supersampling(logos, target_dims, ss_factor=1):
	ss_dims = nearest_integer_scale(target_dims, scale_factor=ss_factor)
	return {key: logo.resize(ss_dims) for key, logo in logos.items()}


def crop_image_with_supersampling(image, bbox, ss_factor=1):
	crop = image.crop(box=bbox)
	ss_dims = nearest_integer_scale(crop.size, scale_factor=ss_factor)
	return crop.resize(ss_dims)


def draw_ellipse_with_supersampling(image, bbox, color, ss_factor=1):
	ss_bbox = nearest_integer_scale(bbox, scale_factor=ss_factor)
	ImageDraw.Draw(image).ellipse(ss_bbox, fill=color)
	return image


def dims_from_bbox(bbox):
	x0, y0, x1, y1 = bbox
	return x1 - x0, y1 - y0


def resize_to_bbox_size(image, bbox):
	dims = dims_from_bbox(bbox)
	return image.resize(dims)


def paste_image_on_image_at_bbox(image, pasted_image, bbox, copy_image=False):
	new_image = image.copy() if copy_image else image
	mask = pasted_image if pasted_image.mode == "RGBA" else None
	new_image.paste(pasted_image, bbox[:2], mask)
	return new_image


# Watermark an image with a given position and color
def generate_watermarked_image(image, logo_ss, circle_color, ss_factor, positioning_data):
	watermark_canvas_ss = crop_image_with_supersampling(image,
											   			bbox=positioning_data["watermark_bbox"],
														ss_factor=ss_factor)
	
	if circle_color is not None:
		watermark_canvas_ss = draw_ellipse_with_supersampling(	watermark_canvas_ss,
																bbox=positioning_data["circle_bbox_in_watermark_bbox"],
																color=circle_color,
																ss_factor=ss_factor)
	
	watermark_canvas_ss = paste_image_on_image_at_bbox(	watermark_canvas_ss,
														pasted_image=logo_ss,
														bbox=positioning_data["logo_pos_in_watermark_ss_bbox"])

	watermark_canvas = resize_to_bbox_size(	watermark_canvas_ss,
								   			bbox=positioning_data["watermark_bbox"])
	
	watermarked_image = paste_image_on_image_at_bbox(	image,
											   		pasted_image=watermark_canvas,
											   		bbox=positioning_data["watermark_bbox"],
													copy_image=True)
	
	return watermarked_image


# Watermark an image with a given position and a list of colors
def watermark_image_pos(image, path, logos_ss, settings, positioning_data):
	color_mapping = color_mapping_from_setting(settings["color_setting"])
	
	# Loop through the selected colors
	for i, (color_name, color) in enumerate(color_mapping.items()):

		logo_ss = logos_ss[get_dict_value_or_none_value(ESN_CIRCLE_COLOR_MAP, color_name)]
		circle_color = color if settings["draw_circle"] else None

		# image
		# logo color key
		# circle color
		# ss_factor
		# positioning data
		watermarked_image = generate_watermarked_image(	image,
														logo_ss=logo_ss,
														circle_color=circle_color,
														ss_factor=settings["ss_factor"],
														positioning_data=positioning_data)
		
		if len(color_mapping) == 1:
			suffix = ""
		else:
			suffix = "_" + str(i)

	path_out = settings["output_path"] / (settings["prefix"] + path.stem + suffix + "." + settings["format"])
	watermarked_image.save(path_out, format="png", compress_level=4)


def compute_positioning_data(image_size, logo_ss_size, position_str, positioning_settings, ss_factor):
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
	logo_pos_in_watermark_ss_x = int(ss_factor * logo_center_in_watermark_x - logo_ss_w / 2)
	logo_pos_in_watermark_ss_y = int(ss_factor * logo_center_in_watermark_y - logo_ss_h / 2)

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
												ss_factor=settings["ss_factor"])

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
													ss_factor=settings["ss_factor"])

		watermark_image_pos(image,
							path=path,
							logos_ss=logos_ss,
							positioning_data=positioning_data,
							settings=settings)
