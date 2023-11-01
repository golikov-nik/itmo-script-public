CONFIG = {}

def addTable(group, ID, sheet, ranges):
  CONFIG[group] = {"ID": ID, "SHEET": sheet, "RANGES": ranges.copy()}

# ID: название листа в таблице
# HW1: [0; 18], HW2: [19, 36], HW3: [37, 54]
ranges = [0, 18, 36, 54]
addTable('40', 'Запись', 'адрес таблицы (то что после /d/)', ranges)
