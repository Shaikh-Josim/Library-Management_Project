#standard libraries
import sys
import traceback
import os
import json
import random  
import webbrowser

#3rd party libraries
import mysql.connector

#Pyqt6 core
from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton, QCheckBox, QBoxLayout, QVBoxLayout, QGridLayout, QTableWidgetItem, QSpacerItem, QAbstractItemView, QSizePolicy, QMessageBox, QFileDialog, QWidget, QMainWindow, QMenu, QApplication
from PyQt6.QtCore import QSize, QRegularExpression, QTimer, Qt, QObject, QEvent, pyqtSlot
from PyQt6.QtGui import QRegularExpressionValidator, QCloseEvent, QIcon, QPixmap, QPainter, QPainterPath, QAction

# Local application imports
import libui as ui
from db import Dbconnection
from Email_sender import EmailSender
from log import CustomErrorAndLogWriting, ErrorCodes
from link_device import WebSocketServer

try:
    from ctypes import windll

    myappid = "myapp.LibraryManagement.exe"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
except ImportError:
    pass

class RegExp:
    reg = QRegularExpression()

    def stringValidator(self):
        regexp = QRegularExpression("^[A-Za-z]+")
        return regexp
    
    def stringValidatorWithSpace(self):
        regexp = QRegularExpression("^[A-Za-z ]+")
        return regexp
    
    def stringValidatorWithCommas(self):
        regexp = QRegularExpression("^[A-Za-z,]+")
        return regexp
    
    def useridValidator(self):
        regexp = QRegularExpression("^[A-Za-z]+[0-9A-Za-z]+@[A-za-z]+\\.[A-Za-z]+$")
        return regexp
    
    def phnoValidator(self):
        regexp = QRegularExpression("^[0-9]{10}$")
        return regexp
    
    def numbersOnly(self):
        regexp = QRegularExpression("^[0-9]+")
        return regexp
    
    def alphanumericValidator(self):
        regexp = QRegularExpression("[A-Za-z0-9 ]+")
        return regexp
    
    def isbnValidator(self):
        regexp = QRegularExpression("^[0-9]{13}$")
        return regexp
    
    def libcardnoValidator(self):
        regexp = QRegularExpression("^[0-9]{14}$")
        return regexp
    
class CustomValidator(QRegularExpressionValidator):
    def __init__(self, regex,msg, parent=None):
        super().__init__(regex, parent)
        self.desired_input = msg
        self.last_invalid_text = ""  # To track the last invalid input

    def validate(self, input_text, pos):
        state = super().validate(input_text, pos)[0]

        if state == self.State.Invalid:
            # Check if the invalid text is the same as the previous one
            if input_text != self.last_invalid_text:
                self.last_invalid_text = input_text
                self.error_message="Invalid input! Please enter the correct format.\nyour input :\t{}\n".format(self.last_invalid_text)+"desired input:\t"+self.desired_input
                self.show_error_message()
                self.last_invalid_text = ""
        else:
            # Reset the last_invalid_text when the input becomes valid
            self.last_invalid_text = ""

        return state, input_text, pos

    def show_error_message(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowIcon(QIcon('Appdata/images/lib.ico'))
        msg_box.setText(self.error_message)
        msg_box.setWindowTitle("Invalid input")
        msg_box.exec()

class KeyPressEventFilter(QObject):
    def __init__(self, parent = None, lineedits = None):
        self.lineedits = lineedits
        super().__init__(parent)
    
    def getNextindex(self, obj):
        idx = self.lineedits.index(obj)
        if self.lineedits[idx+1].isVisible():
            return idx+1
        else:
            None

    def getPreviousindex(self, obj):
        idx = self.lineedits.index(obj)
        if self.lineedits[idx-1].isVisible():
            return idx-1
        else:
            None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                # Move to the next QLineEdit
                widget = obj
                idx = self.getNextindex(widget)
                if idx:
                    self.lineedits[idx].setFocus()
                return True
            elif event.key() == Qt.Key.Key_Up:
                # Move to the previous QLineEdit
                widget = obj
                idx = self.getPreviousindex(widget)
                if idx:
                    self.lineedits[idx].setFocus()
                return True
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                widget = obj
                if isinstance(widget,QPushButton):
                    widget.click()
        return super().eventFilter(obj, event)


class MyApp(QMainWindow, ui.Ui_MainWindow):
    def __init__(self, ws_server:'WebSocketServer'):
        super().__init__()
        self.ws_server = ws_server
        self.errors_names = []
        self.e_msg = ""
        self.LIBCARD_IMAGES_PATH = os.path.join("Appdata","LibrarycardImages")
        self.setWindowIcon(QIcon('Appdata/images/lib.ico'))
        self.setupUi(self)
        self.restart()
        self.ws_server.message_received.connect(self.display_message)
        self.ws_server.client_disconnected.connect(self.clientDisconnected)
        self.is_device_linked = False
        
      
    def restart(self):
        #things needed to do again if user login once again
        self.db_connected = False 
        self.stackedWidget.setCurrentIndex(0)
        self.sidemenu_btn.hide()
        self.sidemenu_btn.setCheckable(False)
        self.sidemenu_widget.hide();self.sa_sidewidget.hide()
        self.login_btn.setEnabled(False)
        self.create_acc_btn.setEnabled(False)
        self.back_btn2.setHidden(False)
        self.device_connected_lb.setPixmap(QPixmap(r"Appdata/images/scanner_available_false.png"))
        self.device_connected_lb2.setPixmap(QPixmap(r"Appdata/images/scanner_available_false.png"))
        self.is_device_linked = False
        self.device_pic_label.setPixmap(QPixmap(r'Appdata\images\start_connection.jpeg'))

        #Uncomment and Run this code to make and fill a temp library database to run this app

        if Dbconnection().is_connection():
            Dbconnection().makeDatabase()
        
        self.initialTimer()
            
    def install_event_filter_on_line_edits(self):
        '''self.setStyleSheet("""
            QPushButton:focus {
                border-right: 2px solid #0078D7;
                border-bottom: 2px solid #0078D7;
                border-left: none;
                border-top: none;
                padding: 6px;
                }
                """)'''
        #making lineedits take down key as input for switching
        self.lineedits = [ self.create_acc_btn, self.login_btn, self.firstname_input, self.lastname_input, self.userid_input, self.pass_input, self.ok_btn, self.back_btn1, self.userid_lineedit_2, self.pass_lineedit, self.ok_btn2, self.back_btn2, self.first_name_ln, self.last_name_ln, self.state_ln, self.city_ln, self.streetaddress_ln, self.phno_ln, self.userid_ln, self.ok_btn_2, self.booktitle_ln, self.isbn_ln, self.copies_ln, self.authoname_ln, self.newcat_lineedit, self.pushButton, self.libcardno_ln, self.bookisbn_ln1, self.issue_book_btn, self.libcardno_ln_2, self.pushButton_2 ]
              
        event_filter = KeyPressEventFilter(self, lineedits= self.lineedits)
        for widget in self.lineedits:
            widget.installEventFilter(event_filter)
        
    def initialTimer(self):
        #stopping database popup to show first instead of main widget
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.checkDbConnection)
        self.timer.start(200)
        
    def sendAutoEmail(self):
        em = EmailSender()
        if em.isInetConnection():
            em.checkAndSendEmail()
            self.em_timer.stop()
            
    def checkDbConnection(self):
        #checking if database is ready for use
        try:
            m = QMessageBox()
            e = CustomErrorAndLogWriting()
            if not Dbconnection().is_connection():
                msg = QMessageBox.critical(self, "can't proceed", "app is not connected with Mysql. Please connect with Mysql first.\nDo you want to EXIT Application?",buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if msg == QMessageBox.StandardButton.Yes:
                    #self.close()
                    QApplication.instance().quit()
                elif msg == QMessageBox.StandardButton.No:
                    self.checkDbConnection()
                    
            else:
                self.db_connected = True
                self.login_btn.setEnabled(True)
                self.create_acc_btn.setEnabled(True)
                self.showBorrowerPageFun(index=0)
                e = EmailSender()
                mydb = Dbconnection()
                c,db = mydb.makeConnection()
                failed = mydb.updatePenaltyInBorrowerDetails(c)
                if failed:
                    e.err = ErrorCodes(602)
                    raise e
                db.commit()
                self.em_timer = QTimer(self)
                self.em_timer.timeout.connect(self.sendAutoEmail)
                self.em_timer.start(10000)
                self.setui()
        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            
            elif isinstance(e,CustomErrorAndLogWriting):
                error_messages = {
            ErrorCodes(602):"Failed to update penalty of borrowers in borrower details.",
            }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()

            elif isinstance(e,Exception):
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
        
        if self.errors_names and self.e_msg:
            CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
            self.errors_names.clear()
            self.e_msg = ''
            
    def setui(self):
        #setting ui for create acc window
        self.login_btn.clicked.connect(self.showLoginPage)
        self.create_acc_btn.clicked.connect(self.showCreateAccountPage)
        self.checkBox.setChecked(True)
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setToolTip("Password must contain atleast 8 characters")
        self.pass_input.setPlaceholderText("Password must contain atleast 8 characters")
        self.checkBox.clicked.connect(self.toggleHidePassword)
        self.label_3.setText('')
        reg = RegExp()
        self.userid_input.setValidator(CustomValidator(reg.useridValidator(),msg="username12@domain-name.com"))
        self.userid_input.setToolTip("Enter your userid\ne.g: username12@gmail.com")
        self.firstname_input.setValidator(CustomValidator(reg.stringValidator(),msg="firstname containing alphabates"))
        self.firstname_input.setToolTip("Enter your first name")
        self.lastname_input.setValidator(CustomValidator(reg.stringValidator(),msg="lastname containing alphabates"))
        self.lastname_input.setToolTip("Enter your last name")
        self.userid_input.textChanged.connect(self.checkUserId)
        self.ok_btn.clicked.connect(self.createAccPageFun)
        self.back_btn1.clicked.connect(lambda:self.stackedWidget.setCurrentIndex(0))
        
        #setting ui for login window
        self.userid_lineedit_2.setValidator(CustomValidator(reg.useridValidator(),msg="username12@domain-name.com"))
        self.userid_lineedit_2.setToolTip("Enter your email id")
        self.pass_lineedit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_lineedit.setToolTip("Enter password")
        self.pass_lineedit.setPlaceholderText("Password must contain atleast 8 characters")
        self.hide_cb.clicked.connect(self.toggleHidePassword)
        self.ok_btn2.clicked.connect(self.loginPageFun)
        self.back_btn2.clicked.connect(lambda:self.stackedWidget.setCurrentIndex(0))
        self.loginasadmin_btn.clicked.connect(self.loginAsAdminfun)

        #setting afterlogin/sidemenu page widget
        self.sidemenu_btn.setCheckable(True)
        self.sidemenu_btn.clicked.connect(self.on_toggle)
        self.applylibcard_btn.clicked.connect(self.showLibcardApplyPage)
        self.showbook_btn.clicked.connect(self.showAllBooksPage)
        self.showborrower_btn.clicked.connect(self.showBorrowerPage)
        self.addbook_btn.clicked.connect(self.showAddNewBookPage)
        self.bookissue_btn.clicked.connect(self.showBookissuePage)
        self.showborrowerwithpenalty_btn.clicked.connect(self.showBorrowersWithPenaltyPage)
        self.bookreturn_btn.clicked.connect(self.showBookReturnPage)
        self.linkeddevicemanage_btn.clicked.connect(self.showManageLinkedDevicePage)
        self.signout_btn.clicked.connect(self.logout)

        #setting ui for showallbook page
        self.booksearch_ln1.setPlaceholderText("Search...")
        self.booksearch_ln1.textChanged.connect(self.showAllBooksPageFun)

        #setting ui for apply librarycard widget
        self.first_name_ln.setValidator(CustomValidator(reg.stringValidator(),msg="firstname containing alphabates"))
        self.first_name_ln.setToolTip("Enter the first name")
        self.last_name_ln.setValidator(CustomValidator(reg.stringValidator(),msg="lastname containing alphabates"))
        self.last_name_ln.setToolTip("Enter the last name")
        self.phno_ln.setValidator(CustomValidator(reg.phnoValidator(),msg="1234567890"))
        self.phno_ln.setToolTip("Enter phone number")
        self.userid_ln.setValidator(CustomValidator(reg.useridValidator(),msg="username12@domain-name.com"))
        self.userid_ln.setToolTip("Enter userid\n e.g.: abc@gmail.com")
        self.userid_ln.textChanged.connect(self.checkUserId)
        self.label_3a.setText('')
        self.state_ln.setValidator(CustomValidator(reg.stringValidator(),msg="state name containing alphabates"))
        self.state_ln.setToolTip("Enter state")
        self.city_ln.setValidator(CustomValidator(reg.stringValidator(),msg="city name containing alphabates"))
        self.city_ln.setToolTip("Enter city name")
        self.streetaddress_ln.setValidator(CustomValidator(reg.alphanumericValidator(),msg="34,near hosipital"))
        self.streetaddress_ln.setToolTip("Enter your house address")
        self.gen = ''
        self.female_rb.toggled.connect(self.gender)
        self.male_rb.toggled.connect(self.gender)
        self.is_imageset = False
        photo = self.make_circle_pixmap(image_path=r"Appdata/images/user_default_photo.png",diameter=300)
        self.photo_label.setPixmap(photo)
        self.photo_label.setStyleSheet("""#photo_label{
        border: 1px solid black;
        border-radius: 50%;}""")
        self.photo_label.setScaledContents(True)
        self.ok_btn_2.clicked.connect(self.showLibcardApplyPageFun)
        self.addphotobtn.clicked.connect(self.addPhoto)
        
        #setting ui for show borrowers widget
        self.comboBox.currentIndexChanged.connect(self.showBorrowerPageFun)
        self.showBorrowerPageFun(index=0)
        
        #setting ui for add new book widget
        self.pushButton.clicked.connect(self.showAddNewBookPageFun)
        self.authoname_ln.setValidator(CustomValidator(reg.stringValidatorWithSpace(),msg="authorname alphabates only"))
        self.authoname_ln.setToolTip("Enter author name")
        self.booktitle_ln.setValidator(CustomValidator(reg.stringValidatorWithSpace(),msg="book title alphabates only"))
        self.booktitle_ln.setToolTip("Enter book title")
        self.newcat_lineedit.setValidator(CustomValidator(reg.stringValidatorWithSpace(),msg="horror"))
        self.copies_ln.setValidator(CustomValidator(reg.numbersOnly(),msg="numbers only"))
        self.copies_ln.setToolTip("Enter number of copies of books")
        self.isbn_ln.setValidator(CustomValidator(reg.isbnValidator(),msg="9781101989197"))
        self.isbn_ln.setToolTip("Enter isbn number of book here")
        self.findAndSetCategory()
        self.addcat_button.clicked.connect(self.addNewCategory)

        #setting ui for book issue widget
        self.spacerItem15 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.issue_book_btn.clicked.connect(self.showBookissuePageFun)
        self.ok_btn_3.clicked.connect(self.addbooktoissue)
        self.ok_btn_3.setDisabled(True)
        self.libcardno_ln.setValidator(CustomValidator(reg.libcardnoValidator(),msg="numbers only"))
        self.libcardno_ln.textChanged.connect(lambda text, obj=self.libcardno_ln.objectName(): self.showLibcardHolderInfo(obj, text))
        self.libcardno_ln.on_focus.connect(self.onFocus)
        self.bookisbn_ln1.on_focus.connect(self.onFocus)
        self.bookisbn_ln1.setValidator(CustomValidator(reg.isbnValidator(),msg="111-1111-1111-11"))
        self.bookisbn_ln1.textChanged.connect(self.setAddBookbtnEnable)
        self.libcardholderinfo_bookissue_widget.setHidden(True)
        self.scan_n_fetch_btn1.clicked.connect(self.onScanAndFetch)            

        #setting ui for book return widget
        self.pushButton_2.clicked.connect(self.showBookReturnPageFun)
        self.libcardno_ln_2.setValidator(CustomValidator(reg.numbersOnly(),msg="numbers only"))
        self.libcardno_ln_2.textChanged.connect(lambda text, obj=self.libcardno_ln_2.objectName(): self.showLibcardHolderInfo(obj, text))
        self.showreturnedbooks_tableWidget.itemChanged.connect(self.onCBChangeReturnBooks)
        self.libcardholderinfo_bookreturn_widget.setHidden(True)
        self.libcardno_ln_2.on_focus.connect(self.onFocus)
        self.scan_n_fetch_btn2.clicked.connect(self.onScanAndFetch)
        self.pushButton_2.setDisabled(True)
        self.paypenaltybtn.clicked.connect(self.payPenalty)
        self.spacerItem18 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        #set ui for show all registered Users widget
        self.manageuser_btn.clicked.connect(self.showUsersPage)
        self.showusers_page.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.showusers_page.customContextMenuRequested.connect(self.showManageUsersContextMenu)

        ##set ui for show Book management widget
        self.bookmanagement_btn.clicked.connect(self.showBookManagePage)
        self.booksearch_ln.textChanged.connect(self.searchBooks)
        self.booksearch_ln.setPlaceholderText("Search...")
        self.bookmanagement_page.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.bookmanagement_page.customContextMenuRequested.connect(self.showBookManageContextMenu)
        self.bookmanagement_tableWidget.itemChanged.connect(self.changedBookInfo)

        #setting ui for linked device management page
        self.link_device_btn.clicked.connect(lambda: self.startServer(self.link_device_btn.text()))
        self.applink_lb.linkActivated.connect(self.open_link)
        
        self.install_event_filter_on_line_edits()

    def loginAsAdminfun(self):
        '''
        Takes user to login page when user wants to log in as admin.

        This function does not take any parameter and does not return any value.
        '''
        self.showLoginPage()
        self.back_btn2.setHidden(True)
    
    def checkUserId(self):
        '''
        Checks user id if its exist already or not and updating label to show if user id is taken or not.

        This function does not take any parameter and does not return any value.
        '''
        try:
            Mydb = Dbconnection()
            e = CustomErrorAndLogWriting()
            c,db = Mydb.makeConnection()
            ob = self.sender().objectName()
            if ob == self.userid_input.objectName():
                userid = str(self.userid_input.text())
                res = Mydb.search_userid(c,userid)
                if res is None:
                    e.err = ErrorCodes(100)
                    raise e
                
                #updating label to show if userid is taken or not for create new acc page
                if res == True:
                    self.label_3.setText("")
                
                else:
                    self.label_3.setText("User id is already occupied")

            elif ob == self.userid_ln.objectName():
                userid = str(self.userid_ln.text())
                self.is_userid_unique = None #variable to check if userid is unique in apply new libcard page
                res = Mydb.search_userid(c,userid)
                if res == None:
                    e.err = ErrorCodes(101)
                    raise e
                
                #updating label to show if userid is taken or not for new library card apply page.
                if res == True:
                    self.label_3a.setText("")
                    self.is_userid_unique = True
                
                else:
                    self.label_3a.setText("User id is already occupied")
                    self.is_userid_unique = False
            c.close(); db.close()

        except (AttributeError,Exception,CustomErrorAndLogWriting) as e :
            if isinstance(e,CustomErrorAndLogWriting):
                if e.err == ErrorCodes(100):
                    e.writeFailedOperation("Userid search for creating new account failed. Check error log.")
                elif e.err == ErrorCodes(101):
                    e.writeFailedOperation(emsg="Userid search for new libcard failed. Check error log.")
                    
            elif isinstance(e,AttributeError):
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            elif isinstance(e,Exception):
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())

    def gender(self):
        '''
        Takes which gender is selected and storing it into a variable.

        This function does not take any parameter and does not return any value.
        '''
        if self.female_rb.isChecked():
            self.gen = self.female_rb.text()
        elif self.male_rb.isChecked():
            self.gen = self.male_rb.text()
        
    def toggleHidePassword(self):
        '''
        Hides and shows the function when hide/show password checkbox is toggled and updates corresponding image.

        This function does not take any parameter and does not return any value.
        '''
        ob = self.sender().objectName()
        icon = QIcon()
        if ob == "checkBox":
            if  self.checkBox.isChecked():
                icon.addPixmap(QPixmap(r"Appdata/images/invisible.jpg"))
                self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            else: 
                icon.addPixmap(QPixmap(r"Appdata/images/visible.jpg"))
                self.pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.checkBox.setIconSize(QSize(16, 16))
            self.checkBox.setIcon(icon)
        
        elif ob == "hide_cb":
            icon = QIcon()
            if self.hide_cb.isChecked():
                icon.addPixmap(QPixmap(r"Appdata/images/invisible.jpg"), QIcon.Mode.Normal, QIcon.State.Off)
                self.pass_lineedit.setEchoMode(QLineEdit.EchoMode.Password)
            else: 
                icon.addPixmap(QPixmap(r"Appdata/images/visible.jpg"))
                self.pass_lineedit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.hide_cb.setIconSize(QSize(16, 16))
            self.hide_cb.setIcon(icon)

    def beforClose(self):
        '''
        do tasks before closing the app.

        This function does not take any parameter and does not return any value.
        '''
        self.startServer("Disconnect")

    def logout(self):
        '''
        Asks user if they really want to logout if yes then setting the app to default setting else pass.

        This function does not take any parameter and does not return any value.
        '''
        reply = QMessageBox.question(self, 'Log out',
                                     "Are you sure you want to Logout?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.stackedWidget.setCurrentIndex(0)
            self.restart()
        else:
            pass

    def closeEvent(self, event: QCloseEvent):
        '''
        Implimanting the QCloseEvent to ask user if they really want to exit the app if yes then accepting the event else ignore the close event.

        This function does not take any parameter and does not return any value.
        '''
        reply = QMessageBox.question(self, 'Exit Application?',
                                     "Are you sure you want to exit?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.beforClose()
            event.accept()  # Accept the close event and exit
            QApplication.instance().quit()
        else:
            event.ignore()  # Ignore the close event and do not exit
            
    def on_toggle(self,checked):
        '''
        Show and Hide side widget when side menu button is toggeled.

        This function does not take any parameter and does not return any value.
        '''
        if checked:
            self.sidemenu_widget.show();self.sa_sidewidget.show()
        else:
            self.sidemenu_widget.hide();self.sa_sidewidget.hide()
    
    def make_circle_pixmap(self, image_path: str, diameter: int):
        '''
        Makes the picture circular and returns the circular image.

        Parameters:
        image_path (str): path of image need to be made circular.
        diameter (int): diameter to make circular mask on picture
        
        Returns:
            mask (QPixmap): Circular picture.
        '''
        pixmap = QPixmap(image_path)
        # Ensure the image is cropped to a square before resizing
        min_side = min(pixmap.width(), pixmap.height())
        pixmap = pixmap.copy((pixmap.width() - min_side) // 2, (pixmap.height() - min_side) // 2, min_side, min_side)

        # Scale the image down to fit the circular label
        pixmap = pixmap.scaled(diameter, diameter, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # Create a circular mask
        mask = QPixmap(diameter, diameter)
        mask.fill(Qt.GlobalColor.transparent)

        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, diameter, diameter)  # Draw a perfect circle
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        return mask
    
    def addPhoto(self):
        '''
        Takes image input using dialog and set it on label of apply library card page after making the image circular.

        This function does not take any parameter and does not return any value.
        '''
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if file_path:  # Check if a file was selected
            new_pixmap = self.make_circle_pixmap(image_path=file_path,diameter=100)
            self.photo_label.setPixmap(new_pixmap.scaled(self.photo_label.width(), self.photo_label.height(),Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.is_imageset = True
            self.cur_image_path = file_path
                     
    def storeImage(self,libcardno)-> str:
        """
        Stores image in dedicated folder 

        Parameters:
            libcardno (str): libcardno to save image as unique and libcard holder's library card no.

        Returns:
            img_location (str): path of image stored in folder.
        """
        if self.cur_image_path:
            img = self.cur_image_path
            img_fullpath_no_ext = os.path.splitext(img)
            img_ext = img_fullpath_no_ext[1]
            new_img_name = f"{str(libcardno)}{img_ext}"
            img_location = os.path.join(self.LIBCARD_IMAGES_PATH,new_img_name)
            os.replace(img,os.path.join(self.LIBCARD_IMAGES_PATH,new_img_name))
            self.cur_image_path = None
            return img_location
            
    def createAccPageFun(self):
        """
        Function to create new account for the app

        This function does not take any parameters and does not return a value.
        """
        try:
            m = QMessageBox()
            e = CustomErrorAndLogWriting()
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            fn = ' '.join(self.firstname_input.text().split())
            ln = ' '.join(self.lastname_input.text().split())
            userid = self.userid_input.text()
            p = self.pass_input.text()
            
            if (fn != "") and ( ln != "") and (userid != "") and ("@" in userid and ".com" in userid) and (p != "") and len(p)>7:
                ano = Mydb.genid(c,"Ano","passwordsinfo")
                if ano is None:
                    e.err = ErrorCodes(200)
                    raise e
                failed = Mydb.insert_into_passwordinfo(c,ano,fn,ln,userid,p)
                if failed:
                    e.err = ErrorCodes(300)
                    raise e
                db.commit()
                m.information(self,"Success","New User is created sucessfully")
                self.showWelcomePage()
                self.firstname_input.clear()
                self.lastname_input.clear()
                self.userid_input.clear()
                self.pass_input.clear()
                self.is_userid_unique = False
            else:
                m.warning(self,"Failed","Please fill the input fields correctly")
            c.close(); db.close()
        except (AttributeError,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,AttributeError):
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            elif isinstance(e,CustomErrorAndLogWriting):
                if e.err == ErrorCodes(200):
                    e.writeFailedOperation("Failed to generate id for new user for create new account page")
                elif e.err == ErrorCodes(300):
                    e.writeFailedOperation("Failed to insert new user")
                    try:
                        db.rollback()
                    except Exception:
                        #to catch error related to rollback
                        CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            elif isinstance(e,Exception):
                #to catch any error
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())

    def changeFeature(self, role: str):
        """
        Function to add/remove admin feature or librarian features based on user role.

        Parameters:
        role (str): role of user.

        This function does not return a value.
        """
        if role == 'Admin':
            for i in range(self.horizontalLayout_9a.count()):
                widget = self.horizontalLayout_9a.itemAt(i).widget()
                if widget is not None:
                    widget.setVisible(False)

            for i in range(self.horizontalLayout_9b.count()):
                widget = self.horizontalLayout_9b.itemAt(i).widget()
                if widget is not None:
                    widget.setVisible(True)
            
            for i in range(self.horizontalLayout_9c.count()):
                widget = self.horizontalLayout_9c.itemAt(i).widget()
                if widget is not None:
                    widget.setVisible(True)
        elif role == '':
            for i in range(self.horizontalLayout_9b.count()):
                widget = self.horizontalLayout_9b.itemAt(i).widget()
                if widget is not None:
                    widget.setVisible(False)
            
            for i in range(self.horizontalLayout_9c.count()):
                widget = self.horizontalLayout_9c.itemAt(i).widget()
                if widget is not None:
                    widget.setVisible(False)

            for i in range(self.horizontalLayout_9a.count()):
                widget = self.horizontalLayout_9a.itemAt(i).widget()
                if widget is not None:
                    widget.setVisible(True)

    def loginPageFun(self):
        """
        Function to log in the application and show home page.
        
        This function does not take any parameter and does not return value.
        """
        try:
            m = QMessageBox()
            e = CustomErrorAndLogWriting()
            userid = self.userid_lineedit_2.text()
            p = self.pass_lineedit.text()
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            if (p != "") and len(p)>7:
                res = Mydb.checkuser_in_passwordinfo(c,userid,p)
                if res is None:
                    e.err = ErrorCodes(400)
                    raise e
                if len(res) == 0:
                    m.warning(self,"Failed","Login Failed please check the password or userid you entered")
                else:    
                    m.information(self,"LoggedIn","Logged In successfully :)")
                    self.role = res[0][1]
                    self.stackedWidget.setCurrentIndex(3)
                    self.sidemenu_btn.show()
                    self.userid_lineedit_2.clear()
                    p = self.pass_lineedit.clear()
                    
                    #show features according to the role.
                    if self.role == 'Admin':
                        self.changeFeature(role= 'Admin')
                    elif self.role == 'Librarian':
                        self.changeFeature(role= 'Librarian')     
            else:
                m.warning(self,"Failed","Please fill the input fields correctly")
            c.close(),db.close()
        
        except (AttributeError,CustomErrorAndLogWriting) as e:
            if isinstance(e,AttributeError):
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            elif isinstance(e,CustomErrorAndLogWriting):
                if e.err == ErrorCodes(400):
                    e.writeFailedOperation("Cant find userid with corresponding password to login.")
            elif isinstance(e,Exception):
                #to catch any error
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
        
    def showLibcardApplyPageFun(self):
        """
        Function to apply for new library card.
        
        This function does not take any parameter and does not return value.
        """
        try:
        #applying for libcard id
            fn = ' '.join(self.first_name_ln.text().split())
            ln = ' '.join(self.last_name_ln.text().split())
            gen = self.gen
            state = self.state_ln.text()
            city = self.city_ln.text()
            stad = ' '.join(self.streetaddress_ln.text().split())
            phno = self.phno_ln.text()
            userid = self.userid_ln.text()
            e = CustomErrorAndLogWriting()
            m = QMessageBox()
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()

            if (fn != "") and ( ln != "") and (gen != "") and (state != "") and (city != "") and (stad != "") and (phno != "") and (userid != "") and len(phno)==10 and self.is_userid_unique and self.is_imageset:
                #identifying if entered location exists in db or not
                lid = Mydb.genid(c,"libcard_id","library_card_info")
                if lid is None:
                    e.err = ErrorCodes(201)
                    raise e
                    
                libcardno=random.randint(10000000000000,99999999999999)
                msg = "New Library card is created sucessfully\n Your libcard no is: "+str(libcardno)
                photo_path = self.storeImage(libcardno=libcardno)
                
                res = Mydb.checklocation_existence(c,stad,city,state)
                if res is None:
                    e.err = ErrorCodes(102)
                    raise e
                rowc=len(res)
                    #if not
                if(rowc==0):
                    locid = Mydb.genid(c,"lid","location")
                    if locid is None:
                        e.err = ErrorCodes(202)
                        raise e
                    
                    failed1=Mydb.insert_new_location(c,locid,stad,city,state)
                    if failed1:
                        e.err = ErrorCodes(301)
                        raise e
                
                    failed2=Mydb.insert_new_libcard(c,lid,fn,ln,gen,locid,phno,userid,libcardno,photo_path)
                    if failed2:
                        e.err = ErrorCodes(302)
                        raise e
                    
                    db.commit()
                    m.information(self,"success",msg)
                    self.first_name_ln.clear()
                    self.last_name_ln.clear()
                    self.state_ln.clear()
                    self.city_ln.clear()
                    self.streetaddress_ln.clear()
                    self.phno_ln.clear()
                    self.userid_ln.clear()
                    self.is_userid_unique = False
                    self.photo_label.setPixmap(self.make_circle_pixmap(image_path=r"Appdata/images/user_default_photo.png",diameter=300))
                    self.is_imageset = False
                    #if found
                else:
                    for row in res:
                        locid=int(row[0])
                        failed2=Mydb.insert_new_libcard(c,lid,fn,ln,gen,locid,phno,userid,libcardno,photo_path)
                        if failed2:
                            e.err = ErrorCodes(303)
                            raise e
                        
                        db.commit()
                        m.information(self,"success",msg)
                        self.first_name_ln.clear()
                        self.last_name_ln.clear()
                        self.state_ln.clear()
                        self.city_ln.clear()
                        self.streetaddress_ln.clear()
                        self.phno_ln.clear()
                        self.userid_ln.clear()
                        self.is_userid_unique = False
                        self.photo_label.setPixmap(self.make_circle_pixmap(image_path=r"Appdata/images/user_default_photo.png",diameter=300))
                        self.is_imageset = False
                
                c.close();db.close()
            else:
                m.warning(self,"Can't proceed","Please Fill input fields correctly")
        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg+traceback.format_exc()+"\n"
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg+traceback.format_exc()+"\n"
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg+traceback.format_exc()+"\n"

            elif isinstance(e,CustomErrorAndLogWriting):
                if e.err == ErrorCodes(201):
                    e.writeFailedOperation("Failed to genrate new library card id (primary key).")
                elif e.err == ErrorCodes(102):
                    e.writeFailedOperation("Failed to search for given location.")
                elif e.err == ErrorCodes(202):
                    e.writeFailedOperation("Failed to generate new id for new location.")
                elif e.err == ErrorCodes(301):
                    try:
                        db.rollback()
                        e.writeFailedOperation("Failed to insert new location entry in location table.")
                    except Exception:
                        #to catch error related to rollback
                        CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
                elif e.err == ErrorCodes(302):
                    try:
                        db.rollback()
                        e.writeFailedOperation("Failed to insert new library card entry in library_card_info table.")
                    except Exception:
                        #to catch error related to rollback
                        CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
                elif e.err == ErrorCodes(303):
                    try:
                        db.rollback()
                        e.writeFailedOperation("Failed to insert new library card entry having existing location id as argument in library_card_info table.")
                    except Exception:
                        #to catch error related to rollback
                        CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
                    
            elif isinstance(e,Exception):
                #to catch any error
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            if self.errors_names and self.e_msg:            
                CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
                self.errors_names.clear()
                self.e_msg = ''   
        
    def showAllBooksPageFun(self,text):
        """
        Function to show all books.
        
        Parameters:
            text(str): search constraint.

        This function does not return value.
        """
        try:
            Mydb = Dbconnection()
            e = CustomErrorAndLogWriting()
            c,db = Mydb.makeConnection()
            self.showallbooks_tableWidget.clear()
            self.showallbooks_tableWidget.setRowCount(0)
            self.showallbooks_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            header,result = Mydb.showAllBooks(c,str(text))
            if header is None or result is None:
                e.err = ErrorCodes(103)
                raise e
            if result:
                self.showallbooks_tableWidget.setColumnCount(len(result[0]))
            else:
                self.showallbooks_tableWidget.setColumnCount(0)
            self.showallbooks_tableWidget.setHorizontalHeaderLabels(header)
            for rowno, row_data in enumerate(result):
                self.showallbooks_tableWidget.insertRow(rowno)
                for colno, data in enumerate(row_data):
                    self.showallbooks_tableWidget.setItem(rowno,colno,QTableWidgetItem(str(data)))
            c.close();db.close()    
        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.e_msg = self.e_msg = self.e_msg+traceback.format_exc()+"\n"
                self.errors_names.append("value")
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg+traceback.format_exc()+"\n"
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg+traceback.format_exc()+"\n"
            elif isinstance(e,CustomErrorAndLogWriting):
                if e.err == ErrorCodes(103):
                    e.writeFailedOperation(emsg="Failed to search book with given text")

            elif isinstance(e,Exception):
                QMessageBox().critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())

            if self.e_msg and self.errors_names:
                CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
                self.errors_names.clear()
                self.e_msg = ''

    def showBorrowerPageFun(self,index):
        """
        Function to show information about borrowers based on index.
        
        Parameters:
            index(str): index to show different borrowers result.

        This function does not return value.
        """
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            m = QMessageBox()
            self.showborrowers_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            if index == 0:
                result = ()
                self.showborrowers_tableWidget.clear()
                self.showborrowers_tableWidget.setRowCount(0)
                header,result = Mydb.showAllBorrowers(c)
                if header is None or result is None:
                    e.err = ErrorCodes(500)
                    raise e
                if header and result :
                    if len(result) != 0:
                        self.showborrowers_tableWidget.setColumnCount(len(result[0]))
                        self.showborrowers_tableWidget.setHorizontalHeaderLabels(header)
                        for rowno, row_data in enumerate(result):
                            self.showborrowers_tableWidget.insertRow(rowno)
                            for colno, data in enumerate(row_data):
                                self.showborrowers_tableWidget.setItem(rowno,colno,QTableWidgetItem(str(data)))

                    else:
                        m.information(self,"nothing to show","No Records to show")

            elif index == 1:
                result = ()
                self.showborrowers_tableWidget.clear()
                self.showborrowers_tableWidget.setRowCount(0)
                header,result = Mydb.showReturnedBorrowers(c)
                if header is None or result is None:
                    e.err = ErrorCodes(501)
                    raise e
                if len(result) != 0:
                    self.showborrowers_tableWidget.setColumnCount(len(result[0]))
                    self.showborrowers_tableWidget.setHorizontalHeaderLabels(header)
                    for rowno, row_data in enumerate(result):
                        self.showborrowers_tableWidget.insertRow(rowno)
                        for colno, data in enumerate(row_data):
                            self.showborrowers_tableWidget.setItem(rowno,colno,QTableWidgetItem(str(data)))
                else:
                    m.information(self,"nothing to show","No Records to show")
            elif index == 2:
                result = ()
                self.showborrowers_tableWidget.clear()
                self.showborrowers_tableWidget.setRowCount(0)
                
                header,result = Mydb.showNotReturnedBorrowers(c)
                if header is None or result is None:
                    e.err = ErrorCodes(502)
                    raise e
                if len(result) != 0:
                    self.showborrowers_tableWidget.setColumnCount(len(result[0]))
                    self.showborrowers_tableWidget.setHorizontalHeaderLabels(header)
                    for rowno, row_data in enumerate(result):
                        self.showborrowers_tableWidget.insertRow(rowno)
                        for colno, data in enumerate(row_data):
                            self.showborrowers_tableWidget.setItem(rowno,colno,QTableWidgetItem(str(data)))
                else:
                    m.information(self,"nothing to show","No Records to show")
            c.close();db.close()
        except (ValueError,AttributeError,mysql.connector.Error,CustomErrorAndLogWriting,Exception) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg+traceback.format_exc()+"\n"
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg+traceback.format_exc()+"\n"
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg+traceback.format_exc()+"\n"

            elif isinstance(e,CustomErrorAndLogWriting):
                if e.err == ErrorCodes(500):
                    e.writeFailedOperation(emsg="Failed to fetch information about all borrowers. Check logs for more information about errors.")
                elif e.err == ErrorCodes(501):
                    e.writeFailedOperation(emsg="Failed to fetch information about borrowers who have returned the book. Check logs for more information about errors.")
                elif e.err == ErrorCodes(502):
                    e.writeFailedOperation(emsg="Failed to fetch information about borrowers who haven't returned the books. Check logs for more information about errors.")

            elif isinstance(e,Exception):
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            if self.errors_names and self.e_msg:
                CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
                self.errors_names.clear()
                self.e_msg = ''
        
    def findAndSetCategory(self,delete_previous_labels:bool= False):
        """
        Function to set or update category as checkboxes and stores their references.
        
        Parameters:
            delete_previous_labels(bool): boolean value to delete outdated categories checkboxes if true.

        This function does not return value.
        """
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            m = QMessageBox()
            self.c_boxes = []
            categories = []
            
            if delete_previous_labels:
                for i in reversed(range(self.chbox_layout.count())):
                    child_layout = self.chbox_layout.itemAt(i).layout()
                    for j in reversed(range(child_layout.count())):
                        widget = child_layout.itemAt(j).widget()
                        child_layout.removeWidget(widget)
                        widget.deleteLater()
                    child_layout.deleteLater()

            res = Mydb.showAllCategories(c)
            if res is None:
                e.err = ErrorCodes(510)
                raise e
            categories = [row[0] for row in res]
            row_layout = None
            for i, ch in enumerate(categories):
                checkbox = QCheckBox(ch)
                if i % 2 == 0:
                    row_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
                    self.chbox_layout.addLayout(row_layout)
                row_layout.addWidget(checkbox)
                row_layout.setSpacing(1)
                self.c_boxes.append(checkbox)
                self.chbox_layout.update()
            c.close();db.close()
        except (ValueError,AttributeError,mysql.connector.Error,CustomErrorAndLogWriting,Exception) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg+traceback.format_exc()+"\n"
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg+traceback.format_exc()+"\n"
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg+traceback.format_exc()+"\n"
            elif isinstance(e,CustomErrorAndLogWriting):
                error_messages = {
                ErrorCodes(510): "Failed to fetch all categories from db to show it on add new book page."
                }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()
            if self.errors_names and self.e_msg:
                CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
                self.errors_names.clear()
                self.e_msg = ''

    def getCategories(self):
        """
        Function get all checked category checkboxes.
        
        Returns:
            categories(list): category list containing all checked categories.
        """
        categories = []
        for ch in self.c_boxes:
            if ch.isChecked():
                categories.append(ch.text())
        
        return categories
    
    def addNewCategory(self):
        """
        Function add new category and updating category checboxes layout.
        
        This function does not take any parameter and does not return any value.
        """
        try:
            category_name = ' '.join(self.newcat_lineedit.text().split())
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            m = QMessageBox()

            if not category_name:
                m.warning(self,"Error","Please Enter Category name first.")
                raise e
            res=Mydb.getCategoryid(c,category_name)
            if res:
                e.err = ErrorCodes(402)
                raise e
            cid = Mydb.genid(c,"cid","category_details")
            if cid is None:
                e.err = ErrorCodes(205)
                raise e
        
            failed=Mydb.insert_new_category(c,cid,category_name)
            if failed:
                e.err = ErrorCodes(306)
                raise e
            db.commit()
            self.newcat_lineedit.clear()
            c.close();db.close()
            self.findAndSetCategory(delete_previous_labels=True)
        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            
            elif isinstance(e,CustomErrorAndLogWriting):
                error_messages = {
        ErrorCodes(205): "Failed to generate new category ID for adding new book.",
        ErrorCodes(306): "Failed to insert new book for adding new book page.",
        ErrorCodes(402): "The category you are trying to add is already in categories."
    }

                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()
            
            elif isinstance(e,Exception):
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
        
        if self.errors_names and self.e_msg:
            CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
            self.errors_names.clear()
            self.e_msg = ''
   
    def showAddNewBookPageFun(self):
        """
        Function to add new book.
        
        This function does not take any parameter and does not return any value.
        """
        author_name = ' '.join(self.authoname_ln.text().split())
        book_title = ' '.join(self.booktitle_ln.text().split())
        cn = self.getCategories()
        no_of_copies = self.copies_ln.text()
        isbn = self.isbn_ln.text()
        m = QMessageBox()
        Mydb = Dbconnection()
        c,db = Mydb.makeConnection()
        e = CustomErrorAndLogWriting()
        if (author_name != "") and ( book_title != "") and any(cn) and (no_of_copies != "") and (isbn != "") :
            #finding author name in db
            try:
                aid = Mydb.genid(c,"aid","author_details")
                if aid is None:
                    e.err = ErrorCodes(203)
                    raise e
                    
                bid = Mydb.genid(c,"bid","book_details")
                if bid is None:
                    e.err = ErrorCodes(204)
                    raise e
                    
                res2 = Mydb.checkIfBookExist(c,isbn,book_title,author_name)
                if res2 is None:
                    e.err = ErrorCodes(401)
                    raise e
                    
                rowc2=len(res2)
                if rowc2 == 0:
                    res = Mydb.getAuthorid(c,author_name=author_name)
                    if res is None:
                        e.err = ErrorCodes(800)
                        raise e
                        
                    rowc=len(res)
                    if(rowc==0):    #if author name is not in db
                        failed1=Mydb.insert_new_author(c,aid,author_name)
                        if failed1:
                            e.err = ErrorCodes(304)
                            raise e
                        
                        #adding book when author name is not in db
                        failed2=Mydb.insert_new_book(c,bid,isbn,book_title,aid,no_of_copies)
                        if failed2:
                            e.err = ErrorCodes(305)
                            raise e
                            #identifying if entered category exists in db or not
                        for Category_name in cn:
                            res=Mydb.getCategoryid(c,Category_name)
                            if res is None:
                                e.err = ErrorCodes(802)
                                raise e                     
                            for row in res:
                                cid=int(row[0])
                            failed4=Mydb.insert_new_category_in_bookcategory(c,bid,cid)
                            if failed4:
                                e.err = ErrorCodes(307)
                                raise e
                    #if author exist in db    
                    else:
                        for row in res:
                            aid=int(row[0])
                        failed2=Mydb.insert_new_book(c,bid,isbn,book_title,aid,no_of_copies)
                        if failed2:
                                    e.err = ErrorCodes(309)
                                    raise e

                        for Category_name in cn:
                            res=Mydb.getCategoryid(c,Category_name)
                            if res is None:
                                e.err = ErrorCodes(801)
                                raise e
                            #if category is in db
                            for row in res:
                                cid=int(row[0])
                            failed4=Mydb.insert_new_category_in_bookcategory(c,bid,cid)
                            if failed4:
                                e.err = ErrorCodes(308)
                                raise e
                                
                    db.commit()
                    res = Mydb.getBookTitle(c,bid)
                    if res is None:
                        e.err = ErrorCodes(803)
                        raise e
                    for rows in res:
                        booktitle=str(rows[0])
                    m.information(self,"success","The New Book is added sucessfully\n whose title is: {}".format(booktitle))
                    self.showAllBooksPageFun("")
                    self.authoname_ln.clear()
                    self.booktitle_ln.clear()
                    self.newcat_lineedit.clear()
                    self.copies_ln.clear()
                    self.isbn_ln.clear()
                    for ch in self.c_boxes:
                        ch.setChecked(False)
                    self.c_boxes.clear()
                    
                
                else:
                    m.information(self,"error","The Book you are trying to add is already exist")
                c.close(); db.close()

            except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as e:
                if isinstance(e,ValueError):
                    self.errors_names.append("value")
                    self.e_msg = self.e_msg + traceback.format_exc()
                elif isinstance(e,AttributeError):
                    self.errors_names.append("attribute")
                    self.e_msg = self.e_msg + traceback.format_exc()
                elif isinstance(e,mysql.connector.Error):
                    self.errors_names.append("mysql")
                    self.e_msg = self.e_msg + traceback.format_exc()
                
                elif isinstance(e,CustomErrorAndLogWriting):
                    error_messages = {
            ErrorCodes(203): "Failed to generate author ID for adding new book.",
            ErrorCodes(204): "Failed to generate book ID for adding new book.",
            ErrorCodes(401): "Failed to check if book already exists.",
            ErrorCodes(800): "Failed to fetch author ID if it already exists.",
            ErrorCodes(304): "Failed to insert new author for adding a new book.",
            ErrorCodes(305): "Failed to insert new book when author does not exist.",
            ErrorCodes(802): "Failed to get category ID using category name when author does not exist.",
            #ErrorCodes.GENRATE_ID_CATEGORYDETAILS_NOAUTHOR_FAILED: "Failed to generate category ID when author does not exist.",
            #ErrorCodes.INSERT_NEWCATEGORY_CATEGORYDETAILS_NOAUTHOR_FAILED: "Failed to insert new category when author does not exist.",
            #ErrorCodes.INSERT_NEWCATEGORY_BOOKCATEGORY_NOAUTHOR_NOCAT_FAILED: "Failed to insert book-category relation when author and category do not exist.",
            ErrorCodes(307): "Failed to insert book-category relation when author does not exist but category exists.",
            ErrorCodes(309): "Failed to insert new book when author exists.",
            ErrorCodes(801): "Failed to get category ID using category name when author exists.",
            #ErrorCodes.GENRATE_ID_CATEGORYDETAILS_WHENAUTHOR_FAILED: "Failed to generate new category ID when author exists.",
            #ErrorCodes.INSERT_NEWCATEGORY_CATEGORYDETAILS_WITHAUTHOR_FAILED: "Failed to insert new category when author exists.",
            #ErrorCodes.INSERT_NEWCATEGORY_BOOKCATEGORY_WITHAUTHOR_NOCAT_FAILED: "Failed to insert new book-category relation when author exists but category does not.",
            ErrorCodes(308): "Failed to insert new book-category relation when both author and category exist.",
            ErrorCodes(803): "Failed to fetch book title using book ID.",
        }

                    if e.err in error_messages:
                        e.writeFailedOperation(emsg=error_messages[e.err])
                        db.rollback()
                
                elif isinstance(e,Exception):
                    m.critical(self,"Error","Some error occured check logs to see those errors")
                    CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            
            if self.errors_names and self.e_msg:
                CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
                self.errors_names.clear()
                self.e_msg = ''
        
        else:
            m.warning(self,"Can't proceed","Please Fill input fields correctly")      

    def setAddBookbtnEnable(self,text):
        """
        Function to make book issue button enable based on text.
        
        Parameters:
            text(str): text to find if there is entry of book or not in lineedit.
        
        This function does not return any value.
        """
        if text != '':
            self.ok_btn_3.setEnabled(True)
        self.ok_btn_3.setDisabled(True)

    def setScanAndAddbtn(self):
        """
        Function to set scan&fetch button to corresponding lineedit.
        
        This function does not take any parameter and does not return any value.
        """
        sender = self.sender().objectName()
        if sender == 'bookisbn_ln1':
            self.gridLayout_8.removeWidget(self.scan_n_fetch_btn1)
            self.gridLayout_8.addWidget(self.scan_n_fetch_btn1, 3,2,1,1)
        elif sender == 'libcardno_ln':
            self.gridLayout_8.removeWidget(self.scan_n_fetch_btn1)
            self.gridLayout_8.addWidget(self.scan_n_fetch_btn1, 2,2,1,1)
        
    def updateLinkedDeviceStatus(self):
        """
        Function to update status when app is connected to mobile scanner.
        
        This function does not take any parameter and does not return any value.
        """
        if not self.is_device_linked:
            self.device_connected_lb.setPixmap(QPixmap(r"Appdata/images/scanner_available_false.png"))
            self.device_connected_lb2.setPixmap(QPixmap(r"Appdata/images/scanner_available_false.png"))
            self.device_connected_lb3.setPixmap(QPixmap(r"Appdata/images/scanner_available_false.png"))
            self.is_device_linked = False
            self.device_pic_label.setPixmap(QPixmap(r'Appdata\images\start_connection.jpeg'))
            self.client_info_lb.setText("There is no device connected right now")
            self.server_info_lb.setText("Server is not running at this moment")
        else:
            self.device_connected_lb.setPixmap(QPixmap(r"Appdata/images/scanner_available_true.png"))
            self.device_connected_lb2.setPixmap(QPixmap(r"Appdata/images/scanner_available_true.png"))
            self.device_connected_lb3.setPixmap(QPixmap(r"Appdata/images/scanner_available_true.png"))
            self.device_pic_label.setPixmap(QPixmap(r'Appdata\images\device_connected.jpg'))

    def open_link(self, url):
        webbrowser.open(url)            

    @pyqtSlot(str)
    def display_message(self, message):
        """
        Function to get message from websocket and set it to its corresponding lineedit if message does not contains 'deviceInfo' in it.
        
        This function does not take any parameter and does not return any value.
        """
        msg = json.loads(message)
        if "deviceInfo" in msg:
            self.is_device_linked = True
            self.updateLinkedDeviceStatus()
            self.client_info_lb.setText(f"\nName: {msg["deviceInfo"]["name"]}\nModel: {msg["deviceInfo"]["model"]}\nOs: {msg["deviceInfo"]["os"]}")
            QMessageBox.information(self,'Connected', 'Connected with a device successfully')
        else:
            obj = next(iter(msg))
            target = self.findChild(ui.FocusSignalLineEdit, obj)
            target.setText(msg[obj])
        
    @pyqtSlot(bool)
    def clientDisconnected(self,disconnected):
        """
        Function to update status when app gets disconnected from mobile scanner.
        
        This function does not take any parameter and does not return any value.
        """
        if disconnected:
            self.is_device_linked = False
            QMessageBox.information(self,'Disconnected', 'Device is Disconnected!!')
            self.link_device_btn.setEnabled(True)
            self.updateLinkedDeviceStatus()        
    
    @pyqtSlot(str)
    def onFocus(self, lineedit_name):
        """
        Function to send lineedit object name as msg to scanner on websocket when lineedit get in focus.
        
        This function does not take any parameter and does not return any value.
        """
        self.setScanAndAddbtn()
        if self.ws_server.clients:
            msg = {lineedit_name: f"{lineedit_name}"}
            self.ws_server.sendMsg(msg=msg)

    def startServer(self, text):
        """
        Function to start/disconnect websocket server based on text.
        
        Parameter:
            text(str): text of button to trigger funtion based on the context

        This function does not return any value.
        """
        if text == 'Connect':
            self.ws_server.startServer()
            img = self.ws_server.makeQrcodeAndGetResult()
            self.device_pic_label.setPixmap(QPixmap(img))
            self.server_info_lb.setText("Starting Websocket Server at \n IPAddress:{}\n Port:{}\n".format(self.ws_server.IPAddress,self.ws_server.Port))
            self.link_device_btn.setText('Disconnect')
        else:
            self.ws_server.closeServer()
            self.is_device_linked = False
            self.updateLinkedDeviceStatus()
            self.link_device_btn.setText('Connect')

    def onScanAndFetch(self):
        """
        Function to called when scan&fetch button is clicked.
        
        This function does not take any parameter and does not return any value.
        """
        if not self.is_device_linked:
            self.stackedWidget.setCurrentIndex(13)
        else:
            QMessageBox.information(None,'Device Found', 'Already Linked with a device, place the cursor on lineedit to fetch the data')
        #showLibcardHolderBookissue

    def onCBChangeReturnBooks(self, item):
        """
        Function to make book return button enable when atleast one book to be returned is checked.
        
        This function does not take any parameter and does not return any value.
        """
        self.pushButton_2.setEnabled(False)         
        if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
            for cb in self.returnbooks:
                state = cb.checkState()
                if state == Qt.CheckState.Checked:
                    self.pushButton_2.setEnabled(True)         
    
    def checkPenalty(self):
        """
        Function to check if entered library card holder has penalty on him or not.
        
        This function does not take any parameter and does not return any value.
        """
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            m = QMessageBox()
            res = Mydb.checkPenalty(c,self.libcardno_ln_2.text())
            if res is None:
                e.err = ErrorCodes(403)
                raise e
            if len(res) != 0:
                return res
            return None
        
        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as err:
            if isinstance(err,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(err,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(err,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            
            elif isinstance(err,CustomErrorAndLogWriting):
                error_messages = {
                ErrorCodes(403): "Failed to check penalty for the borrower."
                }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()
                
            elif isinstance(e,Exception):
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            
            if self.errors_names and self.e_msg:
                CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
                self.errors_names.clear()
                self.e_msg = ''

    def showPenaltyMSG(self,data: list):
        """
        Function to ask user if they want to pay penalty or not.
        
        Parameter:
            data(list):  data that have info about penalty and borrower.
        
        This function does not return any value.
        """
        msg = QMessageBox(parent=self.bookreturn_page)
        msg.setWindowTitle("Penalty")
        msg.setText("This borrower has penalty on him\n Want to pay penalty right now?")
        btn_proceed = msg.addButton("Proceed", QMessageBox.ButtonRole.YesRole)
        btn_no = msg.addButton("Maybe Later", QMessageBox.ButtonRole.NoRole)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked == btn_proceed:
            self.payPenalty(data)
        elif clicked == btn_no:
            self.paypenaltybtn.setHidden(False)
            pass

    def payPenalty(self,dataset: list):
        """
        Function to pay penalty.
        
        Parameter:
            dataset(list):  dataset that have info about penalty and borrower.

        This function does not return any value.
        """
        class PenaltyWindow(QWidget):
            """
            Make and Manages Penalty related window.

            Attributes:
                pw (MyApp) = parent widget in this case instance of MyApp class.
                dataset (list) = dataset which holds info about borrowers with penalties.
                borwids_penalties (dict) = borwid_penalties which holdes borwid-penalty pair 

            Methods:
                setUi(): Sets the ui of Penalty Window.
                pay(): funtion to pay the penalty of borrower.
                closeEvent(): implemention close event.
            """
            def __init__(self, parent:QWidget=None, dataset:list =None,borwid_penalties:dict = None):
                super().__init__(parent)
                self.pw = parent
                self.dataset = dataset
                self.borwids_penalties = borwid_penalties
                self.setWindowTitle("Pay Penalty")
                self.setUi()
            def setUi(self):
                """
                Function to set ui of penalty window widget.

                This function does not take any Parameter and does not return any value.
                """
                self.setWindowTitle("Pay Penalty")
                self.setGeometry(int(self.pw.bookreturn_page.width()/2), int(self.pw.bookreturn_page.height()/2), 300, 200)
                self.setMaximumSize(300,200)
                layout = QGridLayout()
                self.name_lb = QLabel("Name:")
                self.name_ln = QLineEdit("")
                self.libcardno_lb = QLabel("Library-card no:")
                self.libcardno_ln = QLineEdit("")
                self.booktitle_lb = QLabel("Book titles:")
                self.booktitle_ln = QLineEdit("")
                self.penalty_lb = QLabel("Penalty to be paid:")
                self.penalty_is_ln = QLineEdit("")
                self.penalty_given_lb = QLabel("Penalty amount payment:")
                self.penalty_given_ln = QLineEdit("")

                outer_layout = QVBoxLayout()
                sp_item = QSpacerItem(40, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
                self.pay_penalty_btn = QPushButton("Pay Penalty",self)
                layout.addWidget(self.name_lb, 0, 0, 1, 1)
                layout.addWidget(self.name_ln, 0, 1, 1, 1)
                layout.addWidget(self.libcardno_lb, 1, 0, 1, 1)
                layout.addWidget(self.libcardno_ln, 1, 1, 1, 1)
                layout.addWidget(self.booktitle_lb, 2, 0, 1, 1)
                layout.addWidget(self.booktitle_ln, 2, 1, 1, 1)
                layout.addWidget(self.penalty_lb, 3, 0, 1, 1)
                layout.addWidget(self.penalty_is_ln, 3, 1, 1, 1)
                layout.addWidget(self.penalty_given_lb, 4, 0, 1, 1)
                layout.addWidget(self.penalty_given_ln, 4, 1, 1, 1)
                layout.setSpacing(0)
                layout.setHorizontalSpacing(10)
                layout.setVerticalSpacing(12)
                outer_layout.addLayout(layout)
                outer_layout.addSpacerItem(sp_item)
                outer_layout.addWidget(self.pay_penalty_btn)
                outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setLayout(outer_layout)
                self.pay_penalty_btn.setEnabled(True)
                self.pay_penalty_btn.clicked.connect(self.pay)
                self.pw.bookreturn_page.setEnabled(False)

            def pay(self):
                """
                Function to pay penalty of borrowers.

                This function does not take any Parameter and does not return any value.
                """
                try:
                    Mydb = Dbconnection()
                    c,db = Mydb.makeConnection()
                    e = CustomErrorAndLogWriting()
                    m = QMessageBox(parent= self)
                    amount = int(self.penalty_given_ln.text())
                    if self.name_ln.text() != '' and self.libcardno_ln.text() != '' and self.booktitle_ln.text() != '' and self.penalty_is_ln.text() != '' and self.penalty_given_ln.text():
                        for key,val in self.borwids_penalties.items():
                            at = int(self.borwids_penalties[key]) - amount
                            if at >= 0:
                                failed1=Mydb.adjustPenaltyInBorrowerDetails(c,borwid=key,penalty=val, new_penalty=at)
                                if failed1:
                                    e.err = ErrorCodes(603)
                                    raise e
                                break
                            else:
                                failed1=Mydb.adjustPenaltyInBorrowerDetails(c,borwid=key,penalty=val, new_penalty=0)
                                if failed1:
                                    e.err = ErrorCodes(603)
                                    raise e
                                amount = -at
                                continue
                        db.commit()
                        m.information(self,"Success","Penalty is paid successfully.")
                        self.pw.refreshPenalty()
                        self.close()
                except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as err:
                    if isinstance(err,ValueError):
                        self.pw.errors_names.append("value")
                        self.pw.e_msg = self.pw.e_msg + traceback.format_exc()
                    elif isinstance(err,AttributeError):
                        self.pw.errors_names.append("attribute")
                        self.pw.e_msg = self.pw.e_msg + traceback.format_exc()
                    elif isinstance(err,mysql.connector.Error):
                        self.pw.errors_names.append("mysql")
                        self.pw.e_msg = self.pw.e_msg + traceback.format_exc()
                    
                    elif isinstance(err,CustomErrorAndLogWriting):
                        error_messages = {
                        ErrorCodes(603): "Failed to pay and update penalty."
                        }
                        if e.err in error_messages:
                            e.writeFailedOperation(emsg=error_messages[e.err])
                            db.rollback()
                        
                    elif isinstance(e,Exception):
                        m.critical(self,"Error","Some error occured check logs to see those errors")
                        CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
                    
                    if self.pw.errors_names and self.pw.e_msg:
                        CustomErrorAndLogWriting().writeAllErrorInLog(self.pw.errors_names,self.pw.e_msg)
                        self.pw.errors_names.clear()
                        self.pw.e_msg = ''
                    
            def closeEvent(self, event: QCloseEvent):
                """
                Function implementing close event.

                This function does not take any Parameter and does not return any value.
                """
                self.pw.bookreturn_page.setDisabled(False) 
                event.accept()  # or event.ignore() to prevent closing
        booktitles = []
        penalties = []
        borwid_penalties = {}
        booktitle = ''
        if not dataset:
            dataset = self.checkPenalty()
        for data in dataset:
            borwid = data[0]
            name = data[1]
            libcardno = data[2]
            booktitle = data[3]
            booktitles.append(str(data[3]))
            penalty = int(data[4])
            penalties.append(int(data[4]))
            borwid_penalties[borwid] = penalty
        booktitle = ''
        if len(booktitles) == 1:
            booktitle = booktitle + booktitles[0]
        else:
            for i in range(1,len(booktitles)):
                booktitle = booktitles[i-1]+', '
            booktitle = booktitle+booktitles[-1]
            
        penalty_window = PenaltyWindow(parent=self,dataset=dataset, borwid_penalties=borwid_penalties)
        penalty_window.setWindowFlags(Qt.WindowType.Window)
        penalty_window.setEnabled(True)
        penalty_window.name_ln.setText(name)
        penalty_window.libcardno_ln.setText(str(libcardno))
        penalty_window.booktitle_ln.setText(booktitle)
        penalty_window.penalty_is_ln.setText(str(sum(penalties)))
        penalty_window.name_ln.setDisabled(True)
        penalty_window.libcardno_ln.setDisabled(True)
        penalty_window.booktitle_ln.setDisabled(True)
        penalty_window.penalty_is_ln.setDisabled(True)
        penalty_window.show()

    def refreshPenalty(self):
        """
        Function to update return books widget table with new data.

        This function does not take any Parameter and does not return any value.
        """
        self.showLibcardHolderInfo(self.libcardno_ln_2.objectName(), self.libcardno_ln_2.text())
        self.paypenaltybtn.setHidden(True)
        
    def showLibcardHolderInfo(self, obj, text):
        """
        Function to show borrower info based on obj parameter.

        Parameter:
            obj(str):   obj to find to show borrower info to their respecting widget
            text(str):  text which hold library card no.
            
        This function does not return any value.
        """
        try:
            lineedit = obj
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            m = QMessageBox()
            if len(text) == 14:
                res = Mydb.getLibcardHolderInfo(c,text)
                if res is None:
                    e.err = ErrorCodes(818)
                    raise e
                if lineedit == 'libcardno_ln':
                    name = str(res[0][0])+' '+str(res[0][1])
                    gen = str(res[0][2])
                    mobile = str(res[0][3])
                    userid = str(res[0][4])
                    libcard_no = str(res[0][5])
                    photo_path = str(res[0][6])
                    address = str(res[0][7])+" "+str(res[0][8])+" "+str(res[0][9])
                    self.name_label_bookissue.setText(name)
                    self.libcardnoislabel_bookissue.setText(libcard_no)
                    self.genderislabel_bookissue.setText(gen)
                    self.addressislabel_bookissue.setText(address)
                    self.useridislabel_bookissue.setText(userid)
                    self.phnoislabel_bookissue.setText(mobile)
                    self.photo_label_bookissue.setPixmap(self.make_circle_pixmap(image_path=r"{}".format(photo_path),diameter=196))
                    self.libcardholderinfo_bookissue_widget.setHidden(False)
                    
                elif lineedit == 'libcardno_ln_2':
                    self.returnbooks = []
                    name = str(res[0][0])+' '+str(res[0][1])
                    mobile = str(res[0][3])
                    userid = str(res[0][4])
                    libcard_no = str(res[0][5])
                    photo_path = str(res[0][6])
                    self.name_label_bookreturn.setText(name)
                    self.libcardnoislabel_bookreturn.setText(libcard_no)
                    self.useridislabel_bookreturn.setText(userid)
                    self.phnoislabel_bookreturn.setText(mobile)
                    self.photo_label_bookreturn.setPixmap(self.make_circle_pixmap(image_path=r"{}".format(photo_path),diameter=196))
                    self.libcardholderinfo_bookreturn_widget.setHidden(False)
                    self.showreturnedbooks_tableWidget.setColumnCount(0)
                    self.showreturnedbooks_tableWidget.setRowCount(0)
                    header,res = Mydb.getBorrowerInfo(c,self.libcardno_ln_2.text())
                    if header is None or res is None:
                        e.err = ErrorCodes(819)
                        raise e
                    if len(res) != 0:
                        self.showreturnedbooks_tableWidget.setColumnCount(len(res[0])+1)
                        self.showreturnedbooks_tableWidget.setHorizontalHeaderLabels([""]+header)
                        for rowno, row_data in enumerate(res):
                            self.showreturnedbooks_tableWidget.insertRow(rowno)
                            checkbox_item = QTableWidgetItem()
                            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
                            self.returnbooks.append(checkbox_item)
                            for colno, data in enumerate(row_data):
                                if colno == 0:
                                    self.showreturnedbooks_tableWidget.setItem(rowno,colno,checkbox_item)
                                self.showreturnedbooks_tableWidget.setItem(rowno,colno+1,QTableWidgetItem(str(data)))
                                QTableWidgetItem()
                        self.showreturnedbooks_tableWidget.setColumnHidden(1,True)
                        self.showreturnedbooks_tableWidget.setColumnHidden(2,True)
                        data = self.checkPenalty()
                        if data:
                            self.showPenaltyMSG(data)
                    else:
                        m.information(self,"nothing to show","No Records to show")
            else:
                if not self.libcardholderinfo_bookissue_widget.isHidden():
                    self.libcardholderinfo_bookissue_widget.setHidden(True)
                elif not self.libcardholderinfo_bookreturn_widget.isHidden():
                    self.showreturnedbooks_tableWidget.setRowCount(0)
                    self.showreturnedbooks_tableWidget.setColumnCount(0)
                    self.libcardholderinfo_bookreturn_widget.setHidden(True)
                pass

        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as err:
            if isinstance(err,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(err,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(err,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            
            elif isinstance(err,CustomErrorAndLogWriting):
                error_messages = {
                ErrorCodes(818): "Failed to fetch Library card holder details for book issue.",
                ErrorCodes(819): "Failed to fetch borrower details for book return."
                }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()
                
            elif isinstance(e,Exception):
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            
            if self.errors_names and self.e_msg:
                CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
                self.errors_names.clear()
                self.e_msg = ''

    def addbooktoissue(self):
        """
        Function to add book to be issued in table.

        This function does not take any parameter and does not return any value.
        """
        
        m = QMessageBox()
        Mydb = Dbconnection()
        c,db = Mydb.makeConnection()
        e = CustomErrorAndLogWriting()
        data = []
        try:
            for row in range(self.showissuedbooks_tableWidget.rowCount()):
                row_data = []
                for col in range (self.showissuedbooks_tableWidget.columnCount()):
                    if self.showissuedbooks_tableWidget.item(row,col):
                        row_data = row_data+[str(self.showissuedbooks_tableWidget.item(row,col).text())]
                if row_data:
                    data.append(tuple(row_data))     
            if self.bookisbn_ln1.text():
                header,res = Mydb.getBookInfo(c,self.bookisbn_ln1.text())
                if res is None:
                    e.err = ErrorCodes(817)
                    raise e
                elif not res:
                    m.critical(self,"Error","cant find book need to be issue")
            self.showissuedbooks_tableWidget.setRowCount(0)
            self.showissuedbooks_tableWidget.setColumnCount(0)
            data = data + res     
        
            if data:
                self.showissuedbooks_tableWidget.setRowCount(len(data))
                self.showissuedbooks_tableWidget.setColumnCount(len(data[0]))
                self.showissuedbooks_tableWidget.setHorizontalHeaderLabels(header)
                for i in range(len(data)):
                    for j in range(len(data[i])):
                        item = QTableWidgetItem(str(data[i][j]))
                        self.showissuedbooks_tableWidget.setItem(i,j,item)
            self.delete_action = QAction("Remove Book", self)
            self.delete_action.triggered.connect(self.delete_selected_row)

            # Add the action to the table
            self.showissuedbooks_tableWidget.addAction(self.delete_action)
            self.showissuedbooks_tableWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
            
            data.clear()
            c.close();db.close()

        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as err:
            if isinstance(err,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(err,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(err,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            
            elif isinstance(err,CustomErrorAndLogWriting):
                error_messages = {
                ErrorCodes(817): "Failed to fetch book info while adding it in book issue table."
                }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()
                
            elif isinstance(e,Exception):
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            
            if self.errors_names and self.e_msg:
                CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
                self.errors_names.clear()
                self.e_msg = ''
        
    def delete_selected_row(self):
        """
        Function to remove selected book from table.

        This function does not take any parameter and does not return any value.
        """
        selected = self.showissuedbooks_tableWidget.currentRow()
        if selected >= 0:
            self.showissuedbooks_tableWidget.removeRow(selected)
            
    def showBookissuePageFun(self):
        """
        Function to issue book.

        This function does not take any parameter and does not return any value.
        """
        Mydb = Dbconnection()
        c,db = Mydb.makeConnection()
        e = CustomErrorAndLogWriting()
        try:
            m = QMessageBox()
            libcardno= self.libcardno_ln.text()
            issued_books_isbns = []
            issued_books_names = []
            for row in range(self.showissuedbooks_tableWidget.rowCount()):
                issued_books_isbns.append(self.showissuedbooks_tableWidget.item(row,0).text())
            if libcardno != "" and len(libcardno)==14 and (self.showissuedbooks_tableWidget.rowCount() >0):
                res=Mydb.getLibcardid(c,libcardno)
                if res is None:
                    e.err = ErrorCodes(804)
                    raise e
                    
                rowc=len(res)
                #if library card no. is not in db
                if(rowc==0):
                    m.critical(self,"error","This Library card no. is not valid")
                    
                else:
                    for rows in res:
                        libcard_id=int(rows[0])
                    borwid = Mydb.genid(c,"borwid","borrower_details")
                    if borwid is None:
                        e.err = ErrorCodes(206)
                        raise e
                    for isbn in issued_books_isbns:
                        res=Mydb.getBookid(c,isbn)
                        if res is None:
                            e.err = ErrorCodes(806)
                            raise e
                        else:
                            for rows in res:
                                bid=int(rows[0])
                            failed1=Mydb.insert_in_bookborrower(c,borwid,bid,libcard_id)
                            if failed1:
                                e.err = ErrorCodes(311)
                                raise e
                            failed2= Mydb.updateCopiesInBookDetails(c,bid)
                            if failed2:
                                e.err = ErrorCodes(601)
                                raise e
                            else:
                                res = Mydb.getBookTitle_usingISBN(c,isbn)
                                if res is None:
                                    e.err = ErrorCodes(807)
                                    raise e
                                for rows in res:
                                    bookname=str(rows[0])
                                issued_books_names.append(bookname)
                db.commit()
                booknames = ''
                for bookname in issued_books_names:
                    booknames = booknames + bookname + '\n'
                m.information(self,"success","The books\n '{}' are checked out".format(booknames))
                self.libcardno_ln.clear()
                issued_books_isbns.clear()
                issued_books_names.clear()
                self.showissuedbooks_tableWidget.setRowCount(0)
                self.showissuedbooks_tableWidget.setColumnCount(0)            
                self.showBorrowerPageFun(0)
                self.showAllBooksPageFun("")
            else:
                m.warning(self,"Failed","Please fill the input fields correctly")
            c.close();db.close()
 
        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()

            elif isinstance(e,CustomErrorAndLogWriting):
                error_messages = {
            ErrorCodes(804):"Failed to get libcard id using library card no. for book issue.",
            ErrorCodes(206):"Failed to generate borwid for adding new borrower.",
            ErrorCodes(807):"Failed to get book title using isbn code when one book is being issued.",
            ErrorCodes(806):"Failed to get book id using isbn when more than one book is being issued.",
            ErrorCodes(311):"Failed to insert new borrower in borrower details when more than one book is being issued.",
            ErrorCodes(601):"Failed to update copies in book details when more than one book is being issued.",
            }
                if e.err in error_messages:
                        e.writeFailedOperation(emsg=error_messages[e.err])
                        db.rollback()

            elif isinstance(e,Exception):
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
        
        if self.errors_names and self.e_msg:
            CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
            self.errors_names.clear()
            self.e_msg = ''

    def showBorrowersWithPenaltyPageFun(self):
        """
        Function to show borrowers with penalty.

        This function does not take any parameter and does not return any value.
        """
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            m = QMessageBox()
            e = CustomErrorAndLogWriting()
            
            self.showborrowerwithpenalty_tableWidget.clear()
            self.showborrowerwithpenalty_tableWidget.setRowCount(0)
            self.showborrowerwithpenalty_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            failed = Mydb.updatePenaltyInBorrowerDetails(c)
            if failed:
                e.err = ErrorCodes(602)
                raise e
            db.commit()
            header,result = Mydb.showPenaltyBorrowers(c)
            if header is None or result is None:
                e.err = ErrorCodes(503)
                raise e
                
            if len(result) != 0:
                self.showborrowerwithpenalty_tableWidget.setColumnCount(len(result[0]))
                self.showborrowerwithpenalty_tableWidget.setHorizontalHeaderLabels(header)
                for rowno, row_data in enumerate(result):
                    self.showborrowerwithpenalty_tableWidget.insertRow(rowno)
                    for colno, data in enumerate(row_data):
                        self.showborrowerwithpenalty_tableWidget.setItem(rowno,colno,QTableWidgetItem(str(data)))
            else:
                m.information(self,"nothing to show","No Records to show")
            c.close();db.close()

        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            
            elif isinstance(e,CustomErrorAndLogWriting):
                error_messages = {
            ErrorCodes(602):"Failed to update penalty of borrowers in borrower details.",
            ErrorCodes(503):"Failed to fetch information about borrowers who has penalty."
            }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()

            elif isinstance(e,Exception):
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
        
        if self.errors_names and self.e_msg:
            CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
            self.errors_names.clear()
            self.e_msg = ''

    def showBookReturnPageFun(self):
        """
        Function to return book.

        This function does not take any parameter and does not return any value.
        """
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            m = QMessageBox()
            e = CustomErrorAndLogWriting()
            libcardno = self.libcardno_ln_2.text()
            booktitle = ''
            if libcardno != "":
                for item in self.returnbooks:
                    state = item.checkState()
                    if state == Qt.CheckState.Checked:
                        row = item.row()
                        item = self.showreturnedbooks_tableWidget.item(row, 1)
                        borwid = item.text()
                        item = self.showreturnedbooks_tableWidget.item(row, 2)
                        bid = item.text()

                        failed1=Mydb.updateReturnedBookInBookBorrower(c,borwid,bid)
                        if failed1:
                            e.err = ErrorCodes(606)
                            raise e
                        failed2=Mydb.updateReturnedCopiesInBookDetails(c,bid)
                        if failed2:
                            e.err = ErrorCodes(607)
                            raise e

                        res = Mydb.getBookTitle(c,bid)
                        if res is None:
                            e.err = ErrorCodes(812)
                            raise e
                        booktitle = booktitle + str(row[0]) +'\n'
                            
                m.information(self,"success","The books: '{}' are returned successfully!!".format(str(booktitle)))
                self.libcardno_ln_2.clear()
                self.returnbooks.clear()
                self.showBorrowerPageFun(0)
                self.showAllBooksPageFun("")
                db.commit()    
            else :
                m.warning(self,"Failed","Please fill the input fields correctly")
            c.close();db.close()
        except (ValueError,AttributeError,mysql.connector.Error,UnboundLocalError,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,UnboundLocalError):
                self.errors_names.append("unboundlocal")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,CustomErrorAndLogWriting):
                error_messages = {
            ErrorCodes(812):"Failed to get book title using book id to return book.",
            ErrorCodes.GET_BOOKID_USINGISBN_TORETURNMANYBOOK_FAILED:"Failed to get book id using isbn to return many books.",
            ErrorCodes(606):"Failed to update borrower details when many books are returned.",
            ErrorCodes(607):"Failed to update copies of books when many books are returned.",
            }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()

            elif isinstance(e,Exception):
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
        
        if self.errors_names and self.e_msg:
            CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
            self.errors_names.clear()
            self.e_msg = ''
            
    def showUsersPageFun(self):
        """
        Function to show management people in table.

        This function does not take any parameter and does not return any value.
        """
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            
            self.showusers_tableWidget.clear()
            self.showusers_tableWidget.setRowCount(0)
            self.showusers_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            header,result = Mydb.showAllRegisteredUsers(c)
            if header is None or result  is None:
                e.err = ErrorCodes(504)
                raise e
                
            self.showusers_tableWidget.setColumnCount(len(result[0])+1)
            self.showusers_tableWidget.setHorizontalHeaderLabels(['']+header)
            self.showusers_tableWidget.setColumnWidth(0, 50)
            for rowno, row_data in enumerate(result):
                self.showusers_tableWidget.insertRow(rowno)
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.CheckState.Unchecked)
                self.showusers_tableWidget.setItem(rowno, 0, checkbox_item)
                for colno, data in enumerate(row_data):
                    self.showusers_tableWidget.setItem(rowno,colno+1,QTableWidgetItem(str(data)))
            self.showusers_tableWidget.hideColumn(1)
            c.close();db.close()
        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,CustomErrorAndLogWriting):
                error_messages = {
            ErrorCodes(504):"Failed to fetch information about all registered user in passwordinfo."
            }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()
            
            elif isinstance(e,Exception):
                QMessageBox.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
        
        if self.errors_names and self.e_msg:
            CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
            self.errors_names.clear()
            self.e_msg = ''
            
    def showManageUsersContextMenu(self, pos):
        """
        Function to add context menu to perform actions on management people.

        Parameters:
            pos(QPoint|QPointF):    position on which context menu will be shown.
        
        This function does not return any value.
        """
        context_menu = QMenu(self)
        icona1 = QIcon()
        icona2 = QIcon()
        icona3 = QIcon()

        icona1.addPixmap(QPixmap(r"Appdata/images/delete_users.png"), QIcon.Mode.Normal, QIcon.State.Off)
        icona2.addPixmap(QPixmap(r"Appdata/images/admin.png"), QIcon.Mode.Normal, QIcon.State.Off)
        icona3.addPixmap(QPixmap(r"Appdata/images/remove_admin.png"), QIcon.Mode.Normal, QIcon.State.Off)
        action1 = context_menu.addAction(icona1, "Delete Users")
        action2 = context_menu.addAction(icona2, "Give Admin privilage")
        action3 = context_menu.addAction(icona3, "Remove Admin privilage")

        action1.triggered.connect(self.deleteUser)
        action2.triggered.connect(self.makeAdmin)
        action3.triggered.connect(self.removeAdmin)

        context_menu.exec(self.showusers_page.mapToGlobal(pos))

    def deleteUser(self):
        """
        Function to delete management people.
        
        This function does not take any parameter and does not return any value.
        """
        try:
            ids = []
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            for id in self.get_checked_rows():
                ids.append(id[0])

            for id in ids:
                res = Mydb.deleteUsersFromPasswordinfo(c,uid=id)

            if res is None:
                e.err = ErrorCodes(700)
                raise e
            ids.clear()
            db.commit()
            c.close();db.close()
            self.showUsersPageFun()
        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,CustomErrorAndLogWriting):
                error_messages = {
            ErrorCodes(700):"Failed to delete user from passwordinfo."
            }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()

            elif isinstance(e,Exception):
                QMessageBox.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
        
        if self.errors_names and self.e_msg:
            CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
            self.errors_names.clear()
            self.e_msg = ''
            
    def makeAdmin(self):
        """
        Function to make management people role to admin.
        
        This function does not take any parameter and does not return any value.
        """
        try:
            ids = []
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            for id in self.get_checked_rows():
                ids.append(id[0])
            for id in ids:
               failed = Mydb.updateRoletoAdmin(c,uid=id)
            if failed:
                e.err = ErrorCodes(608)
                raise e
            ids.clear()
            db.commit()
            c.close();db.close()
            self.showUsersPageFun()
        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,CustomErrorAndLogWriting):
                error_messages = {
            ErrorCodes(608):"Failed to update user role to admin in passwordinfo."
            }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()

            elif isinstance(e,Exception):
                QMessageBox.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
        
        if self.errors_names and self.e_msg:
            CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
            self.errors_names.clear()
            self.e_msg = ''
            
    def removeAdmin(self):
        """
        Function to make management people role to librarian.
        
        This function does not take any parameter and does not return any value.
        """
        try:
            ids = []
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            for id in self.get_checked_rows():
                ids.append(id[0])
            for id in ids:
                failed = Mydb.updateRoletolibrarian(c,uid=id)
            if failed:
                e.err = ErrorCodes(609)
                raise e
            ids.clear()
            db.commit()
            c.close();db.close()
            self.showUsersPageFun()
        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,CustomErrorAndLogWriting):
                error_messages = {
            ErrorCodes(609):"Failed to update user role to librarian in passwordinfo."
            }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()

            elif isinstance(e,Exception):
                QMessageBox.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
        
        if self.errors_names and self.e_msg:
            CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
            self.errors_names.clear()
            self.e_msg = ''
            
    def get_checked_rows(self):
        """
        Function to take selected management people to perform actions on them.
        
        This function does not take any parameter and does not return any value.
        """
        checked_rows = []
        for row in range(self.showusers_tableWidget.rowCount()):
            checkbox_item = self.showusers_tableWidget.item(row, 0)
            if checkbox_item is not None and checkbox_item.checkState() == Qt.CheckState.Checked:
                row_data = []
                for col in range(1, self.showusers_tableWidget.columnCount()):  
                    item = self.showusers_tableWidget.item(row, col)
                    if item is not None:
                        row_data.append(item.text())
                checked_rows.append(row_data)
        return checked_rows

    def searchBooks(self,text):
        """
        Function to search book and show them on table based on text.
        
        Parameter:
            text(str):  text to be search.
        
        This function does not return any value.
        """
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            self.bookmanagement_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
            self.bookmanagement_tableWidget.itemChanged.disconnect(self.changedBookInfo)
        except TypeError:
            pass
            
            e = CustomErrorAndLogWriting()
            search_item = str(self.booksearch_ln.text())
            search_item = str(text)
            header,res = Mydb.searchBooks(c,search_item)

            if res is None or header is None:
                e.err = ErrorCodes(505)
                raise e
            if len(res) == 0:
                self.showusers_tableWidget.clear()
                self.showusers_tableWidget.setRowCount(0)
                self.showusers_tableWidget.setColumnCount(0)
            else:
                self.bookmanagement_tableWidget.clear()
                self.bookmanagement_tableWidget.setRowCount(0)
                self.bookmanagement_tableWidget.setColumnCount(len(res[0]))
                self.bookmanagement_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
                self.bookmanagement_tableWidget.setHorizontalHeaderLabels(header)
                for rowno, row_data in enumerate(res):
                    self.bookmanagement_tableWidget.insertRow(rowno)
                    for colno, data in enumerate(row_data):
                        self.bookmanagement_tableWidget.setItem(rowno,colno,QTableWidgetItem(str(data)))
                c.close();db.close()
        except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,CustomErrorAndLogWriting):
                error_messages = {
            ErrorCodes(505):"Failed to fetch all books details to make changes in book details for admin."
            }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()

            elif isinstance(e,Exception):
                QMessageBox.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
        
        if self.errors_names and self.e_msg:
            CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
            self.errors_names.clear()
            self.e_msg = ''
                
    def showBookmanagementFun(self,header,result):
        """
        Function to show books in table for managing.
        
        Parameter:
            header(list):  header of the tabel.
            result(list):  book data of the tabel.
        
        This function does not return any value.
        """
        try:
            self.bookmanagement_tableWidget.itemChanged.disconnect(self.changedBookInfo)
            self.bookmanagement_tableWidget.clear()
            self.bookmanagement_tableWidget.setRowCount(0)
            self.bookmanagement_tableWidget.setColumnCount(len(result[0]))
            self.bookmanagement_tableWidget.setHorizontalHeaderLabels(header)
            self.bookmanagement_tableWidget.setColumnWidth(0, 50)
            for rowno, row_data in enumerate(result):
                self.bookmanagement_tableWidget.insertRow(rowno)
                for colno, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.bookmanagement_tableWidget.setItem(rowno,colno,item)
            self.bookmanagement_tableWidget.hideColumn(0)
            self.bookmanagement_tableWidget.hideColumn(1)
        
        except TypeError:
            pass
        except (ValueError,TypeError,AttributeError,mysql.connector.Error) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,Exception):
                    QMessageBox.critical(self,"Error","Some error occured check logs to see those errors")
                    CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            
        if self.errors_names and self.e_msg:
            CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
            self.errors_names.clear()
            self.e_msg = ''
 
    def showBookManageContextMenu(self, pos):
        """
        Function to show context menu for managing of books in table.
        
        Parameter:
            pos(QPoint| QPointF):  position where context menu will be shown.
        
        This function does not return any value.
        """
        context_menu = QMenu(self)
        action1 = context_menu.addAction("Edit Book-title")
        action2 = context_menu.addAction("Edit isbn code")
        action3 = context_menu.addAction("Edit no. of copies")
        action4 = context_menu.addAction("Edit Author name")

        action1.triggered.connect(self.editBookTitle)
        action2.triggered.connect(self.editISBN)
        action3.triggered.connect(self.editNoOfCopies)
        action4.triggered.connect(self.editAuthorName)
        context_menu.exec(self.showusers_page.mapToGlobal(pos))

    def editBookTitle(self):
        """
        Function to make book title column editable.
        
        This function does not take any parameter and does not return any value.
        """
        try:
            self.bookmanagement_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
            self.bookmanagement_tableWidget.itemChanged.disconnect(self.changedBookInfo)
        except TypeError:
            pass
        for rowno in range(self.bookmanagement_tableWidget.rowCount()):
                for colno in range(self.bookmanagement_tableWidget.columnCount()):
                    if colno == 3:
                        item = self.bookmanagement_tableWidget.item(rowno, colno)
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    else:
                        item = self.bookmanagement_tableWidget.item(rowno, colno)
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        self.bookmanagement_tableWidget.editItem(self.bookmanagement_tableWidget.item(0, 3))
        self.bookmanagement_tableWidget.itemChanged.connect(self.changedBookInfo)
        
    def editISBN(self):
        """
        Function to make book isbn column editable.
        
        This function does not take any parameter and does not return any value.
        """
        try:
            self.bookmanagement_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
            self.bookmanagement_tableWidget.itemChanged.disconnect(self.changedBookInfo)
        except TypeError:
            pass
        for rowno in range(self.bookmanagement_tableWidget.rowCount()):
                for colno in range(self.bookmanagement_tableWidget.columnCount()):
                    if colno == 2:
                        item = self.bookmanagement_tableWidget.item(rowno, colno)
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    else:
                        item = self.bookmanagement_tableWidget.item(rowno, colno)
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        self.bookmanagement_tableWidget.editItem(self.bookmanagement_tableWidget.item(0, 2))
        self.bookmanagement_tableWidget.itemChanged.connect(self.changedBookInfo)

    def editNoOfCopies(self):
        """
        Function to make no. of copies column editable.
        
        This function does not take any parameter and does not return any value.
        """
        try:
            self.bookmanagement_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
            self.bookmanagement_tableWidget.itemChanged.disconnect(self.changedBookInfo)
        except TypeError:
            pass
        for rowno in range(self.bookmanagement_tableWidget.rowCount()):
                for colno in range(self.bookmanagement_tableWidget.columnCount()):
                    if colno == 4:
                        item = self.bookmanagement_tableWidget.item(rowno, colno)
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    else:
                        item = self.bookmanagement_tableWidget.item(rowno, colno)
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        self.bookmanagement_tableWidget.editItem(self.bookmanagement_tableWidget.item(0, 4))
        self.bookmanagement_tableWidget.itemChanged.connect(self.changedBookInfo)
        
    def editAuthorName(self):
        """
        Function to make book author name column editable.
        
        This function does not take any parameter and does not return any value.
        """
        try:
            self.bookmanagement_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
            self.bookmanagement_tableWidget.itemChanged.disconnect(self.changedBookInfo)
        except TypeError:
            pass
        for rowno in range(self.bookmanagement_tableWidget.rowCount()):
                for colno in range(self.bookmanagement_tableWidget.columnCount()):
                    if colno == 5:
                        item = self.bookmanagement_tableWidget.item(rowno, colno)
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    else:
                        item = self.bookmanagement_tableWidget.item(rowno, colno)
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        self.bookmanagement_tableWidget.editItem(self.bookmanagement_tableWidget.item(0, 5))
        self.bookmanagement_tableWidget.itemChanged.connect(self.changedBookInfo)

    def changedBookInfo(self, item:QTableWidgetItem):
        """
        Function to update changed item from book management table.
        
        Parameter:
            item(QTableWidgetItem): item which is changed in book management table.
        This function does not return any value.
        """
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            if item.column() == 2:
                text = item.text()
                id = self.bookmanagement_tableWidget.item(item.row(), 0).text()
                failed = Mydb.updateISBN(c,id,text)
                if failed:
                    e.err = ErrorCodes(610)
                    raise e
                    
                header,res = Mydb.searchBooks(c,
                self.booksearch_ln.text())
                if header is  None or res is None:
                    e.err = ErrorCodes(506)
                    raise e
                    
                self.showBookmanagementFun(header,res)
                self.editISBN()

            elif item.column() == 3:
                text = item.text()
                id = self.bookmanagement_tableWidget.item(item.row(), 0).text()
                failed = Mydb.updateBookTitle(c,id,text)
                if failed:
                    e.err = ErrorCodes(611)
                    raise e
                    
                header,res = Mydb.searchBooks(c,self.booksearch_ln.text())
                if header is  None or res is None:
                    e.err = ErrorCodes(507)
                    raise e
                    
                self.showBookmanagementFun(header,res)
                self.editBookTitle()
            elif item.column() == 4:
                text = item.text()
                id = self.bookmanagement_tableWidget.item(item.row(), 0).text()
                failed = Mydb.updateNoOfCopies(c,id,text)
                if failed:
                    e.err = ErrorCodes(612)
                    raise e
                    
                header,res = Mydb.searchBooks(c,self.booksearch_ln.text())
                if header is  None or res is None:
                    e.err = ErrorCodes(508)
                    raise e
                    
                self.showBookmanagementFun(header,res)
                self.editNoOfCopies()
            elif item.column() == 5:
                text = item.text()
                id = self.bookmanagement_tableWidget.item(item.row(), 1).text()
                failed = Mydb.updateAuthorName(c,id,text)
                if failed:
                    e.err = ErrorCodes(613)
                    raise e
                    
                header,res = Mydb.searchBooks(c,self.booksearch_ln.text())
                if header is  None or res is None:
                    e.err = ErrorCodes(509)
                    raise e
                self.showBookmanagementFun(header,res)
                self.editAuthorName()
            db.commit()
            c.close();db.close()
        except (ValueError,TypeError,AttributeError,mysql.connector.Error,CustomErrorAndLogWriting) as e:
            if isinstance(e,ValueError):
                self.errors_names.append("value")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,AttributeError):
                self.errors_names.append("attribute")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,mysql.connector.Error):
                self.errors_names.append("mysql")
                self.e_msg = self.e_msg + traceback.format_exc()
            elif isinstance(e,CustomErrorAndLogWriting):
                    error_messages = {
                ErrorCodes(610):"Failed to update book isbn.",
                ErrorCodes(506):"Failed to fetch information about books to change isbn.",
                ErrorCodes(611):"Failed to update book title",
                ErrorCodes(507):"Failed to fetch information about books to change booktitle.",
                ErrorCodes(612):"Failed to update book copies.",
                ErrorCodes(508):"Failed to fetch information about books to change no. of copies.",
                ErrorCodes(613):"Failed to update book's author name.",
                ErrorCodes(509):"Failed to fetch information about books to change author name."
                }
                    if e.err in error_messages:
                        e.writeFailedOperation(emsg=error_messages[e.err])
                        db.rollback()
                        
            elif isinstance(e,Exception):
                    QMessageBox.critical(self,"Error","Some error occured check logs to see those errors")
                    CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            
        if self.errors_names and self.e_msg:
            CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
            self.errors_names.clear()
            self.e_msg = ''

    def showWelcomePage(self):
        self.stackedWidget.setCurrentIndex(0)    
    def showCreateAccountPage(self):
        self.stackedWidget.setCurrentIndex(2)
    def showLoginPage(self):
        self.stackedWidget.setCurrentIndex(1)
    def showAfterLoginPage(self):
        self.stackedWidget.setCurrentIndex(3)
    def showLibcardApplyPage(self):
        self.stackedWidget.setCurrentIndex(4)
    def showAllBooksPage(self):
        self.stackedWidget.setCurrentIndex(5)
        self.showAllBooksPageFun("")
    def showBorrowerPage(self):
        self.stackedWidget.setCurrentIndex(6)
    def showAddNewBookPage(self):
        self.stackedWidget.setCurrentIndex(7)
    def showBookissuePage(self):
        self.stackedWidget.setCurrentIndex(8)
    def showBorrowersWithPenaltyPage(self):
        self.stackedWidget.setCurrentIndex(9)
        self.showBorrowersWithPenaltyPageFun()
    def showBookReturnPage(self):
        self.stackedWidget.setCurrentIndex(10)
    def showUsersPage(self):
        self.stackedWidget.setCurrentIndex(11)
        self.showUsersPageFun()
    def showBookManagePage(self):
        self.stackedWidget.setCurrentIndex(12)
        Mydb = Dbconnection()
        c,db = Mydb.makeConnection()
        header,res = Mydb.searchBooks(c,"")
        c.close;db.close()
        self.showBookmanagementFun(header=header, result=res)
    def showManageLinkedDevicePage(self):
        self.stackedWidget.setCurrentIndex(13)
    

if __name__ == "__main__":
    app = QApplication(sys.argv) 
    ws_server = WebSocketServer()
    window = MyApp(ws_server) 
    window.show() 
    
    sys.exit(app.exec()) 
