import os
from datetime import datetime
import traceback
from PyQt6.QtWidgets import QMessageBox
from enum import Enum

class ErrorCodes(Enum):
      # '104 done'
      USERID_SEARCH_NEWACCPAGE_FAILED = '1'
      USERID_SEARCH_APPLYNEWLIBCARDPAGE_FAILED = '2'
      LOCATION_SEARCH_APPLYNEWLIBCARDPAGE_FAILED = '3' 
      BOOK_SEARCH_BOOKDETAILS_FAILED = '4'

      GENRATE_ID_PASSWORDINFO_FAILED = '5'
      GENRATE_ID_LIBRARYCARDINFO_FAILED = '6'
      GENRATE_ID_LOCATION_FAILED = '7' 
      GENRATE_ID_AUTHORDETAILS_FAILED = '8'
      GENRATE_ID_BOOKDETAILS_FAILED = '9'
      GENRATE_ID_CATEGORYDETAILS_FAILED = '99'
      #GENRATE_ID_CATEGORYDETAILS_NOAUTHOR_FAILED = '10'
      #GENRATE_ID_CATEGORYDETAILS_WHENAUTHOR_FAILED = '11'
      GENRATE_ID_BORROWERDETAILS_FAILED = '12'

      SHOW_ALLBORROWERS_BORROWERSDETAILS_FAILED = '13'
      SHOW_BORROWERSRETURNED_BORROWERSDETAILS_FAILED = '14'
      SHOW_BORROWERSNOTRETURNED_BORROWERSDETAILS_FAILED = '15'
      SHOW_BORROWERSWITHPENALTY_BORROWERSDETAILS_FAILED = '16'
      SHOW_ALLUSERS_PASSINFO_FAILED = '17'
      SHOW_ALLBOOKDETAILS_TOCHANGE_FAILED = '18'
      SHOW_ALLBOOKDETAILS_TOCHANGEISBN_FAILED = '19'
      SHOW_ALLBOOKDETAILS_TOCHANGEBOOKTITLE_FAILED = '20'
      SHOW_ALLBOOKDETAILS_TOCHANGECOPIES_FAILED = '21'
      SHOW_ALLBOOKDETAILS_TOCHANGEAUTHOR_FAILED = '22'
      SHOW_ALLCATEGORY_ADDNEWBOOK_FAILED = '74'

      INSERT_NEWUSER_PASSWORDINFO_FAILED = '23'
      INSERT_NEW_LOCATION_FAILED = '24' 
      INSERT_NEW_LIBRARYCARD_FAILED = '25'
      INSERT_NEW_LIBRARYCARD_WITH_LOCID_FAILED = '26' 
      INSERT_NEW_AUTHOR_AUTHORDETAILS_FAILED = '27' 
      INSERT_NEWBOOK_BOOKDETAILS_NOAUTHOR_FAILED = '28'
      INSERT_NEWCATEGORY_CATEGORYDETAILS_FAILED = '98' 
      #INSERT_NEWCATEGORY_CATEGORYDETAILS_NOAUTHOR_FAILED = '29' 
      #INSERT_NEWCATEGORY_CATEGORYDETAILS_WITHAUTHOR_FAILED = '30' 
      #INSERT_NEWCATEGORY_BOOKCATEGORY_NOAUTHOR_NOCAT_FAILED = '31' 
      INSERT_NEWCATEGORY_BOOKCATEGORY_NOAUTHOR_WITHCAT_FAILED = '32' 
      #INSERT_NEWCATEGORY_BOOKCATEGORY_WITHAUTHOR_NOCAT_FAILED = '33' 
      INSERT_NEWCATEGORY_BOOKCATEGORY_WITHAUTHOR_WITHCAT_FAILED = '34' 
      INSERT_NEWBOOK_BOOKDETAILS_WITHAUTHOR_FAILED = '35'
      INSERT_NEWBORROWER_BORROWERDETAILS_WHENONEISBN_FAILED = '36'
      INSERT_NEWBORROWER_BORROWERDETAILS_WHENMANYISBN_FAILED = '37'

      UPDATE_COPIES_BOOKDETAILS_WHENONEISBN_FAILED = '38'
      UPDATE_COPIES_BOOKDETAILS_WHENMANYISBN_FAILED = '39'
      UPDATE_PENALTY_BORROWERDETAILS_FAILED = '40'
      UPDATE_PENALTYPAYMENT_BORROWERDETAILS_FAILED = '104'
      UPDATE_RETURNBOOK_BORROWERDETAILS_FAILED = '41'
      UPDATE_COPIES_BOOKDETAILS_WHENRETURN_FAILED = '42'
      UPDATE_MANYRETURNBOOK_BORROWERDETAILS_FAILED = '43'
      UPDATE_COPIES_BOOKDETAILS_WHENRETURNMANY_FAILED = '44'
      UPDATE_ROLETOADMIN_PASSINFO_FAILED = '45'
      UPDATE_ROLETOLIBRARIAN_PASSINFO_FAILED = '46'
      UPDATE_ISBN_BOOKDETAILS_FAILED = '47'
      UPDATE_BOOKTITLE_BOOKDETAILS_FAILED = '48'
      UPDATE_COPIES_BOOKDETAILS_FAILED = '49'
      UPDATE_AUTHORNAME_BOOKDETAILS_FAILED = '50'
      UPDATE_LASTEMAILSENTDATE_PENALTYBORROWERS_FAILED = '73'
      

      DELETE_USER_PASSINFO_FAILED = "51"

      CHECK_USERID_AND_PASS_PASSWORDINFO_FAILED = '52'
      CHECK_BOOK_BOOKDETAILS_FAILED = '53'
      CHECK_CATEGORYEXISTENCE_CATEGORYDETAILS_FAILED = '97'
      CHECK_PENALTY_BORROWERDETAILS_FAILED='103'

      GET_AUTHORID_USINGAUTHORNAME_FAILED = '54'
      GET_CATEGORYID_WHENAUTHOR_USINGCATEGORYNAME_FAILED = '56'
      GET_CATEGORYID_NOAUTHOR_USINGCATEGORYNAME_FAILED = '57'
      GET_BOOKTITLE_USINGBID_FAILED = '58'
      GET_LIBCARDID_USINGLIBCARDNO_FAILED = '59'
      GET_BOOKID_USINGISBN_WHENONEISBN_FAILED = '60'
      GET_BOOKID_USINGISBN_WHENMANYISBN_FAILED = '61'
      GET_BOOKTITLE_USINGISBN_WHENONEISBN_FAILED = '62'
      GET_BOOKTITLE_USINGISBN_WHENMANYISBN_FAILED = '63'
      GET_LIBCARDID_USINGLIBCARDNO_FORRETURNBOOK_FAILED = '64'
      GET_BORROWERID_USINGLIBCARDID_FORRETURNBOOK_FAILED = '65'
      GET_BOOKID_USINGISBN_TORETURNBOOK_FAILED = '66'
      GET_BOOKTITLE_USINGBID_TORETURNBOOK_FAILED = '67'
      GET_BOOKID_USINGISBN_TORETURNMANYBOOK_FAILED = '68'
      GET_BOOKTITLE_USINGBID_TORETURNMANYBOOK_FAILED = '69'
      GET_RECIEVERDATA_PENALTYBORROWERS_FAILED = '70'
      GET_RECIEVERBOOKTITLES_PENALTYBORROWERS_FAILED = '71'
      GET_BOOKINFOBOOKISSUE_BOOKDETAILS_FAILED = '100'
      GET_LIBCARDHOLDERINFOBOOKISSUE_LIBCARDINFO_FAILED = '101'
      GET_BORROWERBOOKRETURN_BORROWERDETAILS_FAILED = '102'

      ISEMAILNOTSENT_PENALTYBORROWERS_FAILED = '72'

      
      

class CustomErrorAndLogWriting(Exception):
    
    def __init__(self):
          super().__init__(self)
          self.err = None
    def __init__(self, err=None):
        self.err = err

    def __str__(self):
        return f"CustomErrorAndLogWriting: {self.err}"

    def writeAllErrorInLog(self,error_type:list,error_messages:str|None) -> None:
        """
          Function to write error generated in main file in Error_logs.txt file and show all errors in single popup to user.
        """
        show_message = "Errors occured:\n"
        for i in error_type:
            show_message = show_message+str(i)+"\n"
        QMessageBox.critical(None,"Error",show_message+"\n click ok to see Error_logs.txt file to see the logs")
        with open(r'Error_logs.txt', 'a') as file:
                file.write("\n\n---------------------------------------------------------------------------------\nerror occured at:"+str(datetime.now())+"\n"+error_messages+"\n")
        os.startfile(r'Error_logs.txt')
    
    def writeSingleErrorInLog(self,emsg:str) -> None:
        """
          Function to write one error at a time generated in db.py file in Error_logs.txt file and not show popup.
        """
        with open(r'Error_logs.txt', 'a') as file:
                file.write("\n\n---------------------------------------------------------------------------------\nerror occured at:"+str(datetime.now())+"\n\n"+str(emsg)+"\n")

    def writeFailedOperation(self,emsg:str) -> None:
        """
          Function to write custom error in Error_logs.txt file and inform user about it.
        """
        
        with open(r'Error_logs.txt', 'a') as file:
                file.write("\n\n---------------------------------------------------------------------------------\nerror occured at:"+str(datetime.now())+"\n"+str(emsg)+"\n")
        QMessageBox.critical(None,"Error","\n"+str(emsg)+"\n")







class Logs(QMessageBox):
    def writeLog(self,error_type:list) -> None:
        """
          Function to write error generated in main file in Error_logs.txt file and inform user that an error occured.
        """
        error_message = "Errors occured:\n"
        for i in error_type:
             error_message = error_message+str(i)+"\n"
        QMessageBox.critical(self,"Error",error_message+"\n click ok to see Error_logs.txt file to see the logs")
        with open(r'Error_logs.txt', 'a') as file:
                file.write("\n\n---------------------------------------------------------------------------------\nerror occured at:"+str(datetime.now())+"\n"+traceback.format_exc()+"\n")
        os.startfile(r'Error_logs.txt')
        

    def writeDBErrorLog(self,emsg:str) -> None:
        """
          Function to write error generated in db.py file in Error_logs.txt file for not to show popup msg again and again.
        """
        with open(r'Error_logs.txt', 'a') as file:
                file.write("\n\n---------------------------------------------------------------------------------\nerror occured at:"+str(datetime.now())+"\n"+traceback.format_exc()+"\n"+str(emsg)+"\n")
    
    def writeFailedOperation(self,emsg:str) -> None:
        """
          Function to write custom error in Error_logs.txt file and inform user about it.
        """
        with open(r'Error_logs.txt', 'a') as file:
                file.write("\n\n---------------------------------------------------------------------------------\nerror occured at:"+str(datetime.now())+"\n"+str(emsg)+"\n")
        QMessageBox.critical(self,"Error","\n"+str(emsg)+"\n")