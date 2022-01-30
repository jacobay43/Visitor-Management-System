import cv2
import sys
import time
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

class CameraWindow(qtw.QWidget):
    def __init__(self, fname=''):
        super().__init__()
        self.setWindowTitle('Camera Feed')
        self.setWindowFlags(qtc.Qt.WindowTitleHint | qtc.Qt.WindowMinimizeButtonHint) #disable close button
        self.filename = fname + '.png' if fname else ''
        self.frame = None
        
        self.image_label = qtw.QLabel()
        self.camera_btn = qtw.QPushButton('Camera', clicked=self.camera_clicked)
        self.capture_btn = qtw.QPushButton('Capture',clicked=self.capture_clicked)
        
        self.image_label.setMinimumSize(200,200)
        self.image_label.setMaximumSize(200,200)
        self.image_label.sizeHint = lambda : qtc.QSize(200,200)
        self.image_label.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        self.logo = qtg.QPixmap('VMS_def.png')
        self.image_label.setPixmap(self.logo)        
        self.capture_btn.setDisabled(True)
    
        main_layout = qtw.QHBoxLayout()
        sub_layout = qtw.QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(self.image_label)
        main_layout.addLayout(sub_layout)
        sub_layout.addWidget(self.camera_btn)
        sub_layout.addWidget(self.capture_btn)       
        self.show()
    def camera_clicked(self):
        self.cap = cv2.VideoCapture(0) #cv2.CAP_DSHOW slows down program, suppress warning instead
        self.cap.set(4,200)
        self.cap.set(3,200)
        self.capture_btn.setDisabled(False)
        self.timer = qtc.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(5)
    def update_frame(self):
        ret, self.frame = self.cap.read()
        self.frame = cv2.flip(self.frame,1)
        self.display_image(self.frame,1)
    def display_image(self, img, window):
        qformat = qtg.QImage.Format_Indexed8
        if img is None: #if no camera device detected
            qtw.QMessageBox.information(self,'Camera Notification','Please attach a Camera Device')
            self.capture_btn.setDisabled(True) #Disable Capture Button if no Camera is detected
            self.stop_cam()
            return
        if len(img.shape) == 3:
            if img.shape[2] == 4:
                qformat = qtg.QImage.Format_RGBA8888
            else:
                qformat = qtg.QImage.Format_RGB888
        self.out_image = qtg.QImage(img,img.shape[1],img.shape[0],img.strides[0],qformat)
        self.out_image = self.out_image.rgbSwapped()
        if window == 1:
            self.image_label.setPixmap(qtg.QPixmap(self.out_image))
            self.image_label.setScaledContents(True)
    def capture_clicked(self):
        self.camera_btn.setDisabled(True)
        self.capture_btn.setDisabled(True)
        date_str = time.ctime(time.time())
        date_str = date_str.replace(':','-')
        disp = self.filename if self.filename else 'vms_capture_%s.png'%date_str
        cv2.imwrite(disp, self.frame)
        self.close_window()
    def stop_cam(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
    def close_window(self):
        if hasattr(self, 'cap'):
            self.stop_cam() #stop timer
            self.cap.release() #close camera (considerably slow but required to turn off webcam)
            cv2.destroyAllWindows() #release handle to webcam
        self.close() #close window
        
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = CameraWindow()
    sys.exit(app.exec())

