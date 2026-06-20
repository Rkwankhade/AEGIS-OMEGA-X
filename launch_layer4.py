import sys, os
sys.path.insert(0, r"D:\PROJECT RISHI\AEGIS-OMEGA-X")
sys.path.insert(0, r"D:\PROJECT RISHI\AEGIS-OMEGA-X\MEGA-LAYERS-5-14")
sys.path.insert(0, r"D:\PROJECT RISHI\AEGIS-OMEGA-X\MEGA-LAYER-4-AI-CIVILIZATION\backend")
import importlib.util

spec = importlib.util.spec_from_file_location("complete_implementation", r"D:\PROJECT RISHI\AEGIS-OMEGA-X\MEGA-LAYERS-5-14\complete_implementation.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["complete_implementation"] = mod
spec.loader.exec_module(mod)
app = mod.gateway
