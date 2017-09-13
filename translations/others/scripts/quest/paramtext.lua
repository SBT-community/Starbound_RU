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

local function convertNameToObjective(name, gender)
  if gender == nil then return name end
  local consonants = {"ц", "к", "н", "ш", "щ", "з", "х", "ф", "в", "п", "р",
                      "л", "д", "ж", "ч", "с", "м", "т", "б"}
  local variants = {
    [1] = {match = {"й"}, sub = {male = "ю", female = "%1"},},
    [2] = {match = {"ия"}, sub = {male = "ие", female = "ии"},},
    [3] = {match = {"ь"}, sub = {male = "ю", female = "и"},},
    [4] = {match = {"а", "я"}, sub = {male = "е", female = "е"},},
    [5] = {match = consonants, sub = {male = "%1у", female = "%1"},},
  }
  local result, count = name, 0
  for i = 1, #variants, 1 do
    for _, pat in pairs(variants[i].match) do
      result, count = name:gsub("("..pat..")$", variants[i].sub[gender])
      if count > 0 then return result end
    end
  end
  return name
end

local function convertNounAndAdjective(phrase, gender)
  if gender ~= nil then return phrase end
  local result = ""
  local isFemine = true
  for word in phrase:gmatch("%S+") do
    local gotit = 0
    local newword, count = word:gsub("ая$", "ую")
    gotit = count
    newword, count = newword:gsub("яя$", "юю")
    gotit = gotit + count
    if gotit == 0 then
      if word:match("[Сс]емена") or word:match("[Сс]емя") then newword = word
      elseif isFemine then
        newword = word:gsub("а$", "у")
        newword = newword:gsub("я$", "ю")
      else
        newword = word
      end
      isFemine = false
    else isFemine = true
    end
    if result ~= "" then result = result .. " " end
    result = result .. newword
  end
  return result
end

function questParameterText(paramValue, caseModifier)
  caseModifier = caseModifier or function(a) return a end
  if paramValue.name then
    return caseModifier(paramValue.name, paramValue.gender)
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
    result[k..".reflexive"] = questParameterText(v, convertNounAndAdjective)
    result[k..".objective"] = questParameterText(v, convertNameToObjective)
  end
  return result
end
