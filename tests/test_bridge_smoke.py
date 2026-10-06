import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kompas_eai.bridge import (
    connect, create_part, get_part, create_sketch,
    add_circles, add_rectangles, add_polygon, extrude,
    get_bounding_box, get_size, get_mass_properties, set_material,
    save_document, FORWARD, REVERSE, BOTH,
)

STEEL = 0.00785   # г/мм3
OUT = ROOT / "out"


def close(actual, expected, rel=1e-3, name=""):
    assert abs(actual - expected) <= rel * max(abs(expected), 1.0), (
        f"{name}: получено {actual}, ожидалось {expected}"
    )


def new_part(app7):
    doc = create_part(app7)
    return doc, get_part(doc)


def plate_boss(part, direction=FORWARD):
    sketch = create_sketch(part, "XOY")
    add_rectangles(sketch, [(-100, -50, 200, 100)])
    extrude(part, sketch, 10, direction=direction)


def check_plate_with_holes(app7):
    doc, part = new_part(app7)
    plate_boss(part)
    holes = create_sketch(part, "XOY")
    add_circles(holes, [(x, y, 6) for x in (-80, 80) for y in (-30, 30)])
    extrude(part, holes, 10, cut=True)
    set_material(part, "Сталь", STEEL)

    volume = 200 * 100 * 10 - 4 * math.pi * 6 ** 2 * 10
    props = get_mass_properties(part)
    close(props["volume_mm3"], volume, name="плита: объём")
    close(props["mass_kg"], volume * STEEL / 1000, name="плита: масса")

    path = OUT / "smoke_plate.m3d"
    path.unlink(missing_ok=True)
    save_document(doc, path)
    assert path.exists(), "плита не сохранилась"
    print("OK: плита с отверстиями, объём и масса сходятся, файл сохранён")


def check_pipe(app7):
    doc, part = new_part(app7)
    sketch = create_sketch(part, "XOY")
    add_circles(sketch, [(0, 0, 50), (0, 0, 40)])
    extrude(part, sketch, 200)
    set_material(part, "Сталь", STEEL)

    volume = math.pi * (50 ** 2 - 40 ** 2) * 200
    props = get_mass_properties(part)
    close(props["volume_mm3"], volume, name="труба: объём")
    close(props["center_of_mass_mm"][2], 100, name="труба: центр масс по Z")
    print("OK: труба Ø100/Ø80 x 200")


def check_directions(app7):
    # приклеивание: границы по Z
    for direction, z_range in ((FORWARD, (0, 10)), (REVERSE, (-10, 0))):
        _, part = new_part(app7)
        plate_boss(part, direction)
        (_, _, z1), (_, _, z2) = get_bounding_box(part)
        close(z1, z_range[0], name=f"boss {direction}: z min")
        close(z2, z_range[1], name=f"boss {direction}: z max")

    _, part = new_part(app7)
    sketch = create_sketch(part, "XOY")
    add_rectangles(sketch, [(-100, -50, 200, 100)])
    extrude(part, sketch, 10, direction=BOTH)
    (_, _, z1), (_, _, z2) = get_bounding_box(part)
    close(z1, -10, name="boss BOTH: z min")
    close(z2, 10, name="boss BOTH: z max")

    # вырез: FORWARD режет плиту (z 0..10), REVERSE уходит мимо и ничего не режет
    for direction, expect_holes in ((FORWARD, True), (REVERSE, False)):
        _, part = new_part(app7)
        plate_boss(part)
        holes = create_sketch(part, "XOY")
        add_circles(holes, [(0, 0, 20)])
        extrude(part, holes, 10, cut=True, direction=direction)
        set_material(part, "Сталь", STEEL)
        volume = get_mass_properties(part)["volume_mm3"]
        full = 200 * 100 * 10
        cut_volume = full - math.pi * 20 ** 2 * 10
        close(volume, cut_volume if expect_holes else full, name=f"cut {direction}")
    print("OK: направления FORWARD/REVERSE/BOTH для приклеивания и выреза")


def check_angle_on_xoz(app7):
    doc, part = new_part(app7)
    profile = create_sketch(part, "XOZ")
    add_polygon(profile, [(0, 0), (60, 0), (60, 10), (10, 10), (10, 60), (0, 60)])
    extrude(part, profile, 40)
    set_material(part, "Сталь", STEEL)

    props = get_mass_properties(part)
    close(props["volume_mm3"], 1100 * 40, name="уголок: объём")
    dx, dy, dz = get_size(part)
    close(dx, 60, name="уголок: X")
    close(dy, 40, name="уголок: Y (глубина выдавливания)")
    close(dz, 60, name="уголок: Z")
    (_, y1, _), (_, y2, _) = get_bounding_box(part)
    print(f"OK: уголок на XOZ; выдавливание FORWARD идёт по Y от {y1:g} до {y2:g}")


def main():
    OUT.mkdir(exist_ok=True)
    app7 = connect()
    check_plate_with_holes(app7)
    check_pipe(app7)
    check_directions(app7)
    check_angle_on_xoz(app7)
    print("\nВСЕ ПРОВЕРКИ МОСТА ПРОЙДЕНЫ")


if __name__ == "__main__":
    main()