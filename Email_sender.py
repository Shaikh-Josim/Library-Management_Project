import os
import smtplib
import traceback
from dotenv import load_dotenv
from db import Dbconnection
from log import CustomErrorAndLogWriting , ErrorCodes
from email.message import EmailMessage

class EmailSender():

    def __init__(self):
        load_dotenv()
        self.sender_email = os.getenv('EMAIL')
        self.password = os.getenv('PASS')
        
    def sendEmail(self,to,subject,content):
        try:
            
            self.msg = EmailMessage()
            self.msg['From'] = self.sender_email
            self.msg['Subject'] = subject
            self.msg['To'] = to
            self.msg.set_content(content)
            self.msg.add_header('List-Unsubscribe', '<mailto:codevortex124@gmail.com>')
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()  # Start TLS encryption
                server.login(self.sender_email, self.password)  # Log in to the server
                server.send_message(self.msg)  # Send the email
        except Exception as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            
        

    def checkAndSendEmail(self):
        # Recipent name,email, borrowed date, books title, penalty 
        try:
            Mydb = Dbconnection()
            c,db = Mydb.makeConnection()
            err = CustomErrorAndLogWriting()
            self.reciever_info = Mydb.getEmailReceiverData(c)

            if self.reciever_info is None:
                err.err = ErrorCodes.GET_RECIEVERDATA_PENALTYBORROWERS_FAILED
                raise err
            
            for row in self.reciever_info:
                name = str(row[0])+str(row[1])
                userid = str(row[2])
                date = str(row[3])
                penalty = str(row[4])
                reciever_books = ""
                self.reciever_books = Mydb.getReceiverBookTitles(c,row[2])

                if self.reciever_books == None:
                    err.err = ErrorCodes.GET_RECIEVERBOOKTITLES_PENALTYBORROWERS_FAILED
                    raise err
                for row in self.reciever_books:
                    for book in row:
                        reciever_books += str(book) + "\n"

                content = self.emailPenaltyContent(name,userid,date,
                penalty,reciever_books)
                subject = "reminder: book penalty due- action required"
                to = userid
                #check if email is sent already

                email_not_sent = Mydb.isEmailNotSent(c,userid)
                print(email_not_sent)
                if email_not_sent is None:
                    err.err = ErrorCodes.ISEMAILNOTSENT_PENALTYBORROWERS_FAILED
                    raise err
                if email_not_sent:
                    self.sendEmail(to,subject,content)
                    #update email sent date
                    failed = Mydb.updateLastEmailSentDate(c,userid)
                    if failed:
                        err.err = ErrorCodes.UPDATE_LASTEMAILSENTDATE_PENALTYBORROWERS_FAILED
                        raise err
                    db.commit()

        except CustomErrorAndLogWriting as e:
            error_messages = {
            ErrorCodes.GET_RECIEVERDATA_PENALTYBORROWERS_FAILED:"Failed to fetch reciever data to whom penalty msg should be send.",
            ErrorCodes.GET_RECIEVERBOOKTITLES_PENALTYBORROWERS_FAILED:"Failed to fetch book titles needed for penatly msg to send it reciever.",
            ErrorCodes.ISEMAILNOTSENT_PENALTYBORROWERS_FAILED:"Failed to find if email is sent already or not to the receiver.",
            ErrorCodes.UPDATE_LASTEMAILSENTDATE_PENALTYBORROWERS_FAILED:"Failed to update the last date on which email was sent to receiver."
            }
            if e.err in error_messages:
                e.writeFailedOperation(emsg=error_messages[e.err])
                db.rollback()

        except Exception as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
    
    def emailPenaltyContent(self,name,userid,date,penalty,reciever_books):
        books = reciever_books
        
        content = f"""\

        Dear {name},

        We hope this message finds you well. This is a friendly reminder regarding your due book penalty.

        Our records show that a penalty is due for the book(s) borrowed on {date}. The following items are currently overdue:
        {books}

        As per our policy, a penalty of {penalty} is applicable for the overdue period.

        Please visit our library to return the overdue items and settle the penalty.

        If you have any questions or need assistance, feel free to contact us at Library Contact Information.

        Thank you for your attention to this matter.

        Best regards,
        Rakesh Agarwal
        Admin
        Public library
        """
        return content
        


if __name__ == "__main__":

    e = EmailSender()
    e.checkAndSendEmail()

