import xlrd
import xlwt
import re
def isInteger(word):#判断是否整数，用于判断学号
	word = str(word)
	num_pattern = r'^\d+$' #
	if re.match(num_pattern, word):
		return True
	else:
		return False

def isNum(word):#判断是否是数字
	word = str(word)
	num_pattern = r'^[+-]?\d+(\.\d+)?((e|E)[+-]?\d+)?$' #
	if re.match(num_pattern, word):
		return True
	else:
		return False

def loadStudent(filepath,numbcol, namecol):
	workbook = xlrd.open_workbook(filepath)
	sheets = workbook.sheet_names()
	worksheet = workbook.sheet_by_name(sheets[0])
	data = []
	for x in range(0, worksheet.nrows):
		row = worksheet.row(x)
		number = str(row[numbcol-1].value).replace('.','')
		name = str(row[namecol-1].value)
		if not isInteger(number) or isNum(name) or '课程' in name:
			continue
		data.append((number,name))
	return data

def loadScore(filepath,args:list):
	workbook = xlrd.open_workbook(filepath)
	sheets = workbook.sheet_names()
	worksheet = workbook.sheet_by_name(sheets[0])
	datas = []
	for row in range(0, worksheet.nrows):
		data_detail = worksheet.row(row)
		data = []
		for i,index in enumerate(args):
			value = data_detail[int(index)-1].value
			if i == 0: # 学号
				value = str(value).replace('.','')
				if isInteger(value):
					data.append(str(value))
			elif i==1: # 姓名
				if not isNum(value):
					data.append(str(value))
			else:  # 成绩
				if isNum(value):
					data.append(str(value))
		if len(data) == 3:
			datas.append(tuple(data))
	return datas

def set_style(font_name,height,bold=False):
	style = xlwt.XFStyle() # 初始化样式
	al = xlwt.Alignment()
	al.horz = 0x02
	al.vert = 0x01
	style.alignment = al
	font = xlwt.Font()
	font.name = font_name
	font.bold = bold
	font.color_index = 4
	font.height = height*11
	style.font = font
	return style

def get_wordSize(word): #获取单词大小
	word
	size = 0
	for ch in word:
		if '\u4e00' <= ch <= '\u9fff':
			size+=2
		else:
			size+=1
	return size

def dumpData(filePath, headers, datas, sheet_name="sheet1"):
	# 创建一个workbook 设置编码
	space = 2
	size = [get_wordSize(h)+space for h in headers]
	workbook = xlwt.Workbook(encoding = 'utf-8')
	worksheet = workbook.add_sheet(sheet_name,cell_overwrite_ok = True)

	# 保存表头
	for i,header in enumerate(headers):
		worksheet.write(0,i, header ,set_style('宋体',22,True))
		size[i] = get_wordSize(header)+space*2

	#保存数据
	for i,data in enumerate(datas):
		SUM = []
		for j,cell_data in enumerate(data):
			cell_data = str(cell_data)
			worksheet.write(i+1,j, cell_data, set_style('宋体',18))
			if get_wordSize(cell_data)+space > size[j]:
				size[j] = get_wordSize(cell_data)+space
				
	for i,s in enumerate(size):
		worksheet.col(i).width = 256*size[i]
			

	#保存数据
	try:
		workbook.save(filePath)
		return (True, '文件保存成功')
	except PermissionError as info:
		return (False, '文件已在其它地方打开') 
	except FileNotFoundError as info:
		return (False, '文件不存在')

if __name__ == '__main__':
	filepath = 'C:/Users/Hasee/Desktop/成绩管理资料/《高等数学》第一阶段成绩登记表 .xlsx'
	print(loadScore(filepath, [2,3,4]))