#scans subreddit of AmITheAsshole to see if there is a correlation between
#length of the post

import matplotlib
matplotlib.use('TkAgg')
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import praw

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import time

class AssholeDataGrabber:

    def __init__(self):
        #data- list of tuples
            #each tuple: (post_id, postweight, titlelengthchars, postlengthwords, postlengthchars, aholerating)
            #ahole rating of 1.0 indicates asshole, -1.0 indicates not the asshole
        #r- reddit instance
        #sr- subreddit instance
        #feed- actual feed of posts, to be set later
        #startindex- index to start looking through fee
        #stopindex- index to stop looking through fee

        self.__data = []
        self.__r = praw.Reddit(client_id='*****', client_secret='*****',
        username='AssholeTallierBot', password='*****', user_agent='Asshole Tallier v1.0')
        self.__sr = self.__r.subreddit('AmItheAsshole')
        self.feed = None
        self.__startindex = 0
        self.__stopindex = 0

    def setfeed(self, feedname, limit, startindex=None, stopindex=None):
        #first handle the limit, then establish the feed
        try:
            limit = int(limit)
            if limit < 0:
                raise Exception
        except:
            limit = 10
        
        feedname = feedname.lower()
        if feedname == 'topnow':
            self.feed = self.__sr.top('now', limit=limit)
        elif feedname == 'topday':
            self.feed = self.__sr.top('day', limit=limit)
        elif feedname == 'topweek':
            self.feed = self.__sr.top('week', limit=limit)
        elif feedname == 'topmonth':
            self.feed = self.__sr.top('month', limit=limit)
        elif feedname == 'topyear':
            self.feed = self.__sr.top('year', limit=limit)
        elif feedname == 'topall':
            self.feed = self.__sr.top('all', limit=limit)
        elif feedname == 'new':
            self.feed = self.__sr.new(limit=limit)
        else:
            self.feed = self.__sr.hot(limit=limit)
        

        #we now deal with the startindex and stopindex
        try:
            startindex = int(startindex)
            stopindex = int(stopindex)
            if (stopindex >= limit):
                stopindex = limit
            if (startindex < 0):
                startindex = 0
            if (startindex > stopindex):
                raise Exception
        except:
            startindex = 0
            stopindex = limit
        self.__startindex = startindex
        self.__stopindex = stopindex
        
    def addall(self, weighcomments=True):
        if self.feed is None:
            return
        index = 0
        #self.addpost(self.__r.submission(id='c3t5vq'))
        for post in self.feed:
            if (index >= self.__startindex) and (index < self.__stopindex):
                print('Adding post {}/{}'.format(index+1, self.__stopindex - self.__startindex))
                try:
                    self.addpost(post, weighcomments)
                    print('         Now have {} posts.'.format(len(self.__data)))
                except:
                    print('                  Exception occurred.')
            index += 1

    def addpost(self, post, weighcomments=True, rankrange=20):
        #adds (post_id, post_weight, post_title_length, post_length_words, post_length_chars, aholerating),
        #if that post (found by id) is not in the list already and the post is valid
        #post is not valid if stickied, if META in title, or META in body

        #Before we start, we handle weighcomments and rankrange
        if not(weighcomments == True) and not(weighcomments == False):
            weighcomments = True
        if rankrange != 20:
            try:
                rankrange = int(rankrange)
                if rankrange < 3:
                     raise Exception
            except:
                rankrange = 20

        #First do id.
        datalist = []
        datalist.append(post.id)
        #If we already have this post, we return and do not add
        if self.contains(datalist[0]):
            return
        #If the post is stickied we return and do not add
        if post.stickied:
            return
        title = post.title.split()

        #Next do weight
        datalist.append(post.ups)

        #Next do titlelength
        #if the title contains 'META' we return and do not add
        for word in title:
            if word.upper() == 'META':
                return
        title = ' '.join(title)
        datalist.append(len(title))

        #Next do bodylengthwords, bodylengthchars
        postbody = post.selftext.split()
        #if the body contains 'META', we return and do not add
        for word in postbody:
            if word.upper() == 'META':
                return
        datalist.append(len(postbody))
        postbody = ' '.join(postbody)
        datalist.append(len(postbody))

        #next we calculate the aholerating, by weighing each comment (only if weighcomments True)
        aholerating = 0
        totalweight = 0
        comments = post.comments
        for comment in comments:
            try:
                #try block to catch more comments objects
                if comment.stickied:
                    continue
                rankingstring = ' '.join(comment.body.split()).upper()
                #only cut it off if the range is small enough
                if len(rankingstring) > rankrange:
                    rankingstring = rankingstring[0:rankrange]
                #now check about what the raw vote is
                vote = None
                if 'YTA' in rankingstring:
                    #NTA should also not be
                    if not ('NTA' in rankingstring):
                        vote = 1.0
                elif 'NTA' in rankingstring:
                    vote = -1.0
                else:
                    continue
                #now do weight work
                if weighcomments:
                    commentweight = comment.ups
                    if commentweight <= 0:
                        continue
                    aholerating += (vote)*(commentweight)
                    totalweight += commentweight
                else:
                    aholerating += vote
                    totalweight += 1
            except:
                #more comments object found
                continue
        datalist.append(aholerating/totalweight)

        #we now normalize all of the elements and return the tuple
        #lengthtitlechars should be to nearest 10, lengthbodywords to nearest 10, lengthbodychars to nearest 100
        try:
            datalist[2] = 10*int(datalist[2]/10)
            datalist[3] = 10*int(datalist[3]/10)
            datalist[4] = 100*int(datalist[4]/100)
        except:
            #this is a pretty bad error, means did not work, so we return and do not add
            return

        #insert at correct index
        self.__data.insert(self.getinsertindex(datalist[0]), tuple(datalist))
        
    def contains(self, postid):
        #searches its list for a post id
        #returns True if it is there, False if not
        #later will be a binary search, but not yet
        postid = postid.lower()
        for tupelement in self.__data:
            try:
                if tupelement[0].lower() == postid:
                    return True
            except:
                continue
        return False

    def getinsertindex(self, postid):
        #returns the index where a post's data should be inserted so that it is still in order...
        #will later be binary, but not now
        
        postid = postid.lower()
        for index, tupelement in enumerate(self.__data):
            try:
                if tupelement[0].lower() > postid:
                    return index
            except:
                pass
        return len(self.__data)

    def tempset(self, data):
        self.__data = data

    def write(self, path):
        #deal with exceptions later
        with open(path, 'w') as s:
            for tupelement in self.__data:
                line = ''
                for datum in tupelement:
                    line += str(datum) + ' '
                line += '\n'
                s.write(line)
    
    def read(self, path):
        #deal with exceptions later
        self.__data = []
        with open(path, 'r') as r:
            lines = r.readlines()
            for line in lines:
                tobeadded = []
                try:
                    tobeadded.append(line[0: line.index(' ')])
                    line = line[line.index(' ')+1:]
                    tobeadded.append(int(line[0: line.index(' ')]))
                    line = line[line.index(' ')+1:]
                    tobeadded.append(int(line[0: line.index(' ')]))
                    line = line[line.index(' ')+1:]
                    tobeadded.append(int(line[0: line.index(' ')]))
                    line = line[line.index(' ')+1:]
                    tobeadded.append(int(line[0: line.index(' ')]))
                    line = line[line.index(' ')+1:]
                    tobeadded.append(float(line[0: line.index(' ')]))
                    self.__data.append(tuple(tobeadded))
                except Exception as e:
                    print(e)
                    continue

class AssholeGui:
    def __init__(self):
        self.__datagrabber = AssholeDataGrabber()
        #set up main window
        self.__mainwindow = tk.Tk()

        framezero = tk.Frame(self.__mainwindow)
        titlelabel = tk.Label(framezero, text='Asshole Scanner')
        titlelabel.pack()
        framezero.grid(row=0, column=0)

        frameone = tk.Frame(self.__mainwindow)
        helpbutton = tk.Button(frameone, text='Help', bd=2, command=lambda: self.help())
        readbutton = tk.Button(frameone, text='Read from File', bd=2, command=lambda: self.readfile())
        helpbutton.grid(row=0, column=0)
        readbutton.grid(row=0, column=1)
        frameone.grid(row=1, column=0)

        frametwo = tk.Frame(self.__mainwindow)
        feedvar = tk.StringVar(frametwo)
        feedvar.set('Top of All Time')
        feedoptions = tk.OptionMenu(frametwo, feedvar, 'Top of All Time', 'Top of Past Year', 'Top of Past Month',
        'Top of Past Week', 'Top of Past Day', 'Top Now', 'Hot', 'New')
        feedoptions.pack()
        frametwo.grid(row=2, column=0)

        framethree = tk.Frame(self.__mainwindow)
        weighposts = tk.BooleanVar()
        weighposts.set(True)
        weighcomments = tk.BooleanVar()
        weighcomments.set(True)
        weighpostscheck = tk.Checkbutton(framethree, text='Weigh posts by karma', variable=weighposts)
        weighcommentscheck = tk.Checkbutton(framethree, text='Weigh comments by karma', variable=weighcomments)
        weighpostscheck.grid(row=0, column=0)
        weighcommentscheck.grid(row=0, column=1)
        framethree.grid(row=3, column=0)

        framefour = tk.Frame(self.__mainwindow)
        limitlabel = tk.Label(framefour, text='Max limit: ')
        limitentry = tk.Entry(framefour, bd=2)
        limitlabel.grid(row=0, column=0)
        limitentry.grid(row=0, column=1)
        framefour.grid(row=4, column=0)

        framefive = tk.Frame(self.__mainwindow)
        addbutton = tk.Button(framefive, text='Add Posts...', bd=2, function=lambda: self.addposts(feedvar.get(), 
        limitentry.get(), weighposts.get(), weighcomments.get()))
        graphbutton = tk.Button(framefive, text='Graph Data', bd=2)
        savebutton = tk.Button(framefive, text='Save Data', bd=2)
        addbutton.grid(row=0, column=0)
        graphbutton.grid(row=0, column=1)
        savebutton.grid(row=0, column=2)
        framefive.grid(row=5, column=0)

        self.__mainwindow.mainloop()

    def help(self):
        helpmenu = tk.Tk()
        helplabel = tk.Label(helpmenu, text='Read data from a file to load in previous save data.\nSelect which feed to grab posts from.\nSelect options for weighing posts and comments.\nFetch the data.\nThen, save.')
        helplabel.pack()
        helpmenu.mainloop()

    def readfile(self):
        filename = tk.filedialog.askopenfilename(initialdir=os.getcwd(), title='Select file to open', filetypes=(('Text files', '*.txt'),('Binary files', '*.bin')))
        self.__datagrabber.read(filename)

    def addposts(self, feedname, limit, weighposts, weighcomments):
        pass

if __name__ == "__main__":
    a = AssholeGui()

