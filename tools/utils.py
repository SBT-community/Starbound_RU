from sys import stdin


def get_answer(criteria):
  ## Gets an user input matching the "criteria"
  answer = ""
  if type(criteria) is int: # if criteria is an int, it's treated as a minimal length
    while len(answer) < criteria:
      answer = stdin.readline().strip()
  elif type(criteria) is list or type(criteria) is tuple or type(criteria) is dict:
    # if criteria is a list-like type, it's treated as list of possible answer variants
    while answer not in criteria:
      answer = stdin.readline().strip()
  return answer
