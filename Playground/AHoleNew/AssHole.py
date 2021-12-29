import praw

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from math import log
import matplotlib
matplotlib.use('TkAgg')
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time
import os.path

#class to store data about posts that are scraped from r/AmITheAsshole
class PostRank:
    '''
    Variables:
        id: post id
        title_clength: character length of title of post
        body_wlength: word length of body of post
        body_clength: character length of body of post
        rank_weighc: asshole rank (1.0=asshole, -1.0=not asshole) calculated weighing comments by karma
        rank_unweighc: asshole rank not weighing
        postweight: karma weight of post
        stringinput: string written that can then be read into an object
    Methods:
        setvars: takes in kwargs and sets all necessary variables (including stringinput, which will take in a string
            from a save file and set variables based on that)
        tostring: returns string used to write down save file
    '''
    def __init__(self, **kwargs):
        #default
        self.id = None
        self.title_clength = None
        self.body_wlength = None
        self.body_clength = None
        self.rank_weighc = None
        self.rank_unweighc = None
        self.postweight = None
        #set variables now
        self.setvars(**kwargs)
        
    #method to set the variables
    def setvars(self, **kwargs):
        for key, value in kwargs.items():
            if key == 'stringinput':
                #reading in string, get all pieces then recursively call this function
                #split into parts and format the string
                value = value.split(', ')
                try:
                    #cut off the '\n' that should be at the end of the string
                    value[-1] = value[-1][0: value[-1].index('\n')]
                except:
                    #invalid string fed in
                    raise Exception('Invalid stringinput (no \'\\n\' found at end).')

                #we now make a new kwargs to re-call setvars with the correct info
                newkwargs = {}
                for snippet in value:
                    #grab the key (k) and value (v) for the snippet and add them to newkwargs
                    try:
                        k = snippet[0: snippet.index('(')]
                    except:
                        raise Exception('Invalid stringinput (no \'(\' found in snippet)')
                    try:
                        v = snippet[snippet.index('(') + 1: snippet.index(')')]
                    except:
                        raise Exception('Invalid stringinput (no \')\' found).')
                    #need to recast, depending on k
                    if k == 'title_clength' or k == 'body_wlength' or k == 'body_clength':
                        #deal with None exception
                        if v == '':
                            v = None
                        else:
                            try:
                                v = int(v)
                            except:
                                raise Exception('Invalid stringinput (expected int not found).')
                    elif k == 'rank_weighc' or k == 'rank_unweighc' or k == 'postweight':
                        #deal with None exception
                        if v == '':
                            v = None
                        else:
                            try:
                                v = float(v)
                            except:
                                raise Exception('Invalid stringinput (expected float not found).')
                    newkwargs[k] = v
                #make kwargs None so no more setting
                kwargs = None
                #call back now
                self.setvars(**newkwargs)
            elif key == 'id':
                #id is just a simple str
                if isinstance(value, str):
                    self.id = value
            elif key == 'title_clength':
                #title_clength should be a nonnegative int
                if isinstance(value, int) and (value >= 0):
                    self.title_clength = value
            elif key == 'body_wlength':
                #body_wlength should be a nonnegative int
                if isinstance(value, int) and (value >= 0):
                    self.body_wlength = value
            elif key == 'body_clength':
                #body_clength should be a nonnegative int
                if isinstance(value, int) and (value >= 0):
                    self.body_clength = value
            elif key == 'rank_weighc':
                #rank_weighc should be a float (or int) in [-1.0, 1.0]
                if (isinstance(value, int) or isinstance(value, float)) and (value >= -1.0 and value <= 1.0):
                    self.rank_weighc = value
            elif key == 'rank_unweighc':
                #rank_weighc should be a float (or int) in [-1.0, 1.0]
                if (isinstance(value, int) or isinstance(value, float)) and (value >= -1.0 and value <= 1.0):
                    self.rank_unweighc = value
            elif key == 'postweight':
                #postweight should be a nonnegative int (or float)
                if (isinstance(value, int) or isinstance(value, float)) and (value >= 0):
                    self.postweight = value
        
    #method to return string to be written in file
    def tostring(self):
        #will be id(id#), title_clength(length#),..., postweight(postweight#)\n
        output = ''
        #any property that is None is written as ''
        if self.id is None:
            output += 'id(), '
        else:
            output += 'id({}), '.format(self.id)

        if self.title_clength is None:
            output += 'title_clength(), '
        else:
            output += 'title_clength({}), '.format(str(self.title_clength))

        if self.body_wlength is None:
            output += 'body_wlength(), '
        else:
            output += 'body_wlength({}), '.format(str(self.body_wlength))

        if self.body_clength is None:
            output += 'body_clength(), '
        else:
            output += 'body_clength({}), '.format(str(self.body_clength))

        if self.rank_weighc is None:
            output += 'rank_weighc(), '
        else:
            output += 'rank_weighc({}), '.format(str(self.rank_weighc))

        if self.rank_unweighc is None:
            output += 'rank_unweighc(), '
        else:
            output += 'rank_unweighc({}), '.format(str(self.rank_unweighc))

        if self.postweight is None:
            output += 'postweight()\n'
        else:
            output += 'postweight({})\n'.format(str(self.postweight))

        return output


        

class DataGrabber:
    '''
    Variables:
        __r: reddit instance
        __sr: subreddit instance
        __feed: the specific feed
        __feedlength: the number of posts in the feed.
        __data: list of PostRank objects
        __totalvar: stringvar that keeps track of the total number of posts in data
        MAGICWEIRDTOLERANCE: magic number for the tolerance it has of weird comments (NAH, ESH, INFO)
    Methods:
        __init__: sets up DataGrabber and establishes subreddit
        __setfeed(self, feedname, limit): sets the feed. Limit default is 10. Also, sets __feedlength to 
            limit if limit <= 200, otherwise __feedlength will be set in __initializebar
        __addpost(self, post, rankrange=20): backend function to add a single post 
            (will not add if it should not be added). rankrange is how much of each comment to scan for ranking.
            Uses __insertindex
        __insertindex(id): takes in id and finds index to insert it at. Will return -1 if the post is a repeat.
            #TODO: make binary, not linear.
        __write(self, path): backend method that writes save info to a file, will be *.txt or *.bin
        __read(self, path): backend method that reads from a save file, will be *.txt or *.bin.
        run(self): prompts user asking if they want to read a save file. Then, launches main menu.
        __genmainmenu(self): creates main menu, which lets the user choose the feed and either scrape or plot.
        __startscrapesession(self, mainmenu, feedname, limit, startbutton): gets called by scrapebutton in mainmenu, 
            starts scraping and updates user on progress (calls __initializebar)
        __initializebar(self, mainmenu, feedname, limit): called if __feedlength == None, because we need to see
            how many posts are actually in __feed by going through and counting. Generates a progress bar for the
            intializing to coomfort user
        __savefile(self, mainmenu): called by the save button, prompts user to save file as *.txt or *.bin.
        __gen_plot_options(self, mainmenu): called by the plot button, generates menu to get options from user
            about how to plot
        __createplots(self, mainmenu, weighposts, weighcomments, rawplot): called by the Generate Plot button in the 
            plot options window. Weighposts determines whether to weigh posts, weigh comments is similar.
            rawplot overrides these and if True will generate a simple plot with all the points and no smoothing.
    '''
    def __init__(self):
        self.__r = praw.Reddit(client_id='*****', client_secret='*****',
        username='AssholeTallierBot', password='*****', user_agent='Asshole Tallier v1.0')

        self.__sr = self.__r.subreddit('AmItheAsshole')
        self.__feed = None
        self.__feedlength = None
        self.__data = []
        self.__totalvar = None
        self.MAGICWEIRDTOLERANCE = 0.3

    #method to set feed (hot, new, etc)
    def setfeed(self, feedname, limit):
        #first handle the limit, then establish the feed
        try:
            limit = int(limit)
            if limit < 0:
                raise Exception
        except:
            limit = 10
        
        feedname = feedname.lower()
        if feedname == 'top of hour':
            self.__feed = self.__sr.top('hour', limit=limit)
        elif feedname == 'top of day':
            self.__feed = self.__sr.top('day', limit=limit)
        elif feedname == 'top of week':
            self.__feed = self.__sr.top('week', limit=limit)
        elif feedname == 'top of month':
            self.__feed = self.__sr.top('month', limit=limit)
        elif feedname == 'top of year':
            self.__feed = self.__sr.top('year', limit=limit)
        elif feedname == 'top of all time':
            self.__feed = self.__sr.top('all', limit=limit)
        elif feedname == 'new':
            self.__feed = self.__sr.new(limit=limit)
        else:
            self.__feed = self.__sr.hot(limit=limit)
        
        
        if limit <= 200:
            self.__feedlength = limit
    
    #method to add a single post
    def addpost(self, post, rankrange=20):
        #post must be valid to be added
        #valid means not in the list, not stickied, has weight, and does not have 'META' in title or body
        #method checks this throughout because otherwise more requests must be made and it would take too long

        #deal with rankrange, which dictates how much of each comment to look at
        if not isinstance(rankrange, int) or rankrange < 3:
            rankrange = 20
    
        #make kwargs for creating a PostRank object later
        kwargs = {}
    
        #first add id to kwargs
        try:
            kwargs['id'] = post.id
        except:
            raise Exception('Invalid post feed to addpost (no id).')
        #VALIDITY CHECK: post must not be in data already
        #find insertindex, if it is -1 then it is already contained in __data
        insertindex = self.insertindex(kwargs['id'])
        if insertindex == -1:
            return
    
        #next add postweight to kwargs
        try:
            kwargs['postweight'] = post.ups
        except:
            raise Exception('Invalid post feed to addpost (no ups).')
        #VALIDITY CHECK: post must have weight to be considered
        if kwargs['postweight'] <= 0:
            return

        #VALIDITY CHECK: post must not be stickied to be considered
        if post.stickied:
            return
        
        #next add title_clength
        try:
            title = post.title.upper().split()
        except Exception as e:
            raise Exception('Invalid post feed to addpost (no title)... possible formatting exception:\n{}'.format(e))
        #VALIDITY CHECK: post must not have 'META' in title
        for word in title:
            if word == 'META':
                return
        #join title to get title_clength
        title = ' '.join(title)
        kwargs['title_clength'] = len(title)

        #next add body_wlength
        try:
            body = post.selftext.upper().split()
        except Exception as e:
            raise Exception('Invalid post feed to addpost (no body)... possible formatting exception:\n{}'.format(e))
        #VALIDITY CHECK: post must not have 'META' in body
        for word in body:
            if word == 'META':
                return
        kwargs['body_wlength'] = len(body)

        #next add body_clength
        body = ' '.join(body)
        kwargs['body_clength'] = len(body)


        #Now, we have to calculate the rank of the post
        #rank_w weights the comments by karma, rank_u treats all evenly (karma must be nonnegative though)
        #edgevotes is the number of votes that are ESH, NAH, or INFO
        rank_w = 0.0
        totalcommentkarma = 0

        rank_uw = 0.0
        totalcomments = 0
        comments = post.comments

        edgevotes = 0

        for comment in comments:
            #the following try block will catch MoreComments objects, which should not be counted
            try:
                #do not count stickied comments or comments with no ups
                if comment.stickied:
                    continue
                commentweight = comment.ups
                if commentweight <= 0.0:
                    continue
                
                commentbody = ' '.join(comment.body.split()).upper()
                #only cut off the commentbody if it is longer than rankrange
                if len(commentbody) > rankrange:
                    commentbody = commentbody[0:rankrange]
                
                #now check about what the vote is
                vote = None
                #can only have one of the ranking acronyms in beginning
                if 'YTA' in commentbody and not ('NTA' in commentbody or 'ESH' in commentbody or 'NAH' in commentbody or 'INFO' in commentbody):
                    vote = 1.0
                elif 'NTA' in commentbody and not ('YTA' in commentbody or 'ESH' in commentbody or 'NAH' in commentbody or 'INFO' in commentbody):
                    vote = -1.0
                elif 'ESH' in commentbody or 'NAH' in commentbody or 'INFO' in commentbody:
                    edgevotes += 1
                else:
                    continue

                #now do weight work
                rank_w += vote*commentweight
                totalcommentkarma += commentweight

                rank_uw += vote
                totalcomments += 1
            except:
                #more comments object found
                continue

        #check if too many edge votes
        if edgevotes > int(self.MAGICWEIRDTOLERANCE*totalcomments):
            return

        #normalize the rankings and add them to kwargs
        #exception is if totalcommentkarma == 0 or totalcomments == 0
        if totalcomments == 0 or totalcommentkarma == 0:
            return
        kwargs['rank_weighc'] = rank_w/(totalcommentkarma + 0.0)
        kwargs['rank_unweighc'] = rank_uw/(totalcomments + 0.0)

        #add new PostRank object into __data at right position
        self.__data.insert(insertindex, PostRank(**kwargs))

    #method to find the index to insert a new PostRank object at            
    def insertindex(self, id):
        #TODO: use binary later
        if not isinstance(id, str):
            raise Exception('Invalid id feed to insertindex (not a str).')
        #list will be in order already
        for i in range(len(self.__data)):
            pr = self.__data[i]
            #if id is less than pr.id we are before it
            #if equal, there is a duplicate
            #otherwise we have just passed it, return i
            if id == pr.id:
                #duplicate, so should not be inserted, return -1
                return -1
            elif id < pr.id:
                return i
        #return index at end by default
        return len(self.__data)

    #method to write data to a file
    def write(self, path):
        #TODO: make a check for path that makes sure it is legitimate
        #TODO: does path have the name of the save in it? assume so for now.
        if not isinstance(path, str):
            raise Exception('Invalid path feed to write (not a str).')
        
        with open(path, 'w') as f:
            for pr in self.__data:
                f.write(pr.tostring())

    #method to read data from a file
    def read(self, path):
        #TODO: same path work as write
        if not isinstance(path, str):
            raise Exception('Invalid path feed to read (not a str).')
        
        with open(path, 'r') as f:
            lines = f.readlines()
        for line in lines:
            try:
                pr = PostRank(stringinput=line)
            except Exception as e:
                print(e)
                continue
            insertindex = self.insertindex(pr.id)
            #only insert if not a duplicate
            if not (insertindex == -1):
                self.__data.insert(insertindex, pr)
        
    #method to initialize the progress bar for addall (just finds out how many posts in feed)
    def intializebar(self, mainmenu, feedname, limit):
        #frame1 is a simple label, frame2 has a progress bar
        ibwindow = tk.Toplevel(mainmenu)
        ibwindow.minsize(width=300, height=120)
        frame1 = tk.Frame(ibwindow, width=300, height=100)
        frame1.pack_propagate(0)
        frame1.grid(row=0, column=0)
        frame2 = tk.Frame(ibwindow, width=300, height=20)
        frame2.pack_propagate(0)
        frame2.grid(row=1, column=0)

        initlabel = tk.Label(frame1, text='Initializing scrape session...')
        initlabel.pack(fill=tk.BOTH, expand=1)

        progressbar = ttk.Progressbar(frame2, orient='horizontal')
        progressbar.pack(fill=tk.BOTH, expand=1)
        progressbar['maximum'] = 100000

        #we can now begin to go through all the posts
        counter = 0
        ibwindow.update()
        time.sleep(.2)
        for post in self.__feed:
            counter += 1
            progressbar['value'] = int(progressbar['value'] + (progressbar['maximum']/limit))
            ibwindow.update()
        self.__feedlength = counter
        #finish up progress bar
        dist = int(progressbar['maximum'] - progressbar['value'])
        if dist < 1:
            dist = 1
        for i in range(20):
            time.sleep(0.0005)
            progressbar['value'] = int(progressbar['value'] + dist)
            ibwindow.update()
        progressbar['value'] = progressbar['maximum']
        ibwindow.update()
        time.sleep(0.1)
        ibwindow.destroy()

        #restore feed
        self.setfeed(feedname, limit)

    

    #method to open the program and prompt to read in a savefile
    def startgui(self):
        startwindow = tk.Tk()
        startwindow.minsize(width=300, height=120)

        #frame1 is a label prompting user to pick file, frame2 are buttons to do so
        frame1 = tk.Frame(startwindow, width=300, height=60)
        frame1.pack_propagate(0)
        frame1.grid(row=0, column=0, columnspan=2)
        frame2a = tk.Frame(startwindow, width=150, height=60)
        frame2a.pack_propagate(0)
        frame2a.grid(row=1, column=0)
        frame2b = tk.Frame(startwindow, width=150, height=60)
        frame2b.pack_propagate(0)
        frame2b.grid(row=1, column=1)

        promptlabel = tk.Label(frame1, text='Read data from save file?')
        promptlabel.pack(fill=tk.BOTH, expand=1)
        
        #function for clicking yes on opening file prompt
        def yesfunction():
            #TODO: add displaying the actual exception
            filename = filedialog.askopenfilename(initialdir='/', title='Select file',
            filetypes=(('text files', '*.txt'), ('binary files', '*.bin')))
            templength = len(self.__data)
            excep = ''
            try:
                self.read(filename)
            except Exception as e:
                excep = e
                templength = 1000000
            
            if templength > len(self.__data):
                #generate popup
                #no specific exception occurred
                popup = tk.Toplevel(startwindow)
                popup.minsize(width=200, height=200)
                f1 = tk.Frame(popup, width=200, height=200)
                f1.pack_propagate(0)
                f1.grid(row=0, column=0)
                genericlabel = tk.Label(f1, text='Error: no new data found.')
                genericlabel.pack(fill=tk.BOTH, expand=1)
                popup.update()
            else:
                startwindow.destroy()
                self.genmainmenu()
                
        #function for clicking no on opening file prompt
        def nofunction():
            startwindow.destroy()
            self.genmainmenu()
                
        ybutton = tk.Button(frame2a, text='Yes', command=yesfunction)
        ybutton.pack(fill=tk.BOTH, expand=1)

        nbutton = tk.Button(frame2b, text='No', command=nofunction)
        #TODO: figure out why this does not work...
        nbutton.config(relief='sunken')
        nbutton.pack(fill=tk.BOTH, expand=1)

        startwindow.mainloop()
        
    #method to generate main menu
    def genmainmenu(self):
        mainmenu = tk.Tk()
        self.__totalvar = tk.StringVar()
        mainmenu.minsize(width=400, height=500)

        frame0_ = tk.Frame(mainmenu, width=400, height=140)
        frame0_.pack_propagate(0)
        frame0_.grid(row=0, column=0, columnspan=2)

        frame1_ = tk.Frame(mainmenu, width=400, height=100)
        frame1_.pack_propagate(0)
        frame1_.grid(row=1, column=0, columnspan=2)

        frame2a_ = tk.Frame(mainmenu, width=200, height=30)
        frame2a_.pack_propagate(0)
        frame2a_.grid(row=2, column=0)

        frame2b_ = tk.Frame(mainmenu, width=200, height=30)
        frame2b_.pack_propagate(0)
        frame2b_.grid(row=2, column=1)

        frame3a_ = tk.Frame(mainmenu, width=200, height=30)
        frame3a_.pack_propagate(0)
        frame3a_.grid(row=3, column=0)

        frame3b_ = tk.Frame(mainmenu, width=200, height=30)
        frame3b_.pack_propagate(0)
        frame3b_.grid(row=3, column=1)

        frame4_ = tk.Frame(mainmenu, width=400, height=100)
        frame4_.pack_propagate(0)
        frame4_.grid(row=4, column=0, columnspan=2)

        frame5a_ = tk.Frame(mainmenu, width=200, height=100)
        frame5a_.pack_propagate(0)
        frame5a_.grid(row=5, column=0)

        frame5b_ = tk.Frame(mainmenu, width=200, height=100)
        frame5b_.pack_propagate(0)
        frame5b_.grid(row=5, column=1)

        #frame0_ has the title
        titlelabel = tk.Label(frame0_, text='Scraping Settings', font=('Times New Roman', 30))
        titlelabel.pack(fill=tk.BOTH, expand=1)

        #frame1_ has the total count
        self.__totalvar.set('Total posts in data: {}'.format(len(self.__data)))
        totallabel = tk.Label(frame1_, textvariable=self.__totalvar, borderwidth=2, relief='solid', font=('Times New Roman', 20))
        totallabel.pack(fill=tk.BOTH, expand=1)

        #frame2a_ has the drop down menu label and frame2b_ has the menu
        choicelabel = tk.Label(frame2a_, text=' Choose a feed: ', borderwidth=2, relief='solid', anchor='w')
        choicelabel.pack(fill=tk.BOTH, expand=1)

        choices = ['Hot', 'Top of All Time', 'Top of Year', 'Top of Month', 'Top of Week', 'Top of Day', 'Top of Hour', 'New']
        choicevar = tk.StringVar()
        choicevar.set('Hot')
        choicemenu = tk.OptionMenu(frame2b_, choicevar, *choices)
        choicemenu.pack(fill=tk.BOTH, expand=1)

        #frame3a_ and frame3b_ have the label and entry for limit
        limitlabel = tk.Label(frame3a_, text=' Enter limit for feed: ', borderwidth=2, relief='solid', anchor='w')
        limitlabel.pack(fill=tk.BOTH, expand=1)
        limitentry = tk.Entry(frame3b_, bd=2)
        limitentry.pack(fill=tk.BOTH, expand=1)
        
        #frame4_ has the scrape button
        scrapebutton = tk.Button(frame4_, text='Start Scraping Session',
        command=lambda: self.__startscrapesession(mainmenu, choicevar.get(), limitentry.get(), scrapebutton))
        scrapebutton.pack(fill=tk.BOTH, expand=1)

        #frame5a_ has the save button, #frame5b_ has the plot button
        savebutton = tk.Button(frame5a_, text='Save', command=lambda: self.__savefile(savebutton))
        savebutton.pack(fill=tk.BOTH, expand=1)
        plotbutton = tk.Button(frame5b_, text='Plot', command=lambda: self.__gen_plot_options(mainmenu))
        plotbutton.pack(fill=tk.BOTH, expand=1)


        mainmenu.mainloop()

    #method that scrapebutton starts
    def __startscrapesession(self, mainmenu, feedname, limit, startbutton):
        #make sure that they cannot press the button
        startbutton.config(relief=tk.SUNKEN)
        startbutton.config(state=tk.DISABLED)
        try:
            limit = int(limit)
            if limit <= 0:
                limit = 10
        except:
            limit = 10
        
        self.setfeed(feedname, limit)

        #first we may need to intialize the progress bar
        if self.__feedlength is None:
            self.intializebar(mainmenu, feedname, self.__feed.limit)

        #begin setting up scrapesession window
        scrapesesswin = tk.Toplevel(mainmenu)
        scrapesesswin.minsize(420, 400)

        #generate frames (5 rows, 2 columns, each one 90 high except one that is 40 high)
        frame1 = tk.Frame(scrapesesswin, height=90, width=420)
        frame1.pack_propagate(0)
        frame1.grid(row=0, column=0, columnspan=2)

        frame2a = tk.Frame(scrapesesswin, height=90, width=340)
        frame2a.pack_propagate(0)
        frame2a.grid(row=1, column=0)
        frame2b = tk.Frame(scrapesesswin, height=90, width=80)
        frame2b.pack_propagate(0)
        frame2b.grid(row=1, column=1)
       
        frame3a = tk.Frame(scrapesesswin, height=90, width=340)
        frame3a.pack_propagate(0)
        frame3a.grid(row=2, column=0)
        frame3b = tk.Frame(scrapesesswin, height=90, width=80)
        frame3b.pack_propagate(0)
        frame3b.grid(row=2, column=1)

        frame4 = tk.Frame(scrapesesswin, height=40, width=420)
        frame4.pack_propagate(0)
        frame4.grid(row=3, column=0, columnspan=2)
        
        frame5a = tk.Frame(scrapesesswin, height=90, width=340)
        frame5a.pack_propagate(0)
        frame5a.grid(row=4, column=0)
        frame5b = tk.Frame(scrapesesswin, height=90, width=80)
        frame5b.pack_propagate(0)
        frame5b.grid(row=4, column=1)

        #generate elements inside frames
        #first frame1, which is a title for the Scrape Session
        title_scrape_sess_label = tk.Label(frame1, text='Scrape Session', font=('Times New Roman', 30))
        title_scrape_sess_label.pack(fill=tk.BOTH, expand=1)

        #next frame2a and frame2b, which hold a label and the total number of posts
        total_to_add_text_label = tk.Label(frame2a, text=' Total number of posts in current feed: ',
        borderwidth=2, relief='solid', anchor='w')
        total_to_add_text_label.pack(fill=tk.BOTH, expand=1)
        total_to_add_num_label = tk.Label(frame2b, text=str(self.__feedlength), borderwidth=2, relief='solid')
        total_to_add_num_label.pack(fill=tk.BOTH, expand=1)

        #next frame3a and frame3b, which hold a label and the number of posts currently added (will update)
        num_cur_added_var = tk.StringVar()
        num_cur_added_var.set('0')
        cur_added_text_label = tk.Label(frame3a, text=' Number of new posts added to data: ', 
        borderwidth=2, relief='solid',anchor='w')
        cur_added_text_label.pack(fill=tk.BOTH, expand=1)
        cur_added_num_label = tk.Label(frame3b, textvariable=num_cur_added_var, borderwidth=2, relief='solid')
        cur_added_num_label.pack(fill=tk.BOTH, expand=1)

        #next frame4, which holds the progress bar
        progress = ttk.Progressbar(frame4, orient='horizontal', length=420, mode='determinate')
        progress.pack(fill=tk.BOTH, expand=1)
        progress['maximum'] = self.__feedlength

        #next frame5a and frame5b, which hold a label and the time remaining (will update)
        time_remaining_var = tk.StringVar()
        time_remaining_var.set('')
        time_remaining_text_label = tk.Label(frame5a, text=' Estimated time remaining: ', 
        borderwidth=2, relief='solid', anchor='w')
        time_remaining_text_label.pack(fill=tk.BOTH, expand=1)
        time_remaining_num_label = tk.Label(frame5b, textvariable=time_remaining_var, borderwidth=2, relief='solid')
        time_remaining_num_label.pack(fill=tk.BOTH, expand=1)

        scrapesesswin.update()

        #Now that the UI is done, we can begin to start scraping and updating
        #TODO: do button disabling work
        #post index to track how far to go
        #postavg time to tell how long to go
        #temp length variable to tell when one is added
        #totaladded to go into how many added variable
        postindex = 0
        postavgtime = 0.0
        templength = len(self.__data)
        curadded = 0

        ttime = time.time()
        #iterate through posts in feed
        for post in self.__feed:
            t = time.time()
            postindex += 1
            self.addpost(post)
            #calculate average time
            t = time.time() - t
            postavgtime = (postindex - 1.0)*postavgtime + t
            postavgtime = postavgtime/postindex

            if len(self.__data) > templength:
                #a post has been added
                curadded += 1
                templength = len(self.__data)
                #the time should only be updated on screen when a post is added
                #as quick exceptions will skew it too low
                
                time_remaining_var.set(DataGrabber.timeutil(postavgtime*(self.__feedlength - postindex)))

            #update ui elements
            num_cur_added_var.set(str(curadded))
            progress['value'] = postindex
            
            #TODO: should this be update_idletasks
            scrapesesswin.update()

        #finished all posts, now finish the progress bar and create finished window
        #want to know the total time it took
        ttime = time.time() - ttime

        #want bar to finishup
        dist = progress['maximum'] - progress['value']
        #want to pause so that the whole thing will take about 5 seconds
        if dist > 0:
            pause = 5/dist
        for i in range(dist):
            #TODO: deal with random numbers for sleeping
            time.sleep(pause)
            progress['value'] = progress['value'] + 1
            scrapesesswin.update()
        time.sleep(.1)

    
        finishwin = tk.Toplevel(mainmenu)
        finishwin.minsize(400, 100)
        finframe1 = tk.Frame(finishwin, height=50, width=400)
        finframe1.pack_propagate(0)
        finframe1.grid(row=0, column=0)
        finframe2 = tk.Frame(finishwin, height=50, width=400)
        finframe2.pack_propagate(0)
        finframe2.grid(row=1, column=0)

        fin_title_label = tk.Label(finframe1, text='Scraping finished!')
        fin_title_label.pack(fill=tk.BOTH, expand=1)

        finmessage = '{} new posts were added to data in {}.'.format(str(curadded), 
        DataGrabber.timeutil(ttime))
        fin_message_label = tk.Label(finframe2, text=finmessage)
        fin_message_label.pack(fill=tk.BOTH, expand=1)

        #update __totalvar which shows up on mainmenu and restore startbutton 
        self.__totalvar.set('Total posts in data: {}'.format(len(self.__data)))
        mainmenu.update()
        startbutton.config(relief=tk.RAISED)
        startbutton.config(state=tk.NORMAL)

        #kill old frame and replace
        scrapesesswin.destroy()
        finishwin.mainloop()

    #method that savebutton starts
    def __savefile(self, startbutton):
        startbutton.config(relief=tk.SUNKEN)
        startbutton.config(state=tk.DISABLED)
        savepath = filedialog.asksaveasfilename(initialdir='/', title='Select save file',
        filetypes = (('text files', '*.txt'), ('binary files', '*.bin')))
        startbutton.config(relief=tk.RAISED)
        startbutton.config(state=tk.NORMAL)
        #only write if we got back a path
        if not (savepath == ''):
            self.write(savepath)

    #method that plotbutton starts
    def __gen_plot_options(self, mainmenu):
        plotoptionswin = tk.Toplevel(mainmenu)
        plotoptionswin.minsize(300, 200)

        plotoptionsframe1 = tk.Frame(plotoptionswin, width=300, height=50)
        plotoptionsframe1.pack_propagate(0)
        plotoptionsframe1.grid(row=0, column=0)

        plotoptionsframe2 = tk.Frame(plotoptionswin, width=300, height=50)
        plotoptionsframe2.pack_propagate(0)
        plotoptionsframe2.grid(row=1, column=0)

        plotoptionsframe3 = tk.Frame(plotoptionswin, width=300, height=50)
        plotoptionsframe3.pack_propagate(0)
        plotoptionsframe3.grid(row=2, column=0)

        plotoptionsframe4 = tk.Frame(plotoptionswin, width=300, height=50)
        plotoptionsframe4.pack_propagate(0)
        plotoptionsframe4.grid(row=3, column=0)

        #plotoptionsframe1 has title label
        plotoptions_title_label = tk.Label(plotoptionsframe1, text='Plot Options', font=('Times New Roman', 25))
        plotoptions_title_label.pack(fill=tk.BOTH, expand=1)

        #plotoptionsframe2a and 2b has the checkbox for weighing posts by karma and a label
        weigh_posts_var = tk.BooleanVar()
        weigh_posts_var.set(True)
        weigh_posts_checkbutton = tk.Checkbutton(plotoptionsframe2, text=' weigh posts by karma', 
        variable=weigh_posts_var, anchor='w')
        weigh_posts_checkbutton.pack(fill=tk.BOTH, expand=1)

        #plotoptionsframe3 has the checkbox for weighing posts
        weigh_comments_var = tk.BooleanVar()
        weigh_comments_var.set(True)
        weigh_comments_checkbutton = tk.Checkbutton(plotoptionsframe2, text=' weigh comments by karma', 
        variable=weigh_comments_var, anchor='w')
        weigh_comments_checkbutton.pack(fill=tk.BOTH, expand=1)
        
        #plotoptionsframe4 has the button for generating the plot
        gen_plot_button = tk.Button(plotoptionsframe4, text='Press to generate plots', borderwidth=2,
        command=lambda: self.__createplots(mainmenu, weigh_comments_var.get(), weigh_comments_var.get()))
        gen_plot_button.pack(fill=tk.BOTH, expand=1)

        plotoptionswin.mainloop()



    #method that starts from plotoptions window
    def __createplots(self, mainmenu, weighposts, weighcomments):
        #create plotwindow and plotframes
        plotwindow = tk.Toplevel(mainmenu)
        plotframe = tk.Frame(plotwindow)
        plotframe.grid(row=0, column=0)
        
        #do figure work
        testdom = [1,2,3,4,5,6,7,8,9,10]
        testran = [2,4,6,8,10,12,14,16,18,20]
        fig = Figure(figsize=(15,5), dpi=100)

        a1 = fig.add_subplot(131)
        a2 = fig.add_subplot(132)
        a3 = fig.add_subplot(133)

        a1.set_title('Length of Title Plot')
        a1.set_xlabel('Characters in Post Title')
        a1.set_ylabel('Assholeness')

        a2.set_title('Word Length of Body Plot')
        a2.set_xlabel('Words in Post Body')
        a2.set_ylabel('Assholeness')

        a3.set_title('Character Length of Body Plot')
        a3.set_xlabel('Characters in Post Body')
        a3.set_ylabel('Assholeness')

        #first get domains and ranges in order (do not clean yet)
        a1dom = []
        a1ran = []
        #sort __data so can put into a1 (by title_clength)
        self.__data.sort(key=lambda pr: pr.title_clength)
        #have a condition for if we get the points weighing comments or not
        if weighcomments:
            for pr in self.__data:
                a1dom.append(pr.title_clength)
                a1ran.append(pr.rank_weighc)
        else:
            for pr in self.__data:
                a1dom.append(pr.title_clength)
                a1ran.append(pr.rank_unweighc)
        #have to do grouping work now, because otherwise it will not work...
        for i in range(len(a1dom)):
            a1dom[i] = 5*int((a1dom[i] + 2.5) / 5)

        index = 0
        
        while index < len(a1dom):
            totalkarma = self.__data[index].postweight
            if weighposts:
                avg_range_value = a1ran[index]*self.__data[index].postweight
            else:
                avg_range_value = a1ran[index]
            add = 1
            while (index + add < len(a1dom)) and (a1dom[index + add] == a1dom[index]):
                if weighposts:
                        avg_range_value += a1ran[index + add]*self.__data[index + add].postweight
                        totalkarma += self.__data[index + add].postweight
                else:
                    avg_range_value += a1ran[index + add]
                add += 1

            #divide by add if unweighted(1 more than how many added, so the total number of ranges)
            if weighposts:
                avg_range_value = avg_range_value/totalkarma
            else:
                avg_range_value = avg_range_value/add
            #we now need to set the first one to be the average and delete the repeats (in domain and range)
            a1ran[index] = avg_range_value
            for delindex in range(index + 1, index + add):
                #delete these elements
                del(a1dom[delindex])
                del(a1ran[delindex])
            index += 1

        
        a2dom = []
        a2ran = []
        #sort data by body_wlength
        self.__data.sort(key=lambda pr: pr.body_wlength)
        #have a condition for if we get the points weighing comments or not
        if weighcomments:
            for pr in self.__data:
                a2dom.append(pr.body_wlength)
                a2ran.append(pr.rank_weighc)
        else:
            for pr in self.__data:
                a2dom.append(pr.body_wlength)
                a2ran.append(pr.rank_unweighc)

        #have to do grouping work now, because otherwise it will not work...
        for i in range(len(a2dom)):
            a2dom[i] = 10*int((a2dom[i] + 5) / 10)

        index = 0

        while index < len(a2dom):
            totalkarma = self.__data[index].postweight
            if weighposts:
                avg_range_value = a2ran[index]*self.__data[index].postweight
            else:
                avg_range_value = a2ran[index]
            add = 1
            while (index + add < len(a2dom)) and (a2dom[index + add] == a2dom[index]):
                if weighposts:
                        avg_range_value += a2ran[index + add]*self.__data[index + add].postweight
                        totalkarma += self.__data[index + add].postweight
                else:
                    avg_range_value += a2ran[index + add]
                add += 1

            #divide by add if unweighted(1 more than how many added, so the total number of ranges)
            if weighposts:
                avg_range_value = avg_range_value/totalkarma
            else:
                avg_range_value = avg_range_value/add
            #we now need to set the first one to be the average and delete the repeats (in domain and range)
            a2ran[index] = avg_range_value
            for delindex in range(index + 1, index + add):
                #delete these elements
                del(a2dom[delindex])
                del(a2ran[delindex])
            index += 1



        a3dom = []
        a3ran = []
        #sort data by body_clength
        self.__data.sort(key=lambda pr: pr.body_clength)
        #have a condition for if we get the points weighing comments or not
        if weighcomments:
            for pr in self.__data:
                a3dom.append(pr.body_clength)
                a3ran.append(pr.rank_weighc)
        else:
            for pr in self.__data:
                a3dom.append(pr.body_clength)
                a3ran.append(pr.rank_unweighc)

        #have to do grouping work now, because otherwise it will not work...
        for i in range(len(a3dom)):
            a3dom[i] = 100*int((a3dom[i] + 50) / 100)

        index = 0

        while index < len(a3dom):
            totalkarma = self.__data[index].postweight
            if weighposts:
                avg_range_value = a3ran[index]*self.__data[index].postweight
            else:
                avg_range_value = a3ran[index]
            add = 1
            while (index + add < len(a3dom)) and (a3dom[index + add] == a3dom[index]):
                if weighposts:
                        avg_range_value += a3ran[index + add]*self.__data[index + add].postweight
                        totalkarma += self.__data[index + add].postweight
                else:
                    avg_range_value += a3ran[index + add]
                add += 1

            #divide by add if unweighted(1 more than how many added, so the total number of ranges)
            if weighposts:
                avg_range_value = avg_range_value/totalkarma
            else:
                avg_range_value = avg_range_value/add
            #we now need to set the first one to be the average and delete the repeats (in domain and range)
            a3ran[index] = avg_range_value
            for delindex in range(index + 1, index + add):
                #delete these elements
                del(a3dom[delindex])
                del(a3ran[delindex])
            index += 1

        #return __data to normal
        self.__data.sort(key=lambda pr: pr.id)

        #little test
        print('a1: {}=={}?'.format(len(a1dom), len(a1ran)))
        print('a2: {}=={}?'.format(len(a2dom), len(a2ran)))
        print('a3: {}=={}?'.format(len(a3dom), len(a3ran)))

        a1.plot(a1dom, a1ran)
        a2.plot(a2dom, a2ran)
        a3.plot(a3dom, a3ran)

        canvas = FigureCanvasTkAgg(fig, plotframe)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        plotwindow.mainloop()


        

        
        

    #method to convert milliseconds into minutes and seconds and returns a string
    @staticmethod
    def timeutil(seconds):
        output = ''
        m = int(seconds/60)
        s = int(seconds%60)
        if m < 10:
            output += '0'
        output += '{}:'.format(str(m))
        if s < 10:
            output += '0'
        output += str(s)
        return output


    def temptest(self):
        self.startgui()
if __name__ == "__main__":
    dg = DataGrabber()
    dg.temptest()