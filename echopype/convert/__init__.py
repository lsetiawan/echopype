"""
Include code to unpack manufacturer-specific data files into an interoperable netCDF format.

The current version supports:

- Simrad EK60 echosounder ``.raw`` data
- Simrad EK80 echosounder ``.raw`` data
- ASL Environmental Sciences AZFP echosounder ``.01A`` data
"""
# TODO: remove ConvertEK80 in later version
from .convert import Convert, ConvertEK80
from .parse_azfp import ParseAZFP
from .parse_base import ParseBase
from .parse_ek60 import ParseEK60
from .parse_ek80 import ParseEK80
from .set_groups_azfp import SetGroupsAZFP
from .set_groups_ek60 import SetGroupsEK60
from .set_groups_ek80 import SetGroupsEK80

__all__ = [
    Convert,
    ConvertEK80,
    ParseAZFP,
    ParseBase,
    ParseEK60,
    ParseEK80,
    SetGroupsAZFP,
    SetGroupsEK60,
    SetGroupsEK80,
]
