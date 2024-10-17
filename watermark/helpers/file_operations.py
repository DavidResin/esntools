# Default libraries
import shutil
from pathlib import Path

# External libraries
import rawpy as rp
from PIL import Image, ImageSequence, UnidentifiedImageError

# Custom libraries
from helpers.image_manipulation import tilt_img


OTHER_EXTS = ('.jpg', '.png', '.jpeg', '.ico', '.webp')
HEI_EXTS = ('.heic', '.heif')
RAWPY_EXTS = ('.nef',)
IMG_EXTS = OTHER_EXTS + HEI_EXTS + RAWPY_EXTS

IGNORE_EXTS = ('.ds_store')

INVALID_COUNT = 0


# Glob all filenames in a given path with a given pattern, but exclude the patterns in the exclusion list
def glob_all_except(path, base_pattern="*", excluded_patterns=[]):
	matches = set(path.glob(base_pattern))

	for pattern in excluded_patterns:
		matches = matches - set(path.glob(pattern))

	return list(matches)


def extension_match(image_path, extension_list):
    return image_path.suffix.lower() in extension_list


# Flush the output directory
def flush_output(path_out: Path, exts: tuple[str]) -> None:
	for deletion_candidate in path_out.iterdir():
		if extension_match(deletion_candidate, exts):
			deletion_candidate.unlink()


# Move an invalid picture out
def invalidate_path(image_path, path_invalid):
	global INVALID_COUNT
	shutil.move(image_path, path_invalid)
	INVALID_COUNT += 1


# Create a directory if it is missing
def create_dir_if_missing(dir_path):
	try:
		dir_path.mkdir()
	except FileExistsError:
		return True

	return False


def open_rawpy_image(image_path):
    image = rp.imread(image_path)
    image = image.postprocess(use_camera_wb=True)
    image = Image.fromarray(image)
    return image


def open_hei_image(image_path):
    image = Image.open(image_path)
    image = next(ImageSequence.Iterator(image))
    return image


def universal_load_image(image_path):
    image = None
    flag = 'img'
    is_hei = False

    if extension_match(image_path, IGNORE_EXTS):
        flag = 'ignore'
    elif extension_match(image_path, RAWPY_EXTS):
        image = open_rawpy_image(image_path)
    elif extension_match(image_path, HEI_EXTS):
        image = open_hei_image(image_path)
        is_hei = True
    elif extension_match(image_path, OTHER_EXTS):
        image = Image.open(image_path)
    else:
        flag = 'invalid'

    return image, flag, is_hei


def attempt_open_image_attempt_tilt(image):
    # TODO : Implement no-tilt option in CLI arguments
    # For non-HEI file types, try to re-orient the picture if it is allowed and orientation data is available 
    try:
        # TODO : Potentiellement getexif existe partout alors que _getexif pas
        image._getexif()
        image = tilt_img(image)
    except AttributeError:
        # TODO : Setting for what to do when image can't be rotated
        pass
     
    return image


def attempt_open_image(image_path, path_invalid, attempt_rotate):
    image, flag, is_hei = universal_load_image(image_path)

    if flag == 'ignore':
        return None
    elif flag == 'invalid':
        invalidate_path(image_path, path_inv)

    if not is_hei and attempt_rotate:
        image = attempt_open_image_attempt_tilt(image)

    return image
