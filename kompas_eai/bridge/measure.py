import pythoncom

from .connection import api7

# При LengthUnits == 0 и MassUnits == 0 интерфейс масс отдаёт
# длину в см, площадь в см2, объём в см3, массу в кг (проверено на плите).
_CM_TO_MM = 10.0
_CM2_TO_MM2 = 100.0
_CM3_TO_MM3 = 1000.0


def get_bounding_box(part):
    """Габариты тел детали: ((x1, y1, z1), (x2, y2, z2)) в мм."""
    result = part.GetGabarit(False, False)
    # pywin32 отдаёт выходные параметры кортежем: (успех, x1, y1, z1, x2, y2, z2)
    x1, y1, z1, x2, y2, z2 = (float(v) for v in list(result)[-6:])
    return (
        (min(x1, x2), min(y1, y2), min(z1, z2)),
        (max(x1, x2), max(y1, y2), max(z1, z2)),
    )


def get_size(part):
    """Размеры габаритного параллелепипеда: (dx, dy, dz) в мм."""
    (x1, y1, z1), (x2, y2, z2) = get_bounding_box(part)
    return (x2 - x1, y2 - y1, z2 - z1)


def set_material(part, name, density_g_per_mm3):
    """Задаёт материал и плотность (г/мм3; сталь ~ 0.00785)."""
    ok = part.SetMaterial(name, density_g_per_mm3)
    part.Update()
    if ok is False:
        raise RuntimeError(f"КОМПАС не принял материал {name!r}")


def get_mass_inertia(part):
    """Интерфейс массово-центровочных характеристик (IMassInertiaParam7)."""
    return api7.IMassInertiaParam7(
        part._oleobj_.QueryInterface(
            api7.IMassInertiaParam7.CLSID, pythoncom.IID_IDispatch
        )
    )


def get_mass_properties(part):
    """Объём, площадь, масса и центр масс детали в мм, мм2, мм3 и кг.
    Материал должен быть задан (set_material), иначе масса будет нулевой.
    """
    mi = get_mass_inertia(part)
    mi.Calculate()   # возвращает False, но значения при этом корректны
    if mi.LengthUnits != 0 or mi.MassUnits != 0:
        raise RuntimeError(
            f"неожиданные единицы МЦХ: длина={mi.LengthUnits}, масса={mi.MassUnits}"
        )
    return {
        "volume_mm3": mi.Volume * _CM3_TO_MM3,
        "area_mm2": mi.Area * _CM2_TO_MM2,
        "mass_kg": mi.Mass,
        "density_g_mm3": mi.Density,
        "material": mi.Material,
        "center_of_mass_mm": (
            mi.Xc * _CM_TO_MM, mi.Yc * _CM_TO_MM, mi.Zc * _CM_TO_MM,
        ),
    }