import os
from dotenv import load_dotenv
from run_agricare import AgriCareEngine

# Load the environment variables from .env
load_dotenv()

engine = AgriCareEngine()
result = engine.process("My chickens are sneezing, coughing, and have swollen eyes. What should I do?")

print("\n=== AI VET RESPONSE ===")
print(result["answer"])
print("=======================\n")
