import praw

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import matplotlib.pyplot as plt
import time

class GUITest1:
    def __init__(self):
        main = tk.Tk()
        main.minsize(200, 200)
        frame1 = tk.Frame(main, width=200, height=100)
        frame1.pack_propagate(0)
        frame1.grid(row=0, column=0)
        frame2 = tk.Frame(main, width=200, height=100)
        frame2.pack_propagate(0)
        frame2.grid(row=1, column=0)
        l = tk.Label(frame1, text='This is the main window')
        l.pack(fill=tk.BOTH, expand=1)
        b = tk.Button(frame2, text='Gen New Menu', command=lambda: self.genwindow(main))
        b.pack(fill=tk.BOTH, expand=1)

        main.mainloop()
    
    def genwindow(self, main):
        win = tk.Toplevel(main)
        win.minsize(200, 200)
        frame1 = tk.Frame(win, width=200, height=200)
        frame1.pack_propagate(0)
        frame1.grid(row=0, column=0)
        l = tk.Label(frame1, text='This is the popup window')
        l.pack(fill=tk.BOTH, expand=1)
        win.update()
        main.update()
        win.mainloop()

if __name__ == "__main__":
    g = GUITest1()