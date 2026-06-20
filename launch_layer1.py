import sys, os
sys.path.insert(0, r"D:\PROJECT RISHI\AEGIS-OMEGA-X")
import importlib.util

spec = importlib.util.spec_from_file_location("pdt_api", r"D:\PROJECT RISHI\AEGIS-OMEGA-X\MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN\services\pdt_api.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["pdt_api"] = mod
spec.loader.exec_module(mod)
app = mod.app
