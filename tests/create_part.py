import pythoncom
from win32com.client import Dispatch, gencache

const = gencache.EnsureModule("{75C9F5D0-B5B8-4526-8681-9903C567D2ED}", 0, 1, 0).constants
const_3d = gencache.EnsureModule("{2CAF168C-7961-4B90-9DA2-701419BEEFE3}", 0, 1, 0).constants
api7 = gencache.EnsureModule("{69AC2981-37C0-4379-84FD-5DD2F3C0A520}", 0, 1, 0)

app7 = api7.IApplication(
    Dispatch("Kompas.Application.7")._oleobj_.QueryInterface(
        api7.IApplication.CLSID, pythoncom.IID_IDispatch
    )
)
app7.Visible = True

doc = app7.Documents.Add(const.ksDocumentPart, True)
print("Деталь создана:", doc)
import os
path = r"C:\dev\Kompas-EAI\out\test_part.m3d"
doc.SaveAs(path)
print("Файл существует:", os.path.exists(path))
doc3d = api7.IKompasDocument3D(doc)
part = doc3d.TopPart
print("Верхняя деталь:", part)
plane_xoy = part.DefaultObject(const_3d.o3d_planeXOY)
print("Плоскость XOY:", plane_xoy)

container = api7.IModelContainer(part)
sketch = container.Sketchs.Add()
sketch.Plane = plane_xoy
sketch.Update()
print("Эскиз создан:", sketch)

fragment = sketch.BeginEdit()
view = fragment.ViewsAndLayersManager.Views.ActiveView
container = api7.IDrawingContainer(view)
circle = container.Circles.Add()
circle.Xc = 0
circle.Yc = 0
circle.Radius = 50
circle.Style = 1
circle.Update()
print("Выход:", sketch.EndEdit())
container_model = api7.IModelContainer(part)
extrusion = container_model.Extrusions.Add(const_3d.o3d_bossExtrusion)
extrusion.Sketch = sketch
print("Выдавливание создано:", extrusion)
extrusion.SetExtrusionType(True, 0)   # 0 = на глубину (etBlind)
extrusion.SetDepth(True, 100)         # 100 мм в прямом направлении
extrusion.Update()
print("Выдавливание обновлено")