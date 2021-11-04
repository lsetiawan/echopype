import xarray as xr

from ..echodata import EchoData
from .calibrate_azfp import CalibrateAZFP
from .calibrate_ek import CalibrateEK60, CalibrateEK80

CALIBRATOR = {"EK60": CalibrateEK60, "EK80": CalibrateEK80, "AZFP": CalibrateAZFP}


def _compute_cal(
    cal_type,
    echodata: EchoData,
    env_params=None,
    cal_params=None,
    waveform_mode=None,
    encode_mode=None,
):
    # Sanity check on inputs
    if (waveform_mode is not None) and (waveform_mode not in ("BB", "CW")):
        raise ValueError("Input waveform_mode not recognized!")
    if (encode_mode is not None) and (encode_mode not in ("complex", "power")):
        raise ValueError("Input encode_mode not recognized!")

    # Set up calibration object
    cal_obj = CALIBRATOR[echodata.sonar_model](
        echodata,
        env_params=env_params,
        cal_params=cal_params,
        waveform_mode=waveform_mode,
        encode_mode=encode_mode,
    )
    # Perform calibration
    if cal_type == "Sv":
        return cal_obj.compute_Sv(waveform_mode=waveform_mode, encode_mode=encode_mode)
    else:
        return cal_obj.compute_Sp(waveform_mode=waveform_mode, encode_mode=encode_mode)


def compute_Sv(echodata: EchoData, **kwargs) -> xr.Dataset:
    """
    Compute volume backscattering strength (Sv) from raw data.

    The calibration routine varies depending on the sonar type.
    Currently this operation is supported for the following ``sonar_model``s:
    EK60, AZFP, EK80 (see below for detail).

    The EK80 echosounder can be configured to transmit
    either broadband (``waveform_mode="BB"``) or narrowband (``waveform_mode="CW"``) signals.
    When transmitting in broadband mode, the returned echoes are
    encoded as complex samples (``encode_mode="complex"``).
    When transmitting in narrowband mode, the returned echoes can be encoded
    either as complex samples or as power/angle combinations in a format similar to
    those recorded by EK60 echosounders (``encode_mode="power"``).

    The current calibration implemented for EK80 broadband complex data
    uses band-integrated Sv with the gain computed at the center frequency
    of the transmit signal.

    Parameters
    ----------
    waveform_mode : {"CW", "BB"}, optional
        Type of transmit waveform.
        - `"CW"` for CW-mode samples, either recorded as complex or power/angle samples
        - `"BB"` for BB-mode samples, recorded as complex samples
        This parameter is only used if `sonar_model` is `"EK60"` or `"EK80"`,
        and in those cases it must be specified.
    encode_mode : {"complex", "power"}, optional
        Type of encoded return echo data.
        - `"complex"` to use complex samples
        - `"power"` to use power/angle samples
        This parameter is only used if `sonar_model` is `"EK80"`.

    Returns
    -------
    xr.Dataset
        The calibrated Sv dataset, including calibration and environmental variables
        used in the calibration operations.
    """
    return _compute_cal(cal_type="Sv", echodata=echodata, **kwargs)


def compute_Sp(echodata: EchoData, **kwargs):
    """
    Compute point backscattering strength (Sp) from raw data.

    The calibration routine varies depending on the sonar type.
    Currently this operation is supported for the following ``sonar_model``s:
    EK60, AZFP, EK80 (see below for detail).

    The EK80 echosounder can be configured to transmit
    either broadband (``waveform_mode="BB"``) or narrowband (``waveform_mode="CW"``) signals.
    When transmitting in broadband mode, the returned echoes are
    encoded as complex samples (``encode_mode="complex"``).
    When transmitting in narrowband mode, the returned echoes can be encoded
    either as complex samples or as power/angle combinations in a format similar to
    those recorded by EK60 echosounders (``encode_mode="power"``).

    The current calibration implemented for EK80 broadband complex data
    uses band-integrated Sv with the gain computed at the center frequency
    of the transmit signal.

    Parameters
    ----------
    waveform_mode : {"CW", "BB"}, optional
        Type of transmit waveform.
        - `"CW"` for CW-mode samples, either recorded as complex or power/angle samples
        - `"BB"` for BB-mode samples, recorded as complex samples
        This parameter is only used if `sonar_model` is `"EK60"` or `"EK80"`,
        and in those cases it must be specified.
    encode_mode : {"complex", "power"}, optional
        Type of encoded return echo data.
        - `"complex"` to use complex samples
        - `"power"` to use power/angle samples
        This parameter is only used if `sonar_model` is `"EK80"`.

    Returns
    -------
    xr.Dataset
        The calibrated Sp dataset, including calibration and environmental variables
        used in the calibration operations.
    """
    return _compute_cal(cal_type="Sp", echodata=echodata, **kwargs)
