"""
EchoData classes are data models that keep track of various types of data,
such as those stored in the converted raw data files (raw backscatter,
environmental parameters, instrument settings)
or derived data variables (Sv, Sv_clean, MVBS, Sp)

Users use Process objects to perform computation on EchoData objects and
use Plot objects for visualization.
"""

import functools
import os

import xarray as xr

from ..utils import io


class EchoData:
    """Echo data model base class.
    """

    DATA_TYPES = ["raw", "Sv", "Sv_clean", "Sp", "MVBS"]

    class DataSetGet:
        """A descriptor that handles data"""

        def __set_name__(self, owner, name):
            self.name = "_" + name

        def __get__(self, instance, owner):
            return getattr(instance, self.name)

        def __set__(self, instance, value):
            setattr(instance, self.name, value)

    class PathSetGet:
        """A descriptor that handles data paths"""

        def __set_name__(self, owner, name):
            self.name = "_" + name

        def __get__(self, instance, owner):
            return getattr(instance, self.name)

        def __set__(self, instance, value):
            instance._update_data_pointer(value, attr_path=self.name)

    for attr in DATA_TYPES:
        vars()[attr] = DataSetGet()
        vars()[attr + "_path"] = PathSetGet()

    def __init__(
        self, raw_path=None, Sv_path=None, Sv_clean_path=None, Sp_path=None, MVBS_path=None
    ):

        self._file_format = None
        # Data that is handled in Process
        for attr in self.DATA_TYPES:
            # Initialize data pointers and paths to files
            setattr(self, "_" + attr, None)
            setattr(self, "_" + attr + "_path", None)
            files = eval(attr + "_path")
            files = [files] if isinstance(files, str) else files
            # Set the file format
            if self._file_format is None and files is not None:
                self._file_format = io.get_file_format(files[0])
            # Sets pointer to filepath and lazy load data
            setattr(self, attr + "_path", files)

        self._sonar_model = None
        self.range = None

    @property
    def sonar_model(self):
        if self._sonar_model is None:
            with xr.open_dataset(self.raw_path[0], engine=self._file_format) as ds:
                self._sonar_model = ds.keywords
        return self._sonar_model

    def _check_key_param_consistency():
        """Decorator to check if raw files can be opened together by
         seeing if key parameters stay the same across files.
        """

        def wrapper(open_dataset):
            functools.wraps(open_dataset)

            def from_raw(ed):
                if ed.raw_path is None:
                    raise ValueError("No raw files to open")
                else:
                    try:
                        return open_dataset(ed)
                    except xr.MergeError as e:
                        var = str(e).split("'")[1]
                        raise ValueError(
                            f"Files cannot be opened due to {var} changing across the files"
                        )

            return from_raw

        return wrapper

    # TODO: overarching changes needed:
    #  - basic cleaning of data to drop NaN pings before going forward for calibration etc
    #  - cannot use combine='nested' but should force to have monotonically varying ping_time
    #  - see convert/convert_combine.py for handling different sonar models

    @_check_key_param_consistency()
    def get_env_from_raw(self):
        """Open the Environment group from raw data files.
        """
        return xr.open_mfdataset(
            self.raw_path,
            group="Environment",
            combine="nested",
            concat_dim="ping_time",
            data_vars="minimal",
            engine=self._file_format,
        )

    @_check_key_param_consistency()
    def get_vend_from_raw(self):
        """Open the Vendor group from raw data files.
        """
        return xr.open_mfdataset(
            self.raw_path,
            group="Vendor",
            combine="nested",
            compat="no_conflicts",
            data_vars="minimal",
            engine=self._file_format,
        )

    @_check_key_param_consistency()
    def get_beam_from_raw(self):
        """Open the Beam group from raw data files.
        """
        # TODO: self._file_format is empty when this is called (so reading from .zarr fails),
        #  there must be some logic or sequence error when _open and the calling methods are called
        return xr.open_mfdataset(
            self.raw_path,
            group="Beam",
            combine="nested",
            concat_dim="ping_time",
            data_vars="minimal",
            engine=self._file_format,
        )

    def _get_data_from_file(self, files):
        """Open files with data in the top level like Sv, Sp, and MVBS"""
        engine = io.get_file_format(files)
        try:
            return xr.open_mfdataset(
                files, combine="nested", concat_dim="ping_time", data_vars="minimal", engine=engine
            )
        except xr.MergeError as e:
            var = str(e).split("'")[1]
            raise ValueError(f"Files cannot be opened due to {var} changing across the files")

    def _open(self, files, group=None):
        """Opens a list of files. Called by update data pointer"""
        if group == "Beam":
            # Opens the beam group of the raw file
            return self.get_beam_from_raw()
        else:
            # Opens files with data in toplevel like Sv and Sp
            return self._get_data_from_file(files)

    def _update_file_list(self, path, file_list):
        """Update the path specified by user to a list of all files to be opened together.
        """
        # If user passes in a list in self.X_path, use that list directly.
        # If user passes in a path to folder in self.X_path, index all files in the folder.
        if isinstance(path, str):
            ext = os.path.splitext(path)[1]
            # Check for folder to paths
            if ext == "":
                setattr(self, file_list, io.get_files_from_dir(path))
            # Check single file path
            elif ext in [".nc", ".zarr"]:
                setattr(self, file_list, path)
            else:
                raise ValueError("Unsupported file path")
        else:
            # Check for list of paths
            if isinstance(path, list):
                setattr(self, file_list, path)
            else:
                raise ValueError("Unsupported file path")

    def _update_data_pointer(self, path, attr_path):
        """Update pointer to data for the specified type and path.
        """
        attr = "_".join(attr_path.split("_")[:-1])
        if path is None:
            setattr(self, attr, None)
            setattr(self, attr_path, None)
        else:
            self._update_file_list(path, attr_path)
            group = "Beam" if attr == "_raw" else None
            # Lazy load data into instance variable ie. self.Sv, self.raw, etc
            setattr(self, attr, self._open(getattr(self, attr_path), group=group))

    def close(self):
        """Close open datasets
        """
        for data_type in self.DATA_TYPES:
            data = getattr(self, data_type)
            if data is not None:
                data.close()