import sys
import time
from pathlib import Path
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtMultimedia as qtmm
import PyQt5.QtMultimediaWidgets as qtmmw

class MainWindow(qtw.QWidget):
    def __init__(self,fname=''):
        super().__init__()
        self.setWindowTitle('Capture Window')
        self.setMaximumSize(250,250)
        self.setWindowFlags(qtc.Qt.WindowTitleHint)
        self.thread_override = False #bool to indicate whether thread in vms should keep waiting for image capture(False) or terminate from user explicitly clicking close btn(True), this prevents from infinte running threads caused from closed cam windows from vms_gui
        self.info_label = qtw.QLabel()
        self.fname = fname
        self.switch_btn = qtw.QPushButton('Switch Camera',clicked=self.switch)
        self.capture_btn = qtw.QPushButton('Capture',clicked=self.capture_img)
        self.close_btn = qtw.QPushButton('Close',clicked=lambda : self.close_window(True))
        self.viewfinder = qtmmw.QCameraViewfinder()
        self.viewfinder.setMinimumSize(320,225)
        self.capture_settings = qtmm.QImageEncoderSettings()
        #print(self.capture_settings.resolution())
        self.capture_settings.setCodec("image/jpeg")
        self.capture_settings.setResolution(qtc.QSize(300,200))
        #print(self.capture_settings.resolution())
        self.cameras = qtmm.QCameraInfo.availableCameras()
        if not self.cameras:
            self.info_label.setText('No camera detected')
            self.camera = None
            self.image_capture = None
            #self.switch_btn.setDisabled(True)
        else:
            self.camera = qtmm.QCamera(self.cameras[0])
            self.camera.setCaptureMode(qtmm.QCamera.CaptureStillImage)
            self.camera.setViewfinder(self.viewfinder)
            self.image_capture = qtmm.QCameraImageCapture(self.camera)
            #print(self.image_capture.supportedResolutions())
            self.image_capture.setEncodingSettings(self.capture_settings)
            self.image_capture.imageSaved.connect(lambda : self.close_window(True)) #only quit program if captured image was saved successfully
            #self.image_capture.imageCaptured
            self.camera.start()
        self.cameras_combo = qtw.QComboBox(self,editable=False) #combobox for viewing and switching btw all available connected cameras
        if self.cameras:
            self.cameras_combo.addItems([cam.description() for cam in self.cameras])
        self.cameras_combo.currentTextChanged.connect(self.change_device) #if a different camera is chosen, switch to it as the qcamera, this logic is better than switch_btn which is unpredictable
        self.refresh_btn = qtw.QPushButton('Detect Cameras',clicked=self.refresh_manager)
        main_layout = qtw.QGridLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(self.info_label,0,1,1,3)
        main_layout.addWidget(self.viewfinder,1,0,1,4)
        main_layout.addWidget(self.cameras_combo,2,0)
        main_layout.addWidget(self.refresh_btn,2,1)
        main_layout.addWidget(self.capture_btn,2,2)
        main_layout.addWidget(self.close_btn,2,3)
        self.show()
    def change_device(self,text): #also indirectly called by refreshed_manager slot when currentText is changed
        self.cameras = qtmm.QCameraInfo.availableCameras()
        self.cam_dict = {cam.description():cam for cam in self.cameras} #dict of camera descr to camera object
        cam = self.cam_dict.get(text,[])
        if cam:
            if self.camera is not None:
                self.camera.stop()
            self.camera = qtmm.QCamera(cam)
            self.camera.setCaptureMode(qtmm.QCamera.CaptureStillImage)
            self.camera.setViewfinder(self.viewfinder)
            self.image_capture = qtmm.QCameraImageCapture(self.camera)
            self.image_capture.setEncodingSettings(self.capture_settings)
            self.image_capture.imageSaved.connect(lambda : self.close_window(True)) #only quit program if captured image was saved successfully
            self.camera.start()
            self.info_label.setText('%s in use'%(text))
    def refresh_manager(self): #refresh btn used to detect if a camera is connected
        self.cameras = qtmm.QCameraInfo.availableCameras()
        self.cameras_combo.clear()
        if self.cameras:
            self.cameras_combo.addItems([cam.description() for cam in self.cameras])
    def switch(self):
        #if self.camera:
        #    self.camera.stop()
        if not self.cameras:
            self.cameras = qtmm.QCameraInfo.availableCameras()
            print(len(self.cameras),self.cameras)
            if self.cameras:
                self.camera = qtmm.QCamera(self.cameras[0])
        elif self.camera is not None and len(self.cameras) == 1:
            self.camera.stop()
            self.camera = qtmm.QCamera(self.cameras[0])
        elif len(self.cameras) > 1:
            if self.camera is self.cameras[0]:
                self.camera = qtmm.QCamera(self.cameras[1])
            else:
                self.camera = qtmm.QCamera(self.cameras[0])
        if self.cameras:
            self.camera.setCaptureMode(qtmm.QCamera.CaptureStillImage)
            self.camera.setViewfinder(self.viewfinder)
            self.image_capture = qtmm.QCameraImageCapture(self.camera)
            self.image_capture.setEncodingSettings(self.capture_settings)
            self.image_capture.imageSaved.connect(lambda : self.close_window(True)) #only quit program if captured image was saved successfully
            self.camera.start()
            self.info_label.setText('Camera detected')
        else:
            self.info_label.setText('No camera detected')
    def capture_img(self):
        if not self.fname:
            date_str = time.ctime(time.time())
            date_str = date_str.replace(':','-').replace(' ','_')
            self.fname = 'capture_%s'%date_str
        if self.camera:
            self.camera.searchAndLock()
            nm = str(Path(self.fname).absolute())
            stat = self.image_capture.capture(nm)#(str(Path(self.fname).absolute()))
            #print(stat)
            self.camera.unlock()
            self.info_label.setText('Image "%s" captured'%self.fname)
        else:
            self.info_label.setText('Error in Image capture')
    def close_window(self,override):
        self.thread_override = override
        if self.camera is not None:
            self.camera.stop()
        self.close()
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec())