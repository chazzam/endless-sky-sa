import copy
import math
import random

def _analyze(state, highs, eg_thrust=50, eg_turn=20, eg_heat=10, eg_capacity=20, eg_mass=10):
  valid = True
  # 50 Want higher thrust
  thrust = state["ship_current"]["thrust"]
  high_thrust = max(thrust, highs["thrust weight"])
  energy = thrust / high_thrust * eg_thrust

  # 20 capacity closer to 0
  # eg_capacity being 14-16 seems like it might be more realistic results, but 10 is best for test data
  capacity = state["ship_current"]["engine capacity"]
  if capacity >= 0:
    energy += eg_capacity - (capacity / state["ship"]["engine capacity"] * eg_capacity)
  else:
    valid = False

  # Only check these validations if they are positive initially
  if state["ship"]["outfit space"] > 0 and state["ship_current"]["outfit space"] < 0:
    valid = False
  if state["ship"]["energy"] > 0:
    if state["ship_current"]["energy"]["thrust"] < 0:
      valid = False
    if state["ship_current"]["energy"]["turn"] < 0:
      valid = False

  # 10 turn closer to turning, but capped at turning
  turn = state["ship_current"]["turn"]
  high_turn = highs["turn weight"]
  # If we have a cap, adjust it
  if state["desired_turn"] > 0:
    high_turn = state["desired_turn"]
  # If we would go greater than our contribution, max out
  high_turn = max(turn, high_turn)
  energy += turn / high_turn * eg_turn

  # 10 mass closer to 0?
  mass = state["ship_current"]["mass"]
  if mass >= 0 and state["ship"]["mass"] > 0:
    energy += eg_mass - (mass / state["ship"]["mass"] * eg_mass)

  # 10 heat closer to 0?
  thrust_heat = state["ship_current"]["heat"]["thrust"]
  thrust_heat_high = max(thrust_heat, highs["thrust heat"])
  if thrust_heat > 0:
    energy += eg_heat - (thrust_heat / thrust_heat_high * eg_heat)

  turn_heat = state["ship_current"]["heat"]["turn"]
  turn_heat_high = max(turn_heat, highs["turn heat"])
  if turn_heat > 0:
    energy += eg_heat - (turn_heat / turn_heat_high * eg_heat)

  return (energy, valid)

def _ship_state(state):
  energy = max(0, state["ship"]["energy"])
  space = max(0, state["ship"]["outfit space"])
  mass = max(0, state["ship"]["mass"])
  status = {
      "energy": {
        "thrust": energy,
        "turn": energy},
      "heat": {
        "thrust": 0,
        "turn": 0},
      "thrust": 0,
      "turn": 0,
      "engine capacity": state["ship"]["engine capacity"],
      "outfit space": space,
      "mass": mass}
  for engine in state["engines"]:
      try:
        status["energy"]["thrust"] -= abs(engine["thrusting energy"])
        status["energy"]["turn"] -= abs(engine["turning energy"])
        status["engine capacity"] -= abs(engine["engine capacity"])
        status["outfit space"] -= abs(engine["outfit space"])
        status["heat"]["thrust"] += abs(engine["thrusting heat"])
        status["heat"]["turn"] += abs(engine["turning heat"])
        status["mass"] += abs(engine["mass"])
        status["turn"] += abs(engine["turn"])
        status["thrust"] += abs(engine["thrust"])
      except Exception as ex:
          print(f"failed accumulating {engine['NAME']}:\n{ex}\n{engine}")
  return status

def _neighbor(state, all_engines):
  # Pick either highest thrust, highest turn, or random
  # Can also remove the last engine
  state_new = copy.deepcopy(state)
  num_engines = len(state_new["engines"])

  # Remove an engine?
  removal = random.randint(1, 4)
  while removal > 0:
    if num_engines == 0:
      break
    # The order of adding engines doesn't matter for neighbors, so always remove at random
    # Remove 0-2 engines
    if  removal >= 3:
      rem = random.randint(0, num_engines - 1)
      del state_new["engines"][rem]
      state_new["ship_current"] = _ship_state(state_new)
      num_engines = len(state_new["engines"])
      #print("removing engines")
    removal -= 1

  capacity = state_new["ship_current"]["engine capacity"]

  filtered = [x for x in all_engines if abs(x["engine capacity"]) < capacity ]

  if len(filtered) == 0:
    return state_new
  sorted_capacity = sorted(filtered, reverse=True,
    key=lambda eng: abs(eng["engine capacity"]))
  sorted_thrust = sorted(sorted_capacity, reverse=True,
    key=lambda eng: eng["thrust"])
  sorted_turn = sorted(sorted_capacity, reverse=True,
    key=lambda eng: eng["turn"])

  # Add an engine
  choice = random.randint(1,3)
  #print("move choice:{}".format(choice))
  if choice == 1:
    # Highest Turn
    state_new["engines"].append(sorted_turn[0])
  elif choice == 2:
    # random by capacity
    index = random.randint(0, len(sorted_capacity) - 1)
    state_new["engines"].append(sorted_capacity[index])
  else:
    # Highest Thrust
    state_new["engines"].append(sorted_thrust[0])

  state_new["ship_current"] = _ship_state(state_new)
  return state_new

def _prob_func(old, new, temperature):
  delta = new["sa_energy"] - old["sa_energy"]
  #print("prob_func delta: {}".format(delta))
  prob = 0.0
  if delta > 0.0:
    prob = math.exp(-delta/temperature)
    #print("probability: {}".format(prob))
  return (prob, delta)

def anneal(
    state, iterations, engines,
    eg_thrust=50, eg_turn=20, eg_heat=10, eg_capacity=20, eg_mass=10,
    verbose=True):
  max_temp = 25000
  min_temp = 2.5
  temp_factor = -math.log(max_temp / min_temp)
  sums = {}
  ratios = {
    "thrust": 0,
    "thrusting heat": 0,
    "turn": 0,
    "turning heat": 0}
  for engine in engines:
    ratio = lambda x: x / abs(engine["engine capacity"])
    # Ratios
    ratios["thrust"] = max(ratio(engine["thrust"]), ratios["thrust"])
    ratios["thrusting heat"] = max(ratio(engine["thrusting heat"]), ratios["thrusting heat"])
    ratios["turn"] = max(ratio(engine["turn"]), ratios["turn"])
    ratios["turning heat"] = max(ratio(engine["turning heat"]), ratios["turning heat"])
    for k,v in engine.items():
      if not isinstance(v, int) and not isinstance(v, float):
        continue
      if k not in sums:
        sums[k] = 0
        ratios[k] = abs(v)
      sums[k] += abs(v)
      ratios[k] = max(abs(v), ratios[k])
  high = lambda x: x * state["ship"]["engine capacity"]
  highs = {
    "thrust heat": high(ratios["thrusting heat"]),
    "turn heat": high(ratios["turning heat"]),
    "thrust weight": high(ratios["thrust"]),
    # ~ "turn weight": high(ratios["turn"]) / 3,
    "turn weight": high(ratios["turn"]),
  }
  state["ship_current"] = _ship_state(state)
  (state["sa_energy"], is_valid) = _analyze(
    state, highs, eg_thrust, eg_turn, eg_heat, eg_capacity, eg_mass)
  if verbose:
    print_state(state)
  best_state = copy.deepcopy(state)

  prev_state = copy.deepcopy(state)
  rejects = 0
  for i in range(1, iterations + 1):
    temp = max_temp * math.exp(temp_factor * i / iterations)
    #print("for {}/{} using temp:{}".format(i,iterations,temp))
    # Try to generate a valid neighbor
    for j in range(0, 10):
      state = _neighbor(state, engines)
      (state["sa_energy"], is_valid) = _analyze(
        state, highs, eg_thrust, eg_turn, eg_heat, eg_capacity, eg_mass)
      if is_valid:
        #print("got good neighbor")
        break
    (prob, delta) = _prob_func(prev_state, state, temp)
    #print_state(state)
    if delta > 0.0 and prob < random.uniform(0, 1):
      #print("rejecting state")
      rejects += 1
      state = copy.deepcopy(prev_state)
      if rejects > 11:
        # Reset to best state if we've failed a bunch
        rejects = 0
        state = copy.deepcopy(best_state)
    else:
      #print("accepting state")
      prev_state = copy.deepcopy(state)
      if state["sa_energy"] > best_state["sa_energy"]:
        best_state = copy.deepcopy(state)
        if verbose:
          print("new best state!")
          print_state(best_state)
  return best_state

def print_state(state, current=False):
  if current:
    state["ship_current"] = _ship_state(state)
    state["sa_energy"] = 0.0

  thrust_energy = state["ship"]["energy"] - state["ship_current"]["energy"]["thrust"]
  turn_energy = state["ship"]["energy"] - state["ship_current"]["energy"]["turn"]
  print("""E={e:.4f}, mass:{m} energy:{en} Remaining (Capacity: {c}, Space: {os})
  Thrust: ({t:.2f}, heat:+{th:.2f}, energy:-{te:.2f}) Th+Tn Energy:-{tne:.2f}
  Turn  : ({n:.2f}, heat:+{nh:.2f}, energy:-{ne:.2f}) Th+Tn Heat:+{tnh:.2f}
  Engines: {s}\n""". format(
    e=state["sa_energy"],
    en=state["ship"]["energy"],
    c=state["ship_current"]["engine capacity"],
    os=state["ship_current"]["outfit space"],
    t=state["ship_current"]["thrust"],
    th=state["ship_current"]["heat"]["thrust"],
    nh=state["ship_current"]["heat"]["turn"],
    tnh=abs(state["ship_current"]["heat"]["thrust"]) + abs(state["ship_current"]["heat"]["turn"]),
    te=thrust_energy,
    ne=turn_energy,
    tne=abs(thrust_energy) + abs(turn_energy),
    m=state["ship_current"]["mass"],
    n=state["ship_current"]["turn"],
    s=", ".join([x["NAME"] for x in state["engines"]])
  ))
