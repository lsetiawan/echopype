"""
Process classes perform computation on EchoData objects.

Some operations are instrument-dependent, such as calibration to obtain Sv.

Some operations are instrument-agnostic, such as obtaining MVBS or detecting bottom.
"""
import warnings
from ..utils import uwa
from . import process_classes
from .echodata import EchoDataBase


class Process:
    """UI class for using process objects.

    Use case (AZFP):
        ed = EchoData(raw_path='some_path_to_converted_raw_data_files')
        proc = Process(model='AZFP')
        proc.env_params = {'salinity': 35, 'pressure': 200}  # set env params needed for calibration
        proc.save_paths['Sv'] = 'some_path_for_Sv'           # set paths to save Sv data to
        proc.get_Sv(ed, save=True, save_format='zarr')

    """
    # A dictionary of supported echosounder types
    PROCESS_SONAR = {
        'AZFP': process_classes.ProcessAZFP(),
        'EK60': process_classes.ProcessEK60(),
        'EK80': process_classes.ProcessEK80(),
        'EA640': process_classes.ProcessEK80(),
    }

    def __init__(self, model=None):
        self.sonar_model = model   # type of echosounder
        self.process_obj = self.PROCESS_SONAR[model]   # process object to use

        # TODO: we need something to restrict the type of parameters users
        #  can put in to these dictionaries,
        #  for example, for env_params we allow only:
        #     'sea_water_salinity'            [psu]
        #     'sea_water_temperature'         [degC]
        #     'sea_water_pressure'            [dbars] (~depth in meters)
        #     'speed_of_sound_in_sea_water'   [m/s]
        #     'seawater_absorption'           [dB/m]
        self._env_params = {}   # env parameters
        self._cal_params = {}   # cal parameters, eg: equivalent beam width sa_correction for EK60
        self._proc_params = {}  # proc parameters, eg: MVBS bin size

    @property
    def proc_params(self):
        # TODO: discussion: use dict of dict
        #   self.proc_params['MVBS'] = {k: v}
        # TODO: ngkavin: implement: get_MVBS() / remove_noise() / get_noise_estimates()
        # get_MVBS() related params:
        #  - MVBS_source: 'Sv' or 'Sv_cleaned'
        #  - MVBS_type: 'binned' or 'rolling'
        #               so far we've only had binned averages (what coarsen is doing)
        #               let's add the functionality to use rolling
        #  - MVBS_ping_num or MVBS_time_interval (one of them has to be given)
        #     - MVBS_ping_num:
        #     - MVBS_time_interval: can use .groupby/resample().mean() or .rolling().mean(),
        #                           based on ping_time
        #       ?? x.resample(time='30s').mean()
        #     - MVBS_distance_interval: can use .groupby().mean(),
        #                               based on distance calculated by lat/lon from Platform group,
        #                               let's put this the last to add
        #  - MVBS_range_bin_num or MVBS_range_interval (use left close right open intervals for now)
        #     - MVBS_range_bin_num:
        #     - MVBS_range_interval: can use .groupby.resample().mean() or .rolling().mean(),
        #                            based on the actual range in meter
        #
        # remove_noise() related params:
        #   - noise_est_ping_num
        #   - noise_est_range_bin_num
        #   - operation: before we calculate the minimum value within each ping number-range bin tile
        #                and use map() to do the noise removal operation.
        #                I think we can use xr.align() with the correct `join` parameter (probably 'left')
        #                to perform the same operation.
        #                Method get_noise_estimates() would naturally be part of the remove_noise() operation.
        #
        # TODO: leewujung: prototype this
        # db_diff() params:
        #   - New method that creates 0-1 (yes-no) masks for crude scatterer classification
        #     based on thresholding the difference of Sv or Sv_clean across pairs of frequencies.
        #   - db_diff_threshold: ('freq1', 'freq2', iterable), the iterable could be
        #
        #   - quick implementation:
        #     ```
        #     # 2-sided threshold: -16 < del_Sv_200_38 <= 2
        #     MVBS_fish_lowrank = xr.where(
        #         -16 < (MVBS_lowrank_200kHz - MVBS_lowrank_38kHz).values,
        #         ds_rpca['low_rank'], np.nan)
        #     MVBS_fish_lowrank = xr.where(
        #         (MVBS_lowrank_200kHz - MVBS_lowrank_38kHz).values <= 2, MVBS_fish_lowrank, np.nan)
        #     ```
        return self._proc_params

    @property
    def env_params(self):
        return self._env_params

    @env_params.setter
    def env_params(self, params):
        if params is None:
            return
        valid_params = ['sea_water_salinity', 'sea_water_temperature',
                        'sea_water_pressure', 'speed_of_sound_in_sea_water', 'seawater_absorption']
        self._env_params.update(params)
        # Removes invalid parameterss
        self._env_params = {k: v for k, v in params.items() if k in valid_params}
        if self._env_params != params:
            invalid = [k for k in params.keys() if k not in valid_params]
            warnings.warn(f'{invalid} will not be used because they are not valid environment parameters.')
        # Recalculate sound speed and absorption coefficient when environment parameters are changed
        self.recalculate_environment()

    def recalculate_environment(self, ed=None):
        if ed is None:
            ed = self.ed
        self.env_params['speed_of_sound_in_sea_water'] = self.process_obj.calc_sound_speed(self.env_params)
        self.env_params['seawater_absorption'] = self.process_obj.calc_seawater_absorption(ed, self.env_params)

    def _check_model_echodata_match(self, ed):
        """Check if sonar model corresponds with the type of data in EchoData object.
        """
        # Check is self.sonar_model and ed.sonar_model are the same
        # Raise error if they do not match

    def _autofill_save_path(self, save_type):
        """
        Autofill the paths to save the processing results if not already set.
        The default paths will be to the same folder as the raw data files.

        Use case is something like:
            proc._autofill_save_path(save_type='Sv')

        Parameters
        ----------
        save_type
        """

    def align_to_range(self, ed, param_source='file'):
        """
        Align raw backscatter data along `range` in meter
        instead of `range_bin` in the original data files.

        Parameters
        ----------
        ed : EchoDataBase
            EchoData object to operate on
        param_source
        """
        # Check if we already have range calculated from .calibrate()
        # and if so we can just get range from there instead of re-calculating.

        # Check if sonar model matches
        self._check_model_echodata_match(ed)

        # Obtain env parameters
        #  Here we want to obtain the env params stored in the data file, but
        #  overwrite those that are specified by user
        #  We can first do a check to see what parameters we still need to get
        #  from the raw files before retrieving them (I/O is slow,
        #  so let's not do that unless needed).

        # To get access to parameters stored in the raw data, use:
        ed.get_env_from_raw()
        ed.get_vend_from_raw()

        #  If not already specifed by user, calculate sound speed and absorption
        self.env_params['speed_of_sound_in_sea_water'] = self.process_obj.calc_sound_speed()
        self.env_params['seawater_absorption'] = self.process_obj.calc_seawater_absorption()

        # Calculate range
        self.process_obj.calc_range(ed)

        # Swap dim to align raw backscatter to range instead of range_bin
        # Users then have the option to use ed.Sv.to_zarr() or other xarray function
        # to explore the data.

    def calibrate(self, ed, param_source='file', save=True, save_format='zarr'):
        """Calibrate raw data.

        Parameters
        ----------
        ed : EchoDataBase
            EchoData object to operate on
        param_source : str
            'file' or 'user'
        save : bool
        save_format : str
        """
        # Check if sonar model matches
        self._check_model_echodata_match(ed)

        # Obtain env parameters
        #  Here we want to obtain the env params stored in the data file, but
        #  overwrite those that are specified by user
        #  We can first do a check to see what parameters we still need to get
        #  from the raw files before retrieving them (I/O is slow,
        #  so let's not do that unless needed).

        # To get access to parameters stored in the raw data, use:
        ed.get_env_from_raw()
        ed.get_vend_from_raw()

        # Obtain cal parameters
        #  Operations are very similar to those from the env parameters,
        #  for AZFP AFAIK some additional parameters are needed from the vendor group
        #  to calculate range

        # Autofill save paths if not already generated
        if save and ('Sv' not in self.save_paths):
            self._autofill_save_path('Sv')

        # Perform calibration
        #  this operation should make an xarray Dataset in ed.Sv
        #  if save=True: save the results as zarr in self.save_paths['Sv'] and update ed.Sv_path
        #  users obviously would have the option to do ed.Sv.to_zarr() to wherever they like
        self.process_obj.get_Sv(
            ed,
            env_params=self.env_params,
            cal_params=self.cal_params,
            save=save,
            save_format=save_format
        )

    def get_Sv(self, ed=None, save=False, save_format='zarr'):
        if ed is None:
            pass
            # ed = self.ed  # TODO: print out the need for ed as an input argument
        # TODO: missing cal_params below
        return self.process_obj.get_Sv(ed=ed, env_params=self.env_params, save=save, save_format=save_format)

    def get_TS(self, ed=None, save=False, save_format='zarr'):
        if ed is None:
            pass
            # ed = self.ed  # TODO: print out the need for ed as an input argument
        # TODO: missing cal_params below
        return self.process_obj.get_TS(ed=ed, env_params=self.env_params, save=save, save_format=save_format)

    def get_MVBS(self, ed=None, save=False, save_format='zarr'):
        if ed is None:
            pass
            # TODO: print out the need for ed as an input argument
        return self.process_obj.get_MVBS(ed=ed, proc_params=self.proc_params, save=save, save_format=save_format)

    def remove_noise(self, ed=None, save=False, save_format='zarr'):
        if ed is None:
            pass
            # TODO: print out the need for ed as an input argument
        return self.process_obj.remove_noise(ed=ed, proc_params=self.proc_params, save=save, save_format=save_format)
