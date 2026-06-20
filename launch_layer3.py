import sys, os
sys.path.insert(0, r"D:\PROJECT RISHI\AEGIS-OMEGA-X")
sys.path.insert(0, r"D:\PROJECT RISHI\AEGIS-OMEGA-X\MEGA-LAYER-3-KNOWLEDGE-UNIVERSE\services")
sys.path.insert(0, r"D:\PROJECT RISHI\AEGIS-OMEGA-X\MEGA-LAYER-3-KNOWLEDGE-UNIVERSE\data-model")
sys.path.insert(0, r"D:\PROJECT RISHI\AEGIS-OMEGA-X\MEGA-LAYER-3-KNOWLEDGE-UNIVERSE\backend")
import importlib.util

spec = importlib.util.spec_from_file_location("knowledge_api", r"D:\PROJECT RISHI\AEGIS-OMEGA-X\MEGA-LAYER-3-KNOWLEDGE-UNIVERSE\services\knowledge_api.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["knowledge_api"] = mod
spec.loader.exec_module(mod)
app = mod.app
