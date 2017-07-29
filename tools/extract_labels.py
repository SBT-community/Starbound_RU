#!/bin/python3
# A script for label extraction from unpacked game assets


from os.path import join, dirname, exists, relpath, abspath, basename
from sys import platform
if platform == "win32":
  from os.path import normpath as normpath_old
  def normpath(path):
    return normpath_old(path).replace('\\', '/')
else:
  from os.path import normpath
from codecs import open as open_n_decode
from shared_path import getSharedPath
from json_tools import prepare, field_by_path, list_field_paths
from re import compile as regex
from multiprocessing import Pool
from os import walk, makedirs, remove
from json import load, dump, loads
from parser_settings import files_of_interest
from utils import get_answer
from bisect import insort_left
from special_cases import specialSections

root_dir = "./assets"
prefix = "./translations"
texts_prefix = "texts"
sub_file = normpath(join(prefix, "substitutions.json"))

glitchEmoteExtractor = regex("^([In]{,3}\s?[A-Za-z-]+\.)\s+(.*)")
glitchIsHere = regex("^.*[gG]litch.*")


def defaultHandler(val, filename, path):
  sec = ""
  for pattern in specialSections:
    if pattern.match(filename, path):
      sec = pattern.name
      break
  return [(sec, val, filename, path)]
  
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
  t = defaultHandler(text, filename, normpath(join(path, "glitchEmotedText")))
  e = defaultHandler(emote, filename, normpath(join(path, "glitchEmote")))
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
  with open_n_decode(filename, "r", "utf-8") as f:
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
  ## {"section": { "label" :
  ##   { "files were it used" : [list of fields were it used in file] } } }
  print("Scanning assets at " + assets_dir)
  db = dict()
  db[""] = dict()
  foi = list()
  endings = tuple(files_of_interest.keys())
  for subdir, dirs, files in walk(assets_dir):
    for thefile in files:
      if thefile.endswith(endings):
        foi.append(normpath(join(subdir, thefile)))
  with Pool() as p:
    r = p.imap_unordered(parseFile, foi)
    for chunk in r:
      for sec, val, fname, path in chunk:
        if sec not in db:
          db[sec] = dict()
        if val not in db[sec]:
          db[sec][val] = dict()
        filename = normpath(relpath(abspath(fname), abspath(assets_dir)))
        if filename not in db[sec][val]:
          db[sec][val][filename] = list()
        if path not in db[sec][val][filename]:
          insort_left(db[sec][val][filename], path)
  return db

def file_by_assets(assets_fname, field, substitutions):
  if assets_fname in substitutions and field in substitutions[assets_fname]:
    return substitutions[assets_fname][field]
  else:
    return normpath(join(texts_prefix, assets_fname)) + ".json"

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
  label, files, oldsubs, section = combo
  substitutions = dict()
  obj_file = normpath(getSharedPath(files.keys()))
  translation = dict()
  if section:
    translation["Comment"] = section
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
      oldfile = normpath(join(prefix, file_by_assets(thefile, field, oldsubs)))
      if exists(oldfile):
        olddata = []
        try:
          with open_n_decode(oldfile, 'r', 'utf-8') as f:
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

def prepare_to_write(database):
  file_buffer = dict()
  substitutions = dict()
  oldsubs = dict()
  print("Trying to merge with old data...")
  try:
    with open_n_decode(sub_file, "r", 'utf-8') as f:
      oldsubs = load(f)
  except:
    print("No old data found, creating new database.")
  for section, thedatabase in database.items():
    with Pool() as p: # Do it parallel
      result = p.imap_unordered(process_label,
        [(f, d, oldsubs, section) for f,d in thedatabase.items() ], 40)
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
  with open_n_decode(filename, "w", 'utf-8') as f:
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
  #with open("testdb.json", "w") as f:
  #  dump(thedatabase, f, ensure_ascii=False, indent=2, sort_keys=True)
  file_buffer = prepare_to_write(thedatabase)
  #with open("testfb.json", "w") as f:
  #  dump(file_buffer, f, ensure_ascii=False, indent=2, sort_keys=True)
  final_write(file_buffer)
