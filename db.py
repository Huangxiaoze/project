
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtSql import *
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableView
from table import studentTable, escoreTable, objective
import json
import os 
class DataBase(QTableView):
    def __init__(self):
        super(DataBase, self).__init__()
        self.db = None
        self.db_connect()
        #self.mysql_connect()
        self.model = QSqlTableModel()
        self.student_table = studentTable.Student(self.model)
        self.escore_table = escoreTable.EScore(self.model)
        self.objective_table = objective.Objective(self.model)
        self.createTable()

    def mysql_connect(self):
        self.db = QSqlDatabase.addDatabase('QMYSQL')
        self.db.setHostName('localhost')
        self.db.setDatabaseName('studentscore')
        self.db.setUserName('root')
        self.db.setPassword('0128huang')
        if not self.db.open():                           # 3
            QMessageBox.critical(self, 'Database Connection', self.db.lastError().text())
     
        

    def createTable(self):
        self.student_table.createTable()
        self.escore_table.createTable()
        self.objective_table.createTable()


    def db_connect(self):
        self.db = QSqlDatabase.addDatabase('QSQLITE')    # 1
        print(os.path.abspath('.'))
        self.db.setDatabaseName('SZU_DB.db')             # 2
        if not self.db.open():                           # 3
            QMessageBox.critical(self, 'Database Connection', self.db.lastError().text())

    def closeDB(self):
        self.db.close()

    def closeEvent(self, QCloseEvent):
        self.db.close()
 
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    DataBas = DataBase()
    DataBas.show()
    sys.exit(app.exec_())
