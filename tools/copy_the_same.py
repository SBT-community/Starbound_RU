#!/bin/python3
from json import load, dump
from copy import deepcopy
import argparse

def parse_arguments():
  parser = argparse.ArgumentParser(
                   description="Copy translations from other db.")
  parser.add_argument('--from-file', help='source json files',
                      metavar='FILE', action="append",
                      type=argparse.FileType('r'))
  parser.add_argument('destination', nargs='+', help='target json files',
                      type=argparse.FileType('r+'))
  return parser.parse_args()

def create_the_base(files):
  result = dict()
  for f in files:
    jsonfile = load(f)
    for entry in jsonfile:
      translations = entry["Texts"]
      if "Rus" in translations and len(translations["Rus"]) > 0:
        eng = translations["Eng"]
        if eng in result:
          print("Translations conflict while reading inputs!")
          print("Original: " + eng)
          print("First: " + translations["Rus"])
          print("Second: " + result[eng])
          print("Autoselecting second for a while... FIXME")
        else:
          result[eng] = translations["Rus"]
  return result

def merge_the_base(base, files):
  for f in files:
    newjson = list()
    jsonfile = load(f)
    for entry in jsonfile:
      newentry = deepcopy(entry)
      eng = entry["Texts"]["Eng"]
      if eng in base and ("Rus" not in entry["Texts"] or
                          len(entry["Texts"]["Rus"]) == 0):
        newentry["Texts"]["Rus"] = base[eng]
      newjson += [newentry]
    f.seek(0)
    f.truncate()
    dump(newjson, f, ensure_ascii=False, indent=2, sort_keys=True)

if __name__ == "__main__":
  arguments = parse_arguments()
  base = create_the_base(arguments.from_file)
  merge_the_base(base, arguments.destination)

