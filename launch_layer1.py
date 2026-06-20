import sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN", "services"))
sys.path.insert(0, os.path.join(BASE, "MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN", "data-model"))
sys.path.insert(0, os.path.join(BASE, "MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN", "backend"))

import importlib.util
spec = importlib.util.spec_from_file_location("pdt_api", os.path.join(BASE, "MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN", "services", "pdt_api.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules["pdt_api"] = mod
spec.loader.exec_module(mod)
app = mod.app
