# -*- coding: utf-8 -*-
import sys
import csv
import time
from pathlib import Path
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
from vms_model import ground_floor, first_floor, second_floor, third_floor, CsvTableModel
#from vms_camera import CameraWindow
import vms_camera_qt
import threading
import ctypes
import random
import os #for creating and changing dirs
import resources #for compiled resource access

"""
VERSION:
NON-DICON SPECIFIC VMS PROGRAM WITH RANDOMIZED BACKGROUNDS 

MODIFICATIONS:
Stronger Security Measures, Login Creds are viewable in regedit to a seasoned cracker
Close button for CameraWindow - done
Improved Camera Window Interface and Label Loading - done
#caution if for some reason, the Image is not saved to disk, this thread will run indefinitely 
Opening File should open it in view_dock widget - done
CSV dock(autosave on fin edit) - done
Camera stream should be handled by another model - done
Password authentication and change option - done
Handle permission error from MS Excel - done
Resource compilation - done
Files should be saved with timestamp of current data only not time e.g record_09_03_2019.csv - done
Check that all fields are filled and Valid (excluding Picture/optional) before Checking In Visitor
(In Building, Checked In, Checked Out Counter)
Add to record on check in -time in, blank time out which can be edited on finish, path to picture - done
Default image save location should be under image/, research how to do this with os module and implement - done
Fix init_file's start minimized if current_action is set at startup - done
Check In and Print Badge Richtext editing feature (Badge requires Picture is loaded), normal Check in does not
Face detection assertion 
"""

class PreferencesWindow(qtw.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Preferences')
        self.setWindowModality(qtc.Qt.ApplicationModal)
        self.setMinimumSize(400,400)
        tabs = qtw.QTabWidget(tabPosition=qtw.QTabWidget.West,tabShape=qtw.QTabWidget.Triangular)
        self.setLayout(qtw.QVBoxLayout())
        self.layout().addWidget(tabs)
        auth_widget = qtw.QWidget()
        auth_layout = qtw.QFormLayout()
        auth_widget.setLayout(auth_layout)
        auth_layout.addRow(qtw.QLabel('Login'))
        login_btn = qtw.QPushButton('Change Login Credentials',clicked=self.open_login)
        auth_layout.addRow(login_btn)
        tabs.addTab(auth_widget,'User Account')
        misc_widget = qtw.QWidget()
        tabs.addTab(misc_widget,'Miscellaneous')
        self.show()
    def open_login(self):
        self.auth_dialog = NewForm() #enter new login credentials or close window
        self.auth_dialog.setWindowTitle('New Login')
        #change uname and password
        self.auth_dialog.p_uname.connect(lambda uname: MainWindow.settings.setValue('username',uname))
        self.auth_dialog.p_passwd.connect(lambda passwd: MainWindow.settings.setValue('passwd',passwd))
        #self.new_auth = LoginForm()
        #self.new_auth.p_uname.connect(lambda uname: print(uname))#MainWindow.settings.setValue('username',uname))
        #self.new_auth.p_passwd.connect(lambda passwd: print(passwd))
    def check_uname(self,text):
        if text != MainWindow.settings.value('username'):
            #qtw.QMessageBox.warning(self,'Authentication Failed','Invalid username and/or password')
            #self.new_auth.close()
            self.auth_dialog.close()
    def check_passwd(self,text):
        if text != MainWindow.settings.value('passwd'):
            qtw.QMessageBox.warning(self,'Authentication Failed','Invalid username and/or password')
            #self.new_auth.close()
            self.auth_dialog.close()
class LoginForm(qtw.QWidget): #login form for authenticating users
    p_uname = qtc.pyqtSignal(str) #custom signals for uname and passwd
    p_passwd = qtc.pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Login')
        self.setWindowFlags(qtc.Qt.WindowTitleHint)
        self.setWindowModality(qtc.Qt.ApplicationModal) #ensure VMS application is disabled until login details are entered
        self.setMinimumSize(320,100)
        self.us_edit = qtw.QLineEdit()
        main_layout = qtw.QFormLayout()
        self.setLayout(main_layout)
        main_layout.addRow(qtw.QLabel('<b>Username</b>'),self.us_edit)
        self.passwd_edit = qtw.QLineEdit(echoMode=qtw.QLineEdit.Password,returnPressed=self.onSubmit) #mask password and on Enter key press, submit credentials
        main_layout.addRow(qtw.QLabel('<b>Password</b>'),self.passwd_edit)
        self.submit_btn = qtw.QPushButton('Submit',clicked=self.onSubmit)
        self.close_btn = qtw.QPushButton('Close',clicked=self.sendWrongs)
        main_layout.addRow(self.submit_btn,self.close_btn)
        self.show()
    @qtc.pyqtSlot()
    def onSubmit(self): #custom slot for submit button
        if self.us_edit.text() and self.passwd_edit.text():
            self.p_uname.emit(self.us_edit.text())
            self.p_passwd.emit(self.passwd_edit.text())
            self.close()
        else:
            qtw.QMessageBox.warning(self,'Login Failed','Invalid username and/or password')
    @qtc.pyqtSlot()
    def sendWrongs(self): #intentionally send wrong login details so program ends (improve this)
        self.p_uname.emit('-999999999999')
        self.p_passwd.emit('-9999999999999')
        self.close()
class NewForm(LoginForm): #new form is a derived class of LoginForm which overrides default behaviour of sendWrongs event handler for when close button is clicked, here the window  is just closed and previous login credentials are preserved
    @qtc.pyqtSlot()
    def sendWrongs(self):
        self.close()
class NumberValidator(qtg.QValidator):
    def validate(self, string, index):
        if not all([x.isdigit() for x in string]):
            state = qtg.QValidator.Invalid
        else:
            state = qtg.QValidator.Acceptable
        return (state,string,index)
    
class MainWindow(qtw.QMainWindow):
    settings = qtc.QSettings('VMS','Auth')
    #settings.setValue('username','dicon')
    #settings.setValue('passwd','dicon1964')
    #usname = qtc.QSettings('username','dicon',type=str)
    #passwd = qtc.QSettings('passwd','dicon1964',type=str)
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Visitor Management System')
        #print(self.settings.value('username'))
        #print(self.settings.value('passwd'))
        if not self.settings.value('username'):
            self.settings.setValue('username','dicon')
        if not self.settings.value('passwd'):
            self.settings.setValue('passwd','dicon1964')
        self.auth_dialog = LoginForm() #show login form on startup, VMS is also shown but is disabled similar to VS 2013
        self.auth_dialog.p_uname.connect(self.check_uname) #if improper login details are entered, exit application
        self.auth_dialog.p_passwd.connect(self.check_passwd)
        #else enable vms
        self.setWindowState(qtc.Qt.WindowMaximized) #maximized with frame around it
        #self.setWindowFlags(qtc.Qt.Window)
        #self.showFullScreen() #full screen, no frame
        main_widget = qtw.QWidget()
        main_widget.sizeHint : lambda : qtc.QSize(1000,800)
        main_widget.setSizePolicy(qtw.QSizePolicy.MinimumExpanding,qtw.QSizePolicy.MinimumExpanding)
        self.setCentralWidget(main_widget)
        main_layout = qtw.QFormLayout()
        main_widget.setLayout(main_layout)
        
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        edit_menu = menubar.addMenu('Settings')
        help_menu = menubar.addMenu('Help')
        open_action = file_menu.addAction('Open CSV file')
        save_action = file_menu.addAction('Save')
        quit_action = file_menu.addAction('Quit')
        pref_action = edit_menu.addAction('Preferences...')
        help_action = qtw.QAction('Help',self)#help_menu.addAction('VMS tutorial')
        reset_action = qtw.QAction('Reset Window', self) #the same slot as new visitor, but without the QMessageBox dialog
        open_action.triggered.connect(self.select_file)
        save_action.triggered.connect(self.save_file)
        quit_action.triggered.connect(self.close)
        reset_action.triggered.connect(self.clear_form) #lambda : qtw.QMessageBox.information(self, 'Reset Window', 'Window reset'))
        pref_action.triggered.connect(self.open_preferences)
        
        toolbar = qtw.QToolBar('File')
        #toolbar.setAllowedAreas(qtc.Qt.LeftToolBarArea)
        #toolbar.setOrientation(qtc.Qt.Vertical)
        self.addToolBar(qtc.Qt.RightToolBarArea, toolbar)
        open_icon = self.style().standardIcon(qtw.QStyle.SP_DirOpenIcon)
        save_icon = self.style().standardIcon(qtw.QStyle.SP_DriveHDIcon)
        quit_icon = self.style().standardIcon(qtw.QStyle.SP_MessageBoxCritical)
        help_icon = self.style().standardIcon(qtw.QStyle.SP_DialogHelpButton)
        reset_icon = self.style().standardIcon(qtw.QStyle.SP_DialogResetButton)
        open_action.setIcon(open_icon)
        save_action.setIcon(save_icon)
        quit_action.setIcon(quit_icon)
        help_action.setIcon(help_icon)
        reset_action.setIcon(reset_icon)
        toolbar.addAction(open_action)
        toolbar.addAction(save_action)
        toolbar.addAction(reset_action)
        #toolbar.addAction(help_action)
        toolbar.addAction(quit_action)        
        self.statusBar().showMessage('Welcome to Visitor Management System')     
        self.current_action = qtw.QLabel("")
        self.statusBar().addPermanentWidget(self.current_action)
        
        
        dock = qtw.QDockWidget('Image Capture')
        self.addDockWidget(qtc.Qt.RightDockWidgetArea, dock)
        dock.setFeatures(qtw.QDockWidget.DockWidgetFloatable)
        dock_widget = qtw.QWidget()
        dock_widget.sizeHint = lambda : qtc.QSize(500,10)#setMaximumSize(600,768)
        dock_widget.setSizePolicy(qtw.QSizePolicy.MinimumExpanding,qtw.QSizePolicy.Maximum)
        dock_widget.setLayout(qtw.QGridLayout())
        dock.setWidget(dock_widget)
        self.image_label = qtw.QLabel('Image')
        self.image_label.setMinimumSize(200,200)
        self.image_label.setMaximumSize(200,200)
        self.image_label.sizeHint = lambda : qtc.QSize(200,200)
        self.image_label.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        self.logo = qtg.QPixmap(':/logos/image_icon.png')#('VMS_DEF.png') #adgustSize of image widget to scale
        self.image_label.setPixmap(self.logo)
        self.imgname = ''
        button_box = qtw.QGridLayout()
        right_pad = qtw.QGridLayout()
        right_pad.addWidget(self.image_label,0,0,2,1)
        right_pad.addLayout(button_box,3,0,1,1)
        dock_widget.layout().addWidget(qtw.QWidget(),0,0,1,1)#pad widgets to the right by filling in a dummy
        dock_widget.layout().addLayout(right_pad,0,1,3,1)
        open_image_btn = qtw.QPushButton('Open from Disk')
        clear_image_btn = qtw.QPushButton('Clear Image')
        open_camera_btn = qtw.QPushButton('Open Camera')
        self.rename_btn = qtw.QPushButton('Rename Image')
        self.rename_btn.setDisabled(True)
        button_box.addWidget(open_image_btn,0,0,2,1)
        button_box.addWidget(open_camera_btn,2,0,2,1)
        #button_box.addWidget(self.rename_btn,4,0,2,1)
        button_box.addWidget(clear_image_btn,4,0,2,1)
        open_image_btn.clicked.connect(self.open_image_from_disk)
        clear_image_btn.clicked.connect(self.clear_image)
        open_camera_btn.clicked.connect(self.open_camera_window)
        
        view_dock = qtw.QDockWidget('Currently Registered')
        self.addDockWidget(qtc.Qt.BottomDockWidgetArea, view_dock)
        view_dock.setFeatures(qtw.QDockWidget.DockWidgetFloatable)# | qtw.QDockWidget.DockWidgetMovable)
        #view_widget = qtw.QTextEdit()
        self.tableview = qtw.QTableView() #table view for displaying CSV file in view_dock QDockWidget
        self.tableview.setSortingEnabled(True)
        self.tableview.setLayout(qtw.QHBoxLayout())
        view_dock.setWidget(self.tableview)
        self.tableview.layout().addStretch()
        #create data/ and images/ dir if they do not already exist
        #use seperate try/except blocks for the two dirs
        try:
            os.makedirs('data')
        except FileExistsError:
            pass
        try:
            os.makedirs('images')
        except FileExistsError:
            pass
        current_time = time.ctime(time.time())
        current_date = '_'.join(current_time.split()[:3])
        year =  time.ctime(time.time()).split()[-1]
        self.filename = r'data/record_'+current_date+'_'+year+'.csv' #create and maintain file on a date basis
        self.init_file()
        #NB Below line causes app to open minimized
        #self.current_action.setText('File opened "%s"'%Path(self.filename).absolute())
        #self.select_file()
        
        dept_list = list(set(map(lambda x: x[0], ground_floor.values())))#['Human Resource','ICT','Security','Registry']
        dept_list.extend(["DG's OFFICE","MA's OFFICE","PA's OFFICE"])
        floor_list = ['Ground Floor','First Floor','Second Floor','Third Floor']
        self.vname_edit = qtw.QLineEdit(placeholderText='Enter full name')
        self.vphone_edit = qtw.QLineEdit()
        self.ename_edit = qtw.QLineEdit(placeholderText='Employee full name')
        self.dept_combo = qtw.QComboBox(self, editable=True, insertPolicy=qtw.QComboBox.InsertAtTop)
        self.floor_combo = qtw.QComboBox()
        self.no_combo = qtw.QComboBox()
        self.pt_edit = qtw.QTextEdit()
        self.apt_edit = qtw.QLineEdit()
        self.visitornum_sb = qtw.QSpinBox(minimum=1,maximum=100,singleStep=2)
        self.accesscardnum_edit = qtw.QLineEdit()
        self.checkin_btn = qtw.QPushButton('Check In')
        self.newvisitor_btn = qtw.QPushButton('New Visitor')
        self.removelast_btn = qtw.QPushButton('Remove Selected Row(s)')
        
        self.vphone_edit.setValidator(NumberValidator())
        self.dept_combo.addItems(dept_list) #accessed through currentText property
        self.floor_combo.addItems(floor_list)
        self.no_combo.addItems(list(sorted(map(lambda x: str(x[1]), ground_floor.values()), key=lambda x: int(x) if x.isdigit() else 1)))#attempt to sort by integer magnitude if an int else push to the top
        self.vname_edit.textChanged.connect(self.attempt_image_load)
        self.dept_combo.currentTextChanged.connect(lambda text : print('Selected',text))
        self.floor_combo.currentTextChanged.connect(self.setAllowedNos)
        self.no_combo.currentTextChanged.connect(self.set_appointment)
        self.checkin_btn.clicked.connect(self.update_file) #save file on each checkin
        self.newvisitor_btn.clicked.connect(self.clear_form)
        self.removelast_btn.clicked.connect(self.remove_rows)
        
        title_font = qtg.QFont('Bookman Old Style',16)
        maintitle_label = qtw.QLabel('<b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;DEFENCE INDUSTRIES CORPORATION OF NIGERIA</b>')
        subtitle_label = qtw.QLabel('<b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(DICON HQ Visitor Management System)</b>')
        maintitle_label.setFont(title_font)
        subtitle_label.setFont(title_font)
        vname_label = qtw.QLabel('Visitor Name:')
        vphone_label = qtw.QLabel('Visitor Phone Number:')
        ename_label = qtw.QLabel('Staff Name:')
        dept_label = qtw.QLabel('Department:')
        floor_label = qtw.QLabel('Floor:')
        office_label = qtw.QLabel('Office No:')
        apt_label = qtw.QLabel('Appointment:')
        visitornum_label = qtw.QLabel('Number of Visitors:')
        accesscardnum_label = qtw.QLabel('Access Card Number:')
        pt_label = qtw.QLabel('Purpose of Visit:')
        #setting font        
        form_font = qtg.QFont('Bookman Old Style',14)
        ename_label.setFont(form_font)
        vname_label.setFont(form_font)
        vphone_label.setFont(form_font)
        dept_label.setFont(form_font)
        floor_label.setFont(form_font)
        office_label.setFont(form_font)
        apt_label.setFont(form_font)
        pt_label.setFont(form_font)
        visitornum_label.setFont(form_font)
        accesscardnum_label.setFont(form_font)
        self.vname_edit.setFont(form_font)        
        self.vphone_edit.setFont(form_font)
        self.ename_edit.setFont(form_font)
        self.dept_combo.setFont(form_font)
        self.floor_combo.setFont(form_font)
        self.no_combo.setFont(form_font)
        self.apt_edit.setFont(form_font)
        self.pt_edit.setFont(form_font)
        self.visitornum_sb.setFont(form_font)
        self.accesscardnum_edit.setFont(form_font)
        
        #multiple items in one row in QFormLayout(widget,layout), first define the last 3 widgets to be on one row 
        s1_lt = qtw.QHBoxLayout()
        s1_lt.addWidget(self.floor_combo,1) #floor_combo should have a higher stretch than the other widgets
        s1_lt.addWidget(office_label)
        s1_lt.addWidget(self.no_combo)
        #multiple items in 2nd row
        s2_lt = qtw.QHBoxLayout()
        s2_lt.addWidget(self.accesscardnum_edit,1)
        s2_lt.addWidget(visitornum_label)
        s2_lt.addWidget(self.visitornum_sb)        
        
        main_layout.addRow(maintitle_label)
        main_layout.addRow(subtitle_label)
        main_layout.addRow(vname_label,self.vname_edit)
        main_layout.addRow(vphone_label,self.vphone_edit)
        main_layout.addRow(ename_label, self.ename_edit)
        main_layout.addRow(dept_label,self.dept_combo)
        main_layout.addRow(floor_label,s1_lt) #appears: Floor: _ Office no: _ 
        main_layout.addRow(apt_label,self.apt_edit)
        main_layout.addRow(accesscardnum_label,s2_lt)
        main_layout.addRow(pt_label,self.pt_edit)
        show_view_cb = qtw.QCheckBox('View Currently Registered Visitors', checked=True)
        bottom_layout = qtw.QGridLayout()
        main_layout.addRow(bottom_layout)
        bottom_layout.addWidget(self.checkin_btn, 0, 0)
        bottom_layout.addWidget(qtw.QPushButton('Check In and Print Badge'),0,1)
        bottom_layout.addWidget(self.newvisitor_btn,0,2)
        bottom_layout.addWidget(self.removelast_btn,0,3)
        bottom_layout.addWidget(show_view_cb,1,0,1,3)        
        show_view_cb.toggled.connect(lambda true: view_dock.setHidden(not true))
        #unticking the checkbox above should hide view_dock widget
        #decoration
        #different background image should show each time app is opened (use random module)
        diffs = ['2','3','4','5']#,'6','7','8','9','10']
        random.seed(time.time())
        img_url = ':/themes/vms '+random.choice(diffs)+'.png'
        QSS = """
                QMainWindow
                {
                border-image: url("%s");
                background-repeat: no-repeat;
                background-position: center;
                }
            """%img_url
        self.setStyleSheet(QSS)
        #window icon
        self.setWindowIcon(qtg.QIcon(':/logos/taskbar_icon.png'))
        #set taskbar icon
        myappid = u'davob.ms.vms.0_0_1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.show()
    def open_preferences(self):
        self.pref_window = PreferencesWindow()
    def check_uname(self,uname):
        if self.settings.value('username') != uname:
            self.close()
    def check_passwd(self,passwd):
        if self.settings.value('passwd') != passwd:
            self.close()
    def setAllowedNos(self, text):
        self.no_combo.clear()
        if 'Ground' in text:
            floor = ground_floor
        elif 'First' in text:
            floor = first_floor
        elif 'Second' in text:
            floor = second_floor
        else:
            floor = third_floor
        
        self.no_combo.addItems(list(set(sorted(map(lambda x: str(x[1]), floor.values()), key=lambda x: int(x) if x.isdigit() else 1))))
        '''
        elif 'First' in text:
            self.no_combo.addItems(list(map(lambda x : str(x), range(100,200))))
        elif 'Second' in text:
            self.no_combo.addItems(list(map(lambda x : str(x), range(200,300))))
        elif 'Third' in text:
            self.no_combo.addItems(list(map(lambda x : str(x), range(300,400))))
        '''
            
    def clear_form(self):
        self.vname_edit.clear()
        self.vphone_edit.clear() 
        self.ename_edit.clear()
        self.dept_combo.setCurrentIndex(0)
        self.floor_combo.setCurrentIndex(0)
        self.no_combo.setCurrentIndex(0) 
        self.visitornum_sb.setValue(1)
        self.accesscardnum_edit.clear()
        self.pt_edit.setPlainText('')
        #reset image_label logo to no_image.png
        self.clear_image()
        
    def openFile(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(
                self,
                'Select a CSV file to open...',
                qtc.QDir.currentPath(),
                'CSV Files (*.csv)',
                'CSV Files (*.csv)',
                qtw.QFileDialog.DontResolveSymlinks)
        #open filename and process with csv module
    def saveFile(self):
        filename, _ = qtw.QFileDialog.getSaveFileName(
                self,
                'Select the file to save to...',
                qtc.QDir.currentPath(),
                'CSV Files (*.csv) ;;Text Files (*.txt) ;;All Files (*)'
                )
        #save file based on format chosen
    def open_image_from_disk(self):
        imgname, _ = qtw.QFileDialog.getOpenFileName(
                self,
                'Select an image to open...',
                qtc.QDir.currentPath(),
                'PNG Files (*.png) ;;JPG Files (*.jpg)',
                'PNG Files (*.png)',
                qtw.QFileDialog.DontResolveSymlinks)
        #update img_label logo here
        if imgname: #imgname should be made persistent when it is time to save
            self.logo = qtg.QPixmap(imgname)
            self.image_label.setPixmap(self.logo.scaled(self.image_label.width(),self.image_label.height(),qtc.Qt.KeepAspectRatio)) #scale image appropriately before it is displayed
            self.imgname = imgname
        
    def attempt_image_load(self, text): #attempt to automatically load an image from disk if it is present in the current directory
        #ensure camera isn't recording first
        if Path('images/'+text+'.png').exists():
            self.logo = qtg.QPixmap(str('images/'+text+'.png')) #imgname should be made persistent when it is time to save
            self.image_label.setPixmap(self.logo.scaled(self.image_label.width(),self.image_label.height(),qtc.Qt.KeepAspectRatio)) #scale image appropriately before it is displayed
            self.imgname = 'images/'+text+'.png' #potential hazard until data/ is handled
        elif Path('images/'+text+'.jpg').exists():
            self.logo = qtg.QPixmap(str('images/'+text+'.jpg'))
            self.image_label.setPixmap(self.logo.scaled(self.image_label.width(),self.image_label.height(),qtc.Qt.KeepAspectRatio)) #scale image appropriately before it is displayed
            self.imgname = 'images/'+text+'.jpg'
    
    def clear_image(self):
        self.logo = qtg.QPixmap(':/logos/image_icon.png')
        self.image_label.setPixmap(self.logo)
        self.imgname = ''
        
    def set_appointment(self, value):
        if 'Ground' in self.floor_combo.currentText():
            floor = ground_floor
        elif 'First' in self.floor_combo.currentText():
            floor = first_floor
        elif 'Second' in self.floor_combo.currentText():
            floor = second_floor
        else:
            floor = third_floor
        for k, v in floor.items():
            if str(v[1]) == value:
                self.apt_edit.setText(k)
                break
    def init_file(self):
        if not Path(self.filename).exists():
            with open(self.filename, 'w', newline='') as fh:
                writer = csv.writer(fh)
                writer.writerow(['Visitor Name','Phone','Staff Name','Department','Floor','Office no','Appointment','No. of Visitors','Access Card Number','Purpose','Image Path','Check In Time','Check Out Time'])
        self.model = CsvTableModel(self.filename)
        self.tableview.setModel(self.model)
    def update_file(self):
        try:
            with open(self.filename, 'a', newline='') as fh:
                writer = csv.writer(fh)
                if self.imgname:
                    tosave = str(Path(self.imgname).absolute())
                else:
                    tosave = ''                
                writer.writerow([self.vname_edit.text(), self.vphone_edit.text(),self.ename_edit.text(),self.dept_combo.currentText(),self.floor_combo.currentText(),self.no_combo.currentText(),self.apt_edit.text(),str(self.visitornum_sb.value()),self.accesscardnum_edit.text(),self.pt_edit.toPlainText(),tosave,time.ctime(time.time()).split()[3],''])
            self.model = CsvTableModel(self.filename)
            self.tableview.setModel(self.model)
            self.save_file() #proper saving after update, similar to db commit
            self.clear_form() #reset window on each checkin
        except PermissionError: #handle record open in maybe MS Excel and user still attempting manip in VMS
            qtw.QMessageBox.warning(self,'Permission Error','Please ensure the record is not open in another spreadsheet software')
    def select_file(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(
                self,
                'Select a CSV file to open...',
                qtc.QDir.currentPath(),
                'CSV Files (*.csv)'
                )
        if filename:
            self.model = CsvTableModel(filename)
            self.tableview.setModel(self.model)
            self.filename = filename
            self.current_action.setText('File opened "%s"'%Path(self.filename).absolute())
    def save_file(self):
        if self.model:
            self.model.save_data()
        self.current_action.setText('File saved as "%s"'%Path(self.filename).absolute())
    def remove_rows(self):
        selected = self.tableview.selectedIndexes()
        if selected:
            self.model.removeRows(selected[0].row(),len(selected),None)
        self.save_file()
    def open_camera_window(self):
        if not self.vname_edit.text():
            qtw.QMessageBox.information(self,'Camera Warning','Please Enter Visitor\'s name first')
        else:
            #self.cam = CameraWindow('images/'+self.vname_edit.text())
            self.cam = vms_camera_qt.MainWindow('images/'+self.vname_edit.text())
            self.cam.show()
            self.wait_thread = threading.Thread(target=self.wait_on_image) #create separate thread that attempts loading captured image until CameraWindow is closed .i.e image is captured 
            self.wait_thread.start()
            #caution(FIXED): if for some reason, the Image is not saved to disk, this thread will run indefinitely
    def wait_on_image(self):
        while not self.cam.thread_override: #wait until image has been loaded
            time.sleep(.5)
            self.attempt_image_load(self.vname_edit.text())
            #if self.cam.thread_override:
            #    break
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    windows_style = qtw.QStyleFactory.create('Fusion') #nice QStyle for ComboBox and Dock headers
    app.setStyle(windows_style)
    mw = MainWindow()
    sys.exit(app.exec())        