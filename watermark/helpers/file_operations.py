# Default libraries
import shutil
from pathlib import Path

# External libraries
import rawpy as rp
from PIL import Image, ImageSequence, UnidentifiedImageError

# Custom libraries
from helpers.image_manipulation import tilt_img

EXTS = ('.jpg', '.png', '.jpeg', '.ico', '.webp', '.heic', '.heif', '.nef')
HEI_EXTS = ('.heic', '.heif')
RAWPY_EXTS = ('.nef')

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

def universal_load_image(image_path):
    if extension_match(image_path, RAWPY_EXTS):
        image = rp.imread(image_path)
        image = image.postprocess(use_camera_wb=True)
        image = Image.fromarray(image)
    else:
        image = Image.open(image_path)

    return image

def attempt_open_image_ext_check(image_path, path_invalid):
    # Move picture to 'invalid' if it doesn't have the right file format
    path_is_valid = extension_match(image_path, EXTS)
    
    if not path_is_valid:
        invalidate_path(image_path, path_invalid)

    return path_is_valid
    
def attempt_open_image_load_image(image_path, path_inv):
    image = None

    # Try to load image
    try:
        image = universal_load_image(image_path)
    except (FileNotFoundError, UnidentifiedImageError, ValueError) as e:
        # TODO : Print out a report on the failure, manage failure behaviour in arguments
        invalidate_path(image_path, path_inv)

    return image

def attempt_open_image_hei_process(image, image_path):
    is_hei = extension_match(image_path, HEI_EXTS)

    if is_hei:
        image = next(ImageSequence.Iterator(image))

    return image, is_hei

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
    path_is_valid = attempt_open_image_ext_check(image_path, path_invalid)

    if not path_is_valid:
        return None
    
    image = attempt_open_image_load_image(image_path, path_invalid)

    if image is None:
        return None

    image, is_hei = attempt_open_image_hei_process(image, image_path)

    if not is_hei and attempt_rotate:
        image = attempt_open_image_attempt_tilt(image)

    return image