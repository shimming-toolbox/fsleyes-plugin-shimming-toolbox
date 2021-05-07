import subprocess
import logging
import os
from pathlib import Path
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
