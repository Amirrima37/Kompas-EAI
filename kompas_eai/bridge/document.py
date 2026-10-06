from .connection import api7, const


def create_part(app7):
    """Создаёт пустую деталь и возвращает документ."""
    return app7.Documents.Add(const.ksDocumentPart, True)


def get_part(doc):
    """Возвращает верхнюю деталь (IPart7) из документа-детали."""
    return api7.IKompasDocument3D(doc).TopPart


def save_document(doc, path):
    """Сохраняет документ по указанному пути."""
    doc.SaveAs(str(path))