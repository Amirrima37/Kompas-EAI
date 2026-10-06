import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kompas_eai.bridge import (
    connect, create_part, get_part, create_sketch,
    add_circles, add_rectangles, extrude,
    get_size, get_mass_properties, set_material,
)

STEEL = 0.00785   # г/мм3


def close(actual, expected, rel=1e-3, name=""):
    assert abs(actual - expected) <= rel * max(abs(expected), 1.0), (
        f"{name}: получено {actual}, ожидалось {expected}"
    )


def check_plate(app7):
    doc = create_part(app7)
    part = get_part(doc)

    base = create_sketch(part, "XOY")
    add_rectangles(base, [(-100, -50, 200, 100)])
    extrude(part, base, 10)
    holes = create_sketch(part, "XOY")
    add_circles(holes, [(x, y, 6) for x in (-80, 80) for y in (-30, 30)])
    extrude(part, holes, 10, cut=True)
    set_material(part, "Сталь", STEEL)

    dx, dy, dz = get_size(part)
    close(dx, 200, name="plate dx")
    close(dy, 100, name="plate dy")
    close(dz, 10, name="plate dz")

    volume = 200 * 100 * 10 - 4 * math.pi * 6 ** 2 * 10
    props = get_mass_properties(part)
    close(props["volume_mm3"], volume, name="plate volume")
    close(props["mass_kg"], volume * STEEL / 1000, name="plate mass")
    close(props["center_of_mass_mm"][2], 5, name="plate zc")
    print("OK: плита ->", props)


def check_pipe(app7):
    doc = create_part(app7)
    part = get_part(doc)

    sketch = create_sketch(part, "XOY")
    add_circles(sketch, [(0, 0, 50), (0, 0, 40)])
    extrude(part, sketch, 200)
    set_material(part, "Сталь", STEEL)

    volume = math.pi * (50 ** 2 - 40 ** 2) * 200
    props = get_mass_properties(part)
    close(props["volume_mm3"], volume, name="pipe volume")
    close(props["mass_kg"], volume * STEEL / 1000, name="pipe mass")
    close(props["center_of_mass_mm"][2], 100, name="pipe zc")
    print("OK: труба ->", props)


def main():
    app7 = connect()
    check_plate(app7)
    check_pipe(app7)


if __name__ == "__main__":
    main()