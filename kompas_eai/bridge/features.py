from .connection import api7, const_3d

# Направление выдавливания относительно эскиза.
# Для приклеивания и для выреза оно одинаковое (в сторону нормали эскиза),
# разницу КОМПАСа скрывает extrude().
FORWARD = 0
REVERSE = 1
BOTH = 2

# У выреза КОМПАС трактует FORWARD/REVERSE наоборот (проверено на плите
# на плоскости XOY: cut + FORWARD отверстий не даёт, cut + REVERSE даёт)
_CUT_FLIP = {FORWARD: REVERSE, REVERSE: FORWARD, BOTH: BOTH}


def extrude(part, sketch, depth, cut=False, direction=FORWARD):
    """Выдавливает эскиз на глубину depth (мм).
    cut=True вырезает материал вместо добавления.
    direction: FORWARD, REVERSE или BOTH (depth в каждую сторону).
    Бросает RuntimeError, если КОМПАС не смог построить операцию.
    """
    kind = const_3d.o3d_cutExtrusion if cut else const_3d.o3d_bossExtrusion
    kompas_direction = _CUT_FLIP[direction] if cut else direction

    extrusion = api7.IModelContainer(part).Extrusions.Add(kind)
    extrusion.Sketch = sketch
    extrusion.Direction = kompas_direction

    # Прямая сторона (True) нужна всегда, как в проверенном пути FORWARD.
    extrusion.SetExtrusionType(True, 0)    # 0 = на глубину (etBlind)
    extrusion.SetDepth(True, depth)
    # Для обратного направления и для BOTH задаём и обратную сторону (False).
    if kompas_direction != FORWARD:
        extrusion.SetExtrusionType(False, 0)
        extrusion.SetDepth(False, depth)

    ok = extrusion.Update()
    if ok is False:
        raise RuntimeError(
            f"КОМПАС не построил выдавливание (cut={cut}, direction={direction})"
        )
    return extrusion