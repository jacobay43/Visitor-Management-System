#import json
import csv
import PyQt5.QtCore as qtc

class CsvTableModel(qtc.QAbstractTableModel):
    def __init__(self, csv_file):
        super().__init__()
        self.filename = csv_file
        with open(self.filename) as fh:
            csvreader = csv.reader(fh)
            try:
                self._headers = next(csvreader)
            except:
                self._headers = []
            try:
                self._data = list(csvreader)
            except:
                self._data = []
    def rowCount(self, parent):
        return len(self._data)
    def columnCount(self, parent):
        return len(self._headers)
    def data(self, index, role):
        if role in (qtc.Qt.DisplayRole, qtc.Qt.EditRole):
            try:
                d = self._data[index.row()][index.column()]
            except:
                d = ''
            return d
    def headerData(self, section, orientation, role):
        if orientation == qtc.Qt.Horizontal and role == qtc.Qt.DisplayRole:
            return self._headers[section]
        else:
            return super().headerData(section, orientation, role)
    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        self._data.sort(key=lambda x: x[column])
        if order == qtc.Qt.DescendingOrder:
            self._data.reverse()
        self.layoutChanged.emit()
    def flags(self, index):
        return super().flags(index) | qtc.Qt.ItemIsEditable
    def setData(self, index, value, role):
        if index.isValid() and role == qtc.Qt.EditRole:
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index, [role])
            self.save_data() #on each cell edit, save file to disk
            return True
        else:
            return False
    def insertRows(self, position, rows, parent):
        self.beginInsertRows(parent or qtc.QModelIndex(),
                             position,
                             position + rows - 1
                             )
        for i in range(rows):
            default_row = [''] * len(self._headers)
            self._data.insert(position, default_row)
        self.endInsertRows()
    def removeRows(self, position, rows, parent):
        self.beginRemoveRows(parent or qtc.QModelIndex(),
                             position,
                             position + rows - 1
                             )
        for i in range(rows):
            del(self._data[position])
        self.endRemoveRows()
    def save_data(self):
        with open(self.filename, 'w', encoding='utf-8', newline='') as fh:
            writer =  csv.writer(fh)
            writer.writerow(self._headers)
            for line in self._data:
                if len(line) > 0: #avoid saving blank lines to file
                    writer.writerow(line)
    
directory = {
			'DG':
			{
			 'Director General': (217,200),
			 'MA-DG': (212,201),
			 'PA-DG': (211,202),
			 'AO TO DG': (210,210),
			 'SA TO DG': (221,208)
			},
			'ENGR SERVICES':
			{
			'DES': (121,203),
			'SEC-DES': (122,256),
			'ADES': (19,262), #dont put 0 in front
			'ENGR SERVICES': ('1st Floor',212)
			},
			'HRM':
			{
			'DIRECTOR HRM': (109,244),
			'SEC DIR HRM': (110,206),
			'DEPUTY DIR HRM': (101,219),
			'SEC DEPUTY DIR HRM': (102,214),
			'AO1': (17,227),
			'AO2': (12,259),
			'PEO &AO2': (9,223),
			'REGISTRY': (16,230)
			},
			'LEGAL':
			{
			'SECRETARY/LEGAL ADV': (120,216),
			'PA-SEC LEGAL ADVISER': (120,217),
			'GENERAL LEGAL OFFICE': (220,241),
			'LEGAL': (215,254)
			},
			'SERVICOM':
			{
			'SERVICOM': (123,218)
			},
			'ACCOUNT':
			{
			'CA': (305,222),
			'SEC-CA': (305,238),
			'ACA': ('306/307',236),
			'SALARY/ACCOUNT': (308,235),
			'GENERAL ACCOUNT': (311,233),
			'GENERAL ACCOUNT (B)': (311,245),
			'CASHIER': (311,249),
			'CANTEEN': (14,205)
			},
			'P&BD':
			{
			'DIRECTOR (P&BD)': (105,207),
			'SEC-DIRECTOR (P&BD)': (104,213),
			'ACCO': (6,254),
			'SEC ACCO': (5, 229),
			'GENERAL COMMERCIAL': (7,253),
			'BUSINESS DEV': (8,261)
			},
			'AUDIT':
			{
			'ADIA': (206,246),
			'SEC-ADIA': (206,247),
			'HEO AUDIT': (204,211),
			'GENERAL AUDIT': (205,232)
			},
			'SECURITY':
			{
			'SY COORDINATOR': (202,243),
			'SEC-SY COORDINATOR': (201,260),
			'ACSO': (3,226),
			'HEAD SECURITY': (4,242),
			'RECEPTION': (22,225)
			},
			'PRO':
			{
			'PRO': (208,220),
			'SEC-PRO': (207,255),
			'PRO GENERAL': (18,221)
			},
			'PROCUREMENT':
			{
			'CPO': (302,239),
			'PO': (301,248)
			},
			'BUDGET':
			{
			'ACBO&PO2': (222,231),
			'GENERAL BUDGET': (309,234)
			},
			'SAFETY':
			{
			'DEPUTY DIR SAFETY': (108,251),
			'PA DEPUTY DIR SAFETY': (107,257)
			},
			'COMPUTER':
			{
			'CTO (COMPUTER)': (313,250),
			'CYBER CAFE': (315,240),
			'MTO': ('011B',104),
			'CONFERENCE ROOM': ('CONFERENCE ROOM',251),
			'CHAIRMAN': ('Board',252),
			'Intercom control room': (304,0)
			}
        }
            

#print(json.dumps(directory, indent=4))
ground_floor = {} #floor[APPOINTMENT] = (DEPARTMENT, ROOM NUMBER)
first_floor = {}
second_floor = {}
third_floor = {}
#print('Offices on Ground Floor:')
for key in directory.keys():
    for innerkey in directory[key].keys():
        try:
            if directory[key][innerkey][0] < 100:
                #print(key,'-',innerkey,':',directory[key][innerkey])
                ground_floor[innerkey] = (key, f'{directory[key][innerkey][0]:03d}')
        except (ValueError, TypeError):
            #print(key,'-',innerkey,':',directory[key][innerkey])
            ground_floor[innerkey] = (key, directory[key][innerkey][0])

#print('\nOffices on 1st Floor:')
for key in directory.keys():
    for innerkey in directory[key].keys():
        try:
            if 100 <= directory[key][innerkey][0] < 200:
                #print(key,'-',innerkey,':',directory[key][innerkey])
                first_floor[innerkey] = (key, directory[key][innerkey][0])
        except (ValueError, TypeError):
            pass
     
#print('\nOffices on 2nd Floor:')
for key in directory.keys():
    for innerkey in directory[key].keys():
        try:
            if 200 <= directory[key][innerkey][0] < 300:
                #print(key,'-',innerkey,':',directory[key][innerkey])
                second_floor[innerkey] = (key, directory[key][innerkey][0])
        except (ValueError, TypeError):
            pass
        
#print('\nOffices on 3rd Floor:')
for key in directory.keys():
    for innerkey in directory[key].keys():
        try:
            if 300 <= directory[key][innerkey][0] < 400:
                #print(key,'-',innerkey,':',directory[key][innerkey])
                third_floor[innerkey] = (key, directory[key][innerkey][0])
        except (ValueError, TypeError):
            pass