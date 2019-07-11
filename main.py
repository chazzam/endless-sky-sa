#! /usr/bin/env python
import copy
#import json
#import math
import os
import random
import sa
import endless_sky

random.seed(5)
turning = 0 # set a max cap on turning
iterations = 50000 # Seems to get mostly the same answer at 5k as 10k, but did find a new one at 50k
# Configure ship parameters, remaining: outfit space, engine capacity, energy; current mass
ship = {
  "outfit space": 0, 
  "engine capacity": 210,
  "mass": 940,
  #"heat dissipation": .4,
  "energy": 0,
}
dir_endless_sky_data = "../endless-sky/data/"

# walk data files to find engines
engines = []
for (dirpath, dirnames, filenames) in os.walk(dir_endless_sky_data):
  for f in filenames:
    # ~ try:
      engines.extend(endless_sky.read_file(
        os.path.join(dirpath, f),
        accept={"category":"Engines"}))
    # ~ except Exception as ex:
      # ~ print(f"ERROR reading {dirpath}/{f}")
      # ~ print(ex)
if len(engines) == 0:
  engines = [
    # name: outfit space, engine capacity, thrust, thrusting heat, 
    {
      "name": "X1050 Ion Engines",
      "outfit space": -20,
      "engine capacity": -20,
      "thrust": 4.0,
      "thrusting energy": .4,
      "thrusting heat": .6,
      "turn": 110,
      "turning energy": .25,
      "turning heat": .5,
      "mass": 20},
    {
      "name": "Greyhound Plasma Thruster",
      "outfit space": -34,
      "engine capacity": -34,
      "thrust": 18.4,
      "thrusting energy": 1.8,
      "thrusting heat": 3.4,
      "turn": 0,
      "turning energy": 0,
      "turning heat": 0,
      "mass": 34},
    {
      "name": "A520 Atomic Thruster",
      "outfit space": -82,
      "engine capacity": -82,
      "thrust": 81.9,
      "thrusting energy": 8.3,
      "thrusting heat": 17.4,
      "turn": 0,
      "turning energy": 0,
      "turning heat": 0,
      "mass": 82},
    {
      "name": "X3700 Ion Thruster",
      "outfit space": -46,
      "engine capacity": -46,
      "thrust": 22.1,
      "thrusting energy": 1.9,
      "thrusting heat": 3.2,
      "turn": 0,
      "turning energy": 0,
      "turning heat": 0,
      "mass": 46},
  ]
else:
  # Have engines, need to filter and correct the list
  for i in reversed(range(0, len(engines))):
    if (
           "category" not in engines[i] 
        or engines[i]["category"] != "Engines"):
      del engines[i]
      continue
    if "thrust" not in engines[i]:
      engines[i]["thrust"] = 0
      engines[i]["thrusting energy"] = 0
      engines[i]["thrusting heat"] = 0
    if "turn" not in engines[i]:
      engines[i]["turn"] = 0
      engines[i]["turning energy"] = 0
      engines[i]["turning heat"] = 0
    if engines[i]["thrust"] == 0 and engines[i]["turn"] == 0:
      del engines[i]
    
state = {
  #"ship": copy.deepcopy(ship), # not necessary for simple dict
  "ship": ship.copy(),
  "ship_current": {},
  "desired_turn": turning,
  "engines": [],
  "sa_energy": 0.0,
  "valid": True
}
# ~ for engine in sorted(engines, key=lambda x: x["NAME"]):
  # ~ print(f"""{engine['NAME']: <30}:: size:{engine['engine capacity']:>4}
    # ~ thrust:{engine['thrust']},{engine['thrusting heat']},{engine['thrusting energy']}
    # ~ turn:{engine['turn']},{engine['turning heat']},{engine['turning energy']}""")
print("Working with {} engines\n".format(len(engines)))
print("Initial state")
sa.print_state(state, current=True)

eg_thrust=50; eg_turn=10; eg_heat=10; eg_capacity=20; eg_mass=20
print(f"Trial th{eg_thrust},tn{eg_turn},h{eg_heat},c{eg_capacity},m{eg_mass}:")
sa.print_state(sa.anneal(copy.deepcopy(state), iterations, engines,
    eg_thrust, eg_turn, eg_heat, eg_capacity, eg_mass, verbose=False))

eg_thrust=30; eg_turn=15; eg_heat=20; eg_capacity=5; eg_mass=20
print(f"Trial th{eg_thrust},tn{eg_turn},h{eg_heat},c{eg_capacity},m{eg_mass}:")
sa.print_state(sa.anneal(copy.deepcopy(state), iterations, engines,
    eg_thrust, eg_turn, eg_heat, eg_capacity, eg_mass, verbose=False))

eg_thrust=50; eg_turn=40; eg_heat=10; eg_capacity=20; eg_mass=20
print(f"Trial th{eg_thrust},tn{eg_turn},h{eg_heat},c{eg_capacity},m{eg_mass}:")
sa.print_state(sa.anneal(copy.deepcopy(state), iterations, engines,
    eg_thrust, eg_turn, eg_heat, eg_capacity, eg_mass, verbose=False))

eg_thrust=50; eg_turn=40; eg_heat=1; eg_capacity=1; eg_mass=1
print(f"Trial th{eg_thrust},tn{eg_turn},h{eg_heat},c{eg_capacity},m{eg_mass}:")
sa.print_state(sa.anneal(copy.deepcopy(state), iterations, engines,
    eg_thrust, eg_turn, eg_heat, eg_capacity, eg_mass, verbose=False))

#res = pick_engine(engines[:], ship.copy(), turning)
#print(json.dumps(res, indent=2))
  
# ~ print("\n\n\ntake two, pre-seeding with highest thrust\n")
# ~ sorted_thrust = sorted(engines, reverse=True,
  # ~ key=lambda eng: eng["thrust"])
# ~ #res = pick_engine(engines[:], ship.copy(), turning, [sorted_thrust[1]])
# ~ #print(json.dumps(res, indent=2))

# ~ state2 = copy.deepcopy(state)
# ~ state2["engines"].append(sorted_thrust[0])
# ~ state2["engines"].append(sorted_thrust[0])
# ~ state2 = sa.anneal(state2, iterations, engines)
# ~ print("\n\nBest State2:")
# ~ sa.print_state(state2)

# ~ print("\n\n\ntake three, pre-seeding with highest turn\n")
# ~ sorted_turn = sorted(engines, reverse=True,
  # ~ key=lambda eng: eng["turn"])
# ~ state3 = copy.deepcopy(state)
# ~ state3["engines"].append(sorted_turn[0])
# ~ state3["engines"].append(sorted_turn[0])
# ~ state3["engines"].append(sorted_turn[0])
# ~ state3 = sa.anneal(state3, iterations, engines)
# ~ print("\n\nBest State3:")
# ~ sa.print_state(state3)
