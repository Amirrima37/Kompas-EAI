import os
from kompas_bridge import (
    connect, create_part, get_part, create_sketch,
    add_circles, extrude, save_document,
)

app7 = connect()
doc = create_part(app7)
part = get_part(doc)

sketch = create_sketch(part, "XOY")
add_circles(sketch, [(0, 0, 50), (0, 0, 40)])   # наружный Ø100, внутренний Ø80
extrude(part, sketch, 200)                        # длина 200 мм

path = r"C:\dev\Kompas-EAI\out\pipe_test.m3d"
save_document(doc, path)
print("Файл существует:", os.path.exists(path))