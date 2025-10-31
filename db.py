from __future__ import annotations

import mysql.connector
import random, sys
import traceback
from log import CustomErrorAndLogWriting

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mysql.connector.cursor import MySQLCursorAbstract



class Dbconnection():
    def __init__(self):
        super().__init__()
    
    def makeDatabase(self):
        """
        Makes database for library management app.

        This function does not take any parameter and does not return any value.
        """
        try:
            mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
            )
            c = mydb.cursor()

            db_name = "library_management"
            sqlfilepath = r"Appdata/data/Library_management.sql"

            c.execute("SHOW DATABASES LIKE '{}'".format(db_name))
            if c.fetchone():
                print("Database already exists")
            else:
                print("Creating database....")
                c.execute("CREATE DATABASE {}".format(db_name))
                mydb.commit()
                print("Database created successfully")

            # Select the database
                c.execute("USE {}".format(db_name))

                # Execute the SQL file
                with open(sqlfilepath, 'r') as sqlfile:
                    sql_commands = sqlfile.read()
                    for command in sql_commands.split(';'):
                        if command.strip():
                            c.execute(command)
                    mydb.commit()
                c.close();mydb.close()
        except mysql.connector.Error as err:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=err.msg+traceback.format_exc())

    def makeConnection(self):
        """
        Makes connection with database for library management app.

        This function does not take any parameter 
        
        Returns:
            c(MySQLCursorAbstract): cursor object to execute query.
            db(PooledMySQLConnection | MySQLConnectionAbstract): to make changes in db.
        """
        try:
            if self.is_connection():
            #try:
                self.mydb=mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="library_management"
                )
                self.c=self.mydb.cursor()
                return self.c, self.mydb
            
        except TypeError as err:
            #self.l.writeDBErrorLog(emsg=err)
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=traceback.format_exc())
        except mysql.connector.Error as err:
            if err.errno == 2003:  # Error code for "Can't connect to MySQL server"
                #self.l.writeDBErrorLog(emsg=err.msg)
                CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=err.msg+traceback.format_exc())
        return None, None

    def is_connection(self):
        """
        Check if connects with db or not.

        This function does not take any parameter 
        
        Returns:
            bool: True if connects else False.
        """
        try:
            self.mydb=mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            #database="library_management_DBtry",
            connection_timeout=1
            )
            self.mydb.close()
            return True
        
        except mysql.connector.Error as err :
            #self.l.writeDBErrorLog(err)
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=err.msg+traceback.format_exc()+"ypo")
            return False

    def genid(self,c:'MySQLCursorAbstract',tid:str,tname:str):
        """
        Generates unique id for perticular table

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            tid(str): primary key of table.
            tname(str): table name.
        
        Returns:
            r(int | None): returns the result.
        """
        try:
            r=random.randint(1,100)
            val=[r]
            q = "SELECT "+tid+" FROM "+tname+" WHERE "+tid+"=%s"
            c.execute(q,val)
            result = c.fetchall()
            rowcount = len(result)
            if(rowcount!=0):
                self.r =self.genid(c,tid,tname)
            else:
                self.r = r
            return self.r
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None

        except TypeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=traceback.format_exc())
            return None

    def search_userid(self,c:'MySQLCursorAbstract',userid:str):
        """
        Search given userid existence in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            userid(str): userid to be searched.
        
        Returns:
            r(bool | None): returns the result.
        """
        try:
            q = "SELECT userid FROM library_card_info WHERE userid='"+str(userid)+"' UNION SELECT userid FROM passwordsinfo WHERE userid='"+str(userid)+"';"
            
            c.execute(q)
            res = c.fetchall()
            if len(res) >= 1:
                return False
            else:
                return True
        
        except AttributeError as e :
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None

        except TypeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e+traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None
    
    def insert_into_passwordinfo(self,c:'MySQLCursorAbstract',ano:str,fn:str,ln:str,userid:str,p:str):
        """
        Insert new management user in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            ano(str): primary key of table.
            fn(str): first name.
            ln(str): last name.
            userid(str): userid.
            p(str): password.
        
        Returns:
            failed(bool): returns the failed flag True if failed.
        """
        try:
            val=(ano,fn,ln,userid,p)
            query="INSERT INTO  passwordsinfo (Ano,FirstName,Lastname,userid,pass,role) VALUES (%s,%s,%s,%s,%s,2)" 
            c.execute(query,val)
            failed = False

        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
            
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def checkuser_in_passwordinfo(self,c:'MySQLCursorAbstract',userid:str,p:str):
        """
        Checks userid with password existence in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            userid(str): userid.
            p(str): password.
        
        Returns:
            res(List|None): returns the result else None.
        """
        try:
            q = "SELECT userid,role FROM passwordsinfo WHERE userid=%s AND pass=%s"
            c.execute(q,(userid,p))
            res = c.fetchall()
            return res
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
            
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None

    def checklocation_existence(self,c:'MySQLCursorAbstract',stad:str,city:str,state:str):
        """
        Checks location existence in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            stad(str): street address.
            city(str): city.
            state(str): state.
        
        Returns:
            res(List|None): returns the result or None.
        """
        try:
            q="SELECT lid FROM location WHERE StreetAddress='"+stad+"'AND City='"+city+"' AND State= '"+state+"'"
            c.execute(q)
            res=c.fetchall()
            return res
        except AttributeError as e:
            #self.l.writeDBErrorLog(emsg=e)
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            #self.l.writeDBErrorLog(emsg=e.msg)
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None
    
    def insert_new_location(self,c:'MySQLCursorAbstract',locid:str,stad:str,city:str,state:str):
        """
        Insert new location in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            locid(str): primary key of new location
            stad(str): street address.
            city(str): city.
            state(str): state.
        
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            val=(locid,stad,city,state)
            query="INSERT INTO `location`(`lid`,`StreetAddress`, `City`, `State`) VALUES (%s,%s,%s,%s)"
            c.execute(query,val)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed
    
    def insert_new_libcard(self,c:'MySQLCursorAbstract',lid:str,fn:str,ln:str,gen:str,locid:str,phno:str,userid:str,libcardno:str,photo_path:str):
        """
        Insert new libcard holder.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            lid(str): primary key of new library card holder
            fn(str): first name.
            ln(str): last name.
            gen(str): gender.
            locid(str): location id.
            phno(str): phone no.
            userid(str): userid.
            libcardno(str): library card no.
            photo_path(str): photo of library card holder.
        
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            val=(lid,fn,ln,gen,locid,phno,userid,libcardno,photo_path)
            query="INSERT INTO `library_card_info`(`libcard_id`, `FirstName`, `LastName`, `Gender`, `lid`, `Mobile`, `userid` , `library_cardno`, `photo_path`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            c.execute(query,val)
            failed = False
        
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def showAllBooks(self,c:'MySQLCursorAbstract',s:str):
        """
        Returns book details.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            s(str): search term.
        
        Returns:
            header(List|None): returns the header or None.
            result(List|None): returns the result or None.
        """
        try:
            query="SELECT  book_title, no_of_copies,author_name FROM book_details,author_details WHERE book_details.aid = author_details.aid AND (book_details.book_title LIKE '%"+s+"%' OR book_details.isbn_code LIKE '%"+s+"%' OR author_details.author_name LIKE '%"+s+"%');"
            c.execute(query)
            header = [i[0] for i in c.description]
            result = c.fetchall()

            return header,result
        
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=traceback.format_exc())
            return None,None
            
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None,None

    def showAllBorrowers(self,c:'MySQLCursorAbstract'):
        """
        Returns borrower details.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
        
        Returns:
            header(List|None): returns the header or None.
            result(List|None): returns the result or None.
        """
        try:
            query="SELECT library_card_info.FirstName,library_card_info.LastName,book_details.Book_Title,borrower_details.borrowed_date FROM library_card_info,borrower_details,book_details WHERE book_details.bid=borrower_details.bid AND borrower_details.libcard_id=library_card_info.libcard_id"
            c.execute(query)
            header = [i[0] for i in c.description]
            result = c.fetchall()

            return header,result
        
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None,None

        except TypeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None,None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None,None

    def showReturnedBorrowers(self,c:'MySQLCursorAbstract'):
        """
        Returns borrower details who returned books.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
        
        Returns:
            header(List|None): returns the header or None.
            result(List|None): returns the result or None.
        """
        try:
            query="SELECT library_card_info.FirstName,library_card_info.LastName,book_details.Book_Title,borrower_details.borrowed_date FROM library_card_info,borrower_details,book_details WHERE book_details.bid=borrower_details.bid AND borrower_details.libcard_id=library_card_info.libcard_id AND borrower_details.isreturned=1;"
            c.execute(query)
            header = [i[0] for i in c.description]
            result = c.fetchall()

            return header,result
        
        except AttributeError as e:
            #self.l.writeDBErrorLog(emsg=e)
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None,None
                
        except mysql.connector.Error as e:
            #self.l.writeDBErrorLog(emsg=e.msg)
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None,None

    def showNotReturnedBorrowers(self,c:'MySQLCursorAbstract'):
        """
        Returns borrower details who did not returned books.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
        
        Returns:
            header(List|None): returns the header or None.
            result(List|None): returns the result or None.
        """
        try:
            query="SELECT library_card_info.FirstName,library_card_info.LastName,book_details.Book_Title,borrower_details.borrowed_date,borrower_details.expected_date as Due_date, borrower_details.penalty FROM library_card_info,borrower_details,book_details WHERE borrower_details.libcard_id=library_card_info.libcard_id AND borrower_details.bid = book_details.bid AND borrower_details.isreturned=0;"
            c.execute(query)
            header = [i[0] for i in c.description]
            result = c.fetchall()

            return header,result
        
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None, None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None, None

    def checkIfBookExist(self,c:'MySQLCursorAbstract',isbn:str,book_title:str,author_name:str):
        """
        Return book details if book exist.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            isbn(str): isbn code of book.
            book_title(str): book title.
            author_name(str): author name.

        Returns:
            res(list|None): returns list if query does not fails else None.
        """
        try:
            q="SELECT * FROM `book_details`, `author_details` WHERE book_details.isbn_code = '"+str(isbn)+"' AND book_details.book_title = '"+str(book_title)+"' AND author_details.author_name = '"+str(author_name)+"';"
            c.execute(q)
            res=c.fetchall()
            return res
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None

    def getAuthorid(self,c:'MySQLCursorAbstract',author_name:str):
        """
        Return primary key of author using author name.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            author_name(str): author name.

        Returns:
            res(list|None): returns list if query does not fails else None.
        """
        try:
            q="SELECT aid FROM `author_details` WHERE author_name = '"+author_name+"';"
            c.execute(q)
            res=c.fetchall()
            return res
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None

    def insert_new_author(self,c:'MySQLCursorAbstract',aid:str,author_name:str):
        """
        Insert new author of book in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            aid(str): primary key of new author.
            author_name(str): author name.
        
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            val=(aid,author_name)
            print(val)
            query="INSERT INTO `author_details`(`aid`,`author_name`) VALUES (%s,%s)"
            c.execute(query,val)
            failed = False
            
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def insert_new_book(self,c:'MySQLCursorAbstract',bid:str,isbn:str,book_title:str,aid:str,no_of_copies:str):
        """
        Insert new book in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            bid(str): primary key of new book.
            isbn(str): isbn code of book.
            book_title(str): book title.
            aid(str): Foreign key of author.
            no_of_copies(str): no. of copies.
        
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            val=(bid,isbn,book_title,aid,no_of_copies,no_of_copies)
            print(val)
            query="INSERT INTO `book_details`(`bid`,`ISBN_code`,`Book_Title`,`aid`,`no_of_copies`,`no_of_copies_available`) VALUES (%s,%s,%s,%s,%s,%s)"
            c.execute(query,val)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def showAllCategories(self,c:'MySQLCursorAbstract'):
        """
        Return categories name.

        Parameters:
            c(MySQLCursorAbstract): cursor object.

        Returns:
            res(list|None): returns list if query does not fails else None.
        """
        try:
            q="SELECT category_name FROM `category_details` ORDER BY category_name;"
            c.execute(q)
            res=c.fetchall()
            return res
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None

    def getCategoryid(self,c:'MySQLCursorAbstract',category_name:str):
        """
        Return primary key of category using category name.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            category_name(str): category name.

        Returns:
            res(list|None): returns list if query does not fails else None.
        """
        try:
            q="SELECT cid FROM `category_details` WHERE Category_name = '"+category_name+"';"
            c.execute(q)
            res=c.fetchall()
            return res
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None
        

    def insert_new_category(self,c:'MySQLCursorAbstract',cid:str,category_name:str):
        """
        Insert new category in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            cid(str): primary key of new category.
            category_name(str): category name.
        
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            val=(cid,category_name)
            query="INSERT INTO `category_details`(`cid`,`Category_name`) VALUES (%s,%s)"
            c.execute(query,val)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed
            
    def insert_new_category_in_bookcategory(self,c:'MySQLCursorAbstract',bid:str,cid:str):
        """
        Insert new category id and book id in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            bid(str): Foreign key of book.
            cid(str): Foreign key of category.    
        
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            val=(bid,cid)
            query="INSERT INTO `bookcategory`(`bid`,`cid`) VALUES (%s,%s)"
            c.execute(query,val)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def getBookTitle(self,c:'MySQLCursorAbstract',bid:str):
        """
        Return book title using primary key of book.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            bid(str): primary key of book.

        Returns:
            res(list|None): returns list if query does not fails else None.
        """
        try:
            q="SELECT Book_Title FROM `book_details` WHERE bid = "+str(bid)
            c.execute(q)
            res=c.fetchall()
            return res
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None

    def getLibcardid(self,c:'MySQLCursorAbstract',libcardno:str):
        """
        Return primary key of library card holder using libcard no.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            libcardno(str): library card no.

        Returns:
            res(list|None): returns list if query does not fails else None.
        """
        try:
            q="SELECT libcard_id FROM `library_card_info` WHERE library_cardno ="+str(libcardno)+";"
            c.execute(q)
            res=c.fetchall()
            return res
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
            
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None

    def getBookInfo(self,c:'MySQLCursorAbstract',isbn:str):
        """
        Returns book details based on isbn-code.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            isbn(str): isbn code of book.
        
        Returns:
            header(List|None): returns the header or None.
            result(List|None): returns the result or None.
        """
        try:
            q = "SELECT book_details.isbn_code, book_details.book_title, author_details.author_name FROM book_details, author_details WHERE (book_details.isbn_code = '"+str(isbn)+"') AND (book_details.aid = author_details.aid);"
            c.execute(q)
            header = [i[0] for i in c.description]
            result = c.fetchall()
            return header,result
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
            
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None
        
    def getLibcardHolderInfo(self,c:'MySQLCursorAbstract',libcardno:str):
        """
        Return details of library card holder using library card no.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            libcardno(str): library card no.

        Returns:
            res(list|None): returns list if query does not fails else None.
        """
        try:
            q = "SELECT library_card_info.firstname, library_card_info.lastname, library_card_info.gender, library_card_info.mobile, library_card_info.userid, library_card_info.library_cardno, library_card_info.photo_path, location.streetaddress, location.city, location.state FROM `library_card_info`, `location` WHERE library_card_info.lid = location.lid AND library_card_info.library_cardno = '"+str(libcardno)+"';"
            c.execute(q)
            result = c.fetchall()
            return result
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
            
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None
        
    def getBorrowerInfo(self,c:'MySQLCursorAbstract',libcardno:str):
        """
        Returns borrower details based on library card no.

        Parameter:
            c(MySQLCursorAbstract): cursor object.
            libcardno(str): library card no.
        
        Returns:
            header(List|None): returns the header or None.
            result(List|None): returns the result or None.
        """
        try:
            q = """SELECT borrower_details.borwid,borrower_details.bid,library_card_info.library_cardno, book_details.book_title, borrower_details.borrowed_date, borrower_details.penalty
            FROM borrower_details
            JOIN library_card_info ON borrower_details.libcard_id = library_card_info.libcard_id
            JOIN book_details ON borrower_details.bid = book_details.bid
            WHERE borrower_details.isreturned = 0 AND
            library_card_info.library_cardno = '"""+str(libcardno)+"';"
            c.execute(q)
            header = [i[0] for i in c.description]
            result = c.fetchall()
            return header,result
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
            
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None
      
    def getBookid(self,c:'MySQLCursorAbstract',isbncode:str):
        """
        Return primary key of book using isbncode.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            isbncode(str): isbn code of book.

        Returns:
            res(list|None): returns list if query does not fails else None.
        """
        try:
            q="SELECT bid FROM `book_details` WHERE ISBN_code ='"+str(isbncode)+"';"
            c.execute(q)
            res=c.fetchall()
            return res
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None

    def getBookTitle_usingISBN(self,c:'MySQLCursorAbstract',isbncode:str):
        """
        Return book title using isbn code.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            isbncode(str): isbn code of book.

        Returns:
            res(list|None): returns list if query does not fails else None.
        """
        try:
            q="SELECT Book_Title FROM `book_details` WHERE ISBN_code ='"+str(isbncode)+"';"
            c.execute(q)
            res=c.fetchall()
            return res
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None

    def insert_in_bookborrower(self,c:'MySQLCursorAbstract',borwid:str,bid:str,libcard_id:str):
        """
        Insert new borrower in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            borwid(str): primary key of new borrower.
            bid(str): foreign key of book.
            libcard_id(str): foreign key of library card.
        
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            val=(borwid,bid,libcard_id)
            query="INSERT INTO `borrower_details`(`borwid`,`bid`,`libcard_id`,`borrowed_date`,`expected_date`) VALUES (%s,%s,%s,CURRENT_DATE(),DATE_ADD(CURRENT_DATE(), INTERVAL 14 DAY))"
            c.execute(query,val)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def updateCopiesInBookDetails(self,c:'MySQLCursorAbstract',bid:str):
        """
        Update no. of copies of book available in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            bid(str): primary key of book.
        
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            query="UPDATE book_details SET no_of_copies_available = no_of_copies_available-1 WHERE bid="+str(bid)+";"
            c.execute(query)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def updatePenaltyInBorrowerDetails(self,c:'MySQLCursorAbstract'):
        """
        Update penalty of borrower in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
        
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            query="UPDATE borrower_details SET borrower_details.penalty = DATEDIFF(CURRENT_DATE(), borrower_details.expected_date) * 3 WHERE CURRENT_DATE() > borrower_details.expected_date AND borrower_details.isreturned = 0;"
            c.execute(query)
            failed = False
            
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
            
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            CustomErrorAndLogWriting().writeFailedOperation(emsg="Failed to update penalty in borrower details")
            failed = True
        return failed

    def showPenaltyBorrowers(self,c:'MySQLCursorAbstract'):
        """
        Returns borrower details who has penalty.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
        
        Returns:
            header(List|None): returns the header or None.
            result(List|None): returns the result or None.
        """
        try:            
            query="SELECT library_card_info.FirstName,library_card_info.LastName,book_details.Book_Title, borrower_details.penalty FROM borrower_details, library_card_info,book_details WHERE CURRENT_DATE()>borrower_details.expected_date AND library_card_info.libcard_id = borrower_details.libcard_id AND book_details.bid = borrower_details.bid AND borrower_details.isreturned=0;"
            c.execute(query)
            header = [i[0] for i in c.description]
            result = c.fetchall()

            return header,result
        
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None,None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None,None

    def getborwid(self,c:'MySQLCursorAbstract',libcard_id:str):
        """
        Return primary key of borrower who has penalty based on library card foreign key.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            libcard_id(str): foreign key of library card.

        Returns:
            res(list|None): returns list if query does not fails else None.
        """
        try:
            q="SELECT borrower_details.borwid FROM `borrower_details` WHERE libcard_id='"+str(libcard_id)+"' AND borrower_details.isreturned = 0;"
            c.execute(q)
            res=c.fetchall()
            return res
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None
        
    def checkPenalty(self,c:'MySQLCursorAbstract',libcardno:str):
        """
        Return borrower details who has penalty.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            libcardno(str): library card no.

        Returns:
            result(list|None): returns list if query does not fails else None.
        """
        try:
            q = """SELECT borrower_details.borwid,CONCAT(library_card_info.firstname, ' ', library_card_info.lastname) AS full_name, library_card_info.library_cardno, book_details.book_title,borrower_details.penalty
                FROM borrower_details
                JOIN library_card_info ON borrower_details.libcard_id = library_card_info.libcard_id
                JOIN book_details ON borrower_details.bid = book_details.bid
                WHERE borrower_details.penalty > 0 AND
                library_card_info.library_cardno = '"""+str(libcardno)+"';"
            c.execute(q)
            result = c.fetchall()
            return result
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
            
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None
        
    def adjustPenaltyInBorrowerDetails(self,c:'MySQLCursorAbstract',borwid:str,penalty:str,new_penalty):
        """
        Update penalty of borrower in db if penalty is paid.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            borwid(str): primary key of borrower who has penalty.
            penalty(str): old penalty.
            new_penalty(str): new penalty.
        
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            query="UPDATE borrower_details SET borrower_details.penalty = "+str(new_penalty)+" WHERE borrower_details.borwid="+str(borwid)+" AND borrower_details.penalty="+str(penalty)+";"
            c.execute(query)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed=True
        return failed

    def updateReturnedBookInBookBorrower(self,c:'MySQLCursorAbstract',borwid:str,bid:str):
        """
        Update borrower details in db when book is returned.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            borwid(str): primary key of borrower who has penalty.
            bid(str): foreign key of book.
            
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            query="UPDATE borrower_details SET borrower_details.isreturned = 1,borrower_details.returned_date=CURRENT_DATE() WHERE borrower_details.borwid="+str(borwid)+" AND borrower_details.bid="+str(bid)+";"
            c.execute(query)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed=True
        return failed

    def updateReturnedCopiesInBookDetails(self,c:'MySQLCursorAbstract',bid:str):
        """
        Update book details in db when book is returned.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            bid(str): primary key of book.
            
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            query="UPDATE book_details SET book_details.no_of_copies_available = book_details.no_of_copies_available+1 WHERE book_details.bid="+str(bid)+";"
            c.execute(query)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def showAllRegisteredUsers(self,c:'MySQLCursorAbstract'):
        """
        Returns information of management people.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
        
        Returns:
            header(List|None): returns the header or None.
            result(List|None): returns the result or None.
        """
        try:
            query="select Ano,firstname,lastname,userid,role from passwordsinfo "
            c.execute(query)
            header = [i[0] for i in c.description]
            result = c.fetchall()

            return header,result
        
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None,None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None,None

    def deleteUsersFromPasswordinfo(self,c:'MySQLCursorAbstract',uid:str):
        """
        Delete management user from db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            uid(str): primary key of user
        
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            failed = None
            query="DELETE FROM passwordsinfo WHERE Ano ="+str(uid)+";"
            c.execute(query)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def updateRoletoAdmin(self,c:'MySQLCursorAbstract',uid:str):
        """
        Update management user role in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            uid(str): primary key of user.
            
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            failed = None
            query="UPDATE passwordsinfo SET role = 1 WHERE Ano="+str(uid)+";"
            c.execute(query)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def updateRoletolibrarian(self,c:'MySQLCursorAbstract',uid:str):
        """
        Update user role to default in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            uid(str): primary key of user.
            
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            failed = None
            query="UPDATE passwordsinfo SET role = 2 WHERE Ano="+str(uid)+";"
            c.execute(query)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def searchBooks(self,c:'MySQLCursorAbstract',s:str):
        """
        Returns book details based on search constraint for book management.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            s(str): search term.
        
        Returns:
            header(List|None): returns the header or None.
            result(List|None): returns the result or None.
        """
        try:
            query="SELECT bid, book_details.aid, isbn_code, book_title, no_of_copies,author_name FROM book_details,author_details WHERE book_details.aid = author_details.aid AND (book_details.book_title LIKE '%"+s+"%' OR book_details.isbn_code LIKE '%"+s+"%' OR author_details.author_name LIKE '%"+s+"%');"
            c.execute(query)
            header = [i[0] for i in c.description]
            result = c.fetchall()
            return header,result
        
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None,None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None,None

    def updateISBN(self,c:'MySQLCursorAbstract',id:str,isbn:str):
        """
        Update book isbn code in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            id(str): primary key of book.
            isbn(str): isbn code of book.
            
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            failed = None
            query="UPDATE book_details SET isbn_code = '"+str(isbn)+"' WHERE bid="+str(id)+";"
            c.execute(query)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def updateBookTitle(self,c:'MySQLCursorAbstract',id:str,title:str):
        """
        Update book title in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            id(str): primary key of book.
            title(str): book title.
            
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            query="UPDATE book_details SET book_title = '"+str(title)+"' WHERE bid="+str(id)+";"
            failed = None
            print(query)
            c.execute(query)
            failed = False
            
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def updateNoOfCopies(self,c:'MySQLCursorAbstract',id:str,copies:str):
        """
        Update no. of copies of book in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            id(str): primary key of book.
            copies(str): no. of copies.
            
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            failed = None
            query="UPDATE book_details SET no_of_copies ="+str(copies)+" WHERE bid="+str(id)+";"
            c.execute(query)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def updateAuthorName(self,c:'MySQLCursorAbstract',id:str,name:str):
        """
        Update author name in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            id(str): primary key of author id.
            name(str): name of book.
            
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            failed = None
            query="UPDATE author_details SET author_name = '"+str(name)+"' WHERE aid="+str(id)+";"
            c.execute(query)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            failed = True
            
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            failed = True
        return failed

    def getEmailReceiverData(self,c:'MySQLCursorAbstract'):
        """
        Return borrower details for email content.

        Parameters:
            c(MySQLCursorAbstract): cursor object.

        Returns:
            res(list|None): returns list if query does not fails else None.
        """
        try:
            q="SELECT library_card_info.firstname,library_card_info.lastname,library_card_info.userid, borrower_details.borrowed_date, borrower_details.penalty FROM borrower_details, library_card_info WHERE CURRENT_DATE>expected_date AND CURRENT_DATE>Email_sent_on AND isreturned = 0 AND (borrower_details.libcard_id = library_card_info.libcard_id);"
            c.execute(q)
            res=c.fetchall()
            return res
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=str(e)+traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None

    def getReceiverBookTitles(self,c:'MySQLCursorAbstract',reciever:str):
        """
        Return Book titles.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            reciever(str): userid of borrower.

        Returns:
            res(list|None): result if exist else None.
        """
        try:
            q="SELECT book_details.book_title FROM borrower_details, book_details, library_card_info WHERE library_card_info.userid='"+str(reciever)+"' AND isreturned = 0 AND (borrower_details.bid = book_details.bid) AND (borrower_details.libcard_id = library_card_info.libcard_id);"
            c.execute(q)
            res=c.fetchall()
            return res
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=traceback.format_exc())
            return None
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None

    def isEmailNotSent(self,c:'MySQLCursorAbstract',userid):
        """
        Insert new location in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            userid(str): userid of library card holder.
            
        Returns:
            bool|None: True if email is not sent on present else false. None if query fails.
        """
        try:
            q="SELECT borwid FROM borrower_details, library_card_info WHERE library_card_info.userid = '"+str(userid)+"' AND borrower_details.Email_sent_on<CURRENT_DATE AND borrower_details.isreturned=0;"
            c.execute(q)
            res=c.fetchall()
            if res:
                return True
            else:
                return False
            
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=traceback.format_exc())
            return None    
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(emsg=e.msg+traceback.format_exc())
            return None

    def updateLastEmailSentDate(self,c:'MySQLCursorAbstract',userid:str):
        """
        Update last email sent on date in db.

        Parameters:
            c(MySQLCursorAbstract): cursor object.
            userid(str): userid of library card holder.
            
        Returns:
            failed(bool): True if query fails else False.
        """
        try:
            failed = None
            query="UPDATE borrower_details INNER JOIN library_card_info ON borrower_details.libcard_id = library_card_info.libcard_id SET Email_sent_on = CURRENT_DATE() WHERE CURRENT_DATE() > expected_date AND CURRENT_DATE() > Email_sent_on AND isreturned = 0 AND library_card_info.userid ='"+str(userid)+"';"
            c.execute(query)
            failed = False
        except AttributeError as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            failed = True
                
        except mysql.connector.Error as e:
            CustomErrorAndLogWriting().writeSingleErrorInLog(traceback.format_exc())
            failed = True
        return failed
    

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QWidget
    app = QApplication(sys.argv)
    window = QWidget()
    window.show()
    Mydb = Dbconnection()
    c,db = Mydb.makeConnection()
    sys.exit(app.exec())
    