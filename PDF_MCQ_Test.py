from inspect import getfile
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
import fitz, re


# Question number : [{Question : '', Options : '', Answer: '', MarkedResponse : '', TimeTaken : ''}]
necessary_data = {x:{'Question':'', 'Options':[], 'Answer': '', 'MarkedResponse':'', \
                     'TimeTaken':'', 'Comments': '', 'Explanation' : ''} for x in range(1,101)}


class MainScreen(QtWidgets.QDialog):
    def __init__(self):
        super(MainScreen, self).__init__()
        uic.loadUi('QuizMasterFront.ui', self)
        # self.show()

        self.buttonGroup.buttonClicked.connect(self.selectQuizType)
        self.buttonGroup_2.buttonClicked.connect(self.selectSolutionType)

        self.pushButton.clicked.connect(lambda : self.getFile(1))
        self.pushButton_2.clicked.connect(lambda : self.getFile(2))

        self.radioButton.setChecked(True)
        self.radioButton_3.setChecked(True)
        
        # self.continuebutton = self.findChild(
        #     QtWidgets.QPushButton, 'pushButton_4')
        self.pushButton_4.clicked.connect(self.switchToSecondFrame)
        self.pushButton_4.setDisabled(True)

        self.txtbrwsr_newq = ''
        self.txtbrwsr_oldq = ''
    
    def getFile(self, ptr):
        fileformat = 'json' if 'old' in self.buttonGroup.checkedButton().text().lower() else 'pdf'
        fname = QFileDialog.getOpenFileName(self, 'Open file',
                                            '', f"{fileformat.upper()} (*.{fileformat})")
        txtbrwsr = self.textBrowser if ptr == 1 else self.textBrowser_2
        # print(fname, dir(fname), type(fname))
        txtbrwsr.setText(fname[0])

        if 'old' in self.buttonGroup.checkedButton().text().lower():
            self.pushButton_4.setDisabled(False)
        else:
            if 'separate' not in self.buttonGroup_2.checkedButton().text().lower():
                self.pushButton_4.setDisabled(False)
            elif self.textBrowser_2.toPlainText().endswith('pdf') and self.textBrowser.toPlainText().endswith('pdf'):
                self.pushButton_4.setDisabled(False)
            else:
                self.pushButton_4.setDisabled(True)
    
    def selectQuizType(self):
        if 'old' in self.buttonGroup.checkedButton().text().lower() :
            self.txtbrwsr_newq = self.textBrowser.toPlainText()
            self.textBrowser.setText(self.txtbrwsr_oldq)
            self.label.setText('Attempt (JSON)')
            self.radioButton_3.hide()
            self.radioButton_4.hide()
            self.radioButton_5.hide()
            self.radioButton_6.hide()
            self.label_3.hide()
            self.label_4.hide()
            self.spinBox.hide()
            self.doubleSpinBox.hide()
            self.pushButton_2.hide()
            self.textBrowser_2.hide()
            if self.textBrowser.toPlainText().endswith('json'):
                self.pushButton_4.setDisabled(False)
            else:
                self.pushButton_4.setDisabled(True)

        else:
            self.txtbrwsr_oldq = self.textBrowser.toPlainText()
            self.textBrowser.setText(self.txtbrwsr_newq)
            self.label.setText("Q's PDF")
            self.radioButton_3.show()
            self.radioButton_4.show()
            self.radioButton_5.show()
            self.radioButton_6.show()
            self.label_3.show()
            self.label_4.show()
            self.spinBox.show()
            self.doubleSpinBox.show()
            self.pushButton_2.show()
            self.textBrowser_2.show()
            if self.textBrowser_2.toPlainText().endswith('pdf') and self.textBrowser.toPlainText().endswith('pdf'):
                self.pushButton_4.setDisabled(False)
            else:
                self.pushButton_4.setDisabled(True)

    def selectSolutionType(self):
        selected_mode = self.buttonGroup_2.checkedButton().text().lower()
        # separate, end, after, marked
        if 'separate' not in selected_mode:
            self.pushButton_4.setDisabled(True)
            self.label_3.hide()
            self.pushButton_2.hide()
            self.textBrowser_2.hide()
            if 'end' in selected_mode:
                pass
            elif 'after' in selected_mode:
                pass
            elif 'marked' in selected_mode:
                pass
        else:
            self.label_3.show()
            self.pushButton_2.show()
            self.textBrowser_2.show()
            if self.textBrowser_2.toPlainText().endswith('pdf') and self.textBrowser.toPlainText().endswith('pdf'):
                self.pushButton_4.setDisabled(False)
            else:
                self.pushButton_4.setDisabled(True)


    def switchToSecondFrame(self):
        widget.addWidget(SecondScreen())
        widget.setCurrentIndex(widget.currentIndex()+1)


class SecondScreen(QtWidgets.QDialog):
    def __init__(self):
        super(SecondScreen, self).__init__()
        uic.loadUi('QuizMaster.ui', self)
        # self.show()

        self.pushButton.clicked.connect(self.switchToMainScreen)
        self.pushButton_2.clicked.connect(self.switchToQuestionScreen)

        sol_extraction_mode = mainwindow.buttonGroup_2.checkedButton().text().lower()
        
        file_to_parse = mainwindow.textBrowser.toPlainText()
        file2_to_parse = mainwindow.textBrowser_2.toPlainText() if \
                            'separate' in sol_extraction_mode \
                            else file_to_parse

        if file_to_parse.endswith('json'):
            self.pushButton_2.setDisabled(True)
            pass
        else:
            if 'separate' in mainwindow.buttonGroup_2.checkedButton().text().lower():
                question_data_parsed = fitz.open(file_to_parse)
                solution_data_parsed = fitz.open(file2_to_parse)
                
                parsing_list = [question_data_parsed, solution_data_parsed] if \
                                            file2_to_parse != file_to_parse else \
                                            [question_data_parsed]

                file_being_parsed = 0

                for data_parsed in parsing_list:
                    parsing_question    = 0         # 0 for at options or parsing not started yet; 1 question being parsed
                    question_index      = 0
                    file_being_parsed  += 1
                    for page in range(data_parsed.page_count):
                        page_text = re.sub('([0-9]\.)( ){0,5}\n( ){0,5}([A-Za-z\'\"`\‘\’])', r'\1 \4',
                                            data_parsed[page].get_text())
                        page_text = page_text.split('\n')
                        for page_line in page_text:
                            page_line = page_line.rstrip('\n').rstrip(' ').lstrip(' ')

                            if page_line.__contains__('I N S T R U C T I O N S '):
                                break
                            if len(page_line) <= 1 \
                                    or (page_line and len(page_line.rstrip()) < 3 and page_line[0].isdigit()) \
                                    or (page_line.startswith('www.') and (page_line.endswith('com') or page_line.endswith('org')\
                                                                            or page_line.endswith('in')))\
                                    or (re.search('^Page [0-9]+$', page_line))\
                                    or (page_line.endswith('P a g e') and page_line[0].isdigit())\
                                    or (page_line.startswith('TLP Connect'))\
                                    or (re.search('^20[0-9][0-9]$', page_line))\
                                    or (page_line.__contains__('Prelims Test Series'))\
                                    or (page_line.__contains__('Total Marks :'))\
                                    or (page_line.__contains__('Forum Learning Centre: Delhi'))\
                                    or (page_line.__contains__('Road, Patna, Bihar 800001'))\
                                    or (page_line.__contains__('9821711605'))\
                                    or (page_line.__contains__('DO  NOT  OPEN'))\
                                    or (page_line.__contains__('Copyright © by Vision IAS'))\
                                    or (page_line.__contains__('All rights are reserved. No part of this document'))\
                                    or (page_line.__contains__('transmitted in any form or by any means, electronic,'))\
                                    or (page_line.__contains__('Vision IAS'))\
                                    or (page_line.__contains__('Insights IAS'))\
                                    or (page_line.__contains__('RAUSIAS'))\
                                    or (page_line.__contains__('IAS[ ]{0,5}Baba'))\
                                    or (page_line.__contains__('Total Marks :')):
                                continue
                            
                            if file_being_parsed == 1:
                                
                                if not parsing_question and re.search('^[Q\.]{0,2}[ ]{0,2}[0-9]{1,3}[\.\)]{1}[ ]{0,2}[A-Za-z\'\"`\‘\’]+', page_line):
                                    parsing_question = 1
                                    question_index += 1
                                    necessary_data[question_index]['Question'] += ('\n' if page_line[0].isdigit() else ' ')\
                                                                                    + page_line
                                    continue
                                elif not parsing_question and question_index and \
                                    (not re.search('^[\(]{0,1}[A-Da-d][\)\.]', page_line)):
                                    necessary_data[question_index]['Options'][-1] += page_line + ' '
                                
                                if re.search('^[\(]{0,1}[A-Da-d][\)\.]', page_line):
                                    parsing_question = 0
                                    necessary_data[question_index]['Options'].append(page_line)
                                
                                if parsing_question:
                                    necessary_data[question_index]['Question'] += ('\n' if page_line[0].isdigit() else ' ')\
                                                                                    + page_line
                                
                            else:
                                if re.search('^Q\.[0-9]+\)[ ]+Solution', page_line) or \
                                    re.search('Q\.[0-9]+\)[ ]+Solution[ ]+\([A-Da-d]\)$', page_line) or \
                                    re.search('^Correct[ ]+Answer', page_line) or \
                                    re.search('^Q[ ]{0,5}[0-9]+\.', page_line) or \
                                    re.search('Q[ ]{0,5}[0-9]+\.[A-Da-d]$', page_line) or \
                                    re.search('^[0-9]+\.[ ]+Answer', page_line):
                                    question_index += 1
                                    if page_line[-1].lower() in ['a','b','c','d']:
                                        correct_answer = page_line[-1].lower()
                                    elif page_line[-2].lower() in ['a', 'b', 'c', 'd']:
                                        correct_answer = page_line[-2].lower()
                                    else:
                                        necessary_data[question_index]['Answer'] += page_line
                                        continue
                                    necessary_data[question_index]['Answer'] += correct_answer
                                
                                elif question_index:
                                    necessary_data[question_index]['Explanation'] += page_line

        
        # for data in necessary_data:
        #     print(necessary_data[data])
        #     print()

        
    def switchToMainScreen(self):
        widget.addWidget(mainwindow)
        widget.setCurrentIndex(widget.currentIndex()+1)
    
    def switchToQuestionScreen(self):
        widget.addWidget(QuestionScreen())
        widget.setCurrentIndex(widget.currentIndex()+1)


class QuestionScreen(QtWidgets.QDialog):
    def __init__(self):
        super(QuestionScreen, self).__init__()
        uic.loadUi('QuestionFrame.ui', self)
        # self.show()
        # setGeometry(left, top, width, height)
        self.setFixedSize(666, 600)
        self.location_on_the_screen()
  

        self.pushButton.clicked.connect(self.prevQuestion)
        self.pushButton_2.clicked.connect(self.nextQuestion)
        self.pushButton_5.clicked.connect(self.clearResponse)

        self.presentQuestionIndex = 1
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_lcds)

        self.timer.start(1000)
        self.total_time = 90*60

        self.loadQuestion(self.presentQuestionIndex)
        self.pushButton.setDisabled(True)

        
    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        sg = QDesktopWidget().screenGeometry()

        widget = self.geometry()
        x = ag.width() - widget.width()
        y = 2 * ag.height() - sg.height() - widget.height()
        self.move(x, y)

    def update_lcds(self):
        self.total_time -= 1
        if 15*60 <= self.total_time <= 45*60:
            bg_color = 'orange'
        elif self.total_time < 15*60 :
            bg_color = 'red'
        elif self.total_time > 45*60:
            bg_color = 'green'
        self.lcdNumber.setStyleSheet(f'background:{bg_color}')
        self.lcdNumber.display(str(self.total_time//60) + ': ' + str(self.total_time%60))


    def clearResponse(self):
        necessary_data[self.presentQuestionIndex]['MarkedResponse'] = ''
        self.responseCleanup(self.presentQuestionIndex)


    def prevQuestion(self):

        self.saveResponse(self.presentQuestionIndex)
        
        self.presentQuestionIndex -= 1
        if self.presentQuestionIndex == 1:
            self.pushButton.setDisabled(True)
        else:
            self.pushButton.setDisabled(False)
        
        self.loadQuestion(self.presentQuestionIndex)


    def nextQuestion(self):
        self.pushButton.setDisabled(False)
        
        self.saveResponse(self.presentQuestionIndex)
            
        self.presentQuestionIndex += 1
        
        self.loadQuestion(self.presentQuestionIndex)
    

    def saveResponse(self, idx):
        for i, button in enumerate(self.buttonGroup.buttons()):
            if button.isChecked():
                necessary_data[idx]['MarkedResponse'] = 'A' if i == 0 else \
                                                       ('B' if i == 1 else \
                                                       ('C' if i == 2 else 'D'))
                break

    
    def responseCleanup(self, idx):

        mresponse = necessary_data[idx]['MarkedResponse'].upper()
        
        button_mapping = {'A': self.radioButton, 'B': self.radioButton_2,
                          'C': self.radioButton_3, 'D': self.radioButton_4}
        
        self.buttonGroup.setExclusive(False)
        
        for resp in button_mapping:
            if resp == mresponse:
                button_mapping[resp].setChecked(True)
            else:
                button_mapping[resp].setChecked(False)
            
        self.buttonGroup.setExclusive(True)


    def loadQuestion(self, idx=1):
        self.textBrowser.setText(necessary_data[idx]['Question'])
        self.radioButton.setText(necessary_data[idx]['Options'][0])
        self.radioButton_2.setText(necessary_data[idx]['Options'][1])
        self.radioButton_3.setText(necessary_data[idx]['Options'][2])
        self.radioButton_4.setText(necessary_data[idx]['Options'][3])

        self.responseCleanup(idx)
        


app = QtWidgets.QApplication(sys.argv)
mainwindow = MainScreen()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainwindow)
widget.show()
app.exec_()