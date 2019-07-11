import copy

def _try_type_convert(raw):
  if raw is None:
    return raw
  if isinstance(raw, list):
    return [_single_types_convert(x) for x in raw]
  return _single_types_convert(raw)

def _single_types_convert(raw):
  # Try to get this value as a float or int
  # Otherwise return it unchanged
  for trial_type in [float, int]:
    (result, value) = _single_type_convert(raw, trial_type)
    if result:
      return value
  return raw

def _single_type_convert(raw, trial_type):
  try:
    final = trial_type(raw)
    if (
          str(final) == raw 
        or f"{final}" == raw.rstrip('0') # Handle trailing 0 being dropped
        or f"{final}" == raw.strip('0') # Handle leading and/or trailing 0 drop
        or f"{raw}0" == str(final) # single trailing 0 on floats
        or f"0{raw}" == str(final)): # leading 0 on floats
      # Handle random incomplete floats
      return (True, final)
  except:
    pass
  return (False, raw)

def _separate_entry(line):
  parts = [x.strip() for x in line.split('"') if x.strip() != '']
  if line.count('"') > 0 and len(parts) == 1:
    # Check for a flag value
    parts.append("True")
  elif len(parts) == 1:
    parts = line.strip().split()
  return parts

def read_file(filename, accept={}):
  entries = []
  with open(filename, "r") as infile:
    line = "start"
    on_entry = False
    entry = {}
    last_key = ""
    indent = -1
    while line:
      line = infile.readline()
      if line.strip().startswith("#"):
        continue
      if len(line.strip()) == 0:
        on_entry = False
        continue
      #import pdb;pdb.set_trace()
      if indent == -1:
        indent = len(line) - len(line.lstrip())
      line_indent = len(line) - len(line.lstrip())

      if line_indent == 0:
        parts = _separate_entry(line)
        if len(parts) < 2:
          continue
        # Update on_entry and reset indent
        on_entry = True
        indent = -1
        last_key = ""
        # Save any built-up entry
        if len(entry) > 0:
          # If all accept pairs are present, add to list
          for key in accept:
            if key not in entry or entry[key] != accept[key]:
              break
          else:
            entries.append(copy.deepcopy(entry))
          entry = dict()
        entry = {
          "NAME": parts[1],
          "TYPE": parts[0]
        }
        continue
      if not on_entry:
        continue
      parts = _separate_entry(line)
      if len(parts) < 1: 
        #print(f"ERROR parsing {line}")
        continue
      key = parts[0].strip()
      # ~ import pdb;pdb.set_trace()
      if last_key == "":
        last_key = key
      value = ""
      if len(parts) > 2:
        value = [x.strip() for x in parts[1:]]
      elif len(parts) == 1:
        value = {}
      else:
        value = parts[1].strip()
      # ~ print(f"DEBUG: last:{last_key} now:{key}={value} all:{entry}")
      if line_indent > indent:
        # Handle this happening on very first key...
        last_val = value
        if last_key in entry:
          last_val = entry[last_key]
        # update last key, and make this a child
        if not isinstance(last_val, dict):
          entry[last_key] = {last_key: last_val}
        entry[last_key][key] = _try_type_convert(value)
        # Reset key to track entries properly
        key = last_key
      elif key in entry:
        # Convert the value to a list
        last_val = entry[key]
        if not isinstance(last_val, list):
          entry[key] = [last_val]
        entry[key].append(value)
      else:
        entry[key] = _try_type_convert(value)
      last_key = key
  return entries
