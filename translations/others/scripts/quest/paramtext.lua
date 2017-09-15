function itemShortDescription(itemDescriptor)
  return root.itemConfig(itemDescriptor).config.shortdescription or itemDescriptor.name
end

local function getCountEnding(count)
  local residue = count % 10
  if count > 10 and count < 21 then return ""
  elseif resudue == 1 then return "а"
  elseif residue > 1 and residue < 5 then return "и"
  else return "" end
end

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

local function matchTable(object, mtable)
  local plain = type(object) == "string"
  local name = plain and object or object.name
  if not plain then
    mtable.remove_guards = {
      nonstop = true,
      newSub(":guard:(.*)", {any = "%1"}),
    }
    local gender = object.gender or "plural"
    local rules = mtable[object.species] or {}
    local act = function(pat, rule, nonstop)
      local result, count = name:gsub(pat.."$", rule.sub[gender])
      if count > 0 then
      if nonstop then name = result return
      else return result end end
    end
    local additionals = rules.additional or {"any"}
    table.insert(additionals, "remove_guards")
    name = iterateRules(rules, act) or name
    for i, e in pairs(additionals) do
      name = iterateRules(mtable[e] or {}, act) or name
    end
    return name
  elseif mtable.item and mtable.item.formdetector then
    local rules = mtable.item
    local form, subform
    local tailname = ""
    local matcher = function(pat, rule)
      if name:match(pat.."$") then
        form = form or rule.form
        if not subform then
          if rule.subform == "of" then
            name, tailname = name:match("^(.-)(%s.+)$")
          end
          subform = rule.subform
       end
      end
      if form and subform then return form end
    end
    local newobj = {
      gender = iterateRules(rules.formdetector, matcher),
      species = "item",
    }
    newobj.name = name
    return matchTable(newobj, mtable)..tailname
  end
  return name
end

local formdetector = {
  {match = {"емена.*"}, form = "plural"},
  {match = {"ие%s.+", "ые%s.+"}, form = "plural", subform = "normal"},
  {match = {"ое%s.+", "ее%s.+"}, form = "neutral", subform = "normal"},
  {match = {"емя.*", "o"}, form = "neutral"},
  {match = {"ая%s.+", "яя%s.+"},form = "female", subform = "normal"},
  {match = {"й%s.+", "е%s.+"}, subform = "normal"},
  {match = {".%s.+"}, subform = "of"},
  {match = {"и", "ы"}, form = "plural"},
  {match = {"а", "я", "сть"}, form = "female"},
  {match = {"."}, form = "male", subform = "normal"},
}
local consonants = {"ц", "к", "н", "ш", "щ", "з", "х", "ф", "в", "п",
                    "р", "л", "д", "ж", "ч", "с", "м", "т", "б"}

local function convertToObjective(object)
  local variants = {
    any = {
      newSub("й", {male = "ю"}),
      newSub("ия", {male = "ие", female = "ии"}),
      newSub("ень", {male = "ню"}),
      newSub("ь", {male = "ю", female = "и"}),
      newSub({"а", "я"}, {any = "е", neutral = "ени", plural = "%0м"}),
      newSub("ы", {plural = "ам"}),
      newSub({"(г)и", "(к)и"}, {plural = "%1ам:guard:"}),
      newSub("и", {plural = "ям"}),
      newSub("е(%s.+)", {plural = "м%1"}),
      newSub(consonants, {male = "%0у"}),
      nonstop = true,
    },
    glitch = {
      newSub({"ый(.+)", "ой(.+)", "ое(.*)"}, {any = "ому%1", female = "%0"}),
      newSub({"(к)ий(.+)", "(г)ий(.+)"}, {male = "%1ому%2"}),
      newSub("ий(.+)", {male = "ему%1"}),
      newSub("ая(.+)", {female = "ой%1"}),
      newSub("яя(.+)", {female = "ей%1"}),
      newSub({"е", "о"}, {any = "у"}),
      newSub({"ок", "ек"}, {any = "ку"}),
      nonstop = true,
    },
    item = {
      formdetector = formdetector,
      additional = {"glitch", "any"},
    }
  }
  return matchTable(object, variants)
end

local function convertToReflexive(object)
  local variants = {
    any = {
      newSub("а", {any = "у"}),
      newSub("я", {any = "ю"}),
      newSub("е(%s.+)", {plural = "х%1"}),
      newSub({"(г)и", "(к)и"}, {plural = "%1ов:guard:"}),
      newSub("и", {plural = "ей"}),
      newSub("ы", {plural = "ов"}),
      newSub("й", {male = "я"}),
      newSub("ень", {male = "ня"}),
      newSub("ь", {male = "я"}),
      newSub(consonants, {male = "%0а"}),
      nonstop = true,
    },
    glitch = {
      newSub({"ый(.+)", "ой(.+)", "oe(.*)"}, {any = "ого%1", female = "%0"}),
      newSub({"(к)ий(.+)", "(г)ий(.+)"}, {male = "%1ого%2"}),
      newSub("ий(.+)", {male = "его%1"}),
      newSub({"ок", "ек"}, {male = "ка:guard:"}),
      -- :guard: notation will be removed automatically at the end of processing
      -- it is necessary to prevent changing this ending
      additional = {"any", "item"},
      nonstop = true,
    },
    item = {
      formdetector = formdetector,
      additional = {},
      nonstop = true,
      newSub("ая(.+)", {female = "ую%1"}),
      newSub("яя(.+)", {female = "юю%1"}),
      newSub("а", {female = "у"}),
      newSub("я", {female = "ю"}),
    },
  }
  return matchTable(object, variants)
end

function questParameterText(paramValue, caseModifier)
  caseModifier = caseModifier or
    function(a) return type(a) == "string" and a or a.name end
  if paramValue.name then
    return caseModifier(paramValue)
  end

  if paramValue.type == "item" then
    return caseModifier(itemShortDescription(paramValue.item))
  elseif paramValue.type == "itemList" then
    local listString = ""
    local count = 0
    for _,item in ipairs(paramValue.items) do
      if listString ~= "" then
        if count > 1 then
          listString = "; " .. listString
        else
          listString = " и " .. listString
        end
      end
      local description = caseModifier(itemShortDescription(item))
      if item.count > 1 then
        local thingEnd = getCountEnding(item.count)
        listString = string.format("%s, %s штук%s", description, item.count,
                                   thingEnd) .. listString
      else
        listString = description .. listString
      end
      count = count + 1
    end
    return listString
  end
end

function questParameterTags(parameters)
  local result = {}
  for k, v in pairs(parameters) do
    result[k] = questParameterText(v)
    result[k..".reflexive"] = questParameterText(v, convertToReflexive)
    result[k..".objective"] = questParameterText(v, convertToObjective)
  end
  return result
end
