import os
import shutil
import numpy as np
import xarray as xr
import pandas as pd
import pytest
from ..convert import Convert


def _check_file_group(data_file, engine, groups):
    for g in groups:
        ds = xr.open_dataset(data_file, engine=engine, group=g)

        assert isinstance(ds, xr.Dataset) is True


def _converted_group_checker(model, engine, out_file, multiple_files):
    groups = ['Environment', 'Platform', 'Provenance', 'Sonar']
    if model in ['EK60', 'EK80']:
        groups = groups + ['Beam', 'Vendor']

    if multiple_files:
        dirname = os.path.abspath(out_file)
        out_files = [os.path.join(dirname, f) for f in os.listdir(dirname)]
        for data_file in out_files:
            _check_file_group(data_file, engine, groups)
    else:
        _check_file_group(out_file, engine, groups)


def _file_export_checks(ec, model, export_engine, multiple_files):
    if export_engine == "netcdf4":
        out_file = f"./test_{model.lower()}.nc"
        if multiple_files:
            out_file = out_file.replace(".nc", "")
        ec.to_netcdf(save_path=out_file, overwrite=True)
    elif export_engine == "zarr":
        out_file = f"./test_{model.lower()}.zarr"
        if multiple_files:
            out_file = out_file.replace(".zarr", "")
        ec.to_zarr(save_path=out_file, overwrite=True)

    _converted_group_checker(
        model=model, engine=export_engine,
        out_file=out_file, multiple_files=multiple_files
    )

    # Cleanup
    if os.path.isfile(out_file):
        os.unlink(out_file)
    else:
        shutil.rmtree(out_file)


@pytest.mark.parametrize("model", ["AZFP"])
@pytest.mark.parametrize(
    "file",
    [
        "https://rawdata.oceanobservatories.org/files/CE01ISSM/R00007/instrmts/dcl37/ZPLSC_sn55075/ce01issm_zplsc_55075_recovered_2017-10-27/DATA/201703/17032923.01A"
    ],
)
@pytest.mark.parametrize(
    "xml_path",
    [
        "https://rawdata.oceanobservatories.org/files/CE01ISSM/R00007/instrmts/dcl37/ZPLSC_sn55075/ce01issm_zplsc_55075_recovered_2017-10-27/DATA/201703/17032922.XML"
    ],
)
@pytest.mark.parametrize("storage_options", [{'anon': True}])
@pytest.mark.parametrize("export_engine", ["netcdf4", "zarr"])
def test_convert_azfp(model, file, xml_path, storage_options, export_engine):
    if isinstance(file, str):
        multiple_files = False
        if not file.startswith("s3://"):
            storage_options = {}
    else:
        multiple_files = True
        if not file[0].startswith("s3://"):
            storage_options = {}

    ec = Convert(
        file=file,
        model=model,
        xml_path=xml_path,
        storage_options=storage_options,
    )

    if multiple_files:
        assert sorted(ec.source_file) == sorted(file)
    else:
        assert ec.source_file[0] == file
    assert ec.xml_path == xml_path

    _file_export_checks(ec, model, export_engine, multiple_files)


@pytest.mark.parametrize("model", ["EK60"])
@pytest.mark.parametrize(
    "file",
    [
        "https://ncei-wcsd-archive.s3-us-west-2.amazonaws.com/data/raw/Bell_M._Shimada/SH1707/EK60/Summer2017-D20170615-T190214.raw",
        "s3://ncei-wcsd-archive/data/raw/Bell_M._Shimada/SH1707/EK60/Summer2017-D20170615-T190214.raw",
        [
            'https://ncei-wcsd-archive.s3-us-west-2.amazonaws.com/data/raw/Bell_M._Shimada/SH1707/EK60/Summer2017-D20170615-T190214.raw',
            'https://ncei-wcsd-archive.s3-us-west-2.amazonaws.com/data/raw/Bell_M._Shimada/SH1707/EK60/Summer2017-D20170615-T190843.raw',
            'https://ncei-wcsd-archive.s3-us-west-2.amazonaws.com/data/raw/Bell_M._Shimada/SH1707/EK60/Summer2017-D20170615-T212409.raw'
        ]
    ],
)
@pytest.mark.parametrize("storage_options", [{'anon': True}])
@pytest.mark.parametrize("export_engine", ["netcdf4", "zarr"])
def test_convert_ek60(model, file, storage_options, export_engine):
    if isinstance(file, str):
        multiple_files = False
        if not file.startswith("s3://"):
            storage_options = {}
    else:
        multiple_files = True
        if not file[0].startswith("s3://"):
            storage_options = {}

    ec = Convert(file=file, model=model, storage_options=storage_options)

    if multiple_files:
        assert sorted(ec.source_file) == sorted(file)
    else:
        assert ec.source_file[0] == file

    _file_export_checks(ec, model, export_engine, multiple_files)


@pytest.mark.parametrize("model", ["EK80"])
@pytest.mark.parametrize(
    "file",
    [
        "https://ncei-wcsd-archive.s3-us-west-2.amazonaws.com/data/raw/Bell_M._Shimada/SH1707/EK80/D20170826-T205615.raw",
        "s3://ncei-wcsd-archive/data/raw/Bell_M._Shimada/SH1707/EK80/D20170826-T205615.raw",
    ],
)
@pytest.mark.parametrize("storage_options", [{'anon': True}])
@pytest.mark.parametrize("export_engine", ["netcdf4", "zarr"])
def test_convert_ek80(model, file, storage_options, export_engine):
    if isinstance(file, str):
        multiple_files = False
        if not file.startswith("s3://"):
            storage_options = {}
    else:
        multiple_files = True
        if not file[0].startswith("s3://"):
            storage_options = {}

    ec = Convert(file=file, model=model, storage_options=storage_options)

    if multiple_files:
        assert sorted(ec.source_file) == sorted(file)
    else:
        assert ec.source_file[0] == file

    _file_export_checks(ec, model, export_engine, multiple_files)
