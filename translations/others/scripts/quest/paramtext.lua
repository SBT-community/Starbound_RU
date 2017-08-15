function itemShortDescription(itemDescriptor)
  return root.itemConfig(itemDescriptor).config.shortdescription or itemDescriptor.name
end

function questParameterText(paramValue)
  if paramValue.name then return paramValue.name end

  if paramValue.type == "item" then
    return itemShortDescription(paramValue.item)

  elseif paramValue.type == "itemList" then
    local listString = ""
    for _,item in ipairs(paramValue.items) do
      if listString ~= "" then
        listString = listString .. ", "
      end
      listString = listString .. string.format("%s %s", item.count, itemShortDescription(item))
    end
    return listString
  end
end

function questParameterTags(parameters)
  return util.map(parameters, questParameterText)
end
