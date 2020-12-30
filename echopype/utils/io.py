"""
echopype utilities for file handling
"""
import os
import functools
import xarray as xr
from fsspec.mapping import FSMap
from collections import MutableMapping


# TODO: @ngkavin: if you are using this only for the process objects, this should not be here.
#  My suggestion to factor this out was to have it work for both convert and process.
#  Let's discuss what you are doing differently in both cases and see if can combine.

def validate_proc_path(ed, postfix, save_path=None):
    """Creates a directory if it doesn't exist. Returns a valid save path.
    """
    def _assemble_path():
        file_in = os.path.basename(ed.raw_path[0])
        file_name, file_ext = os.path.splitext(file_in)
        return file_name + postfix + file_ext

    if save_path is None:
        save_dir = os.path.dirname(ed.raw_path[0])
        file_out = _assemble_path()
    else:
        path_ext = os.path.splitext(save_path)[1]
        # If given save_path is file, split into directory and file
        if path_ext != '':
            save_dir, file_out = os.path.split(save_path)
            if save_dir == '':  # save_path is only a filename without directory
                save_dir = os.path.dirname(ed.raw_path)  # use directory from input file
        # If given save_path is a directory, get a filename from input .nc file
        else:
            save_dir = save_path
            file_out = _assemble_path()

    # Create folder if not already exists
    if save_dir == '':
        save_dir = os.getcwd()
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    return os.path.join(save_dir, file_out)


def get_files_from_dir(folder):
    valid_ext = ['.nc', '.zarr']
    return [f for f in os.listdir(folder) if os.path.splitext(f)[1] in valid_ext]


def save_file(ds, path, mode, engine, group=None, compression_settings=None):
    encoding = {var: compression_settings for var in ds.data_vars} if compression_settings is not None else {}

    # Allows saving both NetCDF and Zarr files from an xarray dataset
    if engine == 'netcdf4':
        ds.to_netcdf(path=path, mode=mode, group=group, encoding=encoding)
    elif engine == 'zarr':
        ds.to_zarr(store=path, mode=mode, group=group, encoding=encoding)


def get_file_format(file):
    file = file.root if isinstance(file, FSMap) else file
    if file.endswith('.nc'):
        return 'netcdf4'
    elif file.endswith('.zarr'):
        return 'zarr'


def check_file_permissions(FILE_DIR):
    try:
        if isinstance(FILE_DIR, FSMap):
            base_dir = os.path.dirname(FILE_DIR.root)
            TEST_FILE = os.path.join(base_dir, ".permission_test")
            with FILE_DIR.fs.open(TEST_FILE, "w") as f:
                f.write("testing\n")
            FILE_DIR.fs.delete(TEST_FILE)
        else:
            TEST_FILE = os.path.join(FILE_DIR, ".permission_test")
            with open(TEST_FILE, "w") as f:
                f.write("testing\n")
            os.remove(TEST_FILE)
        return True
    except Exception as e:  # pragma: no cover
        print(e)
        return False
