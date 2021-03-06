from inspect import getfile
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
import fitz
import pytesseract
from PIL import Image
import re, json, os
from datetime import datetime
from time import sleep


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

MAX_QUESTIONS_NUM = 100

necessary_data = {x:{'Question':'', 'Options':[], 'Answer': '', 'MarkedResponse':'', \
                     'TimeTaken':0, 'Comments': '', 'Explanation' : ''} for x in range(1,MAX_QUESTIONS_NUM+1)}

max_questions           = 0
total_time_available    = 0
total_time_left         = 0
attempted_questions     = 0
present_ques_index      = 0
quiz_type               = 0

NOT_SUPPORTED = ['GSSCORE', 'INSIGHTSIAS', 'FORUMIAS']

qo_format = {'iasbaba'      : ['^Q\.[ \t]*([0-9]{1,3})\)[ \t]*[A-Za-z\'\"`\‘\’]+',
                                                        '^[a-d]\)'],
                                 
             'visionias'    : ['^([0-9]{1,3})\.[ \t]*[A-Za-z\'\"`\‘\’]+', 
                                    '\([a-d]\)'],
             
             'gsscore'      : ['^([0-9]{1,3})\.[ \t]*[A-Za-z\'\"`\‘\’]+', 
                                    '\([a-d]\)'],
             
             'vajiram'      : ["^Q[ \t]*([0-9]{1,3})[ \t]*\.[ \t]*[A-Za-z\'\"`\‘\’]+",
                                                        '^[a-dA-D][\)\.]'],
                                 
             'rausias'      : ['^([0-9]{1,3})\.[ \t]*[A-Za-z\'\"`\‘\’]+', 
                                    '\([a-d]\)'],
                                 
             'forum'        : ['^Q\.[ \t]*([0-9]{1,3})\)[ \t]*[A-Za-z\'\"`\‘\’]+', 
                                    '^[a-d]\)'],
                                 
             'default'      : ['^[Q\.]{0,2}[ \t]*([0-9]{1,3})[\.\)]{1}[ \t]*[A-Za-z\'\"`\‘\’]+',
                               '^[\(]{0,1}[A-Da-d][\)\.]'],
            }
                    
sol_format = {
             'iasbaba'      : 'Q\.([0-9]+)\)[ \t]*Solution',

             'visionias'    : 'Q[ \t]*([0-9]+)\.',

             'gsscore'      : '\nCorrect[ ]+Option:.*?\n([0-9]+)\.[ \t]*',
                                 
             'vajiram'      : r'[Q]?([0-9]+)\.[ \t]*(\bExplanation\b)?.*?(\bAnswer\b)',

             'rausias'      : '([0-9]+)\.[ \t]*Answer',
                                 
            #  'forum'        : 'Q\.[ \t]?([0-9]{1,3})\)[ \t]?[A-Za-z\'\"`\‘\’]+',
                                 
             'default'      : 'Q\.([0-9]+)[ \t]*\)[]+Solution[] +\([A-Da-d]\)$',
            }

selected_format = 'default'

class MainScreen(QtWidgets.QDialog):
    def __init__(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type

        super(MainScreen, self).__init__()
        frontscreen = resource_path('QuizMasterFront.ui')
        uic.loadUi(frontscreen, self)
        # self.show()

        self.buttonGroup.buttonClicked.connect(self.selectQuizType)
        self.buttonGroup_2.buttonClicked.connect(self.selectSolutionType)

        self.pushButton.clicked.connect(lambda : self.getFile(1))
        self.pushButton_2.clicked.connect(lambda : self.getFile(2))

        self.radioButton.setChecked(True)
        self.radioButton_3.setChecked(True)
        
        # self.continuebutton = self.findChild(
        #     QtWidgets.QPushButton, 'pushButton_4')
        self.pushButton_4.clicked.connect(self.switchToNextFrame)
        self.pushButton_4.setDisabled(True)

        self.txtbrwsr_newq = ''
        self.txtbrwsr_oldq = ''
    
    def getFile(self, ptr):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type

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
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type
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
            quiz_type = 1

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
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type
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


    def switchToNextFrame(self):
        global necessary_data, max_questions, attempted_questions
        if 'old' in self.buttonGroup.checkedButton().text().lower():
            nextScreen = QuestionScreen
            new_dict = json.loads(
                               json.load(open(self.textBrowser.toPlainText())))
            necessary_data = {int(x):y for (x,y) in zip(new_dict.keys(), new_dict.values())}
            max_questions  = len(set([necessary_data[x]['Question'] for x in range(1, len(necessary_data)+1) if \
                                        len(necessary_data[x]['Question']) >= 2]))

            attempted_questions = len([necessary_data[x]['MarkedResponse'] \
                                        for x in range(1, len(necessary_data)+1)\
                                            if necessary_data[x]['MarkedResponse'].upper() in ['A', 'B', 'C', 'D']])
        else:
            nextScreen = SecondScreen
        if widget.count() <= 1:
            widget.addWidget(nextScreen())
        widget.setCurrentIndex(widget.currentIndex()+1)


class SecondScreen(QtWidgets.QDialog):

    progress_value  = 0
    question_file   = ''
    solution_file   = ''
    
    def __init__(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type, selected_format
        super(SecondScreen, self).__init__()
        secondscreen = resource_path('QuizMaster.ui')
        uic.loadUi(secondscreen, self)
        # self.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progressbar)
        self.timer.start(100)

        self.pushButton.clicked.connect(self.switchToMainScreen)
        self.pushButton_2.clicked.connect(self.switchToQuestionScreen)
        self.pushButton_2.setText('Parse Data')

        widget.currentChanged.connect(self.check_file_update)

        sol_extraction_mode = mainwindow.buttonGroup_2.checkedButton().text().lower()
        self.question_file  = mainwindow.textBrowser.toPlainText()
        self.solution_file  = mainwindow.textBrowser_2.toPlainText() if \
                                        'separate' in sol_extraction_mode \
                                         else self.question_file
        

    def check_file_update(self):
        global necessary_data

        if self.question_file != mainwindow.textBrowser.toPlainText() or \
            self.solution_file != mainwindow.textBrowser_2.toPlainText():

            necessary_data = {x:{'Question':'', 'Options':[], 'Answer': '', 'MarkedResponse':'', \
                     'TimeTaken':0, 'Comments': '', 'Explanation' : ''} for x in range(1,MAX_QUESTIONS_NUM+1)}
            
            self.progress_value = 0
            self.update_progressbar()
            self.pushButton_2.setText('Parse Data')
            self.pushButton_2.setDisabled(False)

            sol_extraction_mode = mainwindow.buttonGroup_2.checkedButton().text().lower()
            self.question_file  = mainwindow.textBrowser.toPlainText()
            self.solution_file  = mainwindow.textBrowser_2.toPlainText() if \
                                        'separate' in sol_extraction_mode \
                                         else self.question_file

            
    def parseRequiredData(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type, selected_format

        self.pushButton_2.setDisabled(True)

        if 'separate' in mainwindow.buttonGroup_2.checkedButton().text().lower():
            question_data_parsed = fitz.open(self.question_file)
            solution_data_parsed = fitz.open(self.solution_file)
                
            parsing_list = [question_data_parsed, solution_data_parsed] if \
                                        self.question_file != self.solution_file else \
                                        [question_data_parsed]

            file_being_parsed   = 0
            question_index      = 0

            for data_parsed in parsing_list:
                parsing_question    = 0         # 0 for at options or parsing not started yet; 1 question being parsed
                max_questions       = max(max_questions, question_index)
                question_index      = 0
                file_being_parsed  += 1
                self.progress_value = 50 if data_parsed == solution_data_parsed else 0
                    
                for page in range(data_parsed.page_count):
                        
                    self.progress_value += 1
                    self.progress_value =  min(99, self.progress_value)

                    self.update_progressbar()

                    page_text = re.sub('([0-9][\.\)])([ ]{0,5})\n([ ]{0,5})([A-Za-z\'\"`\‘\’])', r'\1 \4',
                                        data_parsed[page].get_text())
                        
                    if not len(page_text):
                        try:
                            page_contents = data_parsed[page] # number of pages
                            mat           = fitz.Matrix(2.25, 2.25)
                            pix           = page_contents.get_pixmap(matrix = mat)
                            output = f'temp_{page}_parsing.jpg'
                            pix.save(output)
                            
                            page_text = re.sub('([0-9][\.\)])([ ]{0,5})\n([ ]{0,5})([A-Za-z\'\"`\‘\’])', r'\1 \4',
                                                    str(((pytesseract.image_to_string(Image.open(output))))))

                            os.remove(output)

                        except:
                            pass
                        

                    page_text = page_text.split('\n')

                    for page_line in page_text:
                        page_line = page_line.rstrip('\n').rstrip(' ').lstrip(' ').lstrip('\n')

                        if page_line.__contains__('I N S T R U C T I O N S'):
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
                                or (page_line.__contains__('Contact[ ]*[:]?[ ]*[0-9]+'))\
                                or (page_line.__contains__('Join Our Telegram Channel'))\
                                or (page_line.__contains__('DO  NOT  OPEN'))\
                                or (page_line.__contains__('@UpscMaterialsNotes'))\
                                or (page_line.__contains__('@CivilServicePDF'))\
                                or (page_line.__contains__('Copyright © by Vision IAS'))\
                                or (page_line.__contains__('All rights are reserved. No part of this document'))\
                                or (page_line.__contains__('transmitted in any form or by any means, electronic,'))\
                                or (page_line.__contains__('Vision IAS'))\
                                or (page_line.__contains__('Insights IAS'))\
                                or (page_line.__contains__('RAUSIAS'))\
                                or (page_line.__contains__('Vajiram'))\
                                or (page_line.__contains__('VAJIRAM'))\
                                or (page_line.__contains__('GS SCORE'))\
                                or (page_line.__contains__('iasscore'))\
                                or (page_line.__contains__('IAS[ ]{0,5}Baba'))\
                                or (page_line.__contains__('Total Marks :')):
                            if page_line.__contains__('Vision IAS'):
                                    selected_format = 'visionias'
                            elif page_line.__contains__('RAUSIAS'):
                                    selected_format = 'rausias'
                            elif page_line.startswith('TLP Connect'):
                                    selected_format = 'iasbaba'
                            elif page_line.startswith('SFG 20'):
                                    selected_format = 'forum'
                            elif page_line.__contains__('Vajiram') or page_line.__contains__('VAJIRAM'):
                                    selected_format = 'vajiram'
                            elif page_line.__contains__('GS SCORE') or page_line.__contains__('iasscore'):
                                    selected_format = 'gsscore'
                            
                            continue
                            
                        if file_being_parsed == 1:
                                
                            # print(page_line, question_index, selected_format)
                            if not parsing_question and re.search(qo_format.get(selected_format, 'default')[0], page_line):
                                parsing_question = 1
                                question_index = re.search(qo_format.get(selected_format, 'default')[0], page_line)
                                question_index = int(question_index.group(1))
                                necessary_data[question_index]['Question'] += ('\n' if page_line[0].isdigit() else ' ')\
                                                                                + page_line
                                continue

                            elif not parsing_question and question_index and \
                                (not re.search(qo_format.get(selected_format, 'default')[1], page_line)):
                                necessary_data[question_index]['Options'][-1] += page_line + ' '


                            if re.search(qo_format.get(selected_format, 'default')[1], page_line):
                                parsing_question = 0
                                necessary_data[question_index]['Options'].append(page_line)
                                
                            if parsing_question:
                                necessary_data[question_index]['Question'] += ('\n' if page_line[0].isdigit() else ' ')\
                                                                                + page_line
                                
                        else:
                            # print(page_line)
                            if re.search(sol_format.get(selected_format, 'default'), page_line):
                                
                                question_index = re.search(
                                    sol_format.get(selected_format, 'default'), page_line)
                                
                                question_index = int(
                                    question_index.group(1))

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
            
            self.progress_value = 100

            # for data in necessary_data:
            #     print(necessary_data[data],'\n')

    def update_progressbar(self):
        self.progressBar.setValue(self.progress_value)
        if self.progress_value == 100 : self.pushButton_2.setDisabled(False)
        
    def switchToMainScreen(self):
        # widget.addWidget(mainwindow)
        widget.setCurrentIndex(widget.currentIndex()-1)

    def switchToQuestionScreen(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type
        if self.pushButton_2.text() == 'Parse Data':
            self.pushButton_2.setText('Parsing...')
            self.pushButton_2.setDisabled(True)
            self.parseRequiredData()
            self.pushButton_2.setText('Continue')
            self.pushButton_2.setDisabled(False)
        else:
            total_time_available = self.spinBox.value()*60
            if widget.count() <= 2:
                widget.addWidget(QuestionScreen())
            widget.setCurrentIndex(widget.currentIndex()+1)


class QuestionScreen(QtWidgets.QDialog):

    def __init__(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type
        super(QuestionScreen, self).__init__()
        quescreen = resource_path('QuestionFrame.ui')
        uic.loadUi(quescreen, self)
        self.setFixedSize(875, 600)
        
        self.pushButton.clicked.connect(self.prevQuestion)
        self.pushButton_2.clicked.connect(self.nextQuestion)
        self.pushButton_4.clicked.connect(self.switchToConfirmScreen)
        self.pushButton_5.clicked.connect(self.clearResponse)
        self.listWidget.itemDoubleClicked.connect(self.moveToQuestion)

        self.plainTextEdit.setReadOnly(True if quiz_type == 1 else False)

        for data in necessary_data:
            if len(necessary_data[data]['Question']) > 2:
                if necessary_data[data]['Question'].find('\n',2) == -1:
                    break_idx = min(55, len(necessary_data[data]['Question']))
                else:
                    break_idx = min(55, necessary_data[data]['Question'].find('\n',2))

                self.listWidget.addItem(necessary_data[data]['Question'][1:][:break_idx-1])
            else:
                self.listWidget.addItem(necessary_data[data]['Question'])
                self.listWidget.item(self.listWidget.count()-1).setHidden(True)
        
        if quiz_type == 1:
            for item_idx in range(self.listWidget.count()):
                if necessary_data[item_idx+1]['Answer'].lower() == necessary_data[item_idx+1]['MarkedResponse'].lower():
                    self.listWidget.item(item_idx).setForeground(QBrush(QColor("green")))
                elif necessary_data[item_idx+1]['MarkedResponse'].lower() in ['a', 'b', 'c', 'd']:
                    self.listWidget.item(item_idx).setForeground(QBrush(QColor("red")))

        present_ques_index = 1
        
        if quiz_type == 1:
            self.lcdNumber_2.display(str(necessary_data[present_ques_index]['TimeTaken']//60) +
                                 ': ' + str(necessary_data[present_ques_index]['TimeTaken'] % 60))
        
            if necessary_data[present_ques_index]['TimeTaken']//60 == 1:
                self.lcdNumber_2.setStyleSheet(f'background:orange')
            elif necessary_data[present_ques_index]['TimeTaken']//60 > 1:
                self.lcdNumber_2.setStyleSheet(f'background:red')
            else:
                self.lcdNumber_2.setStyleSheet(f'background:green')
            
        else:
            self.textBrowser_3.hide()
            self.plainTextEdit.resize(845, 130)
            self.plainTextEdit.setPlaceholderText('Comments...')
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_lcds) if total_time_available else None

            self.timer.start(1000)

        self.loadQuestion(present_ques_index)
        self.pushButton.setDisabled(True)

        total_time_left = total_time_available


    def update_lcds(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type

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
        
        necessary_data[present_ques_index]['TimeTaken'] += 1
        self.lcdNumber_2.display(str(necessary_data[present_ques_index]['TimeTaken']//60) +
                                 ': ' + str(necessary_data[present_ques_index]['TimeTaken'] % 60))
        
        if necessary_data[present_ques_index]['TimeTaken']//60 == 1:
            self.lcdNumber_2.setStyleSheet(f'background:orange')
        elif necessary_data[present_ques_index]['TimeTaken']//60 > 1:
            self.lcdNumber_2.setStyleSheet(f'background:red')
        else:
            self.lcdNumber_2.setStyleSheet(f'background:green')

        if total_time_left <= 1:
            self.switchToConfirmScreen()


    def moveToQuestion(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type

        self.saveResponse(present_ques_index) if quiz_type == 0 else None

        question_index      = re.search(qo_format.get(selected_format, 'default')[0], self.listWidget.currentItem().text())
        present_ques_index  = int(question_index.group(1))

        if present_ques_index == 1:
            self.pushButton.setDisabled(True)
        else:
            self.pushButton.setDisabled(False)
        
        if present_ques_index == max_questions:
            self.pushButton_2.setText('Submit') if quiz_type == 0 else self.pushButton_2.setDisabled(True)
        else:
            self.pushButton_2.setText('Next')

        self.loadQuestion(present_ques_index)


    def prevQuestion(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type

        self.saveResponse(present_ques_index) if quiz_type == 0 else None
        self.listWidget.item(present_ques_index-1).setSelected(False)
        
        present_ques_index -= 1
        if present_ques_index == 1:
            self.pushButton.setDisabled(True)
        else:
            self.pushButton.setDisabled(False)
        
        self.listWidget.item(present_ques_index-1).setSelected(True)

        self.loadQuestion(present_ques_index, -1)

        self.pushButton_2.setText('Next')
        self.pushButton_2.setDisabled(False)


    def nextQuestion(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type

        if self.pushButton_2.text() != 'Submit':
            self.pushButton.setDisabled(False)
            self.saveResponse(present_ques_index) if quiz_type == 0 else None
            self.listWidget.item(present_ques_index-1).setSelected(False)
            present_ques_index += 1
            self.listWidget.item(present_ques_index-1).setSelected(True)
            self.loadQuestion(present_ques_index, 1)
            if present_ques_index == max_questions:
                self.pushButton_2.setText('Submit') if quiz_type == 0 else self.pushButton_2.setDisabled(True)
            
        else:
            self.saveResponse(present_ques_index) if quiz_type == 0 else None
            self.switchToConfirmScreen()
    

    def switchToConfirmScreen(self):
        if widget.count() <= 3:
            widget.addWidget(ConfirmScreen())
        widget.setCurrentIndex(widget.currentIndex()+1)


    def clearResponse(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type
        
        if necessary_data[present_ques_index]['MarkedResponse'].upper() in ['A','B','C','D']:
            attempted_questions -= 1
        necessary_data[present_ques_index]['MarkedResponse'] = ''
        self.responseCleanup(present_ques_index)
        self.listWidget.item(present_ques_index-1).setForeground(QBrush(QColor("black")))
    
    
    def saveResponse(self, idx):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type
        
        for i, button in enumerate(self.buttonGroup.buttons()):
            if button.isChecked():
                attempted_questions += (1 if necessary_data[idx]['MarkedResponse'].upper() not in ['A', 'B', 'C', 'D'] else 0)
                necessary_data[idx]['MarkedResponse'] = 'A' if i == 0 else \
                                                       ('B' if i == 1 else \
                                                       ('C' if i == 2 else 'D'))
                self.listWidget.item(idx-1).setForeground(QBrush(QColor("cyan")))
                break
        
        if self.plainTextEdit.toPlainText() != 'Comments...':
            necessary_data[idx]['Comments'] = self.plainTextEdit.toPlainText()

    
    def responseCleanup(self, idx):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type

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


    def loadQuestion(self, idx=1, prevnext = 1, recurse_level = 0):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type
        
        self.textBrowser.setText(necessary_data[idx]['Question'])

        if len(necessary_data[idx]['Options']) == 4 and necessary_data[idx]['Question'] != '':
            self.radioButton.setText(necessary_data[idx]['Options'][0])
            self.radioButton_2.setText(necessary_data[idx]['Options'][1])
            self.radioButton_3.setText(necessary_data[idx]['Options'][2])
            self.radioButton_4.setText(necessary_data[idx]['Options'][3])
            self.listWidget.scrollToItem(self.listWidget.item(present_ques_index-1))
            self.listWidget.item(present_ques_index-1).setSelected(True)
            if necessary_data[idx]['Comments'] != '':
                self.plainTextEdit.setPlainText(necessary_data[idx]['Comments'])
            else:
                self.plainTextEdit.setPlainText('')
                self.plainTextEdit.setPlaceholderText('Comments...')
        else:
            if (present_ques_index < max_questions and prevnext == 1) or \
                    (present_ques_index > 1 and prevnext == -1 ):
                present_ques_index += prevnext
                self.loadQuestion(idx+prevnext, prevnext, recurse_level+prevnext)
            else:
                if present_ques_index == 1 and prevnext == -1:
                    present_ques_index -= recurse_level
                    self.loadQuestion(present_ques_index, 1, 0)
                elif present_ques_index == max_questions and prevnext == 1:
                    present_ques_index -= recurse_level
                    self.loadQuestion(present_ques_index, -1, 0)
                    self.pushButton_2.setText('Submit') if quiz_type == 0 else self.pushButton_2.setDisabled(True)
            return
        
        if quiz_type == 1:
            self.lcdNumber_2.display(str(necessary_data[present_ques_index]['TimeTaken']//60) +
                                 ': ' + str(necessary_data[present_ques_index]['TimeTaken'] % 60))
        
            if necessary_data[present_ques_index]['TimeTaken']//60 == 1:
                self.lcdNumber_2.setStyleSheet(f'background:orange')
            elif necessary_data[present_ques_index]['TimeTaken']//60 > 1:
                self.lcdNumber_2.setStyleSheet(f'background:red')
            else:
                self.lcdNumber_2.setStyleSheet(f'background:green')
            

            button_mapping = {'A': self.radioButton, 'B': self.radioButton_2,
                          'C': self.radioButton_3, 'D': self.radioButton_4}
            
            mresponse   = necessary_data[idx]['MarkedResponse'].upper()
            answer      = necessary_data[idx]['Answer'].upper()

            for button in list(button_mapping.values()):
                button.setCheckable(True)
                button.setChecked(False)
                button.setStyleSheet("color : black")

            if mresponse in ['A', 'B', 'C', 'D']:
                button_mapping[mresponse].setStyleSheet("color : red")
                button_mapping[mresponse].setChecked(True)
            else:
                for button in list(button_mapping.values()):
                    button.setCheckable(False)

            if answer in ['A', 'B', 'C', 'D']:
                button_mapping[answer].setStyleSheet("color : green")
            
            if len(necessary_data[idx]['Comments']) :
                self.plainTextEdit.setPlaceholderText(necessary_data[idx]['Comments'])
            else:
                self.plainTextEdit.setPlaceholderText('Comments...')
            
            self.textBrowser_3.setText(necessary_data[idx]['Explanation'])

        else:
            self.responseCleanup(idx)
        

class ConfirmScreen(QtWidgets.QDialog):
    def __init__(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type
        
        super(ConfirmScreen, self).__init__()
        confirmscreen = resource_path('ConfirmFrame.ui')
        uic.loadUi(confirmscreen, self)

        self.pushButton.clicked.connect(self.switchToQuestionScreen)
        self.pushButton_2.clicked.connect(self.viewSaveResult_Restart)
        widget.currentChanged.connect(self.update_lcds)

        self.lcdNumber_6.display(max_questions)

        for data in necessary_data:
            if len(necessary_data[data]['Question']) > 2:
                if necessary_data[data]['Question'].find('\n',2) == -1:
                    break_idx = min(55, len(necessary_data[data]['Question']))
                else:
                    break_idx = min(55, necessary_data[data]['Question'].find('\n',2))

                self.listWidget.addItem(necessary_data[data]['Question'][1:][:break_idx-1])
        
        if quiz_type == 0:
            self.label_5.hide()
            self.label_7.hide()
            self.label_8.hide()
            self.lcdNumber.hide()
            self.lcdNumber_3.hide()
            self.lcdNumber_4.hide()
        else:
            self.viewSaveResult_Restart(force_display = True)

        if total_time_left <= 1:
            self.pushButton.setDisabled(True if quiz_type == 0 else False)

    def update_lcds(self):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type
        
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
            self.pushButton.setDisabled(True if quiz_type == 0 else False)



    def switchToQuestionScreen(self):
        # widget.addWidget(QuestionScreen())
        widget.setCurrentIndex(widget.currentIndex()-1)
    
    def viewSaveResult_Restart(self, force_display = False):
        global total_time_available, total_time_left, max_questions, attempted_questions, present_ques_index, quiz_type
        if 'submit' in self.pushButton_2.text().lower() or force_display:
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
            self.pushButton_2.setText('Save Attempt Data' if quiz_type == 0 else 'Restart GUI')
            self.pushButton.setDisabled(True if quiz_type == 0 else False)

            for item_idx in range(self.listWidget.count()):
                if necessary_data[item_idx+1]['Answer'].lower() == necessary_data[item_idx+1]['MarkedResponse'].lower():
                    if necessary_data[item_idx+1]['MarkedResponse'].lower() in ['a', 'b', 'c', 'd']:
                        self.listWidget.item(item_idx).setForeground(QBrush(QColor("green")))
                elif necessary_data[item_idx+1]['MarkedResponse'].lower() in ['a', 'b', 'c', 'd']:
                    self.listWidget.item(item_idx).setForeground(QBrush(QColor("red")))

        elif 'attempt' in self.pushButton_2.text().lower():
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
                json.dump(json.dumps(necessary_data), 
                                outfile, indent=4, separators=(', ', ': '))
            
            self.pushButton_2.setText('Restart GUI')
        
        elif 'restart' in self.pushButton_2.text().lower():
            os.execv(sys.executable, [sys.executable] + sys.argv)

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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainwindow = MainScreen()
    # mainwindow.setWindowFlags(mainwindow.windowFlags() & ~QtCore.Qt.WindowMaximizeButtonHint)
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(mainwindow)
    widget.show()
    app.exec_()