import os, json, requests as req

MODEL = "llava:7b"

def collect(lines):
  out = ""
  for line in lines:
    #line = next(lines)
    chunk = json.loads(line.decode("UTF-8"))
    out +=  chunk.get("response", "")
  return out

class Vision:
  def __init__(self, args):
    host = args.get("OLLAMA_HOST", os.getenv("OLLAMA_HOST"))
    auth = args.get("AUTH", os.getenv("AUTH"))
    self.url = f"https://{auth}@{host}/api/generate"

  def decode(self, img):
    msg = {
      "model": MODEL,
      "prompt": "describe the image",
      "images": [img]
    }
    try:
      lines = req.post(self.url, json=msg, stream=True).iter_lines()
    except Exception as e:
      return str(e)
    return collect(lines)

