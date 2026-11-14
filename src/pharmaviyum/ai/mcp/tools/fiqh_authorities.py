"""Country-level default fiqh authority metadata used by the Halal compliance tool."""

from typing import TypedDict


class FiqhAuthority(TypedDict):
    school: str
    marja: str


COUNTRY_FIQH: dict[str, FiqhAuthority] = {
    "SA": {"school": "Hanbali", "marja": "state_mufti"},
    "AE": {"school": "Maliki", "marja": "state_mufti"},
    "QA": {"school": "Hanbali", "marja": "state_mufti"},
    "KW": {"school": "Maliki", "marja": "state_mufti"},
    "BH": {"school": "Maliki", "marja": "state_mufti"},
    "OM": {"school": "Ibadi", "marja": "state_mufti"},
    "VN": {"school": "Hanafi", "marja": "local_authority"},
    "TH": {"school": "Shafii", "marja": "local_authority"},
    "ID": {"school": "Shafii", "marja": "local_authority"},
    "MY": {"school": "Shafii", "marja": "state_authority"},
    "SG": {"school": "Shafii", "marja": "state_authority"},
}
