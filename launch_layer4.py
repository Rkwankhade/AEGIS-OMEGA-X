import sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "MEGA-LAYERS-5-14"))
sys.path.insert(0, os.path.join(BASE, "MEGA-LAYER-4-AI-CIVILIZATION", "backend"))

import importlib.util
spec = importlib.util.spec_from_file_location("complete_implementation", os.path.join(BASE, "MEGA-LAYERS-5-14", "complete_implementation.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules["complete_implementation"] = mod
spec.loader.exec_module(mod)
app = mod.gateway
