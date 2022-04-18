from inspect import getfile
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
import fitz, re, json
from datetime import datetime


# Question number : [{Question : '', Options : '', Answer: '', MarkedResponse : '', TimeTaken : ''}]
necessary_data = {x:{'Question':'', 'Options':[], 'Answer': '', 'MarkedResponse':'', \
                     'TimeTaken':'', 'Comments': '', 'Explanation' : ''} for x in range(1,101)}

max_questions           = 0
total_time_available    = 0
total_time_left         = 0
attempted_questions     = 0
present_ques_index      = 0

class MainScreen(QtWidgets.QDialog):
    def __init__(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index

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
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index

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
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index
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
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index
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
        if widget.count() <= 1:
            widget.addWidget(SecondScreen())
        widget.setCurrentIndex(widget.currentIndex()+1)


class SecondScreen(QtWidgets.QDialog):
    
    def __init__(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index
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
                question_index      = 0

                for data_parsed in parsing_list:
                    parsing_question    = 0         # 0 for at options or parsing not started yet; 1 question being parsed
                    max_questions       = max(max_questions, question_index)
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

        
    def switchToMainScreen(self):
        # widget.addWidget(mainwindow)
        widget.setCurrentIndex(widget.currentIndex()-1)
    
    def switchToQuestionScreen(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index
        total_time_available = self.spinBox.value()*60
        if widget.count() <= 2:
            widget.addWidget(QuestionScreen())
        widget.setCurrentIndex(widget.currentIndex()+1)


class QuestionScreen(QtWidgets.QDialog):

    def __init__(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index
        super(QuestionScreen, self).__init__()
        uic.loadUi('QuestionFrame.ui', self)
        self.setFixedSize(666, 600)
        self.location_on_the_screen()

        self.pushButton.clicked.connect(self.prevQuestion)
        self.pushButton_2.clicked.connect(self.nextQuestion)
        self.pushButton_4.clicked.connect(self.switchToConfirmScreen)
        self.pushButton_5.clicked.connect(self.clearResponse)

        present_ques_index = 1
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_lcds)

        self.timer.start(1000)

        self.loadQuestion(present_ques_index)
        self.pushButton.setDisabled(True)

        total_time_left = total_time_available

        
    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        sg = QDesktopWidget().screenGeometry()

        widget = self.geometry()
        x = ag.width() - widget.width()
        y = 2 * ag.height() - sg.height() - widget.height()
        self.move(x, y)

    def update_lcds(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index

        total_time_left -= 1
        if total_time_available*0.2 <= total_time_left <= total_time_available*0.45:
            bg_color = 'orange'
        elif total_time_left < total_time_available*0.2:
            bg_color = 'red'
        elif total_time_left > total_time_available*0.45:
            bg_color = 'green'
        self.lcdNumber.setStyleSheet(f'background:{bg_color}')
        self.lcdNumber.display(str(total_time_left//60) +
                               ': ' + str(total_time_left % 60))
        if total_time_left <= 1:
            self.switchToConfirmScreen()


    def clearResponse(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index
        
        necessary_data[present_ques_index]['MarkedResponse'] = ''
        self.responseCleanup(present_ques_index)
        attempted_questions -= 1


    def prevQuestion(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index

        self.saveResponse(present_ques_index)
        
        present_ques_index -= 1
        if present_ques_index == 1:
            self.pushButton.setDisabled(True)
        else:
            self.pushButton.setDisabled(False)
        
        self.loadQuestion(present_ques_index)

        self.pushButton_2.setText('Next')


    def nextQuestion(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index

        if self.pushButton_2.text() != 'Submit':
            self.pushButton.setDisabled(False)
            self.saveResponse(present_ques_index)
            present_ques_index += 1
            self.loadQuestion(present_ques_index)
            if present_ques_index == max_questions:
                self.pushButton_2.setText('Submit')
        else:
            self.switchToConfirmScreen()
    
    def switchToConfirmScreen(self):
        if widget.count() <= 3:
            widget.addWidget(ConfirmScreen())
        widget.setCurrentIndex(widget.currentIndex()+1)
    
    
    def saveResponse(self, idx):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index
        
        for i, button in enumerate(self.buttonGroup.buttons()):
            if button.isChecked():
                necessary_data[idx]['MarkedResponse'] = 'A' if i == 0 else \
                                                       ('B' if i == 1 else \
                                                       ('C' if i == 2 else 'D'))
                attempted_questions += 1
                break

    
    def responseCleanup(self, idx):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index

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
        

class ConfirmScreen(QtWidgets.QDialog):
    def __init__(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index
        
        super(ConfirmScreen, self).__init__()
        uic.loadUi('ConfirmFrame.ui', self)

        self.pushButton.clicked.connect(self.switchToQuestionScreen)
        self.pushButton_2.clicked.connect(self.viewSaveResult)
        widget.currentChanged.connect(self.update_lcds)

        self.label_5.hide()
        self.label_7.hide()
        self.label_8.hide()
        self.lcdNumber.hide()
        self.lcdNumber_3.hide()
        self.lcdNumber_4.hide()
        self.lcdNumber_6.display(max_questions)

        if total_time_left <= 1:
            self.pushButton.setDisabled(True)

    def update_lcds(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index
        
        if attempted_questions < 0.4*max_questions:
            bg_color = 'red'
        elif 0.4*max_questions <= attempted_questions <= 0.75*max_questions:
            bg_color = 'orange'
        else:
            bg_color = 'green'
        
        self.lcdNumber_5.setStyleSheet(f'background:{bg_color}')
        self.lcdNumber_5.display(attempted_questions)

        if total_time_available*0.1 <= total_time_left <= total_time_available*0.25:
            bg_color = 'orange'
        elif total_time_left < total_time_available*0.1:
            bg_color = 'red'
        elif total_time_left > total_time_available*0.25:
            bg_color = 'green'
        self.lcdNumber_2.setStyleSheet(f'background:{bg_color}')
        self.lcdNumber_2.display(str((total_time_available-total_time_left)//60) +
                                 ': ' + str((total_time_available-total_time_left) % 60))

        if total_time_left <= 1:
            self.pushButton.setDisabled(True)



    def switchToQuestionScreen(self):
        # widget.addWidget(QuestionScreen())
        widget.setCurrentIndex(widget.currentIndex()-1)
    
    def viewSaveResult(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index
        if 'submit' in self.pushButton_2.text().lower() :
            marking_scheme = [mainwindow.spinBox.value(), mainwindow.doubleSpinBox.value(), 0]
            response_data  =  self.analyseResponses()
            marks_acquired = sum([x*y for x,y in zip(response_data, marking_scheme)])
            self.label_5.show()
            self.label_7.show()
            self.label_8.show()
            self.lcdNumber.show()
            self.lcdNumber_3.show()
            self.lcdNumber_4.show()
            marking_scale = max_questions*mainwindow.spinBox.value()

            if marks_acquired <= marking_scale*0.4:
                bg_color = 'red'
            elif marking_scale*0.4 < marks_acquired < marking_scale*0.55 :
                bg_color = 'orange'
            elif marks_acquired :
                bg_color = 'green'
            self.lcdNumber.setStyleSheet(f'background:{bg_color}')
            self.lcdNumber.display(marks_acquired)
            
            self.lcdNumber_5.display(response_data[0]+response_data[1])

            self.lcdNumber_3.display(response_data[0])
            self.lcdNumber_3.setStyleSheet(f'background:green')
            self.lcdNumber_4.display(response_data[1])
            self.lcdNumber_4.setStyleSheet(f'background:red')
            self.pushButton_2.setText('Save Attempt Data')
            self.pushButton.setDisabled(True)
        else:
            name = QFileDialog.getSaveFileName(self, 'Save Attempt Data', '', 'JSON (*.json)')
            if not name[0].endswith('.json'):
                if '.' in name[0]:
                    name = name[0][:name.index('.')] + '.json'
                else:
                    if name[0]:
                        name = name[0] + '.json'
                    else:
                        curr_time = str(datetime.now()).replace('-','').replace(':','_').replace(' ','_')
                        if '.' in curr_time:
                            curr_time = curr_time[:curr_time.index('.')]
                        name = 'attempt_data_' + curr_time + '.json'
            else:
                name = name[0]
            with open(name, 'w') as outfile:
                # json.dump(json.dumps(json.loads(necessary_data), indent=4, separators=(',', ': ')), outfile,
                #           indent=4, separators=(',', ': '))
                # json.dump(json.dumps(necessary_data, indent=4, separators=(', ', ': ')), 
                json.dump(json.dumps(necessary_data), 
                                outfile, indent=4, separators=(', ', ': '))

    def analyseResponses(self):
        correct = 0
        wrong = 0
        skipped = 0
        for data in necessary_data:
            if necessary_data[data]['MarkedResponse'].upper() in ['A', 'B', 'C', 'D']:
                if necessary_data[data]['MarkedResponse'].upper() == necessary_data[data]['Answer'].upper():
                    correct += 1
                else:
                    wrong += 1
            else:
                skipped += 1
        
        return [correct, wrong, skipped]



app = QtWidgets.QApplication(sys.argv)
mainwindow = MainScreen()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainwindow)
widget.show()
app.exec_()