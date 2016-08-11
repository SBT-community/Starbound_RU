#!/bin/python
# A script for export framework data to unpacked mod file structure

from os import walk, makedirs, sep
from os.path import join, relpath, dirname, exists, normpath, basename
from json import load, dump
from shutil import copy
from json_tools import field_by_path

translations_dir = "./translations"
mod_dir = "./new_mod"

patchfiles = dict()

emotes = dict()
glitchFixed = list()
labelsTotal = dict()
labelsTranslated = dict()

others_path = normpath(join(translations_dir, "others"))
others_dest = normpath(mod_dir)


def sum_up_counter(counter):
  result = 0
  for l, n in counter.items():
    if not type(n) is int:
      result += sum_up_counter(n)
    else:
      result += n
  return result

def set_count(counter, path, value):
  ## Sets the count of the translated or total elements for specific path
  thepath = normpath(relpath(path, translations_dir))
  field_by_path(counter, thepath, value, sep)

def add_count(counter, path, value):
  thepath = normpath(relpath(path, translations_dir))
  oldval = field_by_path(counter, thepath, sep=sep)
  field_by_path(counter, thepath, oldval+1, sep)


def check_translation_length(text):
  ## 15 height, 36 width
  words = text.split(' ')
  width = 36
  height = 15
  for word in words:
    if word.endswith('\n'):
      height -= 1
      width = 36
      continue
    width -= len(word)
    if width < 0:
      width = 36 - len(word)
      height -= 1
    width -= 1 # space after
  return height >= 0

specials = dict()

for subdir, dirs, files in walk(translations_dir):
  for thefile in files:
    if thefile in ["substitutions.json", "totallabels.json", "translatedlabels.json"]:
      continue
    filename = normpath(join(subdir, thefile))
    if filename.startswith(others_path):
      filename = relpath(filename, others_path)
      dest = join(others_dest, filename)
      makedirs(dirname(dest), exist_ok = True)
      copy(join(subdir, thefile), dest)
      continue
    filename = normpath(join(subdir, thefile))
    jsondata = list()
    try:
      with open(filename, "r") as f:
        jsondata = load(f)
    except:
      print("Cannot parse file: " + filename)
      continue
    set_count(labelsTotal,filename, len(jsondata))
    set_count(labelsTranslated,filename, 0)
    for label in jsondata:
      if "Rus" not in label["Texts"] or len(label["Texts"]["Rus"]) == 0:
        continue

      add_count(labelsTranslated, filename, 1)
      translation = label["Texts"]["Rus"]
      if filename.endswith("codex.json") and not check_translation_length(translation):
        print("Warning! String too long in file: " + filename)
      
      for originfile, jsonpaths in label["Files"].items():
        patchfile = normpath(join(mod_dir, originfile + ".patch"))
        if patchfile not in patchfiles:
          patchfiles[patchfile] = list()
        for jsonpath in jsonpaths:
          specialpaths = ["glitchEmote", "glitchEmotedText"]
          jsonpathend = basename(jsonpath)
          if jsonpathend in specialpaths:
            if patchfile not in specials:
              specials[patchfile] = dict()
            specials[patchfile][jsonpath] = translation
            specialpaths.remove(jsonpathend)
            basepath = dirname(jsonpath)
            restpath = join(basepath, specialpaths.pop())
            if  restpath in specials[patchfile]:
              emotepath = join(basepath, "glitchEmote")
              textpath = join(basepath, "glitchEmotedText")
              emote = specials[patchfile][emotepath]
              text = specials[patchfile][textpath]
              command = dict()
              command["op"] = "replace"
              command["value"] = emote + " " + text
              command["path"] = basepath
              patchfiles[patchfile].append(command)
          else:
            command = dict()
            command["op"] = "replace"
            command["value"] = translation
            command["path"] = jsonpath
            patchfiles[patchfile].append(command)
              

for pfile, content in patchfiles.items():
  makedirs(dirname(pfile), exist_ok = True)
  with open(pfile, "w") as f:
    dump(content, f, ensure_ascii=False, indent = 2)

labelsTranslatedN = 0
labelsTotalN = 0



labelsTotalN = sum_up_counter(labelsTotal)
labelsTranslatedN = sum_up_counter(labelsTranslated)

  
with open(join(translations_dir, "translatedlabels.json"), "w") as f:
  dump(labelsTranslated, f, indent = 2, sort_keys=True)
with open(join(translations_dir, "totallabels.json"), "w") as f:
  dump(labelsTotal, f, indent = 2, sort_keys=True)

print("Statistics:")
print("Translated labels: " + str(labelsTranslatedN))
print("Summary labels: " + str(labelsTotalN))
print("Completion: " + str(labelsTranslatedN*100/labelsTotalN) + "%")
