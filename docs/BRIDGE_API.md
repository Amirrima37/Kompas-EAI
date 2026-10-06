# Мост с КОМПАС (kompas_eai.bridge)

Импорт: `from kompas_eai.bridge import ...`. Все размеры в мм, масса в кг, плотность в г/мм3.

## Функции

| Модуль | Функция | Что делает |
|---|---|---|
| connection | `connect()` | подключается к КОМПАС-3D v24, возвращает IApplication |
| document | `create_part(app7)` | пустая деталь, возвращает документ |
| document | `get_part(doc)` | верхняя деталь (IPart7) |
| document | `save_document(doc, path)` | сохраняет .m3d |
| sketch | `create_sketch(part, plane)` | эскиз на "XOY", "XOZ" или "YOZ" |
| sketch | `add_circles(sketch, [(xc, yc, r)])` | окружности |
| sketch | `add_rectangles(sketch, [(x, y, w, h)])` | прямоугольники, (x, y) левый нижний угол |
| sketch | `add_lines(sketch, [(x1, y1, x2, y2)])` | отрезки |
| sketch | `add_polygon(sketch, [(x, y), ...])` | замкнутый контур по вершинам |
| sketch | `edit_sketch(sketch)` | контекст для произвольного рисования (IDrawingContainer) |
| features | `extrude(part, sketch, depth, cut=False, direction=FORWARD)` | выдавливание или вырез; FORWARD, REVERSE, BOTH |
| measure | `set_material(part, name, density)` | материал и плотность |
| measure | `get_bounding_box(part)`, `get_size(part)` | габариты |
| measure | `get_mass_properties(part)` | объём, площадь, масса, центр масс |

## Проверенные особенности КОМПАС API
- `part.NewObject` у IPart7 нет: эскиз создаётся через `IModelContainer(part).Sketchs.Add()`.
- Операция попадает в дерево модели только после `Update()`.
- У выреза направления FORWARD/REVERSE в КОМПАС трактуются наоборот; `extrude()` это скрывает, FORWARD всегда идёт в сторону нормали эскиза.
- `IMassInertiaParam7.Calculate()` возвращает False, но значения верны; единицы при LengthUnits=0, MassUnits=0: см, см2, см3, кг. `get_mass_properties` переводит в мм.
- Справка: help.ascon.ru/KOMPAS_SDK/24, методы сверять там, а не угадывать.
- Для `REVERSE` и `BOTH` КОМПАС требует глубину на обеих сторонах (SetExtrusionType/SetDepth для True и False), иначе `Update()` возвращает False; `extrude()` делает это сам.
- Плоскость XOZ: выдавливание FORWARD идёт по +Y (проверено на уголке: Y от 0 до 40).

## Тесты
`tests/test_bridge_smoke.py` приёмочный; `test_sketch_smoke.py` и `test_measure_smoke.py` частные.

