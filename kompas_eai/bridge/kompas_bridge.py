import pythoncom
from win32com.client import Dispatch, gencache

const = gencache.EnsureModule("{75C9F5D0-B5B8-4526-8681-9903C567D2ED}", 0, 1, 0).constants
const_3d = gencache.EnsureModule("{2CAF168C-7961-4B90-9DA2-701419BEEFE3}", 0, 1, 0).constants
api7 = gencache.EnsureModule("{69AC2981-37C0-4379-84FD-5DD2F3C0A520}", 0, 1, 0)


def connect():
    """Подключается к КОМПАС-3D и возвращает IApplication."""
    app7 = api7.IApplication(
        Dispatch("Kompas.Application.7")._oleobj_.QueryInterface(
            api7.IApplication.CLSID, pythoncom.IID_IDispatch
        )
    )
    app7.Visible = True
    return app7

def create_part(app7):
    """Создаёт пустую деталь и возвращает документ."""
    return app7.Documents.Add(const.ksDocumentPart, True)
def save_document(doc, path):
    """Сохраняет документ по указанному пути."""
    doc.SaveAs(path)

_PLANES = {
    "XOY": const_3d.o3d_planeXOY,
    "XOZ": const_3d.o3d_planeXOZ,
    "YOZ": const_3d.o3d_planeYOZ,
}


def get_part(doc):
    """Возвращает верхнюю деталь (IPart7) из документа-детали."""
    return api7.IKompasDocument3D(doc).TopPart


def create_sketch(part, plane="XOY"):
    """Создаёт пустой эскиз на базовой плоскости (XOY, XOZ или YOZ)."""
    plane_obj = part.DefaultObject(_PLANES[plane])
    sketch = api7.IModelContainer(part).Sketchs.Add()
    sketch.Plane = plane_obj
    sketch.Update()
    return sketch


def add_circles(sketch, circles):
    """Рисует окружности в эскизе.
    circles: список кортежей (xc, yc, radius) в мм.
    Две концентрические окружности дадут трубу при выдавливании.
    """
    fragment = sketch.BeginEdit()
    try:
        view = fragment.ViewsAndLayersManager.Views.ActiveView
        drawing = api7.IDrawingContainer(view)
        for xc, yc, radius in circles:
            circle = drawing.Circles.Add()
            circle.Xc = xc
            circle.Yc = yc
            circle.Radius = radius
            circle.Style = 1
            circle.Update()
    finally:
        sketch.EndEdit()


def extrude(part, sketch, depth, cut=False):
    """Выдавливает эскиз на глубину depth (мм) в прямом направлении.
    cut=True вырезает материал вместо добавления.
    """
    kind = const_3d.o3d_cutExtrusion if cut else const_3d.o3d_bossExtrusion
    extrusion = api7.IModelContainer(part).Extrusions.Add(kind)
    extrusion.Sketch = sketch
    extrusion.SetExtrusionType(True, 0)   # 0 = на глубину (etBlind)
    extrusion.SetDepth(True, depth)
    extrusion.Update()
    return extrusion