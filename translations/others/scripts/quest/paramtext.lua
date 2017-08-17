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

function questParameterText(paramValue)
  if paramValue.name then return paramValue.name end

  if paramValue.type == "item" then
    return itemShortDescription(paramValue.item)

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
      if item.count > 1 then
        local thingEnd = getCountEnding(item.count)
        listString = string.format("%s, %s штук%s", itemShortDescription(item), item.count, thingEnd) .. listString
      else
        listString = itemShortDescription(item) .. listString
      end
      count = count + 1
    end
    return listString
  end
end

function questParameterTags(parameters)
  return util.map(parameters, questParameterText)
end
