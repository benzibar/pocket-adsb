CATEGORY_NAMES = {
    "A0": "No category",
    "A1": "Light",
    "A2": "Small",
    "A3": "Large",
    "A4": "High vortex",
    "A5": "Heavy",
    "A6": "High performance",
    "A7": "Rotorcraft",

    "B0": "No category",
    "B1": "Glider",
    "B2": "Lighter-than-air",
    "B3": "Parachutist",
    "B4": "Ultralight",
    "B5": "Reserved",
    "B6": "UAV",
    "B7": "Space vehicle",

    "C0": "No category",
    "C1": "Emergency vehicle",
    "C2": "Service vehicle",
    "C3": "Point obstacle",
    "C4": "Cluster obstacle",
    "C5": "Line obstacle",
}


def category_description(category: str) -> str:
    if not category:
        return "---"

    code = category.upper()
    description = CATEGORY_NAMES.get(code)

    if description is None:
        return code

    return f"{code} / {description}"