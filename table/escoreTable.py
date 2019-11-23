
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtSql import QSqlDatabase, QSqlQueryModel,QSqlQuery
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableView
 
 
class EScore(QTableView):
    def __init__(self, db):
        super(EScore, self).__init__()
        self.db = db

    def createTable(self):
        model = QSqlQuery()
        model.exec_('PRAGMA foreign_keys = ON;')
        model.exec_(
            """
            create table escore(
                id integer not null primary key,
                studentid int,
                examtype varchar(10),
                score_json text,
                constraint studentid foreign key(studentid) references student(id)
            )

            """
            )

    def find(self,**args):
        condition = []
        for key, value in args.items(): 
            if key == 'score_json' or key == 'examtype':  
                condition.append("{0}='{1}'".format(key,value))
            else:
                condition.append("{0}={1}".format(key, value))


        And = " and ".join(condition)
        model = QSqlQuery()
        model.exec_('PRAGMA foreign_keys = ON;')
        if condition!=[]:
            sql = 'select * from escore where {};'.format(And)
        else:
            sql = 'select * from escore'
        model.exec_(sql)
        res = []
        while model.next():
            #print((model.value(0),model.value(1),model.value(2),model.value(3),model.value(4),model.value(5)))
            res.append((model.value(0),model.value(1),model.value(2),model.value(3)))
        return res

    def update(self,id,**args):
        if args == None:
            return
        model = QSqlQuery()
        model.exec_('PRAGMA foreign_keys = ON;')
        for key, value in args.items():
            if key != 'total_score':
                sql = "update escore set {0}='{1}' where id={2}".format(key,value,id)
            else:
                sql = "update escore set {0}={1} where id={2}".format(key,value,id)
            model.exec_(sql)

    def delete(self,**args): # id or studentid + courseid + examid+ classid
        condition = []
        for key, value in args.items(): 
            if key == 'score_json' or key == 'examtype':  
                condition.append("{0}='{1}'".format(key,value))
            else:
                condition.append("{0}={1}".format(key, value))
                
        And = " and ".join(condition)
        model = QSqlQuery()
        model.exec_('PRAGMA foreign_keys = ON;')
        sql = "delete from escore where {}".format(And)
        res = model.exec_(sql)
        return res

    def insert(self, studentid, examtype,score_json):
        try:
            model = QSqlQuery()
            model.exec_('PRAGMA foreign_keys = ON;')
            sql = """
            insert into escore(studentid, examtype,score_json) 
            values({0},'{1}','{2}')
            """.format(studentid, examtype,score_json)
            res = model.exec_(sql)
        except:
            pass
 
 
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    EScor = EScore()
    EScor.show()
    sys.exit(app.exec_())
