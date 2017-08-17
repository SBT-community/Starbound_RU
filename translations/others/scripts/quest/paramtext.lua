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

local function convertNounAndAdjective(phrase)
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
  if paramValue.name then return paramValue.name end

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
  end
  return result
end
