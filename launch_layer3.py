import sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "MEGA-LAYER-3-KNOWLEDGE-UNIVERSE", "services"))
sys.path.insert(0, os.path.join(BASE, "MEGA-LAYER-3-KNOWLEDGE-UNIVERSE", "data-model"))
sys.path.insert(0, os.path.join(BASE, "MEGA-LAYER-3-KNOWLEDGE-UNIVERSE", "backend"))

import importlib.util
spec = importlib.util.spec_from_file_location("knowledge_api", os.path.join(BASE, "MEGA-LAYER-3-KNOWLEDGE-UNIVERSE", "services", "knowledge_api.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules["knowledge_api"] = mod
spec.loader.exec_module(mod)
app = mod.app
