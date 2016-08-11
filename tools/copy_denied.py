#!/bin/python

from os import walk
from os.path import join, relpath, normpath
from json import load, dump
from multiprocessing import Pool

oldpath = "./experimental/translations"
newpath = "./translations"

substitutions = dict()
with open(join(newpath, "substitutions.json"),"r") as f:
  substitutions = load(f)
  
filestowrite = dict()

for subdir, dirs, files in walk(oldpath):
  for thefile in files:
    if (not thefile.endswith(".json")) or thefile == "substitutions.json":
      continue
    oldfile = join(subdir, thefile)
    objlist = {}
    try:
      with open(oldfile, "r") as f:
        objlist = load(f)
    except:
      print("Cann't load: " + oldfile)
      continue
    for obj in objlist:
      if "DeniedAlternatives" not in obj:
        #print("No alternatives for: " + oldfile)
        continue
      denied = obj["DeniedAlternatives"]
      if len(denied) == 0:
        continue
      
      entext = obj["Texts"]["Eng"]
      relfiles = obj["Files"]
      for rlfile in relfiles.keys():
        #relfile = relpath(rlfile, "assets")
        relfile = rlfile
        thelist = [join("texts", relfile + ".json")]
        if relfile in substitutions:
          thelist += list(substitutions[relfile].values())
        for newfile in thelist:
          newfileobj = {}
          newfilename = normpath(join(newpath, newfile))
          if newfilename in filestowrite:
            newfileobj = filestowrite[newfilename]
          else:
            try:
              with open(newfilename, "r") as f:
                newfileobj = load(f)
            except:
              pass
              #print("Cann't read: " + newfilename)
              #raise
          
          changed = False
          for i in range(0, len(newfileobj)):
            if not (newfileobj[i]["Texts"]["Eng"] == entext):
              continue
            if "DeniedAlternatives" not in newfileobj[i]:
              newfileobj[i]["DeniedAlternatives"] = list()
            for alt in denied:
              if alt in newfileobj[i]["DeniedAlternatives"]:
                continue
              newfileobj[i]["DeniedAlternatives"].append(alt)
              changed = True
          if changed:
            filestowrite[newfilename] = newfileobj
                  
                
for newfilename, newfileobj in filestowrite.items():
  with open(newfilename, "w") as f:
    dump(newfileobj, f, ensure_ascii = False, indent = 2)
