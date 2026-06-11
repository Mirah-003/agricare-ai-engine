import sys
from run_agricare import AgriCareEngine
engine = AgriCareEngine()
res = engine.process("My chickens are sneezing")
print(res)
