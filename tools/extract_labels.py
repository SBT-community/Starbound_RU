#!/bin/python3
# A script for label extraction from unpacked game assets


from os.path import join, dirname, exists, normpath, relpath, abspath, basename
from shared_path import getSharedPath
from json_tools import prepare, field_by_path, list_field_paths
from re import compile as regex
from multiprocessing import Pool
from os import walk, makedirs, remove
from json import load, dump, loads
from parser_settings import files_of_interest
from utils import get_answer
from bisect import insort_left

root_dir = "./assets"
prefix = "./translations"
texts_prefix = "texts"
sub_file = normpath(join(prefix, "substitutions.json"))

glitchEmoteExtractor = regex("^([A-Za-z]{,3}\s?[A-Za-z]+\.)\s+(.*)")
glitchIsHere = regex("^.*[gG]litch.*")


def defaultHandler(val, filename, path):
  return [(val, filename, path)]
  
def glitchDescriptionSpecialHandler(val, filename, path):
  ## Handles glitch utterances, and separates it to emote part and text part,
  ## then saves the parts in new paths to database
  ## See details in textHandlers description
  extracted = glitchEmoteExtractor.match(val)
  is_glitch = glitchIsHere.match(path)
  if extracted is None or is_glitch is None:
    return False
  emote = extracted.groups()[0]
  text = extracted.groups()[1]
  t = defaultHandler(text, filename, join(path, "glitchEmotedText"))
  e = defaultHandler(emote, filename, join(path, "glitchEmote"))
  return t + e

textHandlers = [
  ## A list of text handlers.
  ## Handlers needed to handle a special cases of text like glitch emotes
  ## If handler can handle the text, it returns True, otherwise - False
  ## the defaultHandler must always present in the end of the list, 
  ## it always handles the text and returns True
  ## Each handler should receive 3 arguments:
  ##    first - the text should be handled
  ##    second - the filename, where text was found
  ##    third - the path to field inside json, where text was found
  glitchDescriptionSpecialHandler,
  defaultHandler
]


specialSharedPaths = {
  ## A dict with field ends which shold be saved in special files
  "glitchEmote": "glitchEmotes",
}

def parseFile(filename):
  chunk = list()
  with open(filename, "r") as f:
    string = prepare(f)
    jsondata = dict()
    try:
      jsondata = loads(string)
    except:
      print("Cannot parse " + filename)
      return []
    paths = list_field_paths(jsondata)
    dialog =  dirname(filename).endswith("dialog")
    for path in paths:
      for k in files_of_interest.keys():
        if filename.endswith(k) or k == "*":
          for roi in files_of_interest[k]:
            if roi.match(path) or dialog:
              val = field_by_path(jsondata, path)
              if not type(val) is str:
                print("File: " + filename)
                print("Type of " + path + " is not a string!")
                continue
              if val == "":
                continue
              for handler in textHandlers:
                res = handler(val, filename, '/' + path)
                if res:
                  chunk += res
                  break
              break
  return chunk

def construct_db(assets_dir):
  ## Creating a database of text labels from game assets dir given
  ## the database has a following structure:
  ##  { "label" : { "files were it used" : [list of fields were it used in file] } }
  print("Scanning assets at " + assets_dir)
  db = dict()
  foi = list()
  for subdir, dirs, files in walk(assets_dir):
    for thefile in files:
      if thefile.endswith(tuple(files_of_interest.keys())):
        foi.append(join(subdir, thefile))
  with Pool() as p:
    r = p.imap_unordered(parseFile, foi)
    for chunk in r:
      for val, fname, path in chunk:
        if val not in db:
          db[val] = dict()
        filename = normpath(relpath(abspath(fname), abspath(assets_dir)))
        if filename not in db[val]:
          db[val][filename] = list()
        if path not in db[val][filename]:
          insort_left(db[val][filename], path)
  return db

def file_by_assets(assets_fname, field, substitutions):
  if assets_fname in substitutions and field in substitutions[assets_fname]:
    return substitutions[assets_fname][field]
  else:
    return join(texts_prefix, assets_fname) + ".json"

def process_label(combo):
  ## Creates json file structure for given label then returns
  ## tuple of filename, translation and substitutions
  ## combo - a tuple of 3 arguments: label, files and oldsubs
  ##   label - english text from database
  ##   files - filelist were english text used (also from database)
  ##   oldsubs - the parsed json content of substitutions.json from 
  ##             previous database if it exists
  ## Returned tuple:
  ##   translation - a part of json file content to write into the database
  ##   filename - a name of file the translation should be added
  ##   substitutions - a part of new formed substitutions file content
  label, files, oldsubs = combo
  substitutions = dict()
  obj_file = normpath(getSharedPath(files.keys()))
  translation = dict()
  translation["Texts"] = dict()
  translation["Texts"]["Eng"] = label
  translation["DeniedAlternatives"] = list()
  filename = ""
  for thefile, fields in files.items():
    for field in fields:
      fieldend = basename(field)
      if fieldend in specialSharedPaths:
        obj_file = normpath(specialSharedPaths[fieldend])
      if obj_file == '.':
        obj_file = "wide_spread_fields"
      filename = normpath(join(prefix, texts_prefix, obj_file + ".json"))
      if thefile != obj_file or fieldend in ["glitchEmotedText"]:
        if thefile not in substitutions:
          substitutions[thefile] = dict()
        substitutions[thefile][field] = normpath(relpath(filename, prefix))
      oldfile = join(prefix, file_by_assets(thefile, field, oldsubs))
      if exists(oldfile):
        olddata = []
        try:
          with open(oldfile, 'r') as f:
            olddata = load(f)
        except:
          pass # If can not get old translation for any reason just skip it
        for oldentry in olddata:
          if oldentry["Texts"]["Eng"] == label:
            if "DeniedAlternatives" in oldentry:
              for a in oldentry["DeniedAlternatives"]:
                if a not in translation["DeniedAlternatives"]:
                  insort_left(translation["DeniedAlternatives"], a)
            translation["Texts"].update(oldentry["Texts"])
            break
  translation["Files"] = files
  return (filename, translation, substitutions)

def prepare_to_write(thedatabase):
  file_buffer = dict()
  substitutions = dict()
  oldsubs = dict()
  print("Trying to merge with old data...")
  try:
    with open(sub_file, "r") as f:
      oldsubs = load(f)
  except:
    print("No old data found, creating new database.")
  with Pool() as p: # Do it parallel
    result = p.imap_unordered(process_label,
      [(f, d, oldsubs) for f,d in thedatabase.items() ], 40)
    for fn, js, sb in result: # Merge results
      for fs, flds in sb.items():
        if fs not in substitutions:
          substitutions[fs] = flds
        else:
          substitutions[fs].update(flds)
      if fn not in file_buffer:
        file_buffer[fn] = list()
      file_buffer[fn].append(js)
  file_buffer[sub_file] = substitutions
  return file_buffer

def catch_danglings(target_path, file_buffer):
  to_remove = list()
  for subdir, dirs, files in walk(target_path):
    for thefile in files:
      fullname = normpath(join(subdir, thefile))
      if fullname not in file_buffer:
        to_remove.append(fullname)
  return to_remove

def write_file(filename, content):
  
  filedir = dirname(filename)
  if not filename.endswith("substitutions.json"):
    content = sorted(content, key=lambda x: x["Texts"]["Eng"])
  if len(filedir) > 0:
    makedirs(filedir, exist_ok=True)
  else:
    raise Exception("Filename without dir: " + filename)
  with open(filename, "w") as f:
    dump(content, f, ensure_ascii=False, indent=2, sort_keys=True)
  #print("Written " + filename)

def final_write(file_buffer):
  danglings = catch_danglings(join(prefix, "texts"), file_buffer)
  print("These files will be deleted:")
  for d in danglings:
    print('  ' + d)
  print('continue? (y/n)')
  ans = get_answer(['y', 'n'])
  if ans == 'n':
    print('Cancelled!')
    return
  print('Writing...')
  with Pool() as p:
    delete_result = p.map_async(remove, danglings)
    write_result = p.starmap_async(write_file, list(file_buffer.items()))
    p.close()
    p.join()
      
# Start here
if __name__ == "__main__":
  thedatabase = construct_db(root_dir)
  file_buffer = prepare_to_write(thedatabase)
  #with open("testfb.json", "w") as f:
  #  dump(file_buffer, f, ensure_ascii=False, indent=2, sort_keys=True)
  final_write(file_buffer)
