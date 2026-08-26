from dataclasses import dataclass


@dataclass(frozen=True)
class IcaoAllocation:
    start: int
    end: int
    country: str


# ICAO 24-bit address allocation blocks.
# We can expand this table as required.
ALLOCATIONS = [
    IcaoAllocation(0x400000, 0x43FFFF, "United Kingdom"),
    IcaoAllocation(0x440000, 0x447FFF, "Austria"),
    IcaoAllocation(0x448000, 0x44FFFF, "Belgium"),
    IcaoAllocation(0x450000, 0x457FFF, "Bulgaria"),
    IcaoAllocation(0x458000, 0x45FFFF, "Denmark"),
    IcaoAllocation(0x460000, 0x467FFF, "Finland"),
    IcaoAllocation(0x468000, 0x46FFFF, "Greece"),
    IcaoAllocation(0x470000, 0x477FFF, "Hungary"),
    IcaoAllocation(0x478000, 0x47FFFF, "Norway"),
    IcaoAllocation(0x480000, 0x487FFF, "Netherlands"),
    IcaoAllocation(0x488000, 0x48FFFF, "Poland"),
    IcaoAllocation(0x490000, 0x497FFF, "Portugal"),
    IcaoAllocation(0x498000, 0x49FFFF, "Czech Republic"),
    IcaoAllocation(0x4A0000, 0x4A7FFF, "Romania"),
    IcaoAllocation(0x4A8000, 0x4AFFFF, "Sweden"),
    IcaoAllocation(0x4B0000, 0x4B7FFF, "Switzerland"),
    IcaoAllocation(0x4B8000, 0x4BFFFF, "Turkey"),
    IcaoAllocation(0x4CA000, 0x4CAFFF, "Ireland"),
    IcaoAllocation(0x4D0000, 0x4D7FFF, "Luxembourg"),
    IcaoAllocation(0x4D8000, 0x4DFFFF, "Malta"),
    IcaoAllocation(0x500000, 0x5003FF, "San Marino"),
    IcaoAllocation(0x501000, 0x5013FF, "Albania"),
    IcaoAllocation(0x502C00, 0x502FFF, "Latvia"),
    IcaoAllocation(0x503C00, 0x503FFF, "Lithuania"),
    IcaoAllocation(0x504C00, 0x504FFF, "Moldova"),
    IcaoAllocation(0x505C00, 0x505FFF, "Slovakia"),
    IcaoAllocation(0x506C00, 0x506FFF, "Slovenia"),
    IcaoAllocation(0x507C00, 0x507FFF, "Uzbekistan"),
    IcaoAllocation(0x508000, 0x50FFFF, "Ukraine"),
    IcaoAllocation(0x3C0000, 0x3FFFFF, "Germany"),
    IcaoAllocation(0x380000, 0x3BFFFF, "France"),
    IcaoAllocation(0x300000, 0x33FFFF, "Italy"),
    IcaoAllocation(0x340000, 0x37FFFF, "Spain"),
    IcaoAllocation(0xA00000, 0xAFFFFF, "United States"),
    IcaoAllocation(0xC00000, 0xC3FFFF, "Canada"),
]


def country_from_icao(icao: str) -> str:
    try:
        address = int(icao, 16)
    except ValueError:
        return ""

    for allocation in ALLOCATIONS:
        if allocation.start <= address <= allocation.end:
            return allocation.country

    return ""