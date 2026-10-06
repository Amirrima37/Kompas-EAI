import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kompas_eai.bridge import (
    connect, create_part, get_part, create_sketch,
    add_circles, add_rectangles, add_polygon, extrude, save_document,
)


def build_plate(app7, out):
    doc = create_part(app7)
    part = get_part(doc)

    base = create_sketch(part, "XOY")
    add_rectangles(base, [(-100, -50, 200, 100)])
    extrude(part, base, 10)

    holes = create_sketch(part, "XOY")
    add_circles(holes, [(x, y, 6) for x in (-80, 80) for y in (-30, 30)])
    extrude(part, holes, 10, cut=True)

    save_document(doc, out)
    assert out.exists(), f"не сохранился {out}"
    print("OK: плита 200x100x10 с 4 отверстиями Ø12 ->", out)


def build_angle(app7, out):
    doc = create_part(app7)
    part = get_part(doc)

    profile = create_sketch(part, "XOZ")
    add_polygon(profile, [(0, 0), (60, 0), (60, 10), (10, 10), (10, 60), (0, 60)])
    extrude(part, profile, 40)

    save_document(doc, out)
    assert out.exists(), f"не сохранился {out}"
    print("OK: уголок L 60x60, полка 10, длина 40 ->", out)


def main():
    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    plate = out_dir / "smoke_plate.m3d"
    angle = out_dir / "smoke_angle.m3d"
    for f in (plate, angle):
        if f.exists():
            f.unlink()

    app7 = connect()
    build_plate(app7, plate)
    build_angle(app7, angle)


if __name__ == "__main__":
    main()