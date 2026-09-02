with open("src/prompt.py", "r") as f:
    prompt = f.read()

# Replace Icon definition to include allowed values
old_icon_line = '- `Icon`: Displays a material icon. Takes `name`: string.'
new_icon_line = '- `Icon`: Displays a material icon. Takes `name`: string. MUST be one of these EXACT camelCase values: "accountCircle", "add", "arrowBack", "arrowForward", "attachFile", "calendarToday", "call", "camera", "check", "close", "delete", "download", "edit", "event", "error", "fastForward", "favorite", "favoriteOff", "folder", "help", "home", "info", "locationOn", "lock", "lockOpen", "mail", "menu", "moreVert", "moreHoriz", "notificationsOff", "notifications", "pause", "payment", "person", "phone", "photo", "play", "print", "refresh", "rewind", "search", "send", "settings", "share", "shoppingCart", "skipNext", "skipPrevious", "star", "starHalf", "starOff", "stop", "upload", "visibility", "visibilityOff", "volumeDown", "volumeMute", "volumeOff", "volumeUp", "warning". NEVER use snake_case or hallucinate other icons.'

prompt = prompt.replace(old_icon_line, new_icon_line)

# Replace hallucinated icons in the example
prompt = prompt.replace('"auto_awesome"', '"star"')
prompt = prompt.replace('"thumb_up"', '"check"')

with open("src/prompt.py", "w") as f:
    f.write(prompt)
