
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
  SpecialSection("Прилагательное", [], ["^.*quests/generated/pools/guardthemes\.config$"]),
  SpecialSection("Винительный падеж", [], ["^.*quests/generated/pools/weapon\.config$"]),
  SpecialSection("Имена персонажей", [], ["^.*namegen\.config$", "^.*\.namesource$"]),
  SpecialSection("Наречие", [], ["^.*pools/hatadjectives.config$"]),
  SpecialSection("Регулярное выражение (не для перевода, а для поддержки названий на кирилице)", ["^.*/regex$"], ["^.*\.config$"], True),
  SpecialSection("Привязанное к полу прилагательное",
    ["^.*generatedText/fluff/2/.*$"],
    ["^.*quests/generated/templates/spread_rumors.questtemplate$"], True),
  SpecialSection("Предложный падеж", ["^.*generatedText/fluff/3/.*$"],
    ["^.*quests/generated/templates/escort\.questtemplate$"], True),
  SpecialSection("Предложный падеж", [".*generatedText/fluff/5/.*$"],
    ["^.*quests/generated/templates/kidnapping\.questtemplate$"], True),
  SpecialSection("Множественное число", ["^.*generatedText/fluff/3/.*$"],
    ["^.*kill_monster_group\.questtemplate$"], True),
  SpecialSection("Родительный падеж", ["^.+/name$"],
    ["^.*pools/monsterthreats\.config$"], True),
  SpecialSection("Префикс названия банды", ["^.*Prefix/.*"], ["^.*quests/bounty/gang\.config"], True),
  SpecialSection("Основная часть названия банды", ["^.*Mid/.*"], ["^.*quests/bounty/gang\.config"], True),
  SpecialSection("Окончание названия банды", ["^.*suffix/.*"], ["^.*quests/bounty/gang\.config"], True),
  SpecialSection("Префикс главаря банды", ["^.*prefix/.*"], ["^.*quests/bounty/bounty\.config"], True),
  SpecialSection("Окончание главаря банды", ["^.*suffix/.*"], ["^.*quests/bounty/bounty\.config"], True),
]
