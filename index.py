#coding:utf-8
from PyQt5.QtWidgets import *
import sys
from PyQt5.QtGui  import *
from PyQt5.QtCore import * 
from PyQt5.QtWidgets import * 
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog 
import qtawesome as qta
import json
from db import DataBase
import processData 
import time
from collections import defaultdict
from decimal import Decimal
import os
import images
from multiprocessing import Pool
#仅仅windows支持
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('myappid')
####

class loadQSS:
	@staticmethod
	def getStyleSheet(file):
		with open(file,'r') as f:
			return f.read()

class studentScoreManage(QMainWindow):
	def __init__(self):
		splash = QSplashScreen(QPixmap(":./images/start1.png"))
		splash.showMessage("加载中... ", Qt.AlignHCenter | Qt.AlignBottom, Qt.black)
		splash.show()  
		super().__init__()
		self.initDataBase()
		self.initWindow()
		self.installEventFilter(self)
		self.show()
		splash.finish(self)

	def initDataBase(self):
		"""
		初始化数据库
		"""
		self.database = DataBase()

	def setCourseName(self, parent, courseNameCombox):
		courseName_items = self.combox_content[str(parent.currentIndex())]
		courseNameCombox.clear()
		courseNameCombox.addItems(courseName_items)

	def setScoreCombox(self,courseCombox, courseNameCombox, scoreCombox):
		scoreCombox.clear()
		if courseCombox.currentIndex()==1 and courseNameCombox.currentIndex()==1:
			scoreCombox.addItems(['章节测验（1）','章节测验（2）', '期末考试'])
		else:
			scoreCombox.addItems(['期中考试','期末考试'])


	def div_6(self, value):
		return Decimal(str(value))/Decimal('6')
	def div_3(self, value):
		return Decimal(str(value))/Decimal('3')
	def div_2(self, value):
		return Decimal(str(value))/Decimal('2')
	def div_4(self, value):
		return Decimal(str(value))/Decimal('4')
	def div_3_4(self, value):
		return Decimal(str(value))*Decimal('0.75')

	def show_total_normal_score(self,**args):
		sClass = str(self.courseCombox.currentIndex()) + str(self.courseNameCombox.currentIndex())
		all_normal_exam = []
		all_normal_exam.append(sClass+'0')
		if sClass == '11':
			all_normal_exam.append(sClass+'1')
			weights = [self.div_6, self.div_3 , self.div_2]
		else:
			weights = [self.div_4, self.div_3_4]

		headers = ['学号','姓名','平时成绩','平时成绩(加权)']
		for c in all_normal_exam:
			headers.append(self.decode[c])
			headers.append(self.decode[c]+"(加权)")
		all_student = self.database.student_table.find(sClass = sClass)
		student_id = {}
		datas = []

		for student in all_student:
			data = [student[1],student[2]]
			student_id[student[1]] = student[0]
			# 平时成绩
			normal_score_record = self.database.escore_table.find(studentid = student[0], examtype = sClass)[0]
			normal_score = normal_score_record[-2]
			# 平时总成绩
			total = Decimal('0') if normal_score == '' else weights[0](normal_score)			
			data.append(normal_score) # 添加平时成绩
			data.append(str(total)) # 添加平时成绩（加权）

			# 平时考试成绩
			for i,e in enumerate(all_normal_exam):
				score = self.database.escore_table.find(studentid = student[0],examtype = e)
				if score!=[]:
					data.append(score[0][-1]) # 考试成绩
					score_weight = weights[i+1](score[0][-1])# 考试成绩加权
					data.append(str(score_weight)) 
					total = total+ score_weight
				else:
					data.append('')
					data.append('0')
			data.append(int(total+Decimal('0.5')))
			datas.append(data)

		if 'sort_col' not in args.keys():
			args['sort_col'] = 0
		if 'reverse' not in args.keys():
			args['reverse'] = False

		if args['sort_col'] == 0:
			datas = sorted(datas,key = lambda record:int(record[args['sort_col']]),reverse= args['reverse'])
		elif args['sort_col']==1:
			datas = sorted(datas,key = lambda record:record[args['sort_col']],reverse= args['reverse'])
		else:
			datas = sorted(datas,key = lambda record:(float(record[args['sort_col']]) if record[args['sort_col']]!='' else 0.0),reverse= args['reverse'])

		headers.append('最终平时成绩')
		self.TABLE_CONTENT = 2
		self.display_table(headers, datas, student_id)


	def clearStudentScore(self):
		select = self.showSelectBox(QMessageBox.Information,'清空','将清空所有学生及其考试成绩，继续？','确定','取消')
		if select == QMessageBox.No:
			return
		widget = QDialog(self)
		widget.setWindowTitle('清空详情')
		progressbar = QProgressBar()
		progressbar.setValue(0)
		hlayout = QHBoxLayout()
		hlayout.addWidget(QLabel("<font color='white'>进度：</font>"))
		hlayout.addWidget(progressbar)
		widget.setLayout(hlayout)
		widget.setMinimumHeight(115)
		widget.setMinimumWidth(335)
		widget.show()


		sClass= str(self.courseCombox.currentIndex()) + str(self.courseNameCombox.currentIndex())
		examtype = sClass + str(self.scoreCombox.currentIndex())		

		all_normal_exam = [sClass] # 平时成绩
		all_normal_exam.append(sClass+'0') # 第一阶段考试成绩
		all_normal_exam.append(sClass+'1') # 高等代数第二阶段考试成绩 或者其他科目的期末考试成绩
		if sClass == '11':
			all_normal_exam.append(sClass+'2')

		students = self.database.student_table.find(sClass = sClass)
		size = len(students)
		if size == 0:
			progressbar.setValue(100)
		for i, student in enumerate(students):
			for exam in all_normal_exam:
				self.database.escore_table.delete(studentid = student[0], examtype = exam)
			res = self.database.student_table.delete(id = student[0])
			progressbar.setValue((i+1)/size*100)
			QApplication.processEvents()
		widget.close()
		if examtype == '112' or (examtype[-1]=='1' and sClass!='11'):
			stype = '012'
		else:
			stype = '01'
		headers,s_datas, student_id = self.get_single_score(examtype = examtype,sClass = sClass,header_decode = stype)
		self.show_single_score(headers,s_datas,student_id)
		self.showMessageBox(QMessageBox.Information, '清空','成功')

	def showScoreTable(self):
		sClass= str(self.courseCombox.currentIndex()) + str(self.courseNameCombox.currentIndex())
		examtype = sClass + str(self.scoreCombox.currentIndex())
		if examtype == '112' or (examtype[-1]=='1' and sClass!='11'):
			stype = '012'
		else:
			stype = '01'
		headers,s_datas, student_id = self.get_single_score(examtype = examtype,sClass = sClass,header_decode = stype)
		self.show_single_score(headers,s_datas,student_id)

	def initCombox(self):
		self.courseCombox = QComboBox()
		self.courseNameCombox = QComboBox()
		self.scoreCombox = QComboBox()
		self.courseCombox.setObjectName('courseCombox')
		self.courseNameCombox.setObjectName('courseNameCombox')
		self.scoreCombox.setObjectName('scoreCombox')

		# 设置居中
		lineEdit = QLineEdit()
		lineEdit.setAlignment(Qt.AlignCenter)
		lineEdit.setReadOnly(True)
		lineEdit.setFocusPolicy(Qt.NoFocus)
		self.courseCombox.setLineEdit(lineEdit)


		lineEdit1 = QLineEdit()
		lineEdit1.setAlignment(Qt.AlignCenter)
		lineEdit1.setReadOnly(True)
		self.courseNameCombox.setLineEdit(lineEdit1)

		lineEdit2 = QLineEdit()
		lineEdit2.setAlignment(Qt.AlignCenter)
		lineEdit2.setReadOnly(True)
		self.scoreCombox.setLineEdit(lineEdit2)		

		self.courseCombox.setItemDelegate(QStyledItemDelegate())
		self.courseNameCombox.setItemDelegate(QStyledItemDelegate())
		self.scoreCombox.setItemDelegate(QStyledItemDelegate())

		self.courseCombox.currentIndexChanged.connect(lambda :self.setCourseName(self.courseCombox, self.courseNameCombox))
		self.courseNameCombox.currentIndexChanged.connect(lambda:self.setScoreCombox(self.courseCombox,self.courseNameCombox,self.scoreCombox))
		self.scoreCombox.activated.connect(self.showScoreTable)
		self.scoreCombox.currentIndexChanged.connect(self.showScoreTable)
		self.courseCombox.addItems(self.combox_content['course'])

		self.show_total_button = QPushButton('总成绩')
		self.show_total_normal_button = QPushButton('总平时成绩')
		self.load_button = QPushButton("导入成绩")
		self.load_student_button = QPushButton("导入学生")
		self.clear_button = QPushButton('清空')
		self.clear_button.setToolTip("清空学生和学生成绩")
		self.save_button = QPushButton('保存修改')

		self.show_total_button.setObjectName('btn1')
		self.show_total_normal_button.setObjectName('btn2')
		self.load_button.setObjectName('btn3')
		self.load_student_button.setObjectName('btn4')
		self.clear_button.setObjectName('btn5')

		self.show_total_button.clicked.connect(self.show_total_score)
		self.show_total_normal_button.clicked.connect(lambda:self.show_total_normal_score())
		self.load_student_button.clicked.connect(self.loadStudentData)
		self.clear_button.clicked.connect(self.clearStudentScore)
		self.load_button.clicked.connect(self.loadData)
		self.save_button.clicked.connect(self.modifyScore)

		course = QLabel('课程：')
		courseName = QLabel("课程名称：")
		score = QLabel('考试：')
		font = QFont('宋体',13, QFont.Bold)
		course.setFont(font)
		courseName.setFont(font)
		score.setFont(font)

		hlayout = QHBoxLayout()
		hlayout.addWidget(course)
		hlayout.addWidget(self.courseCombox)
		hlayout.addSpacing(0.2)		
		hlayout.addWidget(courseName)
		hlayout.addWidget(self.courseNameCombox)
		hlayout.addSpacing(0.2)
		hlayout.addWidget(score)
		hlayout.addWidget(self.scoreCombox)
		hlayout.addStretch(0.5)
		

		hlayout1 = QHBoxLayout()
		hlayout1.addWidget(self.show_total_button)
		hlayout1.addWidget(self.show_total_normal_button)
		#hlayout1.addWidget(self.load_button)
		#hlayout1.addWidget(self.load_student_button)
		hlayout1.addWidget(self.save_button)
		hlayout1.addWidget(self.clear_button)
		#hlayout1.addStretch(1)

		hlayout.addLayout(hlayout1)
		vlayout = QVBoxLayout()
		#vlayout.addLayout(hlayout1)
		vlayout.addLayout(hlayout)

		self.chooseWidget.setLayout(vlayout)
		self.chooseWidget.setMinimumHeight(80)
		vlayout = QVBoxLayout()
		vlayout.addWidget(self.chooseWidget)
		vlayout.addWidget(self.Table)
		vlayout.setSpacing(0)
		vlayout.setContentsMargins(100,-100,100,0)
		self.centerwidget.setLayout(vlayout)

		

	def initWindow(self):
		"""
		初始化窗口
		"""
		self.resize(1620,650)
		self.setWindowIcon(QIcon(':./images/icon.ico'))
		self.setWindowTitle('成绩管理')

		self.chooseWidget = QWidget()
		self.chooseWidget.setObjectName('widget1')
		#self.chooseWidget.setStyleSheet('background:#F0F0F0;')
		self.Table = QTableWidget()    # 成绩表
		self.centerwidget = QFrame()

		self.setCentralWidget(self.centerwidget) # 先添加到QMainWindow, 再初始化，不然h_splitter会覆盖掉搜索界面
		self.initSetting()
		self.initScoreTable()
		self.initCombox()
		self.initMenu()
		self.initSearchWindow()

		self.setStyleSheet(loadQSS.getStyleSheet('./qss/style.qss'))


	def initSetting(self):
		with open('./setting.json','r') as f:
			content = f.read()
		self.setting = json.loads(content)#设置
		with open('./decode.json','r') as f:
			content = f.read()
		self.decode = json.loads(content)
		with open('./getArray.json','r') as f:
			content = f.read()
		self.combox_content = json.loads(content)

	def initMenu(self):
		"""
		初始化主窗口菜单
		"""
		self.load_menu = self.menuBar().addMenu('导入')  #
		self.help_menu = self.menuBar().addMenu('帮助')  #

		self.load_toolbar = self.addToolBar('导入') # 工具栏
		self.dump_toolbar = self.addToolBar('导出')
		self.func_toolbar = self.addToolBar('Edit')


		self.status_bar = self.statusBar() # 状态显示
		self.status_bar.setStyleSheet('color:white;')
		#self.status_bar.showMessage("hello word")
		self.load_action = QAction('导入成绩', self)				# 动作
		self.dump_action = QAction('导出表格', self)				#
		self.save_action = QAction('保存修改', self)				#
		self.load_studentData_action = QAction('导入学生',self)
		self.find_action = QAction('查找',self)
		self.about_action = QAction('关于{}'.format(self.windowTitle()))
		self.checkTotalScore_action = QAction('总成绩',self)
		self.dumptotal_action = QAction('导出总成绩',self)

		self.find_action.setShortcut('Ctrl+F') 				# 设置快捷键

		self.load_studentData_action.setIcon(QIcon(r':./images/s.ico'))  # 设置图标
		self.load_action.setIcon(QIcon(r':./images/loadScore2.ico'))
		self.dump_action.setIcon(QIcon(r':./images/dump.ico'))
		self.find_action.setIcon(QIcon(r':./images/search96px.ico'))
		self.checkTotalScore_action.setIcon(QIcon(r':./images/totalScore.ico'))
		self.dumptotal_action.setIcon(QIcon(r':./images/dumpTotal.ico'))

		self.load_action.triggered.connect(lambda:self.loadData())		# 动作事件响应
		self.dump_action.triggered.connect(self.dumpData)		#

		self.load_studentData_action.triggered.connect(self.loadStudentData)
		self.find_action.triggered.connect(self.showSearch)
		self.about_action.triggered.connect(self.showSoftwareMessage)
		self.checkTotalScore_action.triggered.connect(self.show_total_score)
		self.dumptotal_action.triggered.connect(self.dumpFinalScore)

																	
		self.load_toolbar.addAction(self.load_studentData_action)	# 将动作添加到工具栏
		self.load_toolbar.addAction(self.load_action)

	
		self.dump_toolbar.addAction(self.dump_action)
		self.dump_toolbar.addAction(self.dumptotal_action)

		self.func_toolbar.addAction(self.find_action)
		self.func_toolbar.addAction(self.checkTotalScore_action)
							
		# 将动作添加到菜单栏
		self.load_menu.addAction(self.load_studentData_action)
		self.load_menu.addAction(self.load_action)

		self.help_menu.addAction(self.about_action)

	def showSoftwareMessage(self):
		widget = QDialog()
		widget.setWindowTitle('关于')
		w = QWidget()
		w.resize(200,2000)
		scroll_area = QScrollArea()
		scroll_area.setWidget(w)
		vlayout = QVBoxLayout()
		vlayout.addWidget(scroll_area)
		widget.setLayout(vlayout)
		widget.exec_()

	def getStudentData(self, **args): #班级确定 学号唯一
		all_students = self.database.student_table.find(sClass = args['sClass'])
		student_id = {}
		datas = []
		headers = ['学号','姓名']
		for student in all_students:
			studentid = student[0]
			number = student[1]
			name = student[2]
			datas.append((number, name))
			student_id[number] = studentid

		if 'sort_col' not in args.keys():
			args['sort_col'] = 0
		if 'reverse' not in args.keys():
			args['reverse'] = False
		if args['sort_col'] == 0:
			datas = sorted(datas,key = lambda record:int(record[args['sort_col']]),reverse= args['reverse'])
		elif args['sort_col']==1:
			datas = sorted(datas,key = lambda record:record[args['sort_col']],reverse= args['reverse'])
		
		return headers, datas, student_id

	def get_single_score(self, **args):#获取表数据
		headers = ['学号','姓名']
		decode = {
			'0':'客观题',
			'1':'主观题',
			'2':'附加题',
			'4':'平时成绩'
		}
		for h in args['header_decode']:
			headers.append(decode[h])

		students = self.database.student_table.find(sClass = args['sClass'])
		datas = []
		student_id = {}
		for student in students:
			id_ = student[0]
			number = student[1]
			name = student[2]
			student_id[number] = id_
			score = self.database.escore_table.find(studentid = id_, examtype = args['examtype'])
			res = [number,name]
			if score!=[] and score[0][-2]!="":  #成绩记录存在
				score_data = json.loads(score[0][-2]) #获取成绩
				for h in args['header_decode']:
					if score_data[h]:
						res.append(score_data[h])
					else:
						res.append('')
				res.append(score[0][-1]) #计算得到的总成绩
			else: #成绩记录不存在
				res.extend(['' for h in args['header_decode']])
				res.append('')
			datas.append(res)

		if 'sort_col' not in args.keys():
			args['sort_col'] = 0
		if 'reverse' not in args.keys():
			args['reverse'] = False

		if args['sort_col'] == 0:
			datas = sorted(datas,key = lambda record:int(record[args['sort_col']]),reverse= args['reverse'])
		elif args['sort_col']==1:
			datas = sorted(datas,key = lambda record:record[args['sort_col']],reverse= args['reverse'])
		else:
			datas = sorted(datas,key = lambda record:(float(record[args['sort_col']]) if record[args['sort_col']]!='' else 0.0),reverse= args['reverse'])
		return headers,datas, student_id


	def loadStudentData(self):

		self.status_bar.showMessage('导入学生')
		widget = QDialog(self)
		widget.setWindowTitle('导入学生')

		self.lS_courseCombox = QComboBox()
		self.lS_courseNameCombox = QComboBox()
		self.lS_scoreCombox = QComboBox()

		self.lS_courseCombox.setItemDelegate(QStyledItemDelegate())
		self.lS_courseNameCombox.setItemDelegate(QStyledItemDelegate())
		self.lS_scoreCombox.setItemDelegate(QStyledItemDelegate())

		self.lS_courseCombox.addItem(self.courseCombox.currentText())
		self.lS_courseNameCombox.addItem(self.courseNameCombox.currentText())
		# self.lS_courseCombox.currentIndexChanged.connect(lambda:self.setCourseName(self.lS_courseCombox,self.lS_courseNameCombox))
		# self.lS_courseCombox.addItems(self.combox_content['course'])

		filepathlabel = QLabel("<font color='white'>文件路径：</font>")
		filepathbutton = QPushButton('点击选择文件')

		self.loadS_filepath = QLineEdit()
		self.loadS_filepath.setMinimumHeight(25)
		filepathbutton.clicked.connect(lambda:self.selectFile(widget,self.loadS_filepath))
		
		load = QPushButton('导入')
		load.clicked.connect(lambda:self.loadStudent(widget))

		self.stunumber_spinbox = QSpinBox()
		self.stuname_spinbox = QSpinBox()
		self.stunumber_spinbox.setRange(1,100)
		self.stuname_spinbox.setRange(1,100)
		self.stunumber_spinbox.setValue(1)
		self.stuname_spinbox.setValue(2)


		#布局
		hlayout1 = QHBoxLayout()
		hlayout1.addWidget(QLabel("<font color='white'>课程：</font>"))
		hlayout1.addWidget(self.lS_courseCombox)

		hlayout2 = QHBoxLayout()
		hlayout2.addWidget(QLabel("<font color='white'>课程名称：</font>"))
		hlayout2.addWidget(self.lS_courseNameCombox)

		hlayout3 = QHBoxLayout()
		hlayout3.addWidget(filepathlabel)
		hlayout3.addWidget(self.loadS_filepath)
		hlayout3.addWidget(filepathbutton)

		hlayout4 = QHBoxLayout()
		hlayout4.addWidget(QLabel("<font color='white'>学号：</font>"))
		hlayout4.addWidget(self.stunumber_spinbox)

		hlayout5 = QHBoxLayout()
		hlayout5.addWidget(QLabel("<font color='white'>姓名：</font>"))
		hlayout5.addWidget(self.stuname_spinbox)

		vlayout = QVBoxLayout()
		vlayout.addLayout(hlayout1)
		vlayout.addLayout(hlayout2)
		vlayout.addLayout(hlayout3)
		vlayout.addWidget(QLabel("<font color='white'>学生信息所在的列数：</font>"))
		vlayout.addLayout(hlayout4)
		vlayout.addLayout(hlayout5)

		self.ls_progressbar = QProgressBar()
		self.ls_progressbar.setValue(0)

		hlayout6 = QHBoxLayout()
		hlayout6.addWidget(QLabel("<font color='white'>进度：</font>"))
		hlayout6.addWidget(self.ls_progressbar)
		
		vlayout.addLayout(hlayout6)
		vlayout.addWidget(load)

		widget.setLayout(vlayout)
		#界面初始化完成后，再添加课程下拉框的内容
		widget.exec_()
		self.status_bar.showMessage('')

	def loadStudent(self, parent): #导入学生表，如果学生已经存在了，还要导入会造成数据重复，还没写这个逻辑
		filepath = self.loadS_filepath.text().strip()
		sClass = str(self.courseCombox.currentIndex()) + str(self.courseNameCombox.currentIndex())
		if filepath == '':
			self.showMessageBox(QMessageBox.Warning,'导入失败','请选择文件')
			return
		elif not os.path.isfile(filepath):
			self.showMessageBox(QMessageBox.Warning,'导入失败','文件不存在')
			return

		try:
			students = processData.loadStudent(filepath,self.stunumber_spinbox.value(),self.stuname_spinbox.value())
		except:
			self.showMessageBox(QMessageBox.Warning,'导入失败','请检查文件类型是否正确')
			return
		
		size = len(students)
		for i,student in enumerate(students):
			# 该学生记录如果不存在则记录到数据库
			if self.database.student_table.find(number = student[0],sClass = sClass) == []:
				self.database.student_table.insert(student[0], student[1], sClass)
				studentid = self.database.student_table.find(number = student[0],sClass = sClass)[0][0]
				self.createScoreRecord(sClass, studentid)
				print('insert')
			else:
				print('exist')
			self.ls_progressbar.setValue((i+1)/size*100)
			QApplication.processEvents()

		#创建考试成绩记录
		headers, datas, student_id = self.getStudentData(sClass = sClass)

		self.showStudentTable(headers,datas, student_id)
		QApplication.processEvents()
		parent.close()
		self.showMessageBox(QMessageBox.Information,'操作结果','导入成功')

	def selectFile(self,parent, lineEdit):
		dig=QFileDialog(parent)
		if dig.exec_():
			#接受选中文件的路径，默认为列表
			filenames=dig.selectedFiles()
			lineEdit.setText(filenames[0])
			#列表中的第一个元素即是文件路径，以只读的方式打开文件
	def showMessageBox(self, icon, title, content,button_text='确定', button_role = QMessageBox.YesRole):
		content = "<font color='white'>"+content+'</font>'
		box = QMessageBox(icon,title, content,parent = self)
		box.addButton(button_text, button_role)
		box.exec_()	
	def showSelectBox(self,icon,title, content,yes_content, no_content):
		content = "<font color='white'>"+content+'</font>'
		box = QMessageBox(QMessageBox.Question,title,content,parent = self)
		yes= box.addButton(yes_content,QMessageBox.YesRole)
		no = box.addButton(no_content,QMessageBox.NoRole)
		box.exec_()
		if box.clickedButton() == yes:
			return QMessageBox.Yes
		elif box.clickedButton() == no:
			return QMessageBox.No
		else:
			return None

	def deleteScoreRecord(self,sClass, studentid):
		all_exam = [sClass]
		all_exam.append(sClass+'0')
		all_exam.append(sClass+'1')
		if sClass == '11':
			all_exam.append(sClass+'2')
			for exam in all_exam:
				self.database.escore_table.delete(studentid = studentid, examtype = exam)
		else:
			for exam in all_exam:
				self.database.escore_table.delete(studentid = studentid, examtype = exam)

	def createScoreRecord(self,sClass, studentid):
		all_exam = []
		all_exam.append(sClass+'0')
		all_exam.append(sClass+'1')
		if sClass == '11':
			all_exam.append(sClass+'2')
			for exam in all_exam:
				if exam[-1] !='2':
					score = {0:None, 1:None}
				else:
					score = {0:None, 1:None, 2:None}
				self.database.escore_table.insert(studentid, exam, json.dumps(score), 0)
			self.database.escore_table.insert(studentid, sClass,"",0) #平时成绩
		else:
			for exam in all_exam:
				if exam[-1] != '1':
					score = {0:None, 1:None}
				else:
					score = {0:None, 1:None, 2:None}
				self.database.escore_table.insert(studentid, exam, json.dumps(score), 0)
			self.database.escore_table.insert(studentid, sClass,"", 0) #平时成绩

	def modifyScore(self): #修改成绩 可以知道，在changeRow中记录为True的行必定发生了改变
		if self.TABLE_CONTENT == 3:
			self.showMessageBox(QMessageBox.Warning,'更改失败','不允许修改总成绩')
			return
		self.IS_USER_CHANGEITEM = False
		modify = []
		add = []
		del_row = []
		all_row = []
		# 获取修改的行的数据
		for row, record in self.changeRow.items():
			if record: # 行被修改
				all_row.append(row)
				if row>=len(self.TABLE_DATA): # 增加行
					add.append(row)
				else:
					count = 0
					for i in range(len(self.TABLE_HEADERS)-1):
						if self.Table.item(row, i).text() == '':
							count+=1
						else:
							break
					if count == len(self.TABLE_HEADERS)-1:
						del_row.append(row)
					else:
						modify.append(row)
		
		# 检查数据是否正确, 正确数据定义为，学号为整数，名字不为空， 成绩是合法的数字：+-1.0 +-1 ,或者为空
		# 根据self.TABLE_QUESTION_WEIGHT是否为None，可以判断此表是否是用于显示某一次成绩，如果是用于显示总成绩时不允许修改数据的。 
		data_correct = True
		for row in all_row:
			if row in del_row:
				continue
			if not processData.isInteger(self.Table.item(row,0).text().strip()):
				self.Table.item(row,0).setBackground(QBrush(QColor(self.setting['table']['cell_data_error'])))
				data_correct = False
				break
			elif self.Table.item(row,1).text().strip() == '':
				self.Table.item(row,1).setBackground(QBrush(QColor(self.setting['table']['cell_data_error'])))
				data_correct = False
				break
			else:
				for i in range(2, len(self.TABLE_HEADERS)-1):
					if self.Table.item(row,i).text().strip() == '':
						continue
					if not processData.isNum(self.Table.item(row,i).text().strip()):
						self.Table.item(row,i).setBackground(QBrush(QColor(self.setting['table']['cell_data_error'])))
						data_correct = False
						break
				if not data_correct:
					break
			QApplication.processEvents()

		if not data_correct:
			self.IS_USER_CHANGEITEM = True	
			self.showMessageBox(QMessageBox.Warning,'更新失败','请检查数据是否正确')
			return
		elif all_row == []:
			self.IS_USER_CHANGEITEM = True
			self.showMessageBox(QMessageBox.Information,'更新结果','数据没有发生改变')
			return
		else:
			check_number_index = [i for i in range(len(self.TABLE_DATA))]
			check_number_index.extend(add)
			student_numbers = []
			for row in check_number_index:
				number = self.Table.item(row, 0).text().strip()
				if number not in student_numbers:
					student_numbers.append(number)
				else:
					items = self.Table.findItems(number, Qt.MatchExactly)#遍历表查找对应的item
					repeat_rows = list(set([item.row() for item in items]))
					for r in repeat_rows:
						self.Table.item(r,0).setBackground(QBrush(QColor(self.setting['table']['cell_data_repeat'])))
					self.IS_USER_CHANGEITEM = True
					self.showMessageBox(QMessageBox.Warning,'更改失败','学号不能重复')
					return
				QApplication.processEvents()
			# 学号不重复， 数据也是正确的
			sClass = str(self.courseCombox.currentIndex()) + str(self.courseNameCombox.currentIndex())
			examtype = sClass + str(self.scoreCombox.currentIndex())
			all_normal_exam = []
			all_normal_exam.append(sClass+'0')
			if sClass == '11':
				all_normal_exam.append(sClass+'1')
				weights = [self.div_6, self.div_3 , self.div_2]
			else:
				weights = [self.div_4, self.div_3_4]

			
			for row in add:
				if self.TABLE_CONTENT == 2:
					break
				number = self.Table.item(row,0).text().strip()
				name = self.Table.item(row,1).text().strip()

				# 插入学生
				self.database.student_table.insert(number, name, sClass)
				# 获取ID
				studentid = self.database.student_table.find(number = number,sClass = sClass)[0][0]
				# 创建考试
				self.createScoreRecord(sClass, studentid)
				# 获取考试成绩记录
				exam_score = self.database.escore_table.find(examtype = examtype, studentid = studentid)[0]
				score = json.loads(exam_score[-2])
				# 更改成绩
				objective = self.Table.item(row,2).text().strip()
				subjective = self.Table.item(row,3).text().strip()

				total_score = 0
				#修改客观题、主观题成绩
				if objective != '':
					score['0'] = objective
					total_score = Decimal(objective)
				else:
					score['0'] = None
				if subjective != '':
					score['1'] = subjective
					total_score = Decimal(total_score) + Decimal(subjective)
				else:
					score['1'] = None

				# 考虑附加题
				if examtype == '112' or (examtype[-1]=='1' and sClass!='11'):
					addition = self.Table.item(row,4).text().strip()
					if addition != '':
						score['2'] = addition
					else:
						score['2'] = None
				self.database.escore_table.update(id = exam_score[0], score_json = json.dumps(score), total_score = total_score)

				# 修改总平时成绩	
				exam_score = self.database.escore_table.find(examtype = sClass, studentid = studentid)
				normal_score = exam_score[0][-2]

				total_score = Decimal('0')
				if normal_score != '':
					total_score = weights[0](normal_score)
				
				for i in range(len(all_normal_exam)):
					score = self.database.escore_table.find(examtype = all_normal_exam[i],studentid = studentid)[0][-1]
					total_score += weights[i+1](score)
				self.database.escore_table.update(id = exam_score[0][0], total_score = int(total_score+Decimal('0.5')))

				QApplication.processEvents()
				
			for row in del_row:
				if self.TABLE_CONTENT == 2:
					break;
				studentid = self.STUDENT_ID[self.TABLE_DATA[row][0]]
				# 获取考试成绩记录
				exam_score = self.database.escore_table.find(examtype = examtype, studentid = studentid)[0]
				score = json.loads(exam_score[-2])

				total_score = 0
				#修改客观题、主观题成绩
				score['0'] = None
				score['1'] = None
				# 考虑附加题
				if examtype == '112' or (examtype[-1]=='1' and sClass!='11'):
					score['2'] = None
				self.database.escore_table.update(id = exam_score[0], score_json = json.dumps(score), total_score = total_score)
				QApplication.processEvents()

			#修改成绩
			for row in modify:
				number = self.Table.item(row,0).text().strip()
				name = self.Table.item(row,1).text().strip()
				studentid = self.STUDENT_ID[self.TABLE_DATA[row][0]]
				#更新学生信息
				self.database.student_table.update(id = studentid, number = number, name=name)
				if self.TABLE_CONTENT == 1: # 修改普通考试成绩
					# 获取考试成绩记录
					exam_score = self.database.escore_table.find(examtype = examtype, studentid = studentid)[0]
					score = json.loads(exam_score[-2])
					# 更改成绩
					objective = self.Table.item(row,2).text().strip()
					subjective = self.Table.item(row,3).text().strip()

					total_score = 0
					#修改客观题、主观题成绩
					if objective != '':
						score['0'] = objective
						total_score = Decimal(objective)
					else:
						score['0'] = None
					if subjective != '':
						score['1'] = subjective
						total_score = Decimal(total_score) + Decimal(subjective)
					else:
						score['1'] = None

					# 考虑附加题
					if examtype == '112' or (examtype[-1]=='1' and sClass!='11'):
						addition = self.Table.item(row,4).text().strip()
						if addition != '':
							score['2'] = addition
						else:
							score['2'] = None
					
					self.database.escore_table.update(id = exam_score[0], score_json = json.dumps(score), total_score = total_score)

					# 修改总平时成绩	
					exam_score = self.database.escore_table.find(examtype = sClass, studentid = studentid)
					normal_score = exam_score[0][-2]

					total_score = Decimal('0')
					if normal_score != '':
						total_score = weights[0](normal_score)
					
					for i in range(len(all_normal_exam)):
						score = self.database.escore_table.find(examtype = all_normal_exam[i],studentid = studentid)[0][-1]
						total_score += weights[i+1](score)
					self.database.escore_table.update(id = exam_score[0][0], total_score = int(total_score+Decimal('0.5')))
		
				elif self.TABLE_CONTENT == 2: # 修改平时成绩	
					exam_score = self.database.escore_table.find(examtype = sClass, studentid = studentid)
					normal_score = self.Table.item(row,2).text().strip()

					score = self.Table.item(row, len(self.TABLE_HEADERS)-1).text().strip()
					if score == '':
						total_score = 0
					else:
						total_score = float(score)
					self.database.escore_table.update(id = exam_score[0][0],score_json = normal_score, total_score = total_score)
				QApplication.processEvents()

			if self.TABLE_CONTENT == 1:# 此时表格显示的是成绩信息
				if examtype == '112' or (examtype[-1]=='1' and sClass!='11'):
					stype = '012'
				else:
					stype = '01'
				headers,datas,student_id = self.get_single_score(examtype = examtype,sClass = sClass,header_decode = stype, sort_col = self.CURRENTCOL, reverse = self.REVERSE)
				self.show_single_score(headers,datas,student_id)
			elif self.TABLE_CONTENT == 2: # 此时表格显示的是总平时成绩
				self.show_total_normal_score(sort_col = self.CURRENTCOL, reverse = self.REVERSE)
			elif self.TABLE_CONTENT == 3:
				self.show_total_score()

		self.showMessageBox(QMessageBox.Information,'更改结果','更改成功')
		self.IS_USER_CHANGEITEM = True		

	def modifyStudent(self):
		if self.TABLE_CONTENT == 2:
			self.showMessageBox(QMessageBox.Information,'更改失败','不允许修改总成绩')
			return
		modify = []
		add = []
		del_row = []
		all_row = []
		self.IS_USER_CHANGEITEM = False
		for row, isModify in self.changeRow.items():
			if isModify:
				all_row.append(row)
				if row>=len(self.TABLE_DATA):
					add.append(row)
				else:
					if self.Table.item(row,0).text()=='' and self.Table.item(row,1).text()=='':
						del_row.append(row)
					else:
						modify.append(row)
		data_correct = True
		# 检查数据是否符合定义
		for row in all_row:
			if row in del_row:
				continue
			if not processData.isInteger(self.Table.item(row,0).text().strip()):
				self.Table.item(row,0).setBackground(QBrush(QColor(self.setting['table']['cell_data_error'])))
				data_correct = False
				break
			elif self.Table.item(row,1).text().strip() == '':
				self.Table.item(row,1).setBackground(QBrush(QColor(self.setting['table']['cell_data_error'])))
				data_correct = False
				break
		if not data_correct:
			self.IS_USER_CHANGEITEM = True
			self.showMessageBox(QMessageBox.Warning,'更改失败','请检查数据是否正确')
			return
		elif modify == [] and add == [] and del_row == []:
			self.IS_USER_CHANGEITEM = True
			self.showMessageBox(QMessageBox.Information,'更改操作','数据没有发生改变')
			return
		else:
			check_number_index = [i for i in range(len(self.TABLE_DATA))]
			check_number_index.extend(add)
			student_numbers = []
			for row in check_number_index:
				number = self.Table.item(row, 0).text().strip()
				if number not in student_numbers:
					student_numbers.append(number)
				else:
					items = self.Table.findItems(number, Qt.MatchExactly)#遍历表查找对应的item
					repeat_rows = list(set([item.row() for item in items]))
					for r in repeat_rows:
						self.Table.item(r,0).setBackground(QBrush(QColor(self.setting['table']['cell_data_repeat'])))
						self.Table.item(r,1).setBackground(QBrush(QColor(self.setting['table']['cell_data_repeat'])))
					self.IS_USER_CHANGEITEM = True
					self.showMessageBox(QMessageBox.Warning,'更改失败','学号不能重复')
					return
			# 学号不是重复的,数据也是正确的 do something
			for r in add:
				number = self.Table.item(r,0).text().strip()
				name = self.Table.item(r,1).text().strip()
				self.database.student_table.insert(number,name,self.CLASSID, self.COURSEID)
			for r in modify:
				number = self.Table.item(r,0).text().strip()
				name = self.Table.item(r,1).text().strip()
				studentid = self.STUDENT_ID[self.TABLE_DATA[r][0]]
				self.database.student_table.update(id = studentid, number = number, name=name)
			
			all_exam = self.database.exam_table.find(classid = self.CLASSID, courseid = self.COURSEID)
			examids = [exam[0] for exam in all_exam]
			for r in del_row:
				studentid = self.STUDENT_ID[self.TABLE_DATA[r][0]]
				for examid in examids:
					self.database.escore_table.delete(
							examid = examid,
							courseid = self.COURSEID,
							classid = self.CLASSID,
							studentid = studentid
						)
				self.database.student_table.delete(id = studentid)
			headers, datas, studentid = self.getStudentData(classid = self.CLASSID, courseid = self.COURSEID)
			self.showStudentTable(headers, datas, studentid)
			self.IS_USER_CHANGEITEM = True
			self.showMessageBox(QMessageBox.Information,'更改结果','更改成功')

	def modifyTable(self):
		"""
		三种操作 增加、删除、修改
		"""
		if not self.IS_USER_CHANGEITEM:
			return
		self.TABLE_CHANGE = True
		self.IS_USER_CHANGEITEM = False

		#需要考虑 此处会再次引发itemChanged事件, 目前解决方案，使用 IS_USER_CHANGEITEM标记是否是用户改变表格
		row = self.Table.currentRow()     # 获取当前单元格所在的行
		col = self.Table.currentColumn()  # 获取当前单元格所在的列
		currentItem = self.Table.item(row,col) # 获取当前单元格
		
		if currentItem: #单元格对象QTableWidgetItem存在
			currentItem.setBackground(QBrush(QColor(self.setting['table']["cell_data_modify"])))
			valid = False # 修改是否有效标记
			isDel = False # 当此次修改是已存在的数据时，用于判断此次操作是否是删除某一行
			
			if row >= len(self.TABLE_DATA):# 该新增行不为空,新增行 添加、修改 两种操作
				if self.TABLE_CONTENT == 1:
					for i in range(len(self.TABLE_HEADERS)-1):
						if self.Table.item(row, i).text() != '': 
							valid = True
							break
				else:
					for i in range(len(self.TABLE_HEADERS)):
						if self.Table.item(row, i).text() != '': 
							valid = True
							break
			else: # 此次更改的行是已存在的行，对于已经存在的行，则分 修改、删除、覆盖 三种操作
				valid = True
				count = 0
				if self.TABLE_CONTENT == 1:
					for i in range(len(self.TABLE_HEADERS)-1):
						if self.Table.item(row,i).text() == '':
							count+=1
					if count == len(self.TABLE_HEADERS)-1:
						isDel = True
				else:
					for i in range(len(self.TABLE_HEADERS)):
						if self.Table.item(row,i).text() == '':
							count+=1
					if count == len(self.TABLE_HEADERS):
						isDel = True
				
			self.changeRow[row] = valid

			# 该行不记录, 恢复正常颜色提示
			if not valid: 
				for i in range(len(self.TABLE_HEADERS)): 
					self.Table.item(row,i).setText('')
					self.Table.item(row,i).setBackground(QBrush(QColor(self.setting['table']["cell_backgroundcolor"])))
				self.IS_USER_CHANGEITEM = True
				return

			# 该行被记录了
			if isDel: 
				# 如果是删除已存在的行，则将背景提示为删除,
				for i in range(len(self.TABLE_HEADERS)): 
					self.Table.item(row,i).setText('')
					self.Table.item(row,i).setBackground(QBrush(QColor(self.setting['table']['table_delRow'])))
				self.IS_USER_CHANGEITEM = True
				return

			if self.TABLE_CONTENT == 0: #处于修改学生信息状态
				print('modify sutdent message')
				if col == 0:
					if not (processData.isInteger(currentItem.text())):
						currentItem.setBackground(QBrush(QColor(self.setting['table']['cell_data_error'])))
					else:
						currentItem.setBackground(QBrush(QColor(self.setting['table']['cell_data_modify'])))
				else:
					if currentItem.text() == '':
						currentItem.setBackground(QBrush(QColor(self.setting['table']['cell_data_error'])))
					else:
						currentItem.setBackground(QBrush(QColor(self.setting['table']['cell_data_modify'])))

			else:# 处于修改成绩表格状态
				print('modify score')				
				if self.TABLE_CONTENT==1 and col>=2:  # 修改成绩
					total = 0.0
					total_is_valid = False
					for i in range(2,len(self.TABLE_HEADERS)-1): #计算总成绩
						if self.Table.item(row,i).text().strip() == '':
							continue
						elif not processData.isNum(self.Table.item(row,i).text().strip()):# 数据如果不正确,将单元格填充为红色
							self.Table.item(row,i).setBackground(QBrush(QColor(self.setting['table']['cell_data_error'])))
						else:														# 数据正确，计算总成绩
							total_is_valid = True
							total = Decimal(str(total)) + Decimal(str(self.Table.item(row,i).text()))
					self.Table.item(row,len(self.TABLE_HEADERS)-1).setText(str(total) if total_is_valid else '')
				
				elif self.TABLE_CONTENT ==2: # 查看平时总成绩
					sClass = str(self.courseCombox.currentIndex()) + str(self.courseNameCombox.currentIndex())
					all_normal_exam = []
					all_normal_exam.append(sClass+'0')
					if sClass == '11':
						all_normal_exam.append(sClass+'1')
						weights = [self.div_6, self.div_3 , self.div_2]
					else:
						weights = [self.div_4, self.div_3_4]	

					normal_score = self.Table.item(row,2).text().strip()
					
					total_score = Decimal('0')
					if normal_score != '':
						total_score = weights[0](normal_score)
						self.Table.item(row,3).setText(str(total_score))

					for i in range(len(all_normal_exam)):
						total_score += weights[i+1](self.Table.item(row,4+2*i).text())

					self.Table.item(row,len(self.TABLE_HEADERS)-1).setText(str(int(total_score+Decimal('0.5'))))

		self.IS_USER_CHANGEITEM = True

	def clickTableHeader(self): # 目前只是简单实现了排序，假设如下：1 用户选择了课程、班级、考试  2 用户处于非查看总成绩状态
		sClass = str(self.courseCombox.currentIndex())+str(self.courseNameCombox.currentIndex())
		examtype = sClass+ str(self.scoreCombox.currentIndex())
		currentColumn = self.Table.currentColumn()
		if currentColumn != self.CURRENTCOL:
			self.CURRENTCOL = currentColumn
			self.REVERSE = False
		else:
			self.REVERSE = not self.REVERSE
		horizontalHeader = self.Table.horizontalHeader()
		horizontalHeader.setSortIndicator(self.CURRENTCOL,Qt.DescendingOrder if self.REVERSE else Qt.AscendingOrder)
		horizontalHeader.setSortIndicatorShown(True);
		r = self.REVERSE
		if self.TABLE_CONTENT == 0: # 此时表格显示的是学生信息
			headers, datas, student_id = self.getStudentData(sClass=sClass, sort_col = self.CURRENTCOL, reverse = self.REVERSE)
			self.showStudentTable(headers, datas, student_id)
		elif self.TABLE_CONTENT == 1:# 此时表格显示的是成绩信息
			if examtype == '112' or (examtype[-1]=='1' and sClass!='11'):
				stype = '012'
			else:
				stype = '01'
			headers,datas,student_id = self.get_single_score(examtype = examtype,sClass = sClass,header_decode = stype, sort_col = self.CURRENTCOL, reverse = self.REVERSE)
			self.show_single_score(headers,datas,student_id)
		elif self.TABLE_CONTENT == 2: # 此时表格显示的是总平时成绩
			self.show_total_normal_score(sort_col = self.CURRENTCOL, reverse = self.REVERSE)
		elif self.TABLE_CONTENT == 3:
			self.show_total_score()
		self.CURRENTCOL = currentColumn
		self.REVERSE = r

	def initScoreTable(self):

		horizontalHeader = self.Table.horizontalHeader()
		verticalHeader = self.Table.verticalHeader()

		horizontalHeader.setFont(QFont('宋体',11,QFont.Bold))
		horizontalHeader.setMinimumHeight(50)

		horizontalHeader.setSectionResizeMode(QHeaderView.Stretch)
		# horizontalHeader.setStretchLastSection(True)
		horizontalHeader.setDefaultSectionSize(self.setting['table']['cell_width'])
		verticalHeader.setDefaultSectionSize(self.setting['table']['cell_height'])
		# self.Table.setFocusPolicy(Qt.NoFocus)
		self.Table.horizontalHeader().sectionClicked.connect(self.clickTableHeader)
		self.Table.itemChanged.connect(self.modifyTable)   # 处于显示成绩状态

		self.formerRow = None
		verticalHeader.setContextMenuPolicy(Qt.CustomContextMenu)
		verticalHeader.customContextMenuRequested.connect(self.createRightMenu_for_table)

		self.TABLE_HEADERS=[]
		self.TABLE_DATA = []
		self.TABLE_QUESTION_WEIGHT =None
		self.TABLE_CHANGE = False
	
	def createRightMenu_for_table(self):
		menu = QMenu(self.Table)
		del_action = QAction('删除',self.Table)
		del_action.setIcon(QIcon("./images/clear.ico"))
		del_action.triggered.connect(self.deleteRow)

		menu.addAction(del_action)
		menu.exec_(QCursor.pos())
	
	def deleteRow(self):
		if self.TABLE_CONTENT == 2 or self.TABLE_CONTENT == 3:
			return
		sClass= str(self.courseCombox.currentIndex()) + str(self.courseNameCombox.currentIndex())
		examtype = sClass + str(self.scoreCombox.currentIndex())
		currentRow = self.Table.currentRow()
		number = self.Table.item(currentRow,0).text()
		studentid = self.STUDENT_ID[number]
		self.deleteScoreRecord(sClass, studentid)
		self.database.student_table.delete(id = studentid)
		if examtype == '112' or (examtype[-1]=='1' and sClass!='11'):
			stype = '012'
		else:
			stype = '01'
		headers,datas,student_id = self.get_single_score(examtype = examtype,sClass = sClass,header_decode = stype, sort_col = self.CURRENTCOL, reverse = self.REVERSE)
		self.show_single_score(headers,datas,student_id)
		

	def show_single_score(self,headers:'表头数据 list', datas, student_id):#显示成绩表
		self.TABLE_CONTENT = 1
		headers.append('成绩')
		self.display_table(headers, datas, student_id)
		QApplication.processEvents()

	def showStudentTable(self, headers, datas, student_id):
		self.TABLE_CONTENT = 0
		self.display_table(headers, datas, student_id)

	def display_table(self,headers, datas , student_id):
		self.TABLE_CHANGE = False
		self.IS_USER_CHANGEITEM = False  # 标记是否是用户改变表格 
		self.addRow = [["" for j in range(len(headers))] for i in range(self.setting['table']['table_addRow'])] # 用于保存新增行中的数据
		self.changeRow = {i:False for i in range(len(datas)+self.setting['table']['table_addRow'])} 			# 用于记录被修改过的行
		self.record_colChange_inRow = {i:list() for i in range(len(datas))} 									# 用于记录某行被修改的列
		self.STUDENT_ID = student_id                    # 学生ID  
		self.TABLE_HEADERS = headers 					# 表头数据
		self.TABLE_DATA = datas  						# 表格原始数据
		self.TABLE_DATA_COPY = [list(d) for d in datas]	# 用于记录修改的成绩以及和一开始的成绩比较，查看数据是否有变动
		self.CURRENTCOL = 0                				# 记录当前排序的列
		self.REVERSE = False               				# 记录当前顺序
		self.Table.clear()							# 清空表格数据
		self.Table.setColumnCount(len(headers))
		self.Table.setRowCount(len(datas)+self.setting['table']['table_addRow'])
		self.Table.setHorizontalHeaderLabels(headers)

		for i, item in enumerate(datas):
			for j, data in enumerate(item):
				node = QTableWidgetItem(str(data))
				node.setTextAlignment(Qt.AlignCenter)
				self.Table.setItem(i,j,node)
				if (self.TABLE_CONTENT==1 and j==len(headers)-1): #禁止修改总成绩
					node.setFlags(Qt.ItemIsEnabled)
				elif self.TABLE_CONTENT == 2:  # 处于查看总平时成绩状态。
					if j!=2 :
						node.setFlags(Qt.ItemIsEnabled)
				elif self.TABLE_CONTENT == 3:  # 处于查看总成绩状态，不允许修改表格。
					node.setFlags(Qt.ItemIsEnabled)

		for i, item in enumerate(self.addRow):
			for j, data in enumerate(item):
				node = QTableWidgetItem(str(data))
				node.setTextAlignment(Qt.AlignCenter)
				self.Table.setItem(i+len(datas),j,node)
				if (self.TABLE_CONTENT==1 and j==len(headers)-1):
					node.setFlags(Qt.ItemIsEnabled)
				elif self.TABLE_CONTENT in [2,3]:
					node.setFlags(Qt.ItemIsEnabled)
		self.IS_USER_CHANGEITEM = True



	def loadData(self):  #导入学生成绩
		self.status_bar.showMessage('导入成绩')
		widget = QDialog(self)
		widget.setWindowTitle('导入到')

		self.ld_courseCombox = QComboBox()
		self.ld_courseNameCombox = QComboBox()
		self.ld_scoreCombox = QComboBox()

		self.ld_courseCombox.setItemDelegate(QStyledItemDelegate())
		self.ld_courseNameCombox.setItemDelegate(QStyledItemDelegate())
		self.ld_scoreCombox.setItemDelegate(QStyledItemDelegate())

		self.ld_courseCombox.addItem(self.courseCombox.currentText())
		self.ld_courseNameCombox.addItem(self.courseNameCombox.currentText())
		self.ld_scoreCombox.addItem(self.scoreCombox.currentText())

		filepathlabel = QLabel("<font color='white'>文件路径：</font>")
		filepathbutton = QPushButton('点击选择文件')
		self.loadscore_filepath = QLineEdit()
		self.loadscore_filepath.setMinimumHeight(25)
		filepathbutton.clicked.connect(lambda:self.selectFile(widget,self.loadscore_filepath))

		hlayout1 = QHBoxLayout()
		hlayout1.addWidget(QLabel("<font color='white'>课程：</font>"))
		hlayout1.addWidget(self.ld_courseCombox)

		hlayout2 = QHBoxLayout()
		hlayout2.addWidget(QLabel("<font color='white'>课程名称：</font>"))
		hlayout2.addWidget(self.ld_courseNameCombox)
		
		hlayout3 = QHBoxLayout()
		hlayout3.addWidget(QLabel("<font color='white'>考试：</font>"))
		hlayout3.addWidget(self.ld_scoreCombox)


		hlayout4 = QHBoxLayout()
		hlayout4.addWidget(filepathlabel)
		hlayout4.addWidget(self.loadscore_filepath)
		hlayout4.addWidget(filepathbutton)

		self.stunumber_spinbox = QSpinBox()
		self.stuname_spinbox = QSpinBox()
		self.objective_spinbox = QSpinBox()
		self.stunumber_spinbox.setRange(1,100)
		self.stuname_spinbox.setRange(1,100)
		self.objective_spinbox.setRange(1,100)
		self.stunumber_spinbox.setValue(1)
		self.stuname_spinbox.setValue(2)
		self.objective_spinbox.setValue(3)

		hlayout5 = QHBoxLayout()
		hlayout5.addWidget(QLabel("<font color='white'>学号：</font>"))
		hlayout5.addWidget(self.stunumber_spinbox)

		hlayout6 = QHBoxLayout()
		hlayout6.addWidget(QLabel("<font color='white'>姓名：</font>"))
		hlayout6.addWidget(self.stuname_spinbox)

		hlayout7 = QHBoxLayout()
		hlayout7.addWidget(QLabel("<font color='white'>客观题：</font>"))
		hlayout7.addWidget(self.objective_spinbox)

		vlayout = QVBoxLayout()
		vlayout.addLayout(hlayout1)
		vlayout.addLayout(hlayout2)
		vlayout.addLayout(hlayout3)
		vlayout.addLayout(hlayout4)
		vlayout.addLayout(hlayout5)
		vlayout.addLayout(hlayout6)
		vlayout.addLayout(hlayout7)

		self.ld_progressbar = QProgressBar()
		self.ld_progressbar.setValue(0)

		hlayout8 = QHBoxLayout()
		hlayout8.addWidget(QLabel("<font color='white'>进度：</font>"))
		hlayout8.addWidget(self.ld_progressbar)
		vlayout.addLayout(hlayout8)

		save_button = QPushButton('导入成绩')
		save_button.clicked.connect(lambda:self.loadScore(widget))
		vlayout.addWidget(save_button)

		widget.setLayout(vlayout)
		widget.exec_()
		self.status_bar.showMessage('')

	def loadScore(self,parent): #导入成绩，接口函数
		sClass = str(self.courseCombox.currentIndex()) + str(self.courseNameCombox.currentIndex())
		examtype = sClass + str(self.scoreCombox.currentIndex())
		# 检查文件路径是否为空，或者文件是否存在
		filepath = self.loadscore_filepath.text()
		if filepath == '':
			self.showMessageBox(QMessageBox.Warning,'导入失败','请选择文件')
			return
		elif not os.path.isfile(filepath):
			self.showMessageBox(QMessageBox.Warning,'导入失败','文件不存在')
			return

		number = self.stunumber_spinbox.value()
		name = self.stuname_spinbox.value()
		objective = self.objective_spinbox.value()
		# 判断是否能正确获取文件数据，文件类型是否正确
		try:
			datas = processData.loadScore(filepath,[number,name,objective])
		except:
			self.showMessageBox(QMessageBox.Information,'导入失败','请检查文件类型是否正确')
			return

		# 数据都没有问题
		all_students = self.database.student_table.find(sClass = sClass)
		d_students = {n[number-1]:n[name-1] for n in datas} #（学号， 姓名）
		s_students = {n[1]:n[2] for n in all_students}

		# 获取到excel表中的学生成绩记录和数据库中的学生成绩记录后检查，两者的学生人数是否一致，不一致的话，不在数据库中的学生需要添加到数据库，已经在数据库中的学生不在成绩表中需要将其成绩设置为0
		# 仅以学号即可区分
		d_sub_s = list(set(d_students.keys()) - set(s_students.keys()))
		s_sub_d = list(set(s_students.keys()) - set(d_students.keys()))
		
		size = len(d_sub_s) + len(datas)
		for i,number in enumerate(d_sub_s): # 数据表减去学生表中剩下的学生即是没有被登记在学生表中的学生，需要添加到学生表中。
			self.database.student_table.insert(number, d_students[number],sClass)
			studentid = self.database.student_table.find(sClass = sClass, number = number)[0][0]
			self.createScoreRecord(sClass, studentid)
			self.ld_progressbar.setValue((i+1)/size*100)			
			QApplication.processEvents()
		# for number in s_sub_d: # 学生表减去成绩表中的学生剩下的即是没有考试成绩记录的学生，需要在末尾添加成绩。

		#更新学生id
		all_students = self.database.student_table.find(sClass = sClass)
		
		student_dict = {}  # 学号对应ID
		for student in all_students:
			student_dict[student[1]] = student[0]
		
		if examtype[-1] == '2' or (examtype[-1]=='1' and sClass !='11'):
			weight = None
		else:
			if sClass == '11':
				if examtype[-1] == '0':
					weight = self.div_3
				else:
					weight = self.div_2
			else:
				weight = self.div_3_4

		# 保存客观题成绩，修改平时总成绩
		count = len(d_sub_s)
		for i, s_score in enumerate(datas):
			exam_score = self.database.escore_table.find(studentid = student_dict[s_score[0]], examtype = examtype)
			score = json.loads(exam_score[0][-2])
			score['0'] = s_score[-1]
			self.database.escore_table.update(exam_score[0][0],score_json = json.dumps(score),total_score = float(s_score[-1]))
			if weight:# 非期末成绩
				normal = self.database.escore_table.find(studentid = student_dict[s_score[0]], examtype = sClass)[0]
				self.database.escore_table.update(id = normal[0], total_score = int(weight(s_score[-1])+Decimal('0.5')))
			self.ld_progressbar.setValue((i+count+1)/size*100)
			QApplication.processEvents()
		
		#显示成绩
		if examtype == '112' or (examtype[-1]=='1' and sClass!='11'):
			stype = '012'
		else:
			stype = '01'	
		headers,s_datas, student_id = self.get_single_score(examtype = examtype,sClass = sClass,header_decode = stype)
		self.show_single_score(headers,s_datas,student_id)
		parent.close()
		self.showMessageBox(QMessageBox.Information,'操作结果','导入成功')

	def dumpFinalScore(self):
		filepath, filetype = QFileDialog.getSaveFileName(self,
			'请选择导出的目录',
			".",
			"""
			Microsoft Excel 文件(*.xlsx);;
			Microsoft Excel 97-2003 文件(*.xls)
			""")
		if filepath=='':
			return

		sClass = str(self.courseCombox.currentIndex())+str(self.courseNameCombox.currentIndex())
		headers, datas ,student_id = self.get_total_score(sClass,isDumpTotal = True)
		success, tip = processData.dumpData(filepath, headers, datas)

		if success:
			self.showMessageBox(QMessageBox.Information,'成功',tip)
		else:
			self.showMessageBox(QMessageBox.Warning,'失败',tip)		

	def dumpData(self):
		filepath, filetype = QFileDialog.getSaveFileName(self,
			'请选择导出的目录',
			".",
			"""
			Microsoft Excel 文件(*.xlsx);;
			Microsoft Excel 97-2003 文件(*.xls)
			""")
		if filepath=='':
			return
		success, tip = processData.dumpData(filepath, self.TABLE_HEADERS, self.TABLE_DATA)

		if success:
			self.showMessageBox(QMessageBox.Information,'成功',tip)
		else:
			self.showMessageBox(QMessageBox.Warning,'失败',tip)

	
	def show_total_score(self):
		sClass = str(self.courseCombox.currentIndex()) + str(self.courseNameCombox.currentIndex())
		headers, datas, studentid = self.get_total_score(
			sClass,
			self.CURRENTCOL,
			self.REVERSE
		)

		self.TABLE_CONTENT = 3
		self.display_table(headers, datas, studentid)
		QApplication.processEvents()
	
	def get_total_score(self, sClass,sort_col= 0, reverse = False, isDumpTotal = False):#查看所有成绩，禁止修改表格，可以修改考试所占比重
		if sClass == '11':
			weights = [0.6, 0.4]
		else:
			weights = [0.4, 0.6]
		if not isDumpTotal:
			headers = ['学号','姓名','总平时成绩','总平时成绩(加权)','期末基本题得分','期末基本题得分(加权)','期末附加题得分','最终总成绩']
		else:
			headers = ['学号','姓名','总平时成绩','期末基本题得分','期末附加题得分','最终总成绩']
		students = self.database.student_table.find(sClass = sClass)
		# 期末考试
		if sClass == '11':
			examtype = sClass+'2'
		else:
			examtype = sClass + '1'
		datas = []
		student_id = {}
		for student in students:
			student_id[student[1]] = student[0]
			data = [student[1],student[2]]
			# 平时成绩
			normal = self.database.escore_table.find(studentid = student[0], examtype = sClass)[0][-1]
			# 期末考试
			score = self.database.escore_table.find(studentid = student[0], examtype = examtype)[0]
			
			data.append(int(normal)) # 总平时成绩
			if not isDumpTotal:
				data.append(Decimal(str(normal))*Decimal(str(weights[0]))) # 总平时成绩（加权）
			data.append(score[-1]) # 期末考试基本题成绩
			if not isDumpTotal:
				data.append(Decimal(str(score[-1]))*Decimal(str(weights[1]))) # 期末考试基本题成绩（加权）

			score_json = json.loads(score[-2]) # 附加题成绩
			if score_json['2'] != None:
				data.append(float(score_json['2']))
			else:
				data.append(0)
			total_score = Decimal(str(normal))*Decimal(str(weights[0])) + Decimal(str(score[-1]))*Decimal(str(weights[1]))
			data.append(str(int(total_score+Decimal('0.5'))))
			datas.append(data)
		
		if sort_col == 0:
			datas = sorted(datas,key = lambda record:int(record[0]), reverse= reverse)
		elif sort_col == 1:
			datas = sorted(datas, key = lambda record:record[1], reverse = reverse)
		else:
			datas = sorted(datas, key = lambda record:float(record[sort_col]) if record[sort_col]!='' else 0.0,reverse = reverse)
		return headers, datas ,student_id

	def searchPre(self):
		if self.showAll == True:
			for row in self.search_rows:
				self.setRowColor(row,self.setting['table']["cell_backgroundcolor"])#恢复表格正常的颜色
			self.showAll = False
		if self.res_is_null:
			self.showMessageBox(QMessageBox.Information,'搜索结果','内容没找到！')
			return
		if self.scrollIndex<=0:
			self.showMessageBox(QMessageBox.Information,'搜索结果','已到达第一个搜索结果')
			return
		else:
			self.setRowColor(self.search_rows[self.scrollIndex],self.setting['table']["cell_backgroundcolor"])#恢复表格正常的颜色
			self.scrollIndex -= 1                                         #获取其行号
			self.setRowColor(self.search_rows[self.scrollIndex],self.setting['table']['search_select_color'])
			self.Table.verticalScrollBar().setSliderPosition(self.search_rows[self.scrollIndex]-2)  #滚轮定位过去
	
	def setRowColor(self, row, backgroundcolor=''):
		temp = self.IS_USER_CHANGEITEM
		self.IS_USER_CHANGEITEM = False
		for i in range(len(self.TABLE_HEADERS)):
			self.Table.item(row,i).setBackground(QBrush(QColor(backgroundcolor)))
		self.IS_USER_CHANGEITEM = temp

	def total_search_Res(self):
		self.showAll = True
		for row in self.search_rows:
			self.setRowColor(row,self.setting['table']['search_select_color'])#恢复表格正常的颜色

	def search(self):
		if self.showAll == True:
			for row in self.search_rows:
				self.setRowColor(row,self.setting['table']["cell_backgroundcolor"])#恢复表格正常的颜色
			self.showAll = False

		if self.search_rows==[]:
			self.showMessageBox(QMessageBox.Information,'搜索结果','内容没找到！')
			return  
		elif self.scrollIndex == len(self.search_rows)-1:
			self.showMessageBox(QMessageBox.Information,'搜索结果','已到达最后一个搜索结果')
			return 

		if self.scrollIndex!= -1:	
			self.setRowColor(self.search_rows[self.scrollIndex],self.setting['table']["cell_backgroundcolor"])#恢复表格正常的颜色
		
		self.scrollIndex+=1
		self.setRowColor(self.search_rows[self.scrollIndex],self.setting['table']['search_select_color'])
		self.Table.verticalScrollBar().setSliderPosition(self.search_rows[self.scrollIndex]-2)  #滚轮定位过去

	def showSearch(self):
		self.searchFrame.setVisible(True)
		self.search_lineEdit.setText('')
		self.search_lineEdit.setFocus(True)

	def hideSearch(self):
		self.searchFrame.setVisible(False)
		for row in self.search_rows:
			self.setRowColor(row,self.setting['table']["cell_backgroundcolor"])#恢复表格正常的颜色

	def findRes(self):
		search_content = self.search_lineEdit.text().strip()
		items = self.Table.findItems(search_content, Qt.MatchExactly)#遍历表查找对应的item
		if self.search_rows!=[]:
			for row in self.search_rows:
				self.setRowColor(row,self.setting['table']["cell_backgroundcolor"])#恢复表格正常的颜色
		self.search_rows = list(set([item.row() for item in items]))
		self.search_rows.sort()

		if self.search_rows!=[]:
			self.res_is_null = False
			self.scrollIndex = -1
			self.showAll = False
		else:
			self.res_is_null = True
			self.showAll = False

	def initSearchWindow(self):
		self.res_is_null = True
		self.scrollIndex = None
		self.showAll = False
		self.search_rows = []
		self.searchFrame = QFrame(self)
		self.searchFrame.setObjectName('search-frame')
		self.searchFrame.resize(self.width(), self.setting['search']["height"])
		self.searchFrame.move(0, self.height()-self.setting['search']["height"])
		#self.searchFrame.setStyleSheet('background:{};border:2px red solid;'.format(self.setting['search']['background-color']))
		
		self.search_lineEdit = QLineEdit(self.searchFrame)
		self.search_lineEdit.setPlaceholderText('请输入搜索内容')
		self.search_lineEdit.setStyleSheet('background:white;border-radius:20px;color:#CE4E40;')
		action = QAction(self)
		action.setIcon(QIcon(':./images/search96px.ico'))
		self.search_lineEdit.addAction(action, QLineEdit.LeadingPosition)
 #        //QLineEdit::LeadingPosition 在左侧TrailingPosition
		self.search_lineEdit.textEdited.connect(self.findRes)
		self.search_lineEdit.returnPressed.connect(self.search)
		self.search_lineEdit.setMinimumHeight(self.setting['search']["height"]-20)
		self.search_lineEdit.setAlignment(Qt.AlignCenter)
		self.search_lineEdit.setFont(QFont('宋体',12))

		
		quit_button = QPushButton("退出")
		quit_button.clicked.connect(self.hideSearch)

		searchbutton = QPushButton('搜索')
		searchbutton.clicked.connect(self.search)

		findPrev = QPushButton('上一个')
		findPrev.clicked.connect(self.searchPre)

		findNext = QPushButton('全部')
		findNext.clicked.connect(self.total_search_Res)

		self.s_hlayout = QHBoxLayout()
		self.s_hlayout.addWidget(self.search_lineEdit)
		self.s_hlayout.addWidget(searchbutton)
		self.s_hlayout.addWidget(findPrev)
		self.s_hlayout.addWidget(findNext)
		self.s_hlayout.addWidget(quit_button)
		self.s_hlayout.setContentsMargins(self.width()*0.3,0,self.width()*0.3,0)
		
		self.searchFrame.setLayout(self.s_hlayout)
		self.searchFrame.show()
		self.searchFrame.setVisible(False)

	def closeEvent(self,event):
		
		if self.TABLE_CHANGE:
			select = self.showSelectBox(
				QMessageBox.Question,
				'关闭',
				'数据改动尚未保存,是否退出？',
				'确定',
				'取消'
				)
			if select == QMessageBox.No:
				event.ignore()
				return
		print('close')
		self.database.closeDB()

	def resizeEvent(self,event):
		self.searchFrame.move(0, self.height()-self.setting["search"]["height"])
		self.searchFrame.resize(self.width(), self.setting['search']["height"])
		
		self.s_hlayout.setContentsMargins(self.width()*0.3,0,self.width()*0.3,0)
	
	def paintEvent(self,event):
		painter = QPainter(self)
		pixmap = QPixmap(":./images/bb3.jpg")
		painter.drawPixmap(self.rect(),pixmap)

	def keyPressEvent(self,event):
		"""
		键盘事件，设置快捷键
		"""
		if QApplication.keyboardModifiers() == Qt.ControlModifier:
			if event.key() == Qt.Key_S:
				if self.TABLE_CONTENT == 0:
					self.modifyStudent()
				elif self.TABLE_CONTENT == 1 or self.TABLE_CONTENT == 2:
					self.modifyScore()
		elif event.key() == Qt.Key_Escape:
			self.hideSearch()


if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = studentScoreManage()
	sys.exit(app.exec())