
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtSql import QSqlDatabase, QSqlQueryModel,QSqlQuery
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableView
 
 
class Objective(QTableView):
    def __init__(self,db):
        super(Objective, self).__init__()
        self.db = db

    def createTable(self):
        model = QSqlQuery()
        model.exec_('PRAGMA foreign_keys = ON;')
        if model.exec_(
            """
            create table objective(
                examtype varchar(10) not null primary key,
                hasObjective int
            )
            """
            ):
            self.insertData()


    def find(self,**args):
        condition = []
        for key, value in args.items():  
            if key == 'id': 
                condition.append("{0}={1}".format(key,value))
            else:
                condition.append("{0}='{1}'".format(key,value))
        And = " and ".join(condition)
        model = QSqlQuery()
        model.exec_('PRAGMA foreign_keys = ON;')
        if condition!=[]:
            sql = 'select * from objective where {}'.format(And)
        else:
            sql = 'select * from objective'
        model.exec_(sql)
        res = []
        while model.next():
            res.append((model.value(0),model.value(1)))
        return res

    def update(self,**args):
        if args == None:
            return
        model = QSqlQuery()
        model.exec_('PRAGMA foreign_keys = ON;')
        for key, value in args.items():
            sql = "update objective set {0}='{1}' where examtype='{2}'".format(key,value,args['examtype'])
            model.exec_(sql)

    def insertData(self):
        examtypes = ["000","001","100","101","110","111","112","200","201","210","211","300","301","310","311","320","321"
            ]
        for examtype in examtypes:
            self.insert(examtype, 1)




    def insert(self, examtype, hasObjective):
        try:
            model = QSqlQuery()
            model.exec_('PRAGMA foreign_keys = ON;')
            sql = """
            insert into objective(examtype, hasObjective) 
            values('{0}',{1})
            """.format(examtype, hasObjective)
            model.exec_(sql)
        except:
            pass
            #print(e)
 
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = Student()
    demo.show()
    sys.exit(app.exec_())
