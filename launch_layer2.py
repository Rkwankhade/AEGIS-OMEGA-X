import sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "MEGA-LAYER-2-SECURITY-GENOME", "services"))
sys.path.insert(0, os.path.join(BASE, "MEGA-LAYER-2-SECURITY-GENOME", "data-model"))
sys.path.insert(0, os.path.join(BASE, "MEGA-LAYER-2-SECURITY-GENOME", "backend"))

import importlib.util
spec = importlib.util.spec_from_file_location("genome_api", os.path.join(BASE, "MEGA-LAYER-2-SECURITY-GENOME", "services", "genome_api.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules["genome_api"] = mod
spec.loader.exec_module(mod)
app = mod.app
