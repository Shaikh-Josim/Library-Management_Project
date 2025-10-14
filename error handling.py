from PyQt6.QtWidgets import QMessageBox, QApplication
import os,datetime,traceback
from log import CustomError

errors = []
error_msgs = ''
def generate_errors():
    global error_msgs
    try:
        # ValueError: Trying to convert an invalid string to an integer
        int("invalid_number")
    except ValueError as e:
        print(f"Caught ValueError: {e}")
        errors.append("value error")
        msg = "\n"+traceback.format_exc()
        error_msgs = error_msgs + msg


    try:
        # AttributeError: Trying to access a non-existent attribute
        class SampleClass:
            def __init__(self):
                self.name = "Example"

        obj = SampleClass()
        print(obj.age)  # 'age' attribute does not exist
    except AttributeError as e:
        print(f"Caught AttributeError: {e}")
        errors.append("Attribute error")
        msg = "\n"+traceback.format_exc()
        error_msgs = error_msgs + msg

    try:
        # UnboundLocalError: Trying to use a variable before defining it
        def unbound_example():
            print(x)  # 'x' is referenced before assignment
            x = 10

        unbound_example()
    except UnboundLocalError as e:
        print(f"Caught UnboundLocalError: {e}")
        errors.append("Unboundlocal error")
        msg = "\n"+traceback.format_exc()
        error_msgs = error_msgs + msg

    
generate_errors()
print(errors)


app = QApplication([]) 
CustomError().writeAllErrorInLog(error_type=errors,error_messages= error_msgs)
try:
        n = 1
        if n == 1:
            raise CustomError()
        
except CustomError :
        CustomError().writeFailedOperation(emsg="Some error occured"+str(n))

errors.clear()
app.exec()

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