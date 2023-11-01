import gspread
from oauth2client.service_account import ServiceAccountCredentials
from random import *
from collections import defaultdict
import pandas as pd
from sys import stderr, argv
from oauth2client.service_account import ServiceAccountCredentials
from config import CONFIG
import datetime

creds = ServiceAccountCredentials.from_json_keyfile_name(filename='credentials.json')

GROUP = argv[1]
CFG = CONFIG[GROUP]
ID = CFG['ID']

SHEET = CFG['SHEET']
banned = set()

SEED = f"{GROUP} {datetime.datetime.now().date()}"
print(f"seed = {SEED}")
seed(SEED)

print("loading sheet...")
URL = f'https://docs.google.com/spreadsheets/d/{ID}/edit#gid=0'
gc = gspread.service_account(filename='credentials.json')
gc_url = gc.open_by_url(URL)
sheet = gc_url.worksheet(SHEET)

table = pd.DataFrame(sheet.get_all_records()).fillna(0)

print("loaded sheet!")

table = table[table['№'] != '']

names = [x for x in list(table.iloc[:, 1]) if x and isinstance(x, str)]
print(f"Number of students: {len(names)}")

def get_points(student):
  if student[0] == 'test':
    return 0
  try:
    return 5 * student[1] + float(table[table['ФИО'] == student[0]]['Баллы'].iloc[0])
  except:
    print(f"unknown student: {student[0]}")
    return 5 * student[1]

ranges = CFG["RANGES"]

# allowedl = list(range(len(ranges)))
allowedl = [-1]
allowed = {x % len(ranges) for x in allowedl}
K = 2
print(f"allowed hw: {allowed}, max attempts: {K}")

def getrange(x):
  for i, r in enumerate(ranges):
    if x <= r:
      return i
  return 100000

def isint(x):
  try:
    x = int(x)
    return True
  except:
    return False

task_names = [x for x in sorted(set(table.columns[3:]), key=lambda s: (len(s), s)) if x not in banned and isint(x)]
# print('have =', ', '.join(task_names))

BANNED_STUDENTS = []

done_tasks = set()
done_students = set()
all_tasks = set()
def read_tasks():
  graph = defaultdict(list)
  inv_graph = defaultdict(list)
  for task in task_names:
    if getrange(int(task)) not in allowed:
      continue
    all_tasks.add(task)
    for student in names:
      if student in BANNED_STUDENTS:
        continue
      score = table[table['ФИО'] == student][task].any()
      if score:
        done_tasks.add(task)
        done_students.add(student)
        for it in range(K):
          graph[(student, it)].append(task)
          inv_graph[task].append((student, it))
  for st, lst in graph.items():
    lst.sort()
  return graph, inv_graph

def find_matching(order, graph):
  pb = dict()
  used = set()

  def kuhn(v):
    used.add(v)
    for u in graph[v]:
      if u not in pb or pb[u] not in used and kuhn(pb[u]):
        pb[u] = v
        return True
    return False

  for who in order:
    if kuhn(who):
      used.clear()
  return pb.items()

graph, inv_graph = read_tasks()

students = []
for s in names:
  for k in range(K):
    students.append((s, k))

# print(students)
shuffle(students)

# print('done =', ', '.join([f"{t}: {c}" for t, c in sorted(sorted([(x, len(inv_graph[x])) for x in done_tasks], key=lambda p: (len(p[0]), p[0])), key=lambda p: -p[1])]))
# print('skipped = ', ' '.join(sorted(set(task_names) - done_tasks, key=lambda s: (len(s), s))))

def getlasthw(x):
  return sum(int(i) > ranges[-2] for i in graph[x])

def comparator(x):
  if x[1]:
    # second or more time
    return (x[1], -getlasthw(x), get_points(x))
  return (x[1], get_points(x), -getlasthw(x))

order = sorted(students, key=lambda x: comparator(x))

matching = find_matching(order, graph)
chosen_students = [x[1] for x in matching]
for task in inv_graph:
  inv_graph[task] = [x for x in inv_graph[task] if x in chosen_students]

task_order = sorted(task_names, key=lambda x: (-getrange(int(x)), int(x)))
matching = find_matching(task_order, inv_graph)

last = -1
print(f"size = {len(matching)}")
count = defaultdict(int)
multiple = set()
max_times = 0
for task, student in sorted([(y, x) for x, y in matching], key=lambda p: (len(p[0]), p[0])):
  cur = getrange(int(task))
  if cur != last:
    print(f"HW {cur}")
    last = cur
  print(f"{task}: {student[0]}")
  if student[1]:
    multiple.add(student[0])
  max_times = max(max_times, student[1] + 1)

print("multiple =", ', '.join(sorted(multiple)))
print("max_times =", max_times)

print("skipped tasks =", ', '.join(sorted(all_tasks - set(y for x, y in matching), key=lambda s: (len(s), s))))
print("left tasks =", ', '.join(sorted(done_tasks - set(y for x, y in matching), key=lambda s: (len(s), s))))
print("left students =", ', '.join(sorted(done_students - set(x[0] for x, y in matching))))
