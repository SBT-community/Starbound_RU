require('/scripts/quest/declension.lua')
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

local function concatList(itemList)
  local listString = ""
  local count = 0
  for item, itemCount in pairs(itemList) do
    if listString ~= "" then
      if count > 1 then  listString = "; " .. listString
      else listString = " и " .. listString end
    end
    if itemCount > 1 then
      local thingEnd = getCountEnding(itemCount)
      listString = string.format("%s, %s штук%s", item, itemCount, thingEnd)
                     .. listString
    else
      listString = item .. listString
    end
    count = count + 1
  end
  return listString
end

function questParameterItemListTag(paramValue, action)
  assert(paramValue.type == "itemList")
  local gender
  local count = 0
  local descriptions = setmetatable({},
    {__index = function(t,k)t[k]={} return t[k] end})
  for _,item in pairs(paramValue.items) do
    local form, mut, immut = detectForm(itemShortDescription(item))
    local phrase = {name = mut, gender = form, species = "item"}
    gender = item.count > 1 and "plural" or gender or form
    injectDecliners(function(casename, decliner)
      descriptions[casename][decliner(phrase)..immut] = item.count
    end)
    count = count + 1
  end
  for casename, items in pairs(descriptions) do
    action(casename, concatList(items))
  end
  if count > 1 then gender = "plural" end
  return gender
end

