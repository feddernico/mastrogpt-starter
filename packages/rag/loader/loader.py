import base64
import numpy as np
import requests
import vdb
import vision2 as vision

from io import BytesIO
from PIL import Image

USAGE = f"""Welcome to the Vector DB Loader.
Write text to insert in the DB. 
Use `@[<coll>]` to select/create a collection and show the collections.
Use `_@[<coll>]` to select/create a collection of pictures and show the collections.
Use `*<string>` to vector search the <string>  in the DB.
Use `#<limit>`  to change the limit of searches.
Use `!<substr>` to remove text with `<substr>` in collection.
Use `!![<collection>]` to remove `<collection>` (default current) and switch to default.
Use a URL starting with http to upload a picture.
"""

IMG_FORMATS = ['.jpeg', '.jpg', '.gif', '.png', '.svg']


def image_url_to_base64(url):
    response = requests.get(url)
    response.raise_for_status()
    content_type = response.headers.get('Content-Type', 'image/jpeg')  # fallback
    return content_type, base64.b64encode(response.content).decode('utf-8')


def load_image(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content)).convert("RGB")


def loader(args):
  #print(args)
  # get state: <collection>[:<limit>]
  collection = "default"
  limit = 30
  sp = args.get("state", "").split(":")
  if len(sp) > 0 and len(sp[0]) > 0:
    collection = sp[0]
  if len(sp) > 1:
    try:
      limit = int(sp[1])
    except: pass
  print(collection, limit)

  out = f"{USAGE}Current collection is {collection} with limit {limit}"
  db = vdb.VectorDB(args, collection)
  inp = str(args.get('input', ""))

  # select collection
  if inp.startswith("@"):
    out = ""
    if len(inp) > 1:
       collection = inp[1:]
       out = f"Switched to {collection}.\n"
    out += db.setup(collection)
  elif inp.startswith("_@"):
    out = ""
    if len(inp) > 1:
       collection = inp[2:]
       out = f"Switched to {collection}.\n"
    out += db.setup_pics(collection)
  # set size of search
  elif inp.startswith("#"):
    try: 
       limit = int(inp[1:])
    except: pass
    out = f"Search limit is now {limit}.\n"
  # run a query
  elif inp.startswith("*"):
    search = inp[1:]
    if search == "":
      search = " "
    res = db.vector_search(search, limit=limit)
    if len(res) > 0:
      out = f"Found:\n"
      for i in res:
        img_tag = ''
        if len(i[2]) > 0:
          content_type, encoded = image_url_to_base64(i[2])
          img_src = f'data:{content_type};base64,{encoded}'
          img_tag = f' <img src="{img_src}" />'
        out += f"({i[0]:.2f}) {i[1]}{img_tag}\n"
    else:
      out = "Not found"
  # remove a collection
  elif inp.startswith("!!"):
    if len(inp) > 2:
      collection = inp[2:].strip()
    out = db.destroy(collection)
    collection = "default"
  # remove content
  elif inp.startswith("!"):
    count = db.remove_by_substring(inp[1:])
    out = f"Deleted {count} records."
  # load a picture
  elif inp.startswith("http") and any(file_format in inp for file_format in IMG_FORMATS):
    content_type, encoded = image_url_to_base64(inp)
    img_src = f'data:{content_type};base64,{encoded}'
    vis = vision.Vision(args)
    pic_description = vis.decode(encoded)
    db.insert_pic(inp, pic_description)
    out = f'Image loaded:  {len(img_src)} <img src="{img_src}" /><br /> Image description: {pic_description}'
  elif inp != '':
    out = "Inserted "
    lines = [inp]
    if args.get("options","") == "splitlines":
      lines = inp.split("\n")
    for line in lines:
      if line == '': continue
      res = db.insert(line)
      out += "\n".join([str(x) for x in res.get("ids", [])])
      out += "\n"

  return {"output": out, "state": f"{collection}:{limit}"}
  
