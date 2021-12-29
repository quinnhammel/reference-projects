#Quinn Hammel: final comp sci

import matplotlib
matplotlib.use('TkAgg')
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import time

class AssingmentGrade:
    def __init__(self, actualpoints, totalpointsposs):
        if isinstance(totalpointsposs, int) and (totalpointsposs > 0):
            #must be an int number of points, and cannot be 0 because of division
            self.totalpointsposs = totalpointsposs
        else:
            self.totalpointsposs = None
        if (isinstance(actualpoints, float)  or isinstance(actualpoints, int)) and (actualpoints >= 0):
            #must be an int number of points, can be 0 but not negative
            self.actualpoints = float(actualpoints)
        else:
            self.actualpoints = None


class AssingmentRoster:
    #name, totalpointsposs, gradelist, curve_func, param, cap
    def __init__(self, name, totalpointsposs=None):
        try:
            self.name = str(name)
        except:
            #name is not valid
            self.name = ''
        try:
            self.totalpointsposs = int(totalpointsposs)
        except:
            #either none or not an int
            self.totalpointsposs = None
        #default values
        self.__grade_list = []
        self.__curve_func = ''
        self.__param = ''
        self.__cap = ''
    
    #simple operations for list
    def set_grade_list(self, gradelist):
        self.__grade_list = []
        if isinstance(gradelist, list):
            for grade in gradelist:
                self.add_assingment_grade(grade)
        
    def add_assingment_grade(self, assingment_grade):
        if isinstance(assingment_grade, AssingmentGrade) and (assingment_grade.totalpointsposs == self.totalpointsposs):
            self.__grade_list.append(assingment_grade)
    
    def order(self):
        self.__grade_list.sort(key=lambda ag: ag.actualpoints)

    #get curved score
    def __get_curved_score(self, assingment_grade):
        if isinstance(assingment_grade, int) and (assingment_grade >= 0 and assingment_grade < len(self.__grade_list)):
            try:
                assingment_grade = self.__grade_list[assingment_grade]
            except:
                #empty list
                return None
        if isinstance(assingment_grade, AssingmentGrade):
            try:
                return self.__curve_func(assingment_grade.actualpoints/(assingment_grade.totalpointsposs+0.0))
            except Exception as e:
                print(e)
                #totalpointsposs is 0
                return None

    #simple get methods
    def get_dom(self):
        dom = []
        for index in range(1, len(self.__grade_list)+1):
            dom.append(index)
        return dom

    def get_rawscores(self):
        rawscores = []
        self.order()
        for grade in self.__grade_list:
            rawscores.append(100*grade.actualpoints/self.totalpointsposs)
        return rawscores

    def get_curvedscores(self):
        curvedscores = []
        self.order()
        for grade in self.__grade_list:
            curvedscores.append(100*self.__get_curved_score(grade))
        return curvedscores

    #update operations (curve_func, param, cap)
    def set_curve(self, curvename):
        try:
            curvename = str(curvename).lower()
        except:
            curvename = ''
        if curvename == 'add_curve':
            self.__curve_func = self.__add_curve
            self.__cap = 10000.0
            self.__param = 0
        elif curvename == 'mult_curve':
            self.__curve_func = self.__mult_curve
            self.__cap = 10000.0
            self.__param = 1
        elif curvename == 'root_curve':
            self.__curve_func = self.__root_curve
            self.__cap = 10000.0
            self.__param = 1
        else:
            self.__curve_func = self.__identity_curve
            self.__cap = 10000.0
            self.__param = 1
    
    def update_vars(self, param, cap):
        try:
            param = float(param)
        except:
            param = 1.0
        try:
            cap = float(cap)
        except:
            cap = 10000.0
        self.__cap = cap
        self.__param = param

    #curve functions
    def __add_curve(self, score):
        try:
            score = float(score)
        except:
            #score is not a float
            return None
        try:
            cap = float(self.__cap)
        except:
            #cap is None or not a float
            cap = 10000.0
        try:
            param = float(self.__param)
        except:
            #param is None or not a float
            param = 0.0
        cscore = score + param
        if cscore < cap:
            return cscore
        return cap
    
    def __identity_curve(self, score):
        try:
            score = float(score)
        except:
            #score is not a float
            return None
        try:
            cap = float(self.__cap)
        except:
            #cap is None or not a float
            cap = 10000.0
        if score < cap:
            return score
        return cap

    def __mult_curve(self, score):
        try:
            score = float(score)
        except:
            #score is not a float
            return None
        try:
            cap = float(self.__cap)
        except:
            #cap is None or not a float
            cap = 10000.0
        try:
            param = float(self.__param)
        except:
            #param is None or not a float
            param = 1.0
        cscore = param*score
        if cscore < cap:
            return cscore
        return cap
    
    def __root_curve(self, score):
        try:
            score = float(score)
        except:
            #score is not a float
            return None
        try:
            cap = float(self.__cap)
        except:
            #cap is None or not a float
            cap = 10000.0
        try:
            param = float(self.__param)
        except:
            #param is None or not a float
            param = 1.0 
        cscore = score**param
        if cscore < cap:
            return cscore
        return cap


class PlotGui:
    def __init__(self):
        #curve menu, roster, plot menu, frame 4
        self.__login_menu = tk.Tk()
        self.__canmanager = CanvasScraper()
        self.__ros = None
        self.__curve_menu = None
        self.__frame4 = None
        self.__dom = None
        self.__rawscores = None
        tframelogin = tk.Frame(self.__login_menu)
        mframelogin = tk.Frame(self.__login_menu)
        bframelogin = tk.Frame(self.__login_menu)
        #title label
        titlelabel = tk.Label(tframelogin, text='Login to Teacher Canvas Account')
        titlelabel.grid(row=0, column=0)
        tframelogin.grid(row=0, column=0)
        #entries and labels
        usernamelabel = tk.Label(mframelogin, text='Username:')
        usernameentry = tk.Entry(mframelogin, bd=2)
        passwordlabel = tk.Label(mframelogin, text='Password:')
        passwordentry = tk.Entry(mframelogin, bd=2, show='*')
        usernamelabel.grid(row=0, column=0)
        usernameentry.grid(row=0, column=1)
        passwordlabel.grid(row=1, column=0)
        passwordentry.grid(row=1, column=1)
        mframelogin.grid(row=1, column=0)
        #button
        loginbutton = tk.Button(bframelogin, bd=2, text='Login', 
        command=lambda: self.__gen_course_menu(usernameentry.get(), passwordentry.get()))
        loginbutton.pack()
        bframelogin.grid(row=2, column=0)
        self.__login_menu.mainloop()

    def __gen_course_menu(self, username, password):
        try: 
            self.__canmanager.login(username, password)
        except Exception as e:
            self.__popup(str(e))
            return
        #we have now successfully logged in, and we grab courses
        course_menu = tk.Tk()
        tframecourse = tk.Frame(course_menu)
        bframecourse = tk.Frame(course_menu)
        titlelabel = tk.Label(tframecourse, text='Choose a Course')
        titlelabel.pack()
        tframecourse.grid(row=0, column=0)
        try:
            classes = self.__canmanager.get_classes()
        except Exception as e:
            self.__popup(str(e))
        buttons = []
        rowindex = 0
        keys = list(classes.keys())
        for kindex, key in enumerate(keys):
            button = tk.Button(bframecourse, text=key, bd=2)
            button.configure(command=lambda k=button['text']: self.__gen_assingment_menu(k, classes[k]))
            buttons.append(button)
            buttons[kindex].grid(row=rowindex, column=kindex%2)
            if kindex%2 == 1:
                rowindex+=1
        bframecourse.grid(row=1, column=0)
        self.__login_menu.destroy()
        course_menu.mainloop()

    def __gen_assingment_menu(self, coursename, courselink):
        try:
            coursename = str(coursename)
            courselink = str(courselink)
        except:
            pass
        try:
            assingments = self.__canmanager.get_assingments(courselink)
        except Exception as e:
            self.__popup(str(e))
            return
        #we only destroy assingment menu if it is already there
        assingment_menu = tk.Tk()
        tframeassingment = tk.Frame(assingment_menu)
        bframeassingment = tk.Frame(assingment_menu)
        titlelabel = tk.Label(tframeassingment, text='Choose an Assignment')
        titlelabel.pack()
        tframeassingment.grid(row=0, column=0)
        buttons = []
        rowindex = 0
        for kindex, key in enumerate(list(assingments.keys())):
            button = tk.Button(bframeassingment, text=key, bd=2)
            button.configure(command=lambda k=button['text']: self.__gen_curve_menu(courselink, k, assingments[k]))
            buttons.append(button)
            buttons[kindex].grid(row=rowindex, column=kindex%2)
            if kindex%2 == 1:
                rowindex += 1
        bframeassingment.grid(row=1, column=0)
        assingment_menu.mainloop()

    def __gen_curve_menu(self, courselink, assingmentname, assingmentlink):
        #we first generate roster
        try:
            self.__ros = self.__canmanager.get_roster(courselink, assingmentname, assingmentlink)
        except Exception as e:
            self.__popup(str(e))
        #make frames for the curve menu now
        self.__curve_menu = tk.Tk()
        tframecurve = tk.Frame(self.__curve_menu)
        bframecurve = tk.Frame(self.__curve_menu)
        tframecurve.pack()
        bframecurve.pack(side=tk.BOTTOM)
        titlelabel = tk.Label(tframecurve, text='Select Curve')
        titlelabel.pack()
        #buttons
        addcurvebutton = tk.Button(bframecurve, text='Add Curve', bd=2, command=lambda: self.__gen_plot('add_curve', assingmentname))
        idecurvebutton = tk.Button(bframecurve, text='Identity Curve', bd=2, command=lambda: self.__gen_plot('', assingmentname))
        mulcurvebutton = tk.Button(bframecurve, text='Multiply Curve', bd=2, command=lambda: self.__gen_plot('mult_curve', assingmentname))
        rootcurvebutton = tk.Button(bframecurve, text='Root Curve', bd=2, command=lambda: self.__gen_plot('root_curve', assingmentname))
        #grid buttons
        addcurvebutton.grid(row=0,column=0)
        idecurvebutton.grid(row=0,column=1)
        mulcurvebutton.grid(row=1,column=0)
        rootcurvebutton.grid(row=1,column=1)
        self.__curve_menu.mainloop()      

    def __popup(self, code):
        print(code)
        popup = tk.Tk()
        popuplabel = None
        try:
            code = str(code)
        except:
            code = ''
        
        popuplabel = tk.Label(popup, text=code)
        popuplabel.pack()
        popup.mainloop()
        
    def __gen_plot(self, curvename, assingmentname):
        stop = True
        if not isinstance(curvename, str):
            curvename = ''
        #first get dom, rawscores, and curvedscores
        self.__ros.set_curve(curvename)
        self.__dom = self.__ros.get_dom()
        self.__rawscores = self.__ros.get_rawscores()
        curvedscores = self.__ros.get_curvedscores()
        #we now make the menu for the plot
        self.__plot_menu = tk.Tk()
        frame1 = tk.Frame(self.__plot_menu)
        frame2 = tk.Frame(self.__plot_menu)
        frame3 = tk.Frame(self.__plot_menu)
        self.__frame4 = tk.Frame(self.__plot_menu)
        titlelabel = tk.Label(frame1, text='Plot for {} (Curve={})'.format(assingmentname, curvename))
        paramlabel = tk.Label(frame2, text='Parameter:')
        caplabel = tk.Label(frame2, text='Cap:')
        paramentry = tk.Entry(frame2, bd=2)
        capentry = tk.Entry(frame2, bd=2)
        updatebutton = ttk.Button(frame3, text='Update plot', command=lambda: self.__update(paramentry.get(),
        capentry.get()))

        #pack buttons and labels
        titlelabel.pack()
        frame1.grid(row=0, column=0)

        paramlabel.grid(row=0, column=0)
        paramentry.grid(row=0, column=1)
        caplabel.grid(row=1, column=0)
        capentry.grid(row=1, column=1)
        frame2.grid(row=1, column=0)

        updatebutton.pack(side=tk.BOTTOM, expand=True)
        frame3.grid(row=2, column=0)

        fig = Figure(figsize=(5,5), dpi=100)
        a = fig.add_subplot(111)
        a.plot(self.__dom, self.__rawscores)
        a.plot(self.__dom, curvedscores)

        #rawscores could be 0
        if len(self.__rawscores) > 0:
            if 100 < self.__rawscores[len(self.__rawscores)-1]:
                max = 1.1*self.__rawscores[len(self.__rawscores)-1]
            else:
                max = 110
            a.set_xlim([self.__dom[0],self.__dom[len(self.__dom)-1]])
            a.set_ylim([0, max])
        else:
            a.set_xlim([0,0])
            a.set_ylim([0,0])

        canvas = FigureCanvasTkAgg(fig, self.__frame4)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.__frame4.grid(row=3, column=0)

        self.__plot_menu.mainloop()
    
    def __update(self, param, cap):
        self.__ros.update_vars(param, cap)
        if self.__dom is None:
            self.__dom = self.__ros.get_dom()
        if self.__rawscores is None:
            self.__rawscores = self.__ros.get_rawscores()
        curvedscores = self.__ros.get_curvedscores()
        tempframe = tk.Frame(self.__plot_menu)
        fig = Figure(figsize=(5,5), dpi=100)
        a = fig.add_subplot(111)
        a.plot(self.__dom, self.__rawscores)
        a.plot(self.__dom, curvedscores)
        if 1 < curvedscores[len(curvedscores)-1]:
            max = curvedscores[len(self.__rawscores)-1]
        else:
            max = 1
        a.set_xlim([self.__dom[0],self.__dom[len(self.__dom)-1]])
        a.set_ylim([0, max])
        #a.axes([self.__dom[0],self.__dom[len(self.__dom)-1],0,max])
        canvas = FigureCanvasTkAgg(fig, tempframe)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.__frame4.destroy()
        self.__frame4 = tempframe
        self.__frame4.grid(row=3, column=0)


class CanvasScraper:
    #has username, password, session
    def __init__(self):
        self.__sess = requests.Session()
        self.__soupgrades = None
        #exceptions and links
        self.INVALIDLOGINEXCEPTION = Exception('Login failed: invalid username or password data.')
        self.INCORRECTLOGINEXCEPTION = Exception('Login failed: incorrect username or password.')
        self.INVALIDGRADELINKEXCEPTION = Exception('Fetching grades failed: invalid link.')
        self.INVALIDPOINTWORTHEXCEPTION = Exception('Getting roster failed: invalid point worth.')
        self.INVALIDASSINGMENTNAMEEXCEPTION = Exception('Getting roster failed: invalid assingment name.')

        self.MAINLINK = 'https://sequoia.instructure.com'
        self.LOGINLINK = 'https://sequoia.instructure.com/login/ldap'
        self.GRADELISTLINK = 'https://sequoia.instructure.com/grades'
        self.GETASSINGMENTSLINK = '/api/v1/courses/:course_id/assignments?per_page=10000'
        self.GETGRADESLINK = '/api/v1/courses/:course_id/gradebook_history/feed?assignment_id=x&per_page=10000'


    def login(self, username, password):
        try:
            username = str(username)
            password = str(password)
        except:
            raise self.INVALIDLOGINEXCEPTION
        
        souplogin = BeautifulSoup(self.__sess.get(self.LOGINLINK).content, 'html.parser').find('form').find_all('input')
        data = {}
        for u in souplogin:
            if u.has_attr('value'):
                data[u['name']] = u['value']
            else:
                if ('id' in u['name']):
                    data[u['name']] = username
                else:
                    data[u['name']] = password
        self.__sess.post(self.LOGINLINK, data)
        #we should now check if the login is valid
        self.__soupgrades = BeautifulSoup(self.__sess.get(self.GRADELISTLINK).content, 'html.parser')
        if '\"status\":\"unauthenticated\"' in self.__soupgrades.text:
            raise self.INCORRECTLOGINEXCEPTION

    def get_classes(self):
        #returns dictionary of names of classes to links
        classes = {}
        #get table from grades link, then iterate through
        gradetable = self.__soupgrades.find('table', class_ = 'teacher_grades')
        for courserow in gradetable.select('tr'):
            content = courserow.contents
            try:
                coursename = content[1].text
                coursepercent = content[3].text
                #should have grades in order to be valid
                if not 'no grades' in coursepercent:
                    classes[coursename] = '{}{}'.format(self.MAINLINK, content[1].find('a')['href'])
            except Exception as e:
                print(e)
        return classes

    def get_assingments(self, ind_class_link):
        #returns dictionary of assingments to their numbers
        assingmentsdict = {}
        #link is either actual link or just number
        if isinstance(ind_class_link, int):
            ind_class_link = str(ind_class_link)
        elif 'https' in ind_class_link:
            ind_class_link = ind_class_link[ind_class_link.index('s/') + 2: ind_class_link.index('/g')]
        ind_class_link = self.MAINLINK + self.GETASSINGMENTSLINK.replace(':course_id', ind_class_link)
        
        #we try to get the link
        try:
            assingmentscomplex = str(self.__sess.get(ind_class_link).content)
        except:
            raise self.INVALIDGRADELINKEXCEPTION
        numassingments = assingmentscomplex.count('e}')
        for index in range(numassingments):
            indcomplex = assingmentscomplex[assingmentscomplex.index('{'):assingmentscomplex.index('e}') + 2]
            #name then date
            assingmentname = indcomplex[indcomplex.index('\"name\":\"') + 8: indcomplex.index('\",\"submission_types\"')]
            try:
                assingmentdate = indcomplex[indcomplex.index('\"due_at\":\"') + 10: indcomplex.index('\"due_at\":\"')+20]
            except:
                assingmentdate = ''
            assingmentdate = CanvasScraper.date_format(assingmentdate)
            assingmentid = indcomplex[indcomplex.index('\"id\":') + 5: indcomplex.index(',\"description\"')]
            assingmentpoints = indcomplex[indcomplex.index('\"points_possible\":') + 18: indcomplex.index(',\"grading_type\"')]
            assingmentpoints = '({} pts.)'.format(assingmentpoints)
            assingmentsdict['{} {} {}'.format(assingmentname, assingmentdate, assingmentpoints)] = assingmentid
            #now need to trim the big string so we don't repeat
            assingmentscomplex = assingmentscomplex[assingmentscomplex.index('e}')+2:]
        return assingmentsdict
    
    def get_roster(self, course_link, assingment_name, assingment_link):
        #link is either an actual link, int, or string of an int
        try:
            assingment_name = str(assingment_name)
        except:
            raise self.INVALIDASSINGMENTNAMEEXCEPTION
        try:
            assingment_link = str(assingment_link)
        except:
            raise self.INVALIDGRADELINKEXCEPTION
        try:
            assingment_link = assingment_link[assingment_link.index('/assingments' + 12):]
        except:
            pass
        try:
            course_link = str(course_link)
        except:
            raise self.INVALIDGRADELINKEXCEPTION
        try:
            course_link = course_link[course_link.index('s/') + 2: course_link.index('/grades')]
        except:
            pass
        try:
            pointworth = float(assingment_name[assingment_name.rfind('(')+1: assingment_name.index(' pts.')])
            pointworth = int(pointworth)
        except:
            raise self.INVALIDPOINTWORTHEXCEPTION

        roster = AssingmentRoster(assingment_name, pointworth)
        
        #we now get all the grades for the roster, and then sort them out
        assingment_link = self.MAINLINK + self.GETGRADESLINK.replace('x', assingment_link).replace(':course_id', course_link)
        try:
            gradescomplex = str(self.__sess.get(assingment_link).content)
        except:
            raise self.INVALIDGRADELINKEXCEPTION
        numgrades = gradescomplex.count('\"}')
        for index in range(numgrades):
            indcomplex = gradescomplex[gradescomplex.index('{\"'): gradescomplex.index('\"}') + 2]
            score = indcomplex[indcomplex.index('\"score\":')+8: indcomplex.index(',\"submitted_at\"')]
            try:
                score = float(score)
            except:
                #not entetered into gradebook
                continue
            roster.add_assingment_grade(AssingmentGrade(score, pointworth))
            gradescomplex = gradescomplex[gradescomplex.index('\"}') + 2:]
        roster.order()
        return roster
            
    @staticmethod
    def date_format(date):
        try:
            return '({}/{}/{})'.format(date[date.index('-')+1:date.rfind('-')],
            date[date.rfind('-')+1:],
            date[0:date.index('-')])
        except:
            return ''

if __name__ == "__main__":
    p = PlotGui()

