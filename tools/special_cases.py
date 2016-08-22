
from re import compile as regex

def matches(patts, filename):
  for p in patts:
    if not p.match(filename) is None:
      return True
  return False

class SpecialSection():

  def __init__(self, name, pathPatterns, filePatterns, all_conditions = False):
    self.name = name
    self.allcond = all_conditions
    self.fpat = []
    self.ppat = []
    for pat in filePatterns:
      self.fpat.append(regex(pat))
    for pat in pathPatterns:
      self.ppat.append(regex(pat))

  def match(self, filename, path):
    fmatch = matches(self.fpat, filename)
    if fmatch and not self.allcond:
      return True
    pmatch = matches(self.ppat, path)
    if pmatch and (fmatch or not self.allcond):
      return True
    return False

specialSections = [
  SpecialSection("npcnames", [], ["^.*namegen\.config$", "^.*\.namesource$"])
]
