import subprocess
import logging
import os
from pathlib import Path
import imageio
import numpy as np
import nibabel as nib

import fsleyes.actions.loadoverlay as loadoverlay

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


def load_png_image_from_path(fsl_panel, image_path, is_mask=False, add_to_overlayList=True,
                             colormap="greyscale"):
    """Convert a 2D image into a NIfTI image and load it as an overlay.

    The parameter ``add_to_overlayList`` enables displaying the overlay in FSLeyes.

    Args:
        image_path (str): The location of the image, including the name and the .extension
        is_mask (bool): (optional) Whether or not this is a segmentation mask. It will be
            treated as a normalads_utils
        add_to_overlayList (bool): (optional) Whether or not to add the image to the overlay
            list. If so, the image will be displayed in the application. This parameter is
            True by default.
        colormap (str): (optional) the colormap of image that will be displayed. This parameter
            is set to greyscale by default.

    Returns:
        overlay: the FSLeyes overlay corresponding to the loaded image.
    """

    # Open the 2D image
    img_png2d = read_image(image_path)

    if is_mask is True:
        img_png2d = img_png2d // np.iinfo(np.uint8).max  # Segmentation masks should be binary

    # Flip the image on the Y axis so that the morphometrics file shows the right coordinates
    img_png2d = np.flipud(img_png2d)

    # Convert image data into a NIfTI image
    # Note: PIL and NiBabel use different axis conventions, so some array manipulation has to be done.
    # TODO: save in the FOV of the current overlay
    nii_img = nib.Nifti1Image(
        np.rot90(img_png2d, k=1, axes=(1, 0)), np.eye(4)
    )

    # Save the NIfTI image in a temporary directory
    fname_out = image_path[:-3] + "nii.gz"
    nib.save(nii_img, fname_out)

    # Load the NIfTI image as an overlay
    img_overlay = loadoverlay.loadOverlays(paths=[fname_out], inmem=True, blocking=True)[0]

    # Display the overlay
    if add_to_overlayList is True:
        fsl_panel.overlayList.append(img_overlay)
        opts = fsl_panel.displayCtx.getOpts(img_overlay)
        opts.cmap = colormap

    return img_overlay
