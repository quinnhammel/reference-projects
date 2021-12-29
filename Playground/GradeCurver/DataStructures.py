import numpy
import os
import tkinter as tk
import matplotlib.pyplot as plt
import time
class AssingmentGrade:
    def __init__(self, actualpoints, totalpointsposs):
        if isinstance(totalpointsposs, int) and (totalpointsposs > 0):
            #must be an int number of points, and cannot be 0 because of division
            self.totalpointsposs = totalpointsposs
        else:
            self.totalpointsposs = None
        if isinstance(actualpoints, int) and (actualpoints >= 0):
            #must be an int number of points, can be 0 but not negative
            self.actualpoints = actualpoints
        else:
            self.actualpoints = None

class AssingmentRoster:
    #list of assingment grades
    #has a curve that it uses
    #has cap for the grade
    #has a param for the grade


    def __init__(self, name, totalpoints, curve_name=None, cap=None, param=None):
        self.__grade_list = []
        if isinstance(name, str):
            self.name = name
        else:
            self.name = 'Assingment Roster'
        try:
            totalpoints = int(totalpoints)
        except:
            totalpoints = 1
        self.totalpointsposs = totalpoints
        self.set_curve(curve_name)
        self.set_cap(cap)
        self.set_param(param)
    
    def add_assingment_grade(self, assingment_grade):
        if isinstance(assingment_grade, AssingmentGrade):
            if len(self.__grade_list) > 0:
                #need to make sure that it is the same total points
                if assingment_grade.totalpointsposs == self.totalpointsposs:
                    self.__grade_list.append(assingment_grade)
            else:
                self.__grade_list.append(assingment_grade)

    def get_curved_score(self, assingment_grade):
        #either an index or an actual assingment grade
        if isinstance(assingment_grade, int):
            #check valid index
            if (assingment_grade >= 0) and (assingment_grade < len(self.__grade_list)):
                assingment_grade = self.__grade_list[assingment_grade]
                return self.__curve_func(assingment_grade.actualpoints/(assingment_grade.totalpointsposs+0.0))
        elif isinstance(assingment_grade, AssingmentGrade):
            if assingment_grade in self.__grade_list:
                return self.__curve_func(assingment_grade.actualpoints/(assingment_grade.totalpointsposs+0.0))
        return -1

    def order(self):
        self.__grade_list.sort(key=lambda ag: ag.actualpoints)

    def set_curve(self, curve_name):
        if isinstance(curve_name, str):
            curve_name = curve_name.lower()
            if curve_name == 'root_curve':
                self.__curve_func = self.root_curve
                self.set_param(0.5)
                return
            elif curve_name == 'mult_curve':
                self.__curve_func = self.mult_curve
                self.set_param(1)
                return
            elif curve_name == 'add_curve':
                self.__curve_func = self.add_curve
                self.set_param(0)
                return
        #default
        self.__curve_func = self.identity_curve
        self.__param = 1.0

    def set_param(self, param):
        #later can add limits depending on the curve
        try:
            param = float(param)
            self.__param = param
        except:
            return

    def set_cap(self, cap):
        try:
            cap = float(cap)
            self.__cap = cap
        except:
            self.__cap = 10000.0

    #curves
    def identity_curve(self, score):
        try:
            score = float(score)
        except Exception as e:
            return -1
        try:
            self.__cap = float(self.__cap)
        except:
            self.__cap = 10000.0
    
        if score < self.__cap:
            return score
        return self.__cap

    def root_curve(self, score):
        try:
            score = float(score)
        except:
            return -1
        try:
            self.__param = float(self.__param)
        except:
            self.__param = 0.5
        try:
            self.__cap = float(self.__cap)
        except:
            self.__cap = 10000.0
        
        cscore = score**self.__param
        if cscore < self.__cap:
            return cscore
        return self.__cap

    def mult_curve(self, score):
        try:
            score = float(score)
        except:
            return -1
        try:
            self.__param = float(self.__param)
        except:
            self.__param = 1.0
        try:
            self.__cap = float(self.__cap)
        except:
            self.__cap = 10000.0
        
        cscore = self.__param*score
        if cscore < self.__cap:
            return cscore
        return self.__cap

    def add_curve(self, score):
        try:
            score = float(score)
        except:
            return -1
        try:
            self.__param = float(self.__param)
        except:
            self.__param = 0.0
        try:
            self.__cap = float(self.__cap)
        except:
            self.__cap = 10000.0

        cscore = score + self.__param
        if cscore < self.__cap:
            return cscore
        return self.__cap

    #taking input from a textfile
    def read_from_text(self, path=None):
        default = '~/Playground/GradeCurver/assingment_input.txt'
        self.__grade_list = []

        if (not isinstance(path, str)) or not (os.path.isfile(path)):
            #now need to check if the default is there or not
            if not os.path.isfile(default):
                return
            path = default
        with open(path, 'r') as f:
            lines = f.readlines()
        #find total from the top line
        try:
            line = lines[0]
            totalpointsposs = int(line[line.index('<') + 1: line.index('>')])
            del(lines[0])
        except:
            raise Exception('Invalid file formatting: <total> not found on line 1.')
        
        for line in lines:
            try:
                actualpoints = int(line)
            except:
                #first try to deal with spaces and stuff
                try:
                    line = ' '.join(line.split())
                    if line == '':
                        continue
                    actualpoints = int(line)
                except:
                    raise Exception('Invalid file formatting: could not read an element in line.')

            self.add_assingment_grade(AssingmentGrade(actualpoints, totalpointsposs))
        self.order()

    #plotting both the normal and the curved
    def plot(self):
        self.order()
        plt.ion()
        xcoords = []
        for index in range(len(self.__grade_list)):
            xcoords.append(index + 1)
        normgrades = []
        curvegrades = []
        for grade in self.__grade_list:
            normgrades.append(grade.actualpoints/self.totalpointsposs)
            curvegrades.append(self.get_curved_score(grade))
        plt.plot(xcoords, normgrades, 'ko', label='Raw Score')
        plt.plot(xcoords, curvegrades, 'ro', label='Curved Score')
        if not (self.__cap == 10000.0):
            plt.axis([1,len(self.__grade_list)+1, 0, self.__cap])
        else:
            plt.axis([1, len(self.__grade_list) + 1, 0, 1.0])
        plt.title('{} ({} points)'.format(self.name, self.totalpointsposs))
        plt.draw()

    def close(self):
        plt.clf()
        plt.close()

    #running function
    def run(self):
        #creating a root window
        root = tk.Tk()
        #top frame and bottom frame
        topframe = tk.Frame(root)
        topframe.pack()
        bottomframe = tk.Frame(root)
        bottomframe.pack(side=tk.BOTTOM)
        #button creations (initially for the curves, and for reading in data, and plot), and labels and entries for params
        import_from_text_button = tk.Button(topframe, text='Read from Text', command=lambda: self.read_from_text())
        plot_button = tk.Button(topframe, text='Plot Curve', command=lambda: self.plot())
        param_label = tk.Label(topframe, text='Parameter:')
        cap_label = tk.Label(topframe, text='Cap:')
        param_entry = tk.Entry(topframe, bd=2)
        cap_entry = tk.Entry(topframe, bd=2)
        #now grid top buttons into frame
        import_from_text_button.grid(row=0, column=0)
        plot_button.grid(row=0, column=1)
        param_label.grid(row=1, column=0)
        param_entry.grid(row=1, column=1)
        cap_label.grid(row=2, column=0)
        cap_entry.grid(row=2, column=1)
        #now create curve selecting buttons into bottom frame
        add_curve_button = tk.Button(bottomframe, text='Addition Curve', command=lambda: self.set_curve('add_curve'))
        identity_curve_button = tk.Button(bottomframe, text='Identity Curve', command=lambda: self.set_curve('identity_curve'))
        mult_curve_button = tk.Button(bottomframe, text='Multiple Curve', command=lambda: self.set_curve('mult_curve'))
        root_curve_button = tk.Button(bottomframe, text='Root Curve', command=lambda: self.set_curve('root_curve'))
        #now grid curve selecting buttons
        add_curve_button.grid(row=0, column=0)
        identity_curve_button.grid(row=0, column=1)
        mult_curve_button.grid(row=1, column=0)
        root_curve_button.grid(row=1, column=1)
        #main loop
        root.mainloop()

