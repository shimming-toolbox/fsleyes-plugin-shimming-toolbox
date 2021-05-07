import subprocess
import logging
import os
from pathlib import Path
import imageio
logger = logging.getLogger(__name__)


# TODO: find a better way to include this as it is defined in utils as well
def run_subprocess(cmd):
    """Wrapper for ``subprocess.run()`` that enables to input ``cmd`` as a full string
        (easier for debugging).

    Args:
        cmd (string): full command to be run on the command line
    """
    logging.debug(f'{cmd}')
    try:
        subprocess.run(
            cmd.split(' '),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as err:
        msg = "Return code: ", err.returncode, "\nOutput: ", err.stderr
        raise Exception(msg)


def get_folder(path):
    """Given a path, get the path to the folder."""
    if is_file(path):
        return os.path.split(path)[0]
    else:
        return path


def is_file(path):
    """Check if a given path is a file."""
    return '.' in Path(path).name


def read_image(filename, bitdepth=8):
    """Read image and convert it to desired bitdepth without truncation."""
    if 'tif' in str(filename):
        raw_img = imageio.imread(filename, format='tiff-pil')
        if len(raw_img.shape) > 2:
            raw_img = imageio.imread(filename, format='tiff-pil', as_gray=True)
    else:
        raw_img = imageio.imread(filename)
        if len(raw_img.shape) > 2:
            raw_img = imageio.imread(filename, as_gray=True)

    img = imageio.core.image_as_uint(raw_img, bitdepth=bitdepth)
    return img


def write_image(filename, img, format='png'):
    """Write image."""
    imageio.imwrite(filename, img, format=format)
