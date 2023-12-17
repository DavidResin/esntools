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

def extension_match(path, exts):
    return any([path.suffix.lower() == "." + ext for ext in exts])

# Flush the output directory
def flush_output(path_out: Path, exts: tuple[str]) -> None:
	for deletion_candidate in path_out.iterdir():
		if extension_match(deletion_candidate, exts):
			deletion_candidate.unlink()

# Move an invalid picture out
def invalidate_path(path_in, path_inv):
	global INVALID_COUNT
	shutil.move(path_in, path_inv)
	INVALID_COUNT += 1
	
# Create a directory if it is missing
def create_dir_if_missing(path):
	try:
		path.mkdir()
	except FileExistsError:
		return True

	return False

def universal_load_image(path_in):
    if extension_match(path_in, RAWPY_EXTS):
        image = rp.imread(path_in)
        image = image.postprocess(use_camera_wb=True)
        image = Image.fromarray(image)
    else:
        image = Image.open(path_in)

    return image

def attempt_open_image_ext_check(path, path_inv):
    # Move picture to 'invalid' if it doesn't have the right file format
    path_is_valid = extension_match(path, EXTS)
    
    if not path_is_valid:
        invalidate_path(path, path_inv)

    return path_is_valid
    
def attempt_open_image_load_image(path, path_inv):
    image = None

    # Try to load image
    try:
        image = universal_load_image(path)
    except (FileNotFoundError, UnidentifiedImageError, ValueError) as e:
        # TODO : Print out a report on the failure, manage failure behaviour in arguments
        invalidate_path(path, path_inv)

    return image

def attempt_open_image_hei_process(image, path):
    is_hei = extension_match(path, HEI_EXTS)

    if is_hei:
        image = next(ImageSequence.Iterator(image))

    return image, is_hei

def attempt_open_image_attempt_tilt(image):
    # TODO : Implement no-tilt option in CLI argumetents
    # For non-HEI file types, try to re-orient the picture if it is allowed and orientation data is available 
    try:
        # TODO : Potentiellement getexif existe partout alors que _getexif pas
        image._getexif()
        image = tilt_img(image)
    except AttributeError:
        # TODO : Setting for what to do when image can't be rotated
        pass
     
    return image
    
def attempt_open_image(path, path_inv, attempt_rotate):
    path_is_valid = attempt_open_image_ext_check(path, path_inv)

    if not path_is_valid:
        return None
    
    img = attempt_open_image_load_image(path, path_inv)

    if img is None:
        return None

    img, is_hei = attempt_open_image_hei_process(img, path)

    if not is_hei and attempt_rotate:
        img = attempt_open_image_attempt_tilt(img)

    return img