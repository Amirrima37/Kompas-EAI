from contextlib import contextmanager

from .connection import api7, const_3d

_PLANES = {
    "XOY": const_3d.o3d_planeXOY,
    "XOZ": const_3d.o3d_planeXOZ,
    "YOZ": const_3d.o3d_planeYOZ,
}

_STYLE_MAIN = 1   # основная линия


def create_sketch(part, plane="XOY"):
    """Создаёт пустой эскиз на базовой плоскости (XOY, XOZ или YOZ)."""
    plane_obj = part.DefaultObject(_PLANES[plane])
    sketch = api7.IModelContainer(part).Sketchs.Add()
    sketch.Plane = plane_obj
    sketch.Update()
    return sketch


@contextmanager
def edit_sketch(sketch):
    """Открывает эскиз на редактирование и отдаёт контейнер графических объектов.
    Выход из режима редактирования гарантирован, даже если внутри была ошибка.
    """
    fragment = sketch.BeginEdit()
    try:
        view = fragment.ViewsAndLayersManager.Views.ActiveView
        yield api7.IDrawingContainer(view)
    finally:
        sketch.EndEdit()


def add_circles(sketch, circles):
    """circles: список (xc, yc, radius), мм."""
    with edit_sketch(sketch) as drawing:
        for xc, yc, radius in circles:
            c = drawing.Circles.Add()
            c.Xc = xc
            c.Yc = yc
            c.Radius = radius
            c.Style = _STYLE_MAIN
            c.Update()


def add_rectangles(sketch, rects):
    """rects: список (x, y, width, height), мм.
    (x, y) - левый нижний угол, ширина вдоль X, высота вдоль Y.
    """
    with edit_sketch(sketch) as drawing:
        for x, y, width, height in rects:
            r = drawing.Rectangles.Add()
            r.X = x
            r.Y = y
            r.Width = width
            r.Height = height
            r.Angle = 0
            r.Style = _STYLE_MAIN
            r.Update()


def add_lines(sketch, lines):
    """lines: список отрезков (x1, y1, x2, y2), мм."""
    with edit_sketch(sketch) as drawing:
        for x1, y1, x2, y2 in lines:
            _add_segment(drawing, x1, y1, x2, y2)


def add_polygon(sketch, points):
    """Замкнутый контур из отрезков по списку вершин [(x, y), ...], мм.
    Последняя вершина автоматически соединяется с первой.
    """
    if len(points) < 3:
        raise ValueError("для контура нужно минимум 3 вершины")
    with edit_sketch(sketch) as drawing:
        n = len(points)
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            _add_segment(drawing, x1, y1, x2, y2)


def _add_segment(drawing, x1, y1, x2, y2):
    s = drawing.LineSegments.Add()
    s.X1 = x1
    s.Y1 = y1
    s.X2 = x2
    s.Y2 = y2
    s.Style = _STYLE_MAIN
    s.Update()