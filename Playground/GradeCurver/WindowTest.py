import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import tkinter as tk
from tkinter import ttk

class PlotWindow(tk.Frame):
    def __init__(self, dom, rawscores, curvedscores, curvename=None):
        #exception checking: should be 3 lists of equal size of doubles
        if not isinstance(dom, list) or not isinstance(rawscores, list) or not isinstance(curvedscores, list):
            raise Exception('Invalid domain and scores given: not all lists.')
        if not(len(dom) == len(rawscores)) or not(len(rawscores) == len(curvedscores)):
            raise Exception('Invalid domain and scores given: not same size.')
        
        
        
        self.__master = tk.Tk()

        tk.Frame.__init__(self.__master)

        frame1 = tk.Frame(self.__master)
        frame2 = tk.Frame(self.__master)
        frame3 = tk.Frame(self.__master)
        frame4 = tk.Frame(self.__master)
        titlelabel = tk.Label(frame1, text='Individual plot for {}'.format(curvename))
        paramlabel = tk.Label(frame2, text='Parameter:')
        caplabel = tk.Label(frame2, text='Cap:')
        paramentry = tk.Entry(frame2, bd=2)
        capentry = tk.Entry(frame2, bd=2)
        updatebutton = ttk.Button(frame3, command=lambda: self.update())

        #pack buttons and labels
        frame1.pack()
        frame2.pack(side=tk.BOTTOM)
        frame3.pack(side=tk.BOTTOM)
        titlelabel.pack()

        paramlabel.grid(row=0, column=0)
        paramentry.grid(row=0, column=1)
        caplabel.grid(row=1, column=0)
        capentry.grid(row=1, column=1)

        updatebutton.pack(expand=True)

        self.__master.mainloop()

        

    def update(self):
        pass


class PlotW:
    def __init__(self, dom, rawscores, curvedscores, curvename=None):
        #exception checking: should be 3 lists of equal size of doubles
        if not isinstance(dom, list) or not isinstance(rawscores, list) or not isinstance(curvedscores, list):
            raise Exception('Invalid domain and scores given: not all lists.')
        if not(len(dom) == len(rawscores)) or not(len(rawscores) == len(curvedscores)):
            raise Exception('Invalid domain and scores given: not same size.')
        if not isinstance(curvename, str):
            curvename = ''
        
        self.__master = tk.Tk()
        self.__dom = dom
        self.__rawscores = rawscores

        frame1 = tk.Frame(self.__master)
        frame2 = tk.Frame(self.__master)
        frame3 = tk.Frame(self.__master)
        self.__frame4 = tk.Frame(self.__master)
        titlelabel = tk.Label(frame1, text='Individual plot {}'.format(curvename))
        paramlabel = tk.Label(frame2, text='Parameter:')
        caplabel = tk.Label(frame2, text='Cap:')
        paramentry = tk.Entry(frame2, bd=2)
        capentry = tk.Entry(frame2, bd=2)
        updatebutton = ttk.Button(frame3, text='Update plot', command=lambda: self.update())

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
        a.plot(dom, rawscores)
        a.plot(dom, curvedscores)

        canvas = FigureCanvasTkAgg(fig, self.__frame4)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.__frame4.grid(row=3, column=0)

        self.__master.mainloop()

    def update(self):
        tempframe = tk.Frame(self.__master)
        fig = Figure(figsize=(5,5), dpi=100)
        a = fig.add_subplot(111)
        a.plot([1,2,3,4], [1,2,3,4])
        a.plot([1,2,3,4],[1,4,6,8])
        canvas = FigureCanvasTkAgg(fig, tempframe)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.__frame4.destroy()
        self.__frame4 = tempframe
        self.__frame4.grid(row=3, column=0)
        

if __name__ == "__main__":
    p = PlotW([1,2,3,4,5,6,7,8], [1,2,3,4,5,6,7,8], [5,6,1,3,8,9,3,5])
