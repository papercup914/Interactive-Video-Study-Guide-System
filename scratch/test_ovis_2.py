import torch
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor
import types

print("Loading Ovis...")
model_id = "ATH-MaaS/OvisOCR2"
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    torch_dtype=dtype, 
    trust_remote_code=True, 
    device_map="auto"
)

# Patch _validate_model_kwargs to bypass strict check
model._validate_model_kwargs = types.MethodType(lambda self, model_kwargs: None, model)

img = Image.new('RGB', (200, 200), color = 'white')
prompt = "<image>\nConvert this document image into structured Markdown, including text, tables, and formulas."

inputs = processor(text=prompt, images=img, return_tensors="pt")
inputs = {k: v.to(device) for k, v in inputs.items()}

print("Generating...")
try:
    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_new_tokens=10, 
            do_sample=False
        )
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
