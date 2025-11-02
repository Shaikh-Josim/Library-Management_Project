import os
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox
from enum import Enum

class ErrorCodes(Enum):
      #search error codes between 100-199
      #id generation error codes 200-299
      #insert error codes 300-399
      #check error codes 400-499
      #fetch info error codes 500-599
      #update error codes 600-699
      #delete error codes 700-799
      #get error codes 800-899
      #is or not error codes 900-999
      USERID_SEARCH_FOR_NEWACCOUNT_FAILED = 100
      USERID_SEARCH_FOR_NEWLIBCARD_FAILED = 101
      LOCATION_SEARCH_APPLYNEWLIBCARDPAGE_FAILED = 102
      BOOK_SEARCH_BOOKDETAILS_FAILED = 103

      GENRATE_ID_PASSWORDINFO_FAILED = 200
      GENRATE_ID_LIBRARYCARDINFO_FAILED = 201
      GENRATE_ID_LOCATION_FAILED = 202 
      GENRATE_ID_AUTHORDETAILS_FAILED = 203
      GENRATE_ID_BOOKDETAILS_FAILED = 204
      GENRATE_ID_CATEGORYDETAILS_FAILED = 205
      GENRATE_ID_BORROWERDETAILS_FAILED = 206

      INSERT_NEWUSER_PASSWORDINFO_FAILED = 300
      INSERT_NEW_LOCATION_FAILED = 301
      INSERT_NEW_LIBRARYCARD_FAILED = 302
      INSERT_NEW_LIBRARYCARD_WITH_LOCID_FAILED = 303 
      INSERT_NEW_AUTHOR_AUTHORDETAILS_FAILED = 304
      INSERT_NEWBOOK_BOOKDETAILS_NOAUTHOR_FAILED = 305
      INSERT_NEWCATEGORY_CATEGORYDETAILS_FAILED = 306
      INSERT_NEWCATEGORY_BOOKCATEGORY_NOAUTHOR_WITHCAT_FAILED = 307
      INSERT_NEWCATEGORY_BOOKCATEGORY_WITHAUTHOR_WITHCAT_FAILED = 308
      INSERT_NEWBOOK_BOOKDETAILS_WITHAUTHOR_FAILED = 309
      INSERT_ADMIN_PASSWORDINFO_FAILED = 310
      INSERT_NEWBORROWER_BORROWERDETAILS_WHENMANYISBN_FAILED = 311
      
      CHECK_USERID_AND_PASS_PASSWORDINFO_FAILED = 400
      CHECK_BOOK_BOOKDETAILS_FAILED = 401
      CHECK_CATEGORYEXISTENCE_CATEGORYDETAILS_FAILED = 402
      CHECK_PENALTY_BORROWERDETAILS_FAILED= 403
      CHECK_EMAILNOTSENT_PENALTYBORROWERS_FAILED = 404
      CHECK_NOADMIN_PASSWORDSINFO_FAILED = 405
      ISEMAILNOTSENT_PENALTYBORROWERS_FAILED = 900

      SHOW_ALLBORROWERS_BORROWERSDETAILS_FAILED = 500
      SHOW_BORROWERSRETURNED_BORROWERSDETAILS_FAILED = 501
      SHOW_BORROWERSNOTRETURNED_BORROWERSDETAILS_FAILED = 502
      SHOW_BORROWERSWITHPENALTY_BORROWERSDETAILS_FAILED = 503
      SHOW_ALLUSERS_PASSINFO_FAILED = 504
      SHOW_ALLBOOKDETAILS_TOCHANGE_FAILED = 505
      SHOW_ALLBOOKDETAILS_TOCHANGEISBN_FAILED = 506
      SHOW_ALLBOOKDETAILS_TOCHANGEBOOKTITLE_FAILED = 507
      SHOW_ALLBOOKDETAILS_TOCHANGECOPIES_FAILED = 508
      SHOW_ALLBOOKDETAILS_TOCHANGEAUTHOR_FAILED = 509
      SHOW_ALLCATEGORY_ADDNEWBOOK_FAILED = 510

      UPDATE_COPIES_BOOKDETAILS_WHENONEISBN_FAILED = 600
      UPDATE_COPIES_BOOKDETAILS_WHENMANYISBN_FAILED = 601
      UPDATE_PENALTY_BORROWERDETAILS_FAILED = 602
      UPDATE_PENALTYPAYMENT_BORROWERDETAILS_FAILED = 603
      UPDATE_MANYRETURNBOOK_BORROWERDETAILS_FAILED = 606
      UPDATE_COPIES_BOOKDETAILS_WHENRETURNMANY_FAILED = 607
      UPDATE_ROLETOADMIN_PASSINFO_FAILED = 608
      UPDATE_ROLETOLIBRARIAN_PASSINFO_FAILED = 609
      UPDATE_ISBN_BOOKDETAILS_FAILED = 610
      UPDATE_BOOKTITLE_BOOKDETAILS_FAILED = 611
      UPDATE_COPIES_BOOKDETAILS_FAILED = 612
      UPDATE_AUTHORNAME_BOOKDETAILS_FAILED = 613
      UPDATE_LASTEMAILSENTDATE_PENALTYBORROWERS_FAILED = 614
    
      DELETE_USER_PASSINFO_FAILED = 700

      GET_AUTHORID_USINGAUTHORNAME_FAILED = 800
      GET_CATEGORYID_WHENAUTHOR_USINGCATEGORYNAME_FAILED = 801
      GET_CATEGORYID_NOAUTHOR_USINGCATEGORYNAME_FAILED = 802
      GET_BOOKTITLE_USINGBID_FAILED = 803
      GET_LIBCARDID_USINGLIBCARDNO_FAILED = 804
      GET_BOOKID_USINGISBN_WHENMANYISBN_FAILED = 806
      GET_BOOKTITLE_USINGISBN_WHENONEISBN_FAILED = 807
      GET_BOOKTITLE_USINGBID_TORETURNBOOK_FAILED = 812
      GET_RECIEVERDATA_PENALTYBORROWERS_FAILED = 815
      GET_RECIEVERBOOKTITLES_PENALTYBORROWERS_FAILED = 816
      GET_BOOKINFOBOOKISSUE_BOOKDETAILS_FAILED = 817
      GET_LIBCARDHOLDERINFOBOOKISSUE_LIBCARDINFO_FAILED = 818
      GET_BORROWERBOOKRETURN_BORROWERDETAILS_FAILED = 819

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
