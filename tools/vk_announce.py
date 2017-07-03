from urllib.request import urlopen
from urllib.parse import urlencode, quote
from json import dumps
from codecs import encode
from os import getenv
from subprocess import check_output

def post_n_pin(token, oid, message, link):
  ## Fallback method
  post_json = dumps({
    "owner_id": oid,
    "from_group": 1,
    "message": message,
    "signed": 0,
    "attachments": link,
    "access_token": token
  }, ensure_ascii=False)
  pin_json = dumps({
    "owner_id": oid,
    "access_token": token
  })
  vkscript = """
  var post = API.wall.post(%s);
  if (post != null && post.post_id != null) {
    var post_id = post.post_id;
    var pin_json = %s;
    pin_json.post_id = post_id;
    var result = API.wall.pin(pin_json);
    return [result, post];
  }
""" % (post_json, pin_json)
  data = urlencode({"code": vkscript,
                    "V": "5.65",
                    "access_token": token}, encoding='utf-8', quote_via=quote)
  return urlopen("https://api.vk.com/method/execute", data.encode('utf-8'))

def post_n_pin_app(token, oid, message, link):
  ## Default publication method
  data = urlencode({"owner_id": oid,
                    "message": message,
                    "link": link,
                    "access_token": token}).encode('utf-8')
  return urlopen("https://api.vk.com/method/execute.announce", data)

atoken = getenv("VK_TOKEN")
group_id = getenv("GROUP_ID")
message = check_output(["git", "log", "-1", "--pretty=%B"])

result = post_n_pin_app(atoken, group_id, message,
  "https://github.com/sbt-community/Starbound_RU/releases/latest/")

print(result.read())

