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