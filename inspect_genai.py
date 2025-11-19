import google.generativeai.types as genai_types
import google.generativeai as genai

print("genai_types attributes:")
print(dir(genai_types))

try:
    print(f"Part in genai_types: {genai_types.Part}")
except AttributeError:
    print("Part NOT in genai_types")

try:
    print(f"Part in genai: {genai.Part}")
except AttributeError:
    print("Part NOT in genai")
