local defaultformdetector = {
  {match = {"емена.*"}, form = "plural"},
  {match = {"ие%s.+", "ые%s.+"}, form = "plural", subform = "normal"},
  {match = {"ое%s.+", "ее%s.+"}, form = "neutral", subform = "normal"},
  {match = {"емя.*", "o"}, form = "neutral"},
  {match = {"ая%s.+", "яя%s.+", "ья%s.+"},form = "female", subform = "normal"},
  {match = {"й%s.+", "е%s.+"}, subform = "normal"},
  {match = {".%s.+"}, subform = "of"},
  {match = {"и", "ы"}, form = "plural"},
  {match = {"а", "я", "сть"}, form = "female"},
  {match = {"."}, form = "male", subform = "normal"},
}

local function newSub(match, subtable)
  return {match = type(match) == "string" and {match} or match,
    sub = setmetatable(subtable, {__index = function(t,k)
      if k == "any" then return end
      if t.any then return t.any end
      if k == "neutral" and t.male then return t.male end
      return "%0"
    end})
  }
end

local consonants = {"ц", "к", "н", "ш", "щ", "з", "х", "ф", "в", "п",
                    "р", "л", "д", "ж", "ч", "с", "м", "т", "г", "б"}


local cases = {
  dative = {
    any = {
      newSub("ень", {male = "ню"}),
      newSub("ия", {male = "ие", female = "ии"}),
      newSub("([иы])е", {plural = "%1м"}),
      newSub({"(г)и", "(к)и"}, {plural = "%1ам:guard:"}),
      newSub("ь", {male = "ю", female = "и"}),
      newSub({"а", "я"}, {any = "е", neutral = "ени", plural = "%0м"}),
      newSub("ы", {plural = "ам"}),
      newSub("и", {plural = "ям"}),
      newSub("й", {male = "ю"}),
      newSub(consonants, {male = "%0у"}),
      nonstop = false,
    },
    glitch = {
      newSub({"ый(.*)", "ой(.*)", "ое(.*)"}, {any = "ому%1", female = "%0"}),
      newSub({"(к)ий(.*)", "(г)ий(.*)"}, {male = "%1ому%2"}),
      newSub("ий(.*)", {male = "ему%1"}),
      newSub("ая(.*)", {female = "ой%1"}),
      newSub({"яя(.*)", "ья(.*)"}, {female = "ей%1"}),
      newSub({"ок", "ек"}, {any = "ку"}),
      newSub({"е", "о"}, {plural = "м", any = "у"}),
      nonstop = true,
    },
    item = {
      additional = {"glitch", "any"},
      nonstop = false
    }
  },
  accusative = {
    any = {
      newSub("ень", {male = "ня"}),
      newSub({"(г)и", "(к)и"}, {plural = "%1ов:guard:"}),
      newSub("аи", {plural = "аев"}),
      newSub("а", {any = "у"}),
      newSub("я", {any = "ю"}),
      newSub("е", {plural = "х"}),
      newSub("и", {plural = "ей"}),
      newSub("ы", {plural = "ов"}),
      newSub("й", {male = "я"}),
      newSub("ь", {male = "я"}),
      newSub(consonants, {male = "%0а"}),
      nonstop = false,
    },
    glitch = {
      newSub({"(к)ий(.+)", "(г)ий(.+)"}, {male = "%1ого%2"}),
      newSub({"ый(.+)", "ой(.+)", "oe(.*)"}, {any = "ого%1", female = "%0"}),
      newSub("ий(.+)", {male = "его%1"}),
      newSub({"ок", "ек"}, {male = "ка:guard:"}),
      -- :guard: notation will be removed automatically at the end of processing
      -- it is necessary to prevent changing this ending
      additional = {"item", "any"},
      nonstop = true,
    },
    item = {
      additional = {},
      nonstop = false,
      newSub("ая(.*)", {female = "ую%1"}),
      newSub("яя(.*)", {female = "юю%1"}),
      newSub("ья(.*)", {female = "ью%1"}),
      newSub("а", {female = "у"}),
      newSub("я", {female = "ю"}),
    },
  },
}


local function iterateRules(rules, matcher)
  assert(type(rules) == "table")
  assert(type(matcher) == "function")
  for i = 1, #rules do
    for _, match in pairs(rules[i].match) do
      local result = matcher(match, rules[i], rules.nonstop)
      if result then
        return result
      end
    end
  end
end

function detectForm(phrase, customformdetector)
  -- Detects form of given phrase using supplied formdetector table.
  -- Returns 3 values:
  -- 1. detected form
  -- 2. mutable part of phrase
  -- 3. immutable part of phase
  -- If formdetector is not supplied, it uses default form detector
  local detector = customformdetector or defaultformdetector
  local form, subform
  local head, tail = phrase, ""
  local matcher = function(pat, rule)
    if head:match(pat.."$") then
      form = form or rule.form
      if not subform then
        if rule.subform == "of" then
          head, tail = head:match("^(.-)(%s.+)$")
        end
        subform = rule.subform
     end
    end
    if form and subform then return form end
  end
  local resultform = iterateRules(detector, matcher)
  return resultform, head, tail
end

local function matchName(name, gender, rules)
  local remove_guards = {
    nonstop = true,
    newSub(":guard:(.*)", {any = "%1"}),
  }
  local act = function(pat, rule, nonstop)
    local result, count = name:gsub(pat.."$", rule.sub[gender])
    if count > 0 then
    if nonstop then name = result return
    else return result end end
  end
  name = iterateRules(rules, act) or name
  name = iterateRules(remove_guards, act) or name
  return name
end

local function matchTable(phrase, mtable)
  -- Converts given phrase according to mtable.
  -- If phrase is string and does not contains any form informations
  -- the function is trying to detect form via detectForm function
  local rules = mtable[phrase.species] or {}
  for _, v in pairs(rules.additional or {"any"}) do
    for k, vv in pairs(mtable[v] or {}) do
      if type(k) == 'number' then table.insert(rules, vv) end
    end
  end
  local tokens = {}
    for n in phrase.name:gmatch("%S+") do
      table.insert(tokens, matchName(n, phrase.gender, rules))
    end
  return table.concat(tokens, ' ')
end

function decline(phrase, case)
  assert(type(phrase) == "table")
  -- phrase = {name, gender, species}
  assert(type(case) == "table")
  -- For dash separated words like "Самураи-отступники"
  -- each part of the word will be conjugated separately.
  -- It does not affect adjectives (no spaces allowed after dash)
  local part1, part2 = phrase.name:match("^([^%-]+)(%-[^%s%-]+)$")
  if part2 then
    local secondphrase = phrase
    secondphrase.name = part2
    phrase.name = part1
    part2 = matchTable(secondphrase, case)
  end
  return matchTable(phrase, case)..(part2 or "")
end

function injectDecliners(action)
  -- Calls `action` with two arguments:
  --   1. case name
  --   2. case decliner function which expects one argument - phrase object to
  --      decline
  assert(type(action) == "function")
  action("", function(p) return p.name end) -- nominative case without changes
  for name, case in pairs(cases) do
    action("."..name, function(p) return decline(p, case) end)
  end
end
