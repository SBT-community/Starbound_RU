#!/bin/python

import os
from os.path import dirname, join, exists, relpath, normpath, splitext
import json
from json_tools import list_field_paths, field_by_path
from shutil import copy
from utils import get_answer
from bisect import insort_left

mod_dir = "./mod_old"
root_dir = "./translations"

def parseFile(filename):
  result = []
  try:
    with open(filename, "r") as f:
      result = json.load(f)
  except:
    print("Failed to parse: " + filename)
    quit(1)
  return result

def get_data(field, target_file, original_file):
  ## Returns json structure from "target_file" and
  ## index of a field in this structure related to "field" in "original_file"
  ## original_file - a file path in game assets the requested data related to
  ## field - path to field of interest inside "original_file" json
  ## target_file - a framework file, containing the requested data
  data = ""
  try:
    with open(target_file, "r") as f:
      data = json.load(f)
  except:
    print("Warning: can not load file " + target_file)
    return None, -1
  index = -1
  for i, label in enumerate(data):
    if original_file in label["Files"] and (field in label["Files"][original_file]):
      index = i
      return data, i

  return None, -1



def replace(target_file, field, newdata, original):
  ## Tries to merge translation to framework
  ## if translation exists and conflicts with new one
  ## asks for user to manual merge
  ## target - file in framework related to file should be translated
  ## field - path of field in game assets json file which should be translated
  ## newdata - translated string
  ## original - path to file in game assets should be translated
  target = join(root_dir, target_file)
  data, index = get_data(field, target, original)
  if not (type(newdata) is str):
    return
  if data is None:
    print("Cannot get data: " + newdata)
    print("Target file: " + target)
    print("Assets file: " + original)
    return
  changed = False
  olddata = ""
  if "DeniedAlternatives" not in data[index]:
    data[index]["DeniedAlternatives"] = list()
  if "Rus" in data[index]["Texts"]:
    olddata = data[index]["Texts"]["Rus"]
  if olddata == newdata or len(newdata) == 0:
    return
  elif newdata in data[index]["DeniedAlternatives"]:
    return
  elif len(olddata) == 0:
    changed = True
    data[index]["Texts"]["Rus"] = newdata
  else:
    print("Target: " + target)
    print("Origin: " + original)
    print("Used in:")
    i = 0
    for f, fields in data[index]["Files"].items():
      if i > 5:
        print("...and in " + str(len(data[index]["Files"])-i) + " more files")
        break
      print("   " + f)
      for p in fields:
        print("     at " + p)
      i += 1
    print("Denied variants:")
    for d in data[index]["DeniedAlternatives"]:
      print('  ' + d)
    print("Field: " + field)
    print("English text:")
    print('  "' + data[index]["Texts"]["Eng"] + '"')
    print("Old Russian text:")
    print('  "' + data[index]["Texts"]["Rus"] + '"')
    print("New Russian text:")
    print("  \"" + newdata + '"')
    print("What text should be used?")
    print(" n - new text")
    print(" o - old text")
    print(" e - enter manually")
    answer = get_answer(["n", "o", "e", "i"])
    if answer == "n":
      print("Setting to the new data...")
      if olddata not in data[index]["DeniedAlternatives"]:
        insort_left(data[index]["DeniedAlternatives"], olddata)
      if newdata in data[index]["DeniedAlternatives"]:
        data[index]["DeniedAlternatives"].remove(newdata)
      data[index]["Texts"]["Rus"] = newdata
      changed = True
    elif answer == "e":
      print("Enter new data:")
      answer = get_answer(3)
      data[index]["Texts"]["Rus"] = answer
      changed = True
      if newdata not in data[index]["DeniedAlternatives"] and newdata != answer:
        insort_left(data[index]["DeniedAlternatives"], newdata)
        changed = True
      if olddata not in data[index]["DeniedAlternatives"] and olddata != answer:
        insort_left(data[index]["DeniedAlternatives"], olddata)
        changed = True
      if answer in data[index]["DeniedAlternatives"]:
        data[index]["DeniedAlternatives"].remove(answer)
      print("Written: " + answer)
    elif answer == "i":
      import code
      code.InteractiveConsole(locals=globals()).interact()
    else:
      print("Keeping old data...")
      if newdata not in data[index]["DeniedAlternatives"]:
        insort_left(data[index]["DeniedAlternatives"],newdata)
        changed = True
      if olddata in data[index]["DeniedAlternatives"]:
        data[index]["DeniedAlternatives"].remove(olddata)
        changed = True
  if changed:
    pass
    with open(target, "w") as f:
      json.dump(data, f, ensure_ascii = False, indent = 2, sort_keys=True)


def handleGlitch(field, newdata, original_file, original_files):
  ## field - path to field of interest inside json
  ## newdata - translated string
  ## original_files - a dict with pairs {field: path}
  emotefield = join(field, "glitchEmote")
  textfield = join(field, "glitchEmotedText")
  if  emotefield not in original_files and textfield not in original_files:
    return False # Not a glitch case, return
  offset = newdata.find(".")
  if offset == -1 or offset + 2 >= len(newdata):
    print("Cann't find separator of glitch emote in " + newdata)
    print("but this text should contain one! Skipping to avoid database damage...")
    return True
  emote = newdata[:offset+1]
  text = newdata[offset+2:]
  while text.startswith(emote): #TODO: Delete after base fix
    text = text[len(emote)+1:]
  emotepath = original_files[emotefield]
  textpath = original_files[textfield]
  replace(emotepath, emotefield, emote, original_file)
  replace(textpath, textfield, text, original_file)
  return True

substitutions = dict()
with open(join(root_dir ,"substitutions.json"), "r") as f:
  substitutions = json.load(f)

specialHandlers = [
  ## Contains handler-functions for special cases
  ## function should return True if it can handle supplied data
  ## otherwise - return False
  ## function should receive 4 arguments:
  ## field - path to field of interest inside json
  ## newdata - translated string
  ## original_file - path to target file in game assets
  ## original_files - a dict with pairs {field: path},
  ##  where:
  ##    path - path to target file in framework
  ##    field - path to field of interest inside json
  ##  this dict can contain a special fields, not existent in real game assets and
  ##  related to internal framework special cases
  ##  such a dict usually can be obtained from substitutions global variable or file
  handleGlitch
]

def process_replacement(field, newdata, original_file):
  ## field - path to field of interest inside json
  ## newdata - translated string
  ## original_file - target file of replacement in game assets
  targetfile = join("texts", original_file + ".json")
  if original_file in substitutions: # We encountered shared field
    if field in substitutions[original_file]:
      targetfile = substitutions[original_file][field]
    else: # Special case like glitchEmote
      for handler in specialHandlers:
        if handler(field, newdata,  original_file, substitutions[original_file]):
          return
  replace(targetfile, field, newdata, original_file)


others_path = normpath(join(root_dir, "others"))
for subdir, dirs, files in os.walk(mod_dir):
  for thefile in files:
    if not thefile.endswith(".patch"):
      # All non-patch files will be copied to others directory
      modpath = join(subdir, thefile) # File path in mod dir
      assetspath = normpath(relpath(modpath, mod_dir)) # File path in packed assets
      fwpath = normpath(join(others_path,assetspath)) # File path in framework
      if exists(fwpath):
        print(fwpath + " already exists! Replacing...")
      os.makedirs(dirname(fwpath), exist_ok = True)
      copy(modpath, fwpath)
      continue
    filename = join(subdir, thefile) # Patch file path
    # File path in packed assets
    fname, ext = splitext(filename)
    assetspath = normpath(relpath(fname, mod_dir))
    replacements = parseFile(filename)
    for replacement in replacements:
      # We expect, that operation is always "replace".
      # If it isn't... Well, something strange will happen.
      newdata = replacement["value"] # Imported translated text
      jsonpath = replacement["path"]
      if type(newdata) is list: # Very special case if value is list
        paths = list_field_paths(newdata)
        for p in paths: # There we are restoring paths to leafs of structure in newdata
          process_replacement(join(jsonpath, p),
            field_by_path(newdata,p), assetspath)
      else: # All as expected, just perform replacement
        process_replacement(jsonpath, newdata, assetspath)
