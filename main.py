import sys,traceback, os
import json
import mysql.connector, random  
from mysql.connector import Error
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMessageBox, QTableWidgetItem, QLineEdit, QAbstractItemView, QFileDialog
from PyQt6.QtCore import QRegularExpression, QTimer, Qt, QObject, QEvent, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QRegularExpressionValidator, QCloseEvent, QIcon, QPixmap, QPainter, QPainterPath, QAction

import libui as ui
from db import Dbconnection
from Email_sender import EmailSender
import log
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
        regexp = QRegularExpression("^[A-Za-z]+[0-9A-Za-z]+@[A-za-z]+\\.com$")
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
        regexp = QRegularExpression("^[0-9][0-9-]{16}$")
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
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                # Move to the next QLineEdit
                widget = obj
                while widget:
                    widget = widget.nextInFocusChain()
                    if isinstance(widget, QLineEdit) and widget.isVisible():
                        widget.setFocus()
                        break
                return True
            elif event.key() == Qt.Key.Key_Up:
                # Move to the previous QLineEdit
                widget = obj
                while widget:
                    widget = widget.previousInFocusChain()
                    if isinstance(widget, QLineEdit) and widget.isVisible():
                        widget.setFocus()
                        break
                return True
        return super().eventFilter(obj, event)



class MyApp(QtWidgets.QMainWindow, ui.Ui_MainWindow):
    def __init__(self, ws_server:'WebSocketServer'):
        super().__init__()
        self.ws_server = ws_server
        self.errors_names = []
        self.e_msg = ""
        self.LIBCARD_IMAGES_PATH = os.path.join("Appdata","LibrarycardImages")
        self.setupUi(self)
        #self.setui()
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
        #making lineedits take down key as input for switching
        event_filter = KeyPressEventFilter(self)
        for child in self.findChildren(QLineEdit):
            child.installEventFilter(event_filter)

    def initialTimer(self):
        #stopping database popup to show first instead of main widget
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.checkDbConnection)
        self.timer.start(200)
        
        

    def checkDbConnection(self):
        #checking if database is ready for use
        if not Dbconnection().is_connection():
            msg = QMessageBox.critical(self, "can't proceed", "app is not connected with Mysql. Please connect with Mysql first.\nDo you want to EXIT Application?",buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if msg == QMessageBox.StandardButton.Yes:
                self.close()

            else:
                self.checkDbConnection()
                
        else:
            self.db_connected = True
            self.login_btn.setEnabled(True)
            self.create_acc_btn.setEnabled(True)
            self.showBorrowerPageFun(index=0)
            e = EmailSender()
            e.checkAndSendEmail()
            self.setui()
            

    def setui(self):
        
        #setting ui for create acc window
        self.setWindowIcon(QIcon('Appdata/images/lib.ico'))
        self.login_btn.clicked.connect(self.showLoginPage)
        self.create_acc_btn.clicked.connect(self.showCreateAccountPage)
        self.checkBox.setChecked(True)
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setToolTip("Password must contain atleast 8 characters")
        self.pass_input.setPlaceholderText("Password must contain atleast 8 characters")
        self.checkBox.clicked.connect(self.unHidePassword)
        self.label_3.setText('')
        reg = RegExp()
        #self.userid_input.setValidator(QRegularExpressionValidator(reg.useridValidator()))
        self.userid_input.setValidator(CustomValidator(reg.useridValidator(),msg="username12@domain-name.com"))
        self.userid_input.setToolTip("Enter your userid\ne.g: username12@gmail.com")
        #self.firstname_input.setValidator(QRegularExpressionValidator(reg.stringValidator()))
        self.firstname_input.setValidator(CustomValidator(reg.stringValidator(),msg="firstname containing alphabates"))
        self.firstname_input.setToolTip("Enter your first name")
        #self.lastname_input.setValidator(QRegularExpressionValidator(reg.stringValidator()))
        self.lastname_input.setValidator(CustomValidator(reg.stringValidator(),msg="lastname containing alphabates"))
        self.lastname_input.setToolTip("Enter your last name")
        self.userid_input.textChanged.connect(self.checkUserId)
        self.ok_btn.clicked.connect(self.createAccPageFun)
        self.back_btn1.clicked.connect(lambda:self.stackedWidget.setCurrentIndex(0))
        
        #setting ui for login window
        #self.userid_lineedit_2.setValidator(QRegularExpressionValidator(reg.useridValidator()))
        self.userid_lineedit_2.setValidator(CustomValidator(reg.useridValidator(),msg="username12@domain-name.com"))
        self.userid_lineedit_2.setToolTip("Enter your email id")
        self.pass_lineedit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_lineedit.setToolTip("Enter password")
        self.pass_lineedit.setPlaceholderText("Password must contain atleast 8 characters")
        self.hide_cb.clicked.connect(self.unHidePassword)
        self.ok_btn2.clicked.connect(self.loginPageFun)
        self.back_btn2.clicked.connect(lambda:self.stackedWidget.setCurrentIndex(0))
        self.loginasadmin_btn.clicked.connect(self.loginAsAdminfun)

        #setting afterlogin/sidemenu page widget
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
        #self.first_name_ln.setValidator(QRegularExpressionValidator(reg.stringValidator()))
        self.first_name_ln.setValidator(CustomValidator(reg.stringValidator(),msg="firstname containing alphabates"))
        self.first_name_ln.setToolTip("Enter the first name")
        #self.last_name_ln.setValidator(QRegularExpressionValidator(reg.stringValidator()))
        self.last_name_ln.setValidator(CustomValidator(reg.stringValidator(),msg="lastname containing alphabates"))
        self.last_name_ln.setToolTip("Enter the last name")
        #self.phno_ln.setValidator(QRegularExpressionValidator(reg.phnoValidator()))
        self.phno_ln.setValidator(CustomValidator(reg.phnoValidator(),msg="1234567890"))
        self.phno_ln.setToolTip("Enter phone number")
        #self.userid_ln.setValidator(QRegularExpressionValidator(reg.useridValidator()))
        self.userid_ln.setValidator(CustomValidator(reg.useridValidator(),msg="username12@domain-name.com"))
        self.userid_ln.setToolTip("Enter userid\n e.g.: abc@gmail.com")
        self.userid_ln.textChanged.connect(self.checkUserId)
        self.label_3a.setText('')
        #self.state_ln.setValidator(QRegularExpressionValidator(reg.stringValidator()))
        self.state_ln.setValidator(CustomValidator(reg.stringValidator(),msg="state name containing alphabates"))
        self.state_ln.setToolTip("Enter state")
        #self.city_ln.setValidator(QRegularExpressionValidator(reg.stringValidator()))
        self.city_ln.setValidator(CustomValidator(reg.stringValidator(),msg="city name containing alphabates"))
        self.city_ln.setToolTip("Enter city name")
        #self.streetaddress_ln.setValidator(QRegularExpressionValidator(reg.alphanumericValidator()))
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
        #self.authoname_ln.setValidator(QRegularExpressionValidator(reg.stringValidatorWithSpace()))
        self.authoname_ln.setValidator(CustomValidator(reg.stringValidatorWithSpace(),msg="authorname alphabates only"))
        self.authoname_ln.setToolTip("Enter author name")
        #self.booktitle_ln.setValidator(QRegularExpressionValidator(reg.stringValidatorWithSpace()))
        self.booktitle_ln.setValidator(CustomValidator(reg.stringValidatorWithSpace(),msg="book title alphabates only"))
        self.booktitle_ln.setToolTip("Enter book title")
        #self.categories_ln.setValidator(QRegularExpressionValidator(reg.stringValidatorWithCommas()))
        self.newcat_lineedit.setValidator(CustomValidator(reg.stringValidatorWithSpace(),msg="horror"))
        #self.copies_ln.setValidator(QRegularExpressionValidator(reg.numbersOnly()))
        self.copies_ln.setValidator(CustomValidator(reg.numbersOnly(),msg="numbers only"))
        self.copies_ln.setToolTip("Enter number of copies of books")
        #self.isbn_ln.setValidator(QRegularExpressionValidator(reg.isbnValidator()))
        self.isbn_ln.setValidator(CustomValidator(reg.isbnValidator(),msg="111-1111-1111-11"))
        self.isbn_ln.setToolTip("Enter isbn number of book here")
        self.findAndSetCategory()
        self.addcat_button.clicked.connect(self.addNewCategory)

        #setting ui for book issue widget
        self.spacerItem15 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.issue_book_btn.clicked.connect(self.showBookissuePageFun)
        self.ok_btn_3.clicked.connect(self.addbooktoissue)
        self.ok_btn_3.setDisabled(True)
        #self.libcardno_ln.setValidator(QRegularExpressionValidator(reg.numbersOnly()))
        self.libcardno_ln.setValidator(CustomValidator(reg.libcardnoValidator(),msg="numbers only"))
        self.libcardno_ln.textChanged.connect(lambda text, obj=self.libcardno_ln.objectName(): self.showLibcardHolderInfo(obj, text))

        self.libcardno_ln.on_focus.connect(self.onFocus)
        self.bookisbn_ln1.on_focus.connect(self.onFocus)
        #self.bookisbn_ln1.setValidator(QRegularExpressionValidator(reg.isbnValidator()))
        self.bookisbn_ln1.setValidator(CustomValidator(reg.isbnValidator(),msg="111-1111-1111-11"))
        self.bookisbn_ln1.textChanged.connect(self.setAddBookbtnEnable)
        self.libcardholderinfo_bookissue_widget.setHidden(True)
        self.scan_n_fetch_btn1.clicked.connect(self.onScanAndFetch)
        """@self.numberofbooks_sb.setMinimum(1)
            pass
        @self.numberofbooks_sb.setMaximum(5)
            pass
        @self.numberofbooks_sb.valueChanged.connect(self.addLineEdits)"""
            

        #setting ui for book return widget
        self.pushButton_2.clicked.connect(self.showBookReturnPageFun)
        #self.libcardno_ln_2.setValidator(QRegularExpressionValidator(reg.numbersOnly()))
        self.libcardno_ln_2.setValidator(CustomValidator(reg.numbersOnly(),msg="numbers only"))
        #self.bookisbn_return_ln.setValidator(QRegularExpressionValidator(reg.isbnValidator()))
        self.libcardno_ln_2.textChanged.connect(lambda text, obj=self.libcardno_ln_2.objectName(): self.showLibcardHolderInfo(obj, text))
        self.showreturnedbooks_tableWidget.itemChanged.connect(self.onCBChangeReturnBooks)
        self.libcardholderinfo_bookreturn_widget.setHidden(True)
        self.libcardno_ln_2.on_focus.connect(self.onFocus)
        self.scan_n_fetch_btn2.clicked.connect(self.onScanAndFetch)
        self.pushButton_2.setDisabled(True)
        self.paypenaltybtn.clicked.connect(self.payPenalty)
        #self.bookisbn_ln1.on_focus.connect(self.onFocus)
        #self.bookisbn_ln1.textChanged.connect(self.setAddBookbtnEnable)
        
        #
        """
        self.bookisbn_return_ln.setValidator(CustomValidator(reg.isbnValidator(),msg="111-1111-1111-11"))
        self.numberofbooks_sb_2.setMinimum(1)
        self.numberofbooks_sb_2.setMaximum(5)
        self.numberofbooks_sb_2.valueChanged.connect(self.addLineEdits)"""
        self.spacerItem18 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)

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
        
        self.install_event_filter_on_line_edits()

    def loginAsAdminfun(self):
        #doing neccessary thing if user is try to log in as admin
        self.showLoginPage()
        self.back_btn2.setHidden(True)
    
    def checkUserId(self):
            #finding if username is already occupied
        try:
            Mydb = Dbconnection()
            e = CustomErrorAndLogWriting()
            c,db = Mydb.makeConnection()
            ob = self.sender().objectName()
            if ob == self.userid_input.objectName():
                userid = str(self.userid_input.text())
                res = Mydb.search_userid(c,userid)
                if res is None:
                    #e.err = ErrorCodes.USERID_SEARCH_NEWACCPAGE_FAILED
                    e.err = ErrorCodes(1)
                    raise e

                if len(res) == 0:
                    self.label_3.setText("")
                
                else:
                    self.label_3.setText("User id is already occupied")

            elif ob == self.userid_ln.objectName():
                userid = str(self.userid_ln.text())
                self.is_userid_unique = None #variable to check if userid is unique in apply new libcard page
                res = Mydb.search_userid(c,userid)
                if res == None:
                    e.err = ErrorCodes.USERID_SEARCH_APPLYNEWLIBCARDPAGE_FAILED
                    raise e
                
                if len(res) == 0:
                    self.label_3a.setText("")
                    self.is_userid_unique = True
                
                else:
                    self.label_3a.setText("User id is already occupied")
                    self.is_userid_unique = False
            c.close(); db.close()

        except (AttributeError,CustomErrorAndLogWriting) as e :
            if isinstance(e,CustomErrorAndLogWriting):
                #if e.err == ErrorCodes.USERID_SEARCH_NEWACCPAGE_FAILED:
                if e.err == ErrorCodes(1):
                    e.writeFailedOperation("Cant search userid for creating new account page. Check error log.")
                elif e.err == ErrorCodes.USERID_SEARCH_APPLYNEWLIBCARDPAGE_FAILED:
                    e.writeFailedOperation(emsg="Cant search userid for apply new libcard page. Check error log.")
                    
            elif isinstance(e,AttributeError):
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())


    def gender(self):
        #fetching gender for libcard apply
        if self.female_rb.isChecked():
            self.gen = self.female_rb.text()
        elif self.male_rb.isChecked():
            self.gen = self.male_rb.text()
        
            

    def unHidePassword(self):
        #making password show or hidden
        ob = self.sender().objectName()
        if ob == "checkBox":
            if  self.checkBox.isChecked():
                self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            else: 
                self.pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
        
        elif ob == "hide_cb":
            if self.hide_cb.isChecked():
                self.pass_lineedit.setEchoMode(QLineEdit.EchoMode.Password)
            else: 
                self.pass_lineedit.setEchoMode(QLineEdit.EchoMode.Normal)

    def logout(self):
        #asking user if he really want to logout
        reply = QMessageBox.question(self, 'Log out',
                                     "Are you sure you want to Logout?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.stackedWidget.setCurrentIndex(0)
            self.restart()

        else:
            pass

    def closeEvent(self, event: QCloseEvent):
        #asking user if he really want to leave the app
        reply = QMessageBox.question(self, 'Exit Application?',
                                     "Are you sure you want to exit?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()  # Accept the close event and exit
            QApplication.instance().quit()
        else:
            event.ignore()  # Ignore the close event and do not exit

    def on_toggle(self,checked):
        #making sidemenu show or hidden
        if checked:
            self.sidemenu_widget.show();self.sa_sidewidget.show()
        else:
            self.sidemenu_widget.hide();self.sa_sidewidget.hide()

    def addLineEdits(self,count):
        #adding lineedits dynamicly
        reg = RegExp()
        ob = self.sender().objectName()
        self.dynamiclineedits= []
        self.dynamiclineedits2= []
        if ob == "numberofbooks_sb":

            for i in reversed(range(self.gridLayout_8.count())):
                widget = self.gridLayout_8.itemAt(i).widget()
                if isinstance(widget, QLineEdit) and widget.objectName() != "libcardno_ln":
                    self.gridLayout_8.removeWidget(widget)
                    widget.deleteLater()
            
            # Add new QLineEdits based on the spin box value
            self.gridLayout_8.removeItem(self.spacerItem15)
            self.gridLayout_8.removeWidget(self.ok_btn_3)
            for i in range(1,count+1):

                self.lineEdit = QLineEdit(self,objectName = "dybookisbn_ln"+str(i))
                #self.lineEdit.setValidator(QRegularExpressionValidator(reg.isbnValidator()))
                self.lineEdit.setValidator(CustomValidator(reg.isbnValidator(),msg="111-1111-1111-11"))
                self.gridLayout_8.addWidget(self.lineEdit,6+i,1,1,1)
                self.dynamiclineedits.append(self.lineEdit)
            
            self.gridLayout_8.addWidget(self.ok_btn_3,6+i+1,1,1,1)
            self.gridLayout_8.addItem(self.spacerItem15,6+i+2,0,1,1)
        
        elif ob == "numberofbooks_sb_2":
            for i in reversed(range(self.gridLayout_9.count())):
                widget = self.gridLayout_9.itemAt(i).widget()
                if isinstance(widget, QLineEdit) and widget.objectName() != "libcardno_ln_2":
                    self.gridLayout_9.removeWidget(widget)
                    widget.deleteLater()
            self.gridLayout_9.removeItem(self.spacerItem18)
            self.gridLayout_9.removeWidget(self.pushButton_2)
            # Add new QLineEdits based on the spin box value
            for i in range(1,count+1):
                
                self.lineEdit = QLineEdit(self,objectName = "dybookisbn_ln"+str(i))
                #self.lineEdit.setValidator(QRegularExpressionValidator(reg.isbnValidator()))
                self.lineEdit.setValidator(CustomValidator(reg.isbnValidator(),msg="111-1111-1111-11"))
                self.gridLayout_9.addWidget(self.lineEdit,6+i,1,1,1)
                self.dynamiclineedits2.append(self.lineEdit)
            
            self.gridLayout_9.addWidget(self.pushButton_2,6+i+1,1,1,1)
            self.gridLayout_9.addItem(self.spacerItem18,6+i+2,0,1,1)

    def is_widget_in_layout(self,layout, widget_to_check):
        #Finding if specific widget is in specific layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() == widget_to_check:
                return True
        return False
    
    def make_circle_pixmap(self, image_path, diameter):
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
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if file_path:  # Check if a file was selected
            new_pixmap = self.make_circle_pixmap(image_path=file_path,diameter=100)
            self.photo_label.setPixmap(new_pixmap.scaled(self.photo_label.width(), self.photo_label.height(),Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.is_imageset = True
            self.cur_image_path = file_path
            
            
    def storeImage(self,libcardno)-> str:
        """store image in folder and return location"""
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
        #creating new acc
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
                    e.err = ErrorCodes.GENRATE_ID_PASSWORDINFO_FAILED
                    raise e
                input()    
                failed = Mydb.insert_into_passwordinfo(c,ano,fn,ln,userid,p)
                if failed:
                    e.err = ErrorCodes.INSERT_NEWUSER_PASSWORDINFO_FAILED
                    raise e

                else:
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
                if e.err == ErrorCodes.GENRATE_ID_PASSWORDINFO_FAILED:
                    e.writeFailedOperation("Can't generate id for new user for create new account page")
                elif e.err == ErrorCodes.INSERT_NEWUSER_PASSWORDINFO_FAILED:
                    e.writeFailedOperation("Cant insert new user")
                    try:
                        db.rollback()
                    except Exception:
                        #to catch error related to rollback
                        CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            elif isinstance(e,Exception):
                #to catch any error
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
                    
                
        

    def Admin(self):
        #adding admin functions
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



    def noAdmin(self):  
        #removing admin functions         
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
        #show login page
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
                    e.err = ErrorCodes.CHECK_USERID_AND_PASS_PASSWORDINFO_FAILED
                    raise e
                if len(res) == 0:
                    m.warning(self,"Failed","Login Failed please check the password or userid you entered")
                else:    
                    m.information(self,"LoggedIn","Logged In successfully :)")
                    self.role = res[0][1]
                    self.stackedWidget.setCurrentIndex(3)
                    self.sidemenu_btn.show()
                    self.sidemenu_btn.setCheckable(True)
                    self.sidemenu_btn.clicked.connect(self.on_toggle)
                    self.userid_lineedit_2.clear()
                    p = self.pass_lineedit.clear()

                    if self.role == 'Admin':
                        self.Admin()
                    elif self.role == 'Librarian':
                        self.noAdmin()
                    
                
            else:
                m.warning(self,"Failed","Please fill the input fields correctly")
            c.close(),db.close()
        
        except (AttributeError,CustomErrorAndLogWriting) as e:
            if isinstance(e,AttributeError):
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            elif isinstance(e,CustomErrorAndLogWriting):
                if e.err == ErrorCodes.CHECK_USERID_AND_PASS_PASSWORDINFO_FAILED:
                    e.writeFailedOperation("Cant find userid with corresponding password to login.")
            elif isinstance(e,Exception):
                #to catch any error
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
        
    
    def showLibcardApplyPageFun(self):
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
            try:
                lid = Mydb.genid(c,"libcard_id","library_card_info")
                if lid is None:
                    e.err = ErrorCodes.GENRATE_ID_LIBRARYCARDINFO_FAILED
                    raise e
                    
                libcardno=random.randint(10000000000000,99999999999999)
                msg = "New Library card is created sucessfully\n Your libcard no is: "+str(libcardno)
                photo_path = self.storeImage(libcardno=libcardno)
                
                res = Mydb.checklocation_existence(c,stad,city,state)
                if res is None:
                    e.err = ErrorCodes.LOCATION_SEARCH_APPLYNEWLIBCARDPAGE_FAILED
                    raise e
                rowc=len(res)
                    #if not
                if(rowc==0):
                    locid = Mydb.genid(c,"lid","location")
                    if locid is None:
                        e.err = ErrorCodes.GENRATE_ID_LOCATION_FAILED
                        raise e
                    
                    failed1=Mydb.insert_new_location(c,locid,stad,city,state)
                    if failed1:
                        e.err = ErrorCodes.INSERT_NEW_LOCATION_FAILED
                        raise e
                
                    failed2=Mydb.insert_new_libcard(c,lid,fn,ln,gen,locid,phno,userid,libcardno,photo_path)
                    if failed2:
                        e.err = ErrorCodes.INSERT_NEW_LIBRARYCARD_FAILED
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
                    #if found
                else:
                    for row in res:
                        locid=int(row[0])
                        failed2=Mydb.insert_new_libcard(c,lid,fn,ln,gen,locid,phno,userid,libcardno,photo_path)
                        if failed2:
                            e.err = ErrorCodes.INSERT_NEW_LIBRARYCARD_WITH_LOCID_FAILED
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
                
                c.close();db.close()
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
                    if e.err == ErrorCodes.GENRATE_ID_LIBRARYCARDINFO_FAILED:
                        e.writeFailedOperation("Failed to genrate new library card id (primary key).")
                    elif e.err == ErrorCodes.LOCATION_SEARCH_APPLYNEWLIBCARDPAGE_FAILED:
                        e.writeFailedOperation("Failed to search for given location existence.")
                    elif e.err == ErrorCodes.GENRATE_ID_LOCATION_FAILED:
                        e.writeFailedOperation("Failed to generate new id for location.")
                    elif e.err == ErrorCodes.INSERT_NEW_LOCATION_FAILED:
                        try:
                            db.rollback()
                            e.writeFailedOperation("Failed to insert new location entry in location table.")
                        except Exception:
                            #to catch error related to rollback
                            CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
                    elif e.err == ErrorCodes.INSERT_NEW_LIBRARYCARD_FAILED:
                        try:
                            db.rollback()
                            e.writeFailedOperation("Failed to insert new library card entry in library_card_info table.")
                        except Exception:
                            #to catch error related to rollback
                            CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
                    elif e.err == ErrorCodes.INSERT_NEW_LIBRARYCARD_WITH_LOCID_FAILED:
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
        else:
            m.warning(self,"Can't proceed","Please Fill input fields correctly")
        
        

    def showAllBooksPageFun(self,text):
        #show all books
        #not fixed
        Mydb = Dbconnection()
        e = CustomErrorAndLogWriting()
        c,db = Mydb.makeConnection()
        try:
            self.showallbooks_tableWidget.clear()
            self.showallbooks_tableWidget.setRowCount(0)
            self.showallbooks_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            header,result = Mydb.showAllBooks(c,str(text))
            if header is None or result is None:
                e.err = ErrorCodes.BOOK_SEARCH_BOOKDETAILS_FAILED
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
                if e.err == ErrorCodes.BOOK_SEARCH_BOOKDETAILS_FAILED:
                    e.writeFailedOperation(emsg="Failed to search book with given text")

            elif isinstance(e,Exception):
                QMessageBox().critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())

            if self.e_msg and self.errors_names:
                CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
                print(self.errors_names,self.e_msg)
                self.errors_names.clear()
                self.e_msg = ''

        
        

    def showBorrowerPageFun(self,index):
        #show borrowers
        Mydb = Dbconnection()
        c,db = Mydb.makeConnection()
        e = CustomErrorAndLogWriting()
        try:
            m = QMessageBox()
            self.showborrowers_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            if index == 0:
                result = ()
                self.showborrowers_tableWidget.clear()
                self.showborrowers_tableWidget.setRowCount(0)
                header,result = Mydb.showAllBorrowers(c)
                if header is None or result is None:
                    e.err = ErrorCodes.SHOW_ALLBORROWERS_BORROWERSDETAILS_FAILED
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
                    e.err = ErrorCodes.SHOW_BORROWERSRETURNED_BORROWERSDETAILS_FAILED
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
                    e.err = ErrorCodes.SHOW_BORROWERSNOTRETURNED_BORROWERSDETAILS_FAILED
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
                if e.err == ErrorCodes.SHOW_ALLBORROWERS_BORROWERSDETAILS_FAILED:
                    e.writeFailedOperation(emsg="Failed to fetch information about all borrowers. Check logs for more information about errors.")
                elif e.err == ErrorCodes.SHOW_BORROWERSRETURNED_BORROWERSDETAILS_FAILED:
                    e.writeFailedOperation(emsg="Failed to fetch information about borrowers who have returned the book. Check logs for more information about errors.")
                elif e.err == ErrorCodes.SHOW_BORROWERSNOTRETURNED_BORROWERSDETAILS_FAILED:
                    e.writeFailedOperation(emsg="Failed to fetch information about borrowers who haven't returned the books. Check logs for more information about errors.")

            elif isinstance(e,Exception):
                m.critical(self,"Error","Some error occured check logs to see those errors")
                CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            if self.errors_names and self.e_msg:
                CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
                self.errors_names.clear()
                self.e_msg = ''
        
    def findAndSetCategory(self,delete_previous_labels=False):
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
                    print("find child layout:",child_layout)
                    for j in reversed(range(child_layout.count())):
                        widget = child_layout.itemAt(j).widget()
                        child_layout.removeWidget(widget)
                        widget.deleteLater()
                        print("find widget:",widget)
                    child_layout.deleteLater()

            res = Mydb.showAllCategories(c)
            if res is None:
                e.err = ErrorCodes.SHOW_ALLCATEGORY_ADDNEWBOOK_FAILED
                raise e
            categories = [row[0] for row in res]
            print(categories)
            row_layout = None
            for i, ch in enumerate(categories):
                checkbox = QtWidgets.QCheckBox(ch)
                if i % 2 == 0:
                    row_layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.Direction.LeftToRight)
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
                ErrorCodes.SHOW_ALLCATEGORY_ADDNEWBOOK_FAILED: "Failed to fetch all categories from db to show it on add new book page."
                }
                if e.err in error_messages:
                    e.writeFailedOperation(emsg=error_messages[e.err])
                    db.rollback()
            if self.errors_names and self.e_msg:
                CustomErrorAndLogWriting().writeAllErrorInLog(self.errors_names,self.e_msg)
                self.errors_names.clear()
                self.e_msg = ''

    def getCategories(self):
        categories = []
        for ch in self.c_boxes:
            if ch.isChecked():
                categories.append(ch.text())
        
        return categories
    
    def addNewCategory(self):
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
                e.err = ErrorCodes.CHECK_CATEGORYEXISTENCE_CATEGORYDETAILS_FAILED
                raise e
            cid = Mydb.genid(c,"cid","category_details")
            if cid is None:
                e.err = ErrorCodes.GENRATE_ID_CATEGORYDETAILS_FAILED
                raise e
        
            failed=Mydb.insert_new_category(c,cid,category_name)
            if failed:
                e.err = ErrorCodes.INSERT_NEWCATEGORY_CATEGORYDETAILS_FAILED
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
        ErrorCodes.GENRATE_ID_CATEGORYDETAILS_FAILED: "Failed to generate new category ID for adding new book.",
        ErrorCodes.INSERT_NEWCATEGORY_CATEGORYDETAILS_FAILED: "Failed to insert new book for adding new book page.",
        ErrorCodes.CHECK_CATEGORYEXISTENCE_CATEGORYDETAILS_FAILED: "The category you are trying to add is already in categories."
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
        #Adding new book
        author_name = ' '.join(self.authoname_ln.text().split())
        book_title = ' '.join(self.booktitle_ln.text().split())
        cn = self.getCategories()
        no_of_copies = self.copies_ln.text()
        isbn = self.isbn_ln.text()
        m = QMessageBox()
        Mydb = Dbconnection()
        c,db = Mydb.makeConnection()
        e = CustomErrorAndLogWriting()
        print("Category:",cn)
        if (author_name != "") and ( book_title != "") and any(cn) and (no_of_copies != "") and (isbn != "") :
            #finding author name in db
            try:
                aid = Mydb.genid(c,"aid","author_details")
                if aid is None:
                    e.err = ErrorCodes.GENRATE_ID_AUTHORDETAILS_FAILED
                    raise e
                    
                bid = Mydb.genid(c,"bid","book_details")
                if bid is None:
                    e.err = ErrorCodes.GENRATE_ID_BOOKDETAILS_FAILED
                    raise e
                    
                res2 = Mydb.checkIfBookExist(c,isbn,book_title,author_name)
                if res2 is None:
                    e.err = ErrorCodes.CHECK_BOOK_BOOKDETAILS_FAILED
                    raise e
                    
                rowc2=len(res2)
                if rowc2 == 0:
                    res = Mydb.getAuthorid(c,author_name=author_name)
                    if res is None:
                        e.err = ErrorCodes.GET_AUTHORID_USINGAUTHORNAME_FAILED
                        raise e
                        
                    rowc=len(res)
                    if(rowc==0):    #if author name is not in db
                        failed1=Mydb.insert_new_author(c,aid,author_name)
                        if failed1:
                            e.err = ErrorCodes.INSERT_NEW_AUTHOR_AUTHORDETAILS_FAILED
                            raise e
                        
                        #adding book when author name is not in db
                        failed2=Mydb.insert_new_book(c,bid,isbn,book_title,aid,no_of_copies)
                        if failed2:
                            e.err = ErrorCodes.INSERT_NEWBOOK_BOOKDETAILS_NOAUTHOR_FAILED
                            raise e
                            #identifying if entered category exists in db or not
                        for Category_name in cn:
                            res=Mydb.getCategoryid(c,Category_name)
                            if res is None:
                                e.err = ErrorCodes.GET_CATEGORYID_NOAUTHOR_USINGCATEGORYNAME_FAILED
                                raise e                     
                            for row in res:
                                cid=int(row[0])
                            failed4=Mydb.insert_new_category_in_bookcategory(c,bid,cid)
                            if failed4:
                                e.err = ErrorCodes.INSERT_NEWCATEGORY_BOOKCATEGORY_NOAUTHOR_WITHCAT_FAILED
                                raise e
                    #if author exist in db    
                    else:
                        for row in res:
                            aid=int(row[0])
                        failed2=Mydb.insert_new_book(c,bid,isbn,book_title,aid,no_of_copies)
                        if failed2:
                                    e.err = ErrorCodes.INSERT_NEWBOOK_BOOKDETAILS_WITHAUTHOR_FAILED
                                    raise e

                        for Category_name in cn:
                            res=Mydb.getCategoryid(c,Category_name)
                            print(Category_name)
                            if res is None:
                                e.err = ErrorCodes.GET_CATEGORYID_WHENAUTHOR_USINGCATEGORYNAME_FAILED
                                raise e
                            #if category is in db
                            for row in res:
                                cid=int(row[0])
                            print("bid:cid =",bid,":",cid)
                            failed4=Mydb.insert_new_category_in_bookcategory(c,bid,cid)
                            if failed4:
                                e.err = ErrorCodes.INSERT_NEWCATEGORY_BOOKCATEGORY_WITHAUTHOR_WITHCAT_FAILED
                                raise e
                                
                    db.commit()
                    res = Mydb.getBookTitle(c,bid)
                    if res is None:
                        e.err = ErrorCodes.GET_BOOKTITLE_USINGBID_FAILED
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
            ErrorCodes.GENRATE_ID_AUTHORDETAILS_FAILED: "Failed to generate author ID for adding new book.",
            ErrorCodes.GENRATE_ID_BOOKDETAILS_FAILED: "Failed to generate book ID for adding new book.",
            ErrorCodes.CHECK_BOOK_BOOKDETAILS_FAILED: "Failed to check if book already exists.",
            ErrorCodes.GET_AUTHORID_USINGAUTHORNAME_FAILED: "Failed to fetch author ID if it already exists.",
            ErrorCodes.INSERT_NEW_AUTHOR_AUTHORDETAILS_FAILED: "Failed to insert new author for adding a new book.",
            ErrorCodes.INSERT_NEWBOOK_BOOKDETAILS_NOAUTHOR_FAILED: "Failed to insert new book when author does not exist.",
            ErrorCodes.GET_CATEGORYID_NOAUTHOR_USINGCATEGORYNAME_FAILED: "Failed to get category ID using category name when author does not exist.",
            #ErrorCodes.GENRATE_ID_CATEGORYDETAILS_NOAUTHOR_FAILED: "Failed to generate category ID when author does not exist.",
            #ErrorCodes.INSERT_NEWCATEGORY_CATEGORYDETAILS_NOAUTHOR_FAILED: "Failed to insert new category when author does not exist.",
            #ErrorCodes.INSERT_NEWCATEGORY_BOOKCATEGORY_NOAUTHOR_NOCAT_FAILED: "Failed to insert book-category relation when author and category do not exist.",
            ErrorCodes.INSERT_NEWCATEGORY_BOOKCATEGORY_NOAUTHOR_WITHCAT_FAILED: "Failed to insert book-category relation when author does not exist but category exists.",
            ErrorCodes.INSERT_NEWBOOK_BOOKDETAILS_WITHAUTHOR_FAILED: "Failed to insert new book when author exists.",
            ErrorCodes.GET_CATEGORYID_WHENAUTHOR_USINGCATEGORYNAME_FAILED: "Failed to get category ID using category name when author exists.",
            #ErrorCodes.GENRATE_ID_CATEGORYDETAILS_WHENAUTHOR_FAILED: "Failed to generate new category ID when author exists.",
            #ErrorCodes.INSERT_NEWCATEGORY_CATEGORYDETAILS_WITHAUTHOR_FAILED: "Failed to insert new category when author exists.",
            #ErrorCodes.INSERT_NEWCATEGORY_BOOKCATEGORY_WITHAUTHOR_NOCAT_FAILED: "Failed to insert new book-category relation when author exists but category does not.",
            ErrorCodes.INSERT_NEWCATEGORY_BOOKCATEGORY_WITHAUTHOR_WITHCAT_FAILED: "Failed to insert new book-category relation when both author and category exist.",
            ErrorCodes.GET_BOOKTITLE_USINGBID_FAILED: "Failed to fetch book title using book ID.",
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
        if text != '':
            self.ok_btn_3.setEnabled(True)
        self.ok_btn_3.setDisabled(True)

    def setScanAndAddbtn(self):
        sender = self.sender().objectName()
        if sender == 'bookisbn_ln1':
            self.gridLayout_8.removeWidget(self.scan_n_fetch_btn1)
            self.gridLayout_8.addWidget(self.scan_n_fetch_btn1, 3,2,1,1)
        elif sender == 'libcardno_ln':
            self.gridLayout_8.removeWidget(self.scan_n_fetch_btn1)
            self.gridLayout_8.addWidget(self.scan_n_fetch_btn1, 2,2,1,1)
        

    def updateLinkedDeviceStatus(self):
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
            

    @pyqtSlot(str)
    def display_message(self, message):
        msg = json.loads(message)
        print(message)
        if "deviceInfo" in msg:
            self.is_device_linked = True
            self.updateLinkedDeviceStatus()
            print("Client device info:", msg["deviceInfo"])
            #self.label.setText(f"CONNECTED WITH DEVICE!!!:\nName: {msg["deviceInfo"]["name"]}\nModel: {msg["deviceInfo"]["model"]}\nOs: {msg["deviceInfo"]["os"]}")
            self.client_info_lb.setText(f"\nName: {msg["deviceInfo"]["name"]}\nModel: {msg["deviceInfo"]["model"]}\nOs: {msg["deviceInfo"]["os"]}")
            QMessageBox.information(None,'Connected', 'Connected with a device successfully')
        else:
            obj = next(iter(msg))
            print("obj:",obj)
            target = self.findChild(ui.FocusSignalLineEdit, obj)
            target.setText(msg[obj])
        
    @pyqtSlot(bool)
    def clientDisconnected(self,disconnected):
        print(disconnected)
        if disconnected:
            self.is_device_linked = False
            QMessageBox.information(None,'Disconnected', 'Device is Disconnected!!')
            self.link_device_btn.setEnabled(True)
            self.updateLinkedDeviceStatus()        
    
    @pyqtSlot(str)
    def onFocus(self, lineedit_name):
        self.setScanAndAddbtn()
        if self.ws_server.clients:
            print("sending")
            msg = {lineedit_name: f"{lineedit_name}"}
            print(msg)#check
            self.ws_server.sendMsg(msg=msg)
            print("send")

    def startServer(self, text):
        print("btn text",text)
        if text == 'Connect':
            self.ws_server.startServer()
            img = self.ws_server.makeQrcodeAndGetResult()
            #self.device_pic_label.setPixmap(QtGui.QPixmap(r'Appdata\images\start_connection.jpeg'))
            self.device_pic_label.setPixmap(QPixmap(img))
            #self.device_pic_label.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignCenter)
            self.server_info_lb.setText("Starting Websocket Server at \n IPAddress:{}\n Port:{}\n".format(self.ws_server.IPAddress,self.ws_server.Port))
            self.link_device_btn.setText('Disconnect')
        else:
            self.ws_server.closeServer()
            self.is_device_linked = False
            self.updateLinkedDeviceStatus()
            self.link_device_btn.setText('Connect')

    def onScanAndFetch(self):
        if not self.is_device_linked:
            self.stackedWidget.setCurrentIndex(13)
        else:
            QMessageBox.information(None,'Device Found', 'Already Linked with a device, place the cursor on lineedit to fetch the data')
        #showLibcardHolderBookissue

    def onCBChangeReturnBooks(self, item):
        # Check if the item is a checkbox
        self.pushButton_2.setEnabled(False)         
        if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
            for cb in self.returnbooks:
                state = cb.checkState()
                if state == Qt.CheckState.Checked:
                    self.pushButton_2.setEnabled(True)         
    
    def checkPenalty(self):
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            m = QMessageBox()
            res = Mydb.checkPenalty(c,self.libcardno_ln_2.text())#64354968968184
            if res is None:
                e.err = ErrorCodes.CHECK_PENALTY_BORROWERDETAILS_FAILED
                raise e
            print(res)
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
                ErrorCodes.CHECK_PENALTY_BORROWERDETAILS_FAILED: "Failed to check penalty for the borrower."
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

    def showPenaltyMSG(self,data):
        msg = QMessageBox(parent=self.bookreturn_page)
        msg.setWindowTitle("Penalty")
        msg.setText("This borrower has penalty on him\n Want to pay penalty right now?")

        # Add custom buttons
        btn_proceed = msg.addButton("Proceed", QMessageBox.ButtonRole.YesRole)
        btn_no = msg.addButton("Maybe Later", QMessageBox.ButtonRole.NoRole)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked == btn_proceed:
            self.payPenalty(data)
        elif clicked == btn_no:
            print("User said NO")
            self.paypenaltybtn.setHidden(False)
            pass

    def payPenalty(self,dataset):
        class PenaltyWindow(QtWidgets.QWidget):
            success = pyqtSignal(object)
            def __init__(self, parent:QtWidgets.QWidget=None, dataset=None,borwid_penalties = None):
                super().__init__(parent)
                self.pw = parent
                self.dataset = dataset
                self.borwids_penalties = borwid_penalties
                self.setWindowTitle("Pay Penalty")
                self.setUi()
            def setUi(self):
                self.setWindowTitle("Pay Penalty")
                self.setGeometry(int(self.pw.bookreturn_page.width()/2), int(self.pw.bookreturn_page.height()/2), 300, 200)
                self.setMaximumSize(300,200)
                layout = QtWidgets.QGridLayout()
                self.name_lb = QtWidgets.QLabel("Name:")
                self.name_ln = QtWidgets.QLineEdit("")
                self.libcardno_lb = QtWidgets.QLabel("Library-card no:")
                self.libcardno_ln = QtWidgets.QLineEdit("")
                self.booktitle_lb = QtWidgets.QLabel("Book titles:")
                self.booktitle_ln = QtWidgets.QLineEdit("")
                self.penalty_lb = QtWidgets.QLabel("Penalty to be paid:")
                self.penalty_is_ln = QtWidgets.QLineEdit("")
                self.penalty_given_lb = QtWidgets.QLabel("Penalty amount payment:")
                self.penalty_given_ln = QtWidgets.QLineEdit("")

                outer_layout = QtWidgets.QVBoxLayout()
                sp_item = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
                self.pay_penalty_btn = QtWidgets.QPushButton("Pay Penalty",self)
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
                try:
                    Mydb = Dbconnection()
                    c,db = Mydb.makeConnection()
                    e = CustomErrorAndLogWriting()
                    m = QMessageBox(parent= self)
                    amount = int(self.penalty_given_ln.text())
                    print("amount",amount)
                    print(self.name_ln.text(), self.libcardno_ln.text(), self.booktitle_ln.text(), self.penalty_is_ln.text(), self.penalty_given_ln.text())
                    if self.name_ln.text() != '' and self.libcardno_ln.text() != '' and self.booktitle_ln.text() != '' and self.penalty_is_ln.text() != '' and self.penalty_given_ln.text():
                        print(dataset)
                        print("going to pay")

                        for key,val in self.borwids_penalties.items():
                            at = int(self.borwids_penalties[key]) - amount
                            if at >= 0:
                                print("set penalty to: ",at)
                                failed1=Mydb.updatePenaltyInBorrowerDetails(c,borwid=key,penalty=val, new_penalty=at)
                                if failed1:
                                    e.err = ErrorCodes.UPDATE_PENALTYPAYMENT_BORROWERDETAILS_FAILED
                                    raise e
                                break
                            else:
                                print("Set book penalty to 0")
                                failed1=Mydb.adjustPenaltyInBorrowerDetails(c,borwid=key,penalty=val, new_penalty=0)
                                if failed1:
                                    e.err = ErrorCodes.UPDATE_PENALTYPAYMENT_BORROWERDETAILS_FAILED
                                    raise e
                                amount = -at
                                continue
                        db.commit()
                        m.information(self,"Success","Penalty is paid successfully.")
                        self.success.emit(self)
                        print(self)
                        self.close()
                except (ValueError,AttributeError,mysql.connector.Error,Exception,CustomErrorAndLogWriting) as err:
                    print(err)
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
                        ErrorCodes.UPDATE_PENALTYPAYMENT_BORROWERDETAILS_FAILED: "Failed to pay and update penalty."
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
                print("Window is being closed!")
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
            for bt in booktitles:
                booktitle = booktitle + bt + ", "
        print(borwid, name, libcardno, booktitle, penalties)
        print(borwid_penalties)
            
        penalty_window = PenaltyWindow(parent=self,dataset=dataset, borwid_penalties=borwid_penalties)
        penalty_window.setWindowFlags(Qt.WindowType.Window)
        penalty_window.setEnabled(True)
        penalty_window.success.connect(self.refreshPenalty)
        penalty_window.name_ln.setText(name)
        penalty_window.libcardno_ln.setText(str(libcardno))
        penalty_window.booktitle_ln.setText(booktitle)
        penalty_window.penalty_is_ln.setText(str(sum(penalties)))
        penalty_window.name_ln.setDisabled(True)
        penalty_window.libcardno_ln.setDisabled(True)
        penalty_window.booktitle_ln.setDisabled(True)
        penalty_window.penalty_is_ln.setDisabled(True)
        penalty_window.show()
        
    pyqtSlot(object)
    def refreshPenalty(self,obj):
        obj.success.disconnect(self.refreshPenalty)
        self.showLibcardHolderInfo(self.libcardno_ln_2, self.libcardno_ln_2.text())
        self.paypenaltybtn.setHidden(True)
        print("done")
        pass
        
    def showLibcardHolderInfo(self, obj, text):
        try:
            lineedit = obj
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            m = QMessageBox()
            print(lineedit," vd")
            if len(text) == 14:
                res = Mydb.getLibcardHolderInfo(c,text)
                if res is None:
                    e.err = ErrorCodes.GET_LIBCARDHOLDERINFOBOOKISSUE_LIBCARDINFO_FAILED
                    raise e
                if lineedit == 'libcardno_ln':
                    print(res)
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
                    print(name, gen, mobile, userid, libcard_no, photo_path, address)
                    self.photo_label_bookissue.setPixmap(self.make_circle_pixmap(image_path=r"{}".format(photo_path),diameter=196))
                    self.libcardholderinfo_bookissue_widget.setHidden(False)
                    print("entered")
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

                    header,res = Mydb.getBorrowerInfo(c,self.libcardno_ln_2.text())#64354968968184
                    if header is None or res is None:
                        e.err = ErrorCodes.GET_BORROWERBOOKRETURN_BORROWERDETAILS_FAILED
                        raise e
                    print(res)
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
                        print(self.returnbooks)
                        data = self.checkPenalty()
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
                ErrorCodes.GET_LIBCARDHOLDERINFOBOOKISSUE_LIBCARDINFO_FAILED: "Failed to fetch Library card holder details for book issue.",
                ErrorCodes.GET_BORROWERBOOKRETURN_BORROWERDETAILS_FAILED: "Failed to fetch borrower details for book return."
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
        print("Book added table")
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
                        print(str(self.showissuedbooks_tableWidget.item(row,col).text()))
                        row_data = row_data+[str(self.showissuedbooks_tableWidget.item(row,col).text())]
                if row_data:
                    data.append(tuple(row_data))     
            if self.bookisbn_ln1.text():
                header,res = Mydb.getBookInfo(c,self.bookisbn_ln1.text())
                if res is None:
                    print("res is none")
                    e.err = ErrorCodes.GET_BOOKINFOBOOKISSUE_BOOKDETAILS_FAILED
                    raise e
                elif not res:
                    m.critical(self,"Error","cant find book need to be issue")
            else:
                print("isbn missing")
            self.showissuedbooks_tableWidget.setRowCount(0)
            self.showissuedbooks_tableWidget.setColumnCount(0)
            data = data + res     
        
            if data:
                self.showissuedbooks_tableWidget.setRowCount(len(data))
                self.showissuedbooks_tableWidget.setColumnCount(len(data[0]))
                self.showissuedbooks_tableWidget.setHorizontalHeaderLabels(header)
                for i in range(len(data)):
                    for j in range(len(data[i])):
                        item = QtWidgets.QTableWidgetItem(str(data[i][j]))
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
                ErrorCodes.GET_BOOKINFOBOOKISSUE_BOOKDETAILS_FAILED: "Failed to fetch book info while adding it in book issue table."
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
    
        # Print the entire table data
        print(data)
    def delete_selected_row(self):
                selected = self.showissuedbooks_tableWidget.currentRow()
                if selected >= 0:
                    self.showissuedbooks_tableWidget.removeRow(selected)
            
    def showBookissuePageFun(self):
        #book issue function
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
            print(issued_books_isbns)
            if libcardno != "" and len(libcardno)==14 and (self.showissuedbooks_tableWidget.rowCount() >0):
                res=Mydb.getLibcardid(c,libcardno)
                if res is None:
                    e.err = ErrorCodes.GET_LIBCARDID_USINGLIBCARDNO_FAILED
                    raise e
                    log.Logs.writeFailedOperation("Failed to get libacard id using library card.")
                    
                rowc=len(res)
                #if library card no. is not in db
                if(rowc==0):
                    m.critical(self,"error","This Library card no. is not valid")
                    
                else:
                    for rows in res:
                        libcard_id=int(rows[0])
                    borwid = Mydb.genid(c,"borwid","borrower_details")
                    if borwid is None:
                        e.err = ErrorCodes.GENRATE_ID_BORROWERDETAILS_FAILED
                        raise e
                        log.Logs.writeFailedOperation("Failed to generate borrower id.")
                    for isbn in issued_books_isbns:
                        res=Mydb.getBookid(c,isbn)
                        if res is None:
                            e.err = ErrorCodes.GET_BOOKID_USINGISBN_WHENMANYISBN_FAILED
                            raise e
                            log.Logs.writeFailedOperation("failed to fetch bookid using book isbn code.")
                        else:
                            for rows in res:
                                bid=int(rows[0])
                            failed1=Mydb.insert_in_bookborrower(c,borwid,bid,libcard_id)
                            if failed1:
                                e.err = ErrorCodes.INSERT_NEWBORROWER_BORROWERDETAILS_WHENMANYISBN_FAILED
                                raise e
                            failed2= Mydb.updateCopiesInBookDetails(c,bid)
                            if failed2:
                                e.err = ErrorCodes.UPDATE_COPIES_BOOKDETAILS_WHENMANYISBN_FAILED
                                raise e
                            else:
                                res = Mydb.getBookTitle_usingISBN(c,isbn)
                                if res is None:
                                    e.err = ErrorCodes.GET_BOOKTITLE_USINGISBN_WHENONEISBN_FAILED
                                    raise e
                                    log.Logs.writeFailedOperation("Failed to fetch booktitle using book isbn.")
                                
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
            
            """if libcardno != "" and (all(ln.text() != "" for ln in self.dynamiclineedits) if not self.is_widget_in_layout(self.gridLayout_8,self.bookisbn_ln1) else self.bookisbn_ln1.text() != ""):
                res=Mydb.getLibcardid(c,libcardno)
                if res is None:
                    e.err = ErrorCodes.GET_LIBCARDID_USINGLIBCARDNO_FAILED
                    raise e
                    log.Logs.writeFailedOperation("Failed to get libacard id using library card.")
                rowc=len(res)
                #if library card no. is not in db
                if(rowc==0):
                    m.critical(self,"error","This Library card no. is not valid")
                    
                else:
                    for rows in res:
                        libcard_id=int(rows[0])
                    borwid = Mydb.genid(c,"borwid","borrower_details")
                    if borwid is None:
                        e.err = ErrorCodes.GENRATE_ID_BORROWERDETAILS_FAILED
                        raise e
                        log.Logs.writeFailedOperation("Failed to generate borrower id.")
                    if  self.is_widget_in_layout(self.gridLayout_8,self.bookisbn_ln1):
                        isbncode = self.bookisbn_ln1.text()
                        res=Mydb.getBookid(c,isbncode)
                        if res is None:
                            e.err = ErrorCodes.GET_BOOKID_USINGISBN_WHENONEISBN_FAILED
                            raise e
                            log.Logs.writeFailedOperation("failed to fetch bookid using book isbn code.")
                        else:
                            for rows in res:
                                bid=int(rows[0])
                            failed1=Mydb.insert_in_bookborrower(c,borwid,bid,libcard_id)
                            if failed1:
                                e.err = ErrorCodes.INSERT_NEWBORROWER_BORROWERDETAILS_WHENONEISBN_FAILED
                                raise e

                            failed2= Mydb.updateCopiesInBookDetails(c,bid)
                            if failed2:
                                e.err = ErrorCodes.UPDATE_COPIES_BOOKDETAILS_WHENONEISBN_FAILED
                                raise e
                            
                            else:
                                db.commit()
                                res = Mydb.getBookTitle_usingISBN(isbncode)
                                if res is None:
                                    e.err = ErrorCodes.GET_BOOKTITLE_USINGISBN_WHENONEISBN_FAILED
                                    raise e
                                    log.Logs.writeFailedOperation("Failed to fetch booktitle using book isbn.")
                                
                                for rows in res:
                                    bookname=str(rows[0])
                                m.information(self,"success","The books '{}' is checked out".format(str(bookname)))
                                self.libcardno_ln.clear()
                                self.numberofbooks_sb.setValue(1)
                                self.bookisbn_ln1.clear()
                        
                    else:
                        books = []
                        for ln in self.dynamiclineedits:
                            books.append(ln.text())
                        for isbncode in books:
                            res=Mydb.getBookid(c,isbncode)
                            if res is None:
                                e.err = ErrorCodes.GET_BOOKID_USINGISBN_WHENMANYISBN_FAILED
                                raise e
                                log.Logs.writeFailedOperation("failed to fetch book id using book isbn code.")
                            
                            for rows in res:
                                bid=int(rows[0])
                            failed1=Mydb.insert_in_bookborrower(c,borwid,bid,libcard_id)
                            if failed1:
                                e.err = ErrorCodes.INSERT_NEWBORROWER_BORROWERDETAILS_WHENMANYISBN_FAILED
                                raise e
                            failed2=Mydb.updateCopiesInBookDetails(c,bid)
                            if failed2:
                                e.err = ErrorCodes.UPDATE_COPIES_BOOKDETAILS_WHENMANYISBN_FAILED
                                raise e
                            
                            res = Mydb.getBookTitle_usingISBN(c,isbncode)
                            if res is None:
                                e.err = ErrorCodes.GET_BOOKTITLE_USINGISBN_WHENMANYISBN_FAILED
                                raise e
                                log.Logs.writeFailedOperation("failed to fetch book title using book isbn.")
                            
                            for rows in res:
                                bookname=str(rows[0])
                            m.information(self,"success","The books '{}' is checked out".format(bookname))
                        self.dynamiclineedits.clear()
                        self.numberofbooks_sb.setValue(1)
                        self.libcardno_ln.clear()
                        for ln in self.dynamiclineedits:
                            ln.clear()
                        
                self.showBorrowerPageFun(0)
                self.showAllBooksPageFun("")
            else:
                m.warning(self,"Failed","Please fill the input fields correctly")
            c.close();db.close()"""

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
            ErrorCodes.GET_LIBCARDID_USINGLIBCARDNO_FAILED:"Failed to get libcard id using library card no. for book issue.",
            ErrorCodes.GENRATE_ID_BORROWERDETAILS_FAILED:"Failed to generate borwid for adding new borrower.",
            ErrorCodes.GET_BOOKID_USINGISBN_WHENONEISBN_FAILED:"Failed to get book id using isbn when one book is being issued",
            ErrorCodes.INSERT_NEWBORROWER_BORROWERDETAILS_WHENONEISBN_FAILED:"Failed to insert new borrower in borrower details when one book is being issued.",
            ErrorCodes.UPDATE_COPIES_BOOKDETAILS_WHENONEISBN_FAILED:"Failed to update copies in book details when one book is being issued.",
            ErrorCodes.GET_BOOKTITLE_USINGISBN_WHENONEISBN_FAILED:"Failed to get book title using isbn code when one book is being issued.",
            ErrorCodes.GET_BOOKID_USINGISBN_WHENMANYISBN_FAILED:"Failed to get book id using isbn when more than one book is being issued.",
            ErrorCodes.INSERT_NEWBORROWER_BORROWERDETAILS_WHENMANYISBN_FAILED:"Failed to insert new borrower in borrower details when more than one book is being issued.",
            ErrorCodes.UPDATE_COPIES_BOOKDETAILS_WHENMANYISBN_FAILED:"Failed to update copies in book details when more than one book is being issued.",
            ErrorCodes.GET_BOOKTITLE_USINGISBN_WHENMANYISBN_FAILED:"Failed to get book title using isbn when more than one book is being issued."
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
        #showing borrowers with penalty
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            m = QMessageBox()
            e = CustomErrorAndLogWriting()
            em = EmailSender()
            em.checkAndSendEmail()
            
            self.showborrowerwithpenalty_tableWidget.clear()
            self.showborrowerwithpenalty_tableWidget.setRowCount(0)
            self.showborrowerwithpenalty_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            failed = Mydb.updatePenaltyInBorrowerDetails(c)
            if failed:
                e.err = ErrorCodes.UPDATE_PENALTY_BORROWERDETAILS_FAILED
                raise e
            db.commit()
            header,result = Mydb.showPenaltyBorrowers(c)
            if header is None or result is None:
                e.err = ErrorCodes.SHOW_BORROWERSWITHPENALTY_BORROWERSDETAILS_FAILED
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
            ErrorCodes.UPDATE_PENALTY_BORROWERDETAILS_FAILED:"Failed to update penalty of borrowers in borrower details.",
            ErrorCodes.SHOW_BORROWERSWITHPENALTY_BORROWERSDETAILS_FAILED:"Failed to fetch information about borrowers who has penalty."
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
        #returning book
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            m = QMessageBox()
            e = CustomErrorAndLogWriting()
            libcardno = self.libcardno_ln_2.text()
            booktitle = ''
            
            #if libcardno != "" and (all(ln.text() != "" for ln in self.dynamiclineedits2) if not self.is_widget_in_layout(self.gridLayout_9, self.bookisbn_return_ln) else self.bookisbn_return_ln.text() != ""):
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
                            e.err = ErrorCodes.UPDATE_MANYRETURNBOOK_BORROWERDETAILS_FAILED
                            raise e
                        failed2=Mydb.updateReturnedCopiesInBookDetails(c,bid)
                        if failed2:
                            e.err = ErrorCodes.UPDATE_COPIES_BOOKDETAILS_WHENRETURNMANY_FAILED
                            raise e

                        res = Mydb.getBookTitle(c,bid)
                        if res is None:
                            e.err = ErrorCodes.GET_BOOKTITLE_USINGBID_TORETURNBOOK_FAILED
                            raise e
                            log.Logs.writeFailedOperation("Failed to get book title using book id for book return")
                        else:
                            for row in res:
                                booktitle = booktitle + str(row[0]) +'\n'
                m.information(self,"success","The book/books: '{}' is/are returned successfully!!".format(str(booktitle)))
                self.libcardno_ln_2.clear()
                self.returnbooks.clear()
                self.showBorrowerPageFun(0)
                self.showAllBooksPageFun("")
                db.commit()    
                """res=Mydb.getLibcardid(c,libcardno)
                if res is None:
                    e.err = ErrorCodes.GET_LIBCARDID_USINGLIBCARDNO_FORRETURNBOOK_FAILED
                    raise e
                else:
                    for row in res:
                        libcard_id=int(row[0])
                res=Mydb.getborwid(c,libcard_id)
                if res is None:
                    e.err = ErrorCodes.GET_BORROWERID_USINGLIBCARDID_FORRETURNBOOK_FAILED
                    raise e
                    log.Logs.writeFailedOperation("Failed to get borrower id who did not returned the book using libcard id")
                else:
                    for row in res:
                        borwid=int(row[0])
                if  self.is_widget_in_layout(self.gridLayout_9,self.bookisbn_return_ln):
                        isbncode = self.bookisbn_return_ln.text()
                        res=Mydb.getBookid(c,isbncode)
                        if res is None:
                            e.err = ErrorCodes.GET_BOOKID_USINGISBN_TORETURNBOOK_FAILED
                            raise e
                            log.Logs.writeFailedOperation("Failed to get book id using isbn code.")
                        else:
                            for rows in res:
                                bid=int(rows[0])
                        failed1=Mydb.updateReturnedBookInBookBorrower(c,borwid,bid)
                        if failed1:
                            e.err = ErrorCodes.UPDATE_RETURNBOOK_BORROWERDETAILS_FAILED
                            raise e
                        failed2=Mydb.updateReturnedCopiesInBookDetails(c,bid)
                        if failed2:
                            e.err = ErrorCodes.UPDATE_COPIES_BOOKDETAILS_WHENRETURN_FAILED
                            raise e

                        res = Mydb.getBookTitle(c,bid)
                        if res is None:
                            e.err = ErrorCodes.GET_BOOKTITLE_USINGBID_TORETURNBOOK_FAILED
                            raise e
                            log.Logs.writeFailedOperation("Failed to get book title using book id for book return")
                        else:
                            for row in res:
                                booktitle = str(row[0])
                            m.information(self,"success","The book: '{}' is returned successfully!!".format(str(booktitle)))
                        self.libcardno_ln_2.clear()
                        self.bookisbn_return_ln.clear()
                else:
                    books = []
                    for ln in self.dynamiclineedits2:
                            books.append(ln.text())
                    for isbncode in books:
                            res= Mydb.getBookid(c,isbncode)
                            if res is None:
                                e.err = ErrorCodes.GET_BOOKID_USINGISBN_TORETURNMANYBOOK_FAILED
                                raise e
                                log.Logs.writeFailedOperation("Failed to get book id using isbncode.")
                            else:
                                for rows in res:
                                    bid=int(rows[0])
                            failed1=Mydb.updateReturnedBookInBookBorrower(c,borwid,bid)
                            if failed1:
                                e.err = ErrorCodes.UPDATE_MANYRETURNBOOK_BORROWERDETAILS_FAILED
                                raise e
                            failed2=Mydb.updateReturnedCopiesInBookDetails(c,bid)
                            if failed2:
                                e.err = ErrorCodes.UPDATE_COPIES_BOOKDETAILS_WHENRETURNMANY_FAILED
                                raise e
                            
                            res = Mydb.getBookTitle(c,bid)
                            if res is None:
                                e.err = ErrorCodes.GET_BOOKTITLE_USINGBID_TORETURNMANYBOOK_FAILED
                                raise e
                                log.Logs.writeFailedOperation("Failed to get book title using book id")
                            
                            for row in res:
                                booktitle = str(row[0])
                            m.information(self,"success","The book: '{}' is returned successfully!!".format(str(booktitle)))
                    for ln in self.dynamiclineedits2:
                        ln.clear()
                    self.libcardno_ln_2.clear()
                self.showBorrowerPageFun(0)
                self.showAllBooksPageFun("")
                db.commit()"""
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
            ErrorCodes.UPDATE_PENALTY_BORROWERDETAILS_FAILED:"Failed to update penalty of borrowers in borrower details.",
            ErrorCodes.GET_LIBCARDID_USINGLIBCARDNO_FORRETURNBOOK_FAILED:"Failed to get libcard id using libcardno for returning book.",
            ErrorCodes.GET_BORROWERID_USINGLIBCARDID_FORRETURNBOOK_FAILED:"Failed to get borrower id using libcard id for returning book.",
            ErrorCodes.GET_BOOKID_USINGISBN_TORETURNBOOK_FAILED:"Failed to get bookid using isbn to return book.",
            ErrorCodes.UPDATE_RETURNBOOK_BORROWERDETAILS_FAILED:"Failed to update borrower details when book is returned.",
            ErrorCodes.UPDATE_COPIES_BOOKDETAILS_WHENRETURN_FAILED:"Failed to update copies of book when book is returned.",
            ErrorCodes.GET_BOOKTITLE_USINGBID_TORETURNBOOK_FAILED:"Failed to get book title using book id to return book.",
            ErrorCodes.GET_BOOKID_USINGISBN_TORETURNMANYBOOK_FAILED:"Failed to get book id using isbn to return many books.",
            ErrorCodes.UPDATE_MANYRETURNBOOK_BORROWERDETAILS_FAILED:"Failed to update borrower details when many books are returned.",
            ErrorCodes.UPDATE_COPIES_BOOKDETAILS_WHENRETURNMANY_FAILED:"Failed to update copies of books when many books are returned.",
            ErrorCodes.GET_BOOKTITLE_USINGBID_TORETURNMANYBOOK_FAILED:"Failed to get book title using book id when many books are returned."
            
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
        #showing all users
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            
            self.showusers_tableWidget.clear()
            self.showusers_tableWidget.setRowCount(0)
            self.showusers_tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            header,result = Mydb.showAllRegisteredUsers(c)
            if header is None or result  is None:
                e.err = ErrorCodes.SHOW_ALLUSERS_PASSINFO_FAILED
                raise e
                
            self.showusers_tableWidget.setColumnCount(len(result[0])+1)
            self.showusers_tableWidget.setHorizontalHeaderLabels(['']+header)
            self.showusers_tableWidget.setColumnWidth(0, 50)
            for rowno, row_data in enumerate(result):
                self.showusers_tableWidget.insertRow(rowno)
                checkbox_item = QtWidgets.QTableWidgetItem()
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
            ErrorCodes.SHOW_ALLUSERS_PASSINFO_FAILED:"Failed to fetch information about all registered user in passwordinfo."
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
        #adding context menu for user management
        context_menu = QtWidgets.QMenu(self)
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
        #deleting other users
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
                e.err = ErrorCodes.DELETE_USER_PASSINFO_FAILED
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
            ErrorCodes.DELETE_USER_PASSINFO_FAILED:"Failed to delete user from passwordinfo."
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
        #making people admin
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
                e.err = ErrorCodes.UPDATE_ROLETOADMIN_PASSINFO_FAILED
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
            ErrorCodes.UPDATE_ROLETOADMIN_PASSINFO_FAILED:"Failed to update user role to admin in passwordinfo."
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
        # removing admin
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
                e.err = ErrorCodes.UPDATE_ROLETOLIBRARIAN_PASSINFO_FAILED
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
            ErrorCodes.UPDATE_ROLETOLIBRARIAN_PASSINFO_FAILED:"Failed to update user role to librarian in passwordinfo."
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
        #getting all checked item from usermanagement table
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
        #showing all books and making all information in editable
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
                    e.err = ErrorCodes.SHOW_ALLBOOKDETAILS_TOCHANGE_FAILED
                    raise e
                if len(res) == 0:
                    self.showusers_tableWidget.clear()
                    self.showusers_tableWidget.setRowCount(0)
                    self.showusers_tableWidget.setColumnCount(0)
                else:
                    print(res)
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
                ErrorCodes.SHOW_ALLBOOKDETAILS_TOCHANGE_FAILED:"Failed to fetch all books details to make changes in book details for admin."
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
        #showing book which get edditable
        try:
            self.bookmanagement_tableWidget.itemChanged.disconnect(self.changedBookInfo)
            self.bookmanagement_tableWidget.clear()
            self.bookmanagement_tableWidget.setRowCount(0)
            
            #print(type(result))
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
        #adding context menu for book management
        context_menu = QtWidgets.QMenu(self)
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
        #making book title column editable
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
        #making ISBN column editable
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
        #making total no. of copies column editable
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
        #making author name column editable
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

    def changedBookInfo(self, item):
        #function to update the book information
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            e = CustomErrorAndLogWriting()
            print("problem:",item.text())
            if item.column() == 2:
                text = item.text()
                id = self.bookmanagement_tableWidget.item(item.row(), 0).text()
                failed = Mydb.updateISBN(c,id,text)
                if failed:
                    e.err = ErrorCodes.UPDATE_ISBN_BOOKDETAILS_FAILED
                    raise e
                    
                header,res = Mydb.searchBooks(c,
                self.booksearch_ln.text())
                if header is  None or res is None:
                    e.err = ErrorCodes.SHOW_ALLBOOKDETAILS_TOCHANGEISBN_FAILED
                    raise e
                    
                self.showBookmanagementFun(header,res)
                self.editISBN()

            elif item.column() == 3:
                text = item.text()
                id = self.bookmanagement_tableWidget.item(item.row(), 0).text()
                failed = Mydb.updateBookTitle(c,id,text)
                if failed:
                    e.err = ErrorCodes.UPDATE_BOOKTITLE_BOOKDETAILS_FAILED
                    raise e
                    
                header,res = Mydb.searchBooks(c,self.booksearch_ln.text())
                if header is  None or res is None:
                    e.err = ErrorCodes.SHOW_ALLBOOKDETAILS_TOCHANGEBOOKTITLE_FAILED
                    raise e
                    
                self.showBookmanagementFun(header,res)
                self.editBookTitle()
            elif item.column() == 4:
                text = item.text()
                id = self.bookmanagement_tableWidget.item(item.row(), 0).text()
                failed = Mydb.updateNoOfCopies(c,id,text)
                if failed:
                    e.err = ErrorCodes.UPDATE_COPIES_BOOKDETAILS_FAILED
                    raise e
                    
                header,res = Mydb.searchBooks(c,self.booksearch_ln.text())
                if header is  None or res is None:
                    e.err = ErrorCodes.SHOW_ALLBOOKDETAILS_TOCHANGECOPIES_FAILED
                    raise e
                    
                self.showBookmanagementFun(header,res)
                self.editNoOfCopies()
            elif item.column() == 5:
                text = item.text()
                id = self.bookmanagement_tableWidget.item(item.row(), 1).text()
                failed = Mydb.updateAuthorName(c,id,text)
                if failed:
                    e.err = ErrorCodes.UPDATE_AUTHORNAME_BOOKDETAILS_FAILED
                    raise e
                    
                header,res = Mydb.searchBooks(c,self.booksearch_ln.text())
                if header is  None or res is None:
                    e.err = ErrorCodes.SHOW_ALLBOOKDETAILS_TOCHANGEAUTHOR_FAILED
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
                ErrorCodes.UPDATE_ISBN_BOOKDETAILS_FAILED:"Failed to update book isbn.",
                ErrorCodes.SHOW_ALLBOOKDETAILS_TOCHANGEISBN_FAILED:"Failed to fetch information about books to change isbn.",
                ErrorCodes.UPDATE_BOOKTITLE_BOOKDETAILS_FAILED:"Failed to update book title",
                ErrorCodes.SHOW_ALLBOOKDETAILS_TOCHANGEBOOKTITLE_FAILED:"Failed to fetch information about books to change booktitle.",
                ErrorCodes.UPDATE_COPIES_BOOKDETAILS_FAILED:"Failed to update book copies.",
                ErrorCodes.SHOW_ALLBOOKDETAILS_TOCHANGECOPIES_FAILED:"Failed to fetch information about books to change no. of copies.",
                ErrorCodes.UPDATE_AUTHORNAME_BOOKDETAILS_FAILED:"Failed to update book's author name.",
                ErrorCodes.SHOW_ALLBOOKDETAILS_TOCHANGEAUTHOR_FAILED:"Failed to fetch information about books to change author name."
                }
                    if e.err in error_messages:
                        print(traceback.format_exc())
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
