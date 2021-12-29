import numpy as np
import matplotlib.pyplot as plt
from glob import glob
import librosa as lr
import time
import random
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

class Snippet:
    #simple class- four boolean variables to determine if beep or pause and if long or short
    def __init__(self, **kwargs):
        #set None as defualt
        self.__isbeep = None
        self.__ispause = None
        self.__islong = None
        self.__isshort = None
        self.setvars(**kwargs)

    #method to set variables
    def setvars(self, **kwargs):
        for key, arg in kwargs.items():
            originalarg = arg
            originalkey = key
            key = key.lower()
            arg = arg.lower()
            #valid keys are value/v or length/l
            if key == 'value' or key == 'v':
                #valid args are beep/b or pause/p
                if arg == 'beep' or arg == 'b':
                    self.__isbeep = True
                    self.__ispause = False
                elif arg == 'pause' or arg == 'p':
                    self.__isbeep = False
                    self.__ispause = True
                else:
                    #invalid argument, raise exception
                    raise Exception('Exception: invalid argument for value/v ({})'.format(originalarg))
            elif key == 'length' or key == 'l':
                #valid args are long/l or short/s
                if arg == 'long' or arg == 'l':
                    self.__islong = True
                    self.__isshort = False
                elif arg == 'short' or arg == 's':
                    self.__islong = False
                    self.__isshort = True
                else:
                    #invalid argument, raise exception
                    raise Exception('Exception: invalid argument for length/l ({})'.format(originalarg))
            else:
                #invalid key, raise exception
                raise Exception('Exception: invalid key ({}) provided along with arg ({}).'.format(originalkey, 
                    originalarg))

    #simple methods to access private variables
    def isbeep(self):
        return self.__isbeep
    def ispause(self):
        return self.__ispause
    def islong(self):
        return self.__islong
    def isshort(self):
        return self.__isshort

    #tostring method
    def tostring(self):
        output = ''
        if (self.__islong is None) or (self.__isshort is None):
            output += 'no length '
        elif self.__islong:
            output += 'long '
        else:
            output += 'short '
        
        if (self.__isbeep is None) or (self.__ispause is None):
            output += 'no value.'
        elif self.__isbeep:
            output += 'beep.'
        else:
            output += 'pause.'
        
        return output
        
class MorseTranslator:
    '''
        Variables:
            __audio: audio from file
            __sfreq: frequency of samples
            __intermediate_snippets: list of tuples used to translate __audiofile to __snippets
            __snippets: list of Snippets which can then be converted into plaintext
            __master_char_dict: dictionary with how many beeps (total) are in each character
            __plaintext: string of message from audio file
            ALL CAPS INDICATES A MAGIC VARIABLE
            __INTERMEDIATE_DESIRED_SFREQ: the sfreq we want to have in __audio; the normalization is done
                in gen_intermediate_snippets(self)
            __INTERMEDIATE_CLUMP_TOLERANCE: the tolerance for how much each individual audio point must be abover
                or below the last ones
            __INTERMEDIATE_LENGTH_TOLERANCE: the tolerance for how close the length of an intermediate
                snippet must be to the (avg + med)/2
            
    '''
    def __init__(self):
        self.__audio = None
        self.__sfreq = None
        self.__intermediate_snippets = None
        self.__snippets = None
        self.__plaintext = None
        self.__master_char_dict = {}
        self.__INTERMEDIATE_DESIRED_SFREQ = 100
        self.__INTERMEDIATE_CLUMP_TOLERANCE = 0.1
        self.__INTERMEDIATE_LENGTH_TOLERANCE = 0.1

        #initiate constant values of __master_char_dict
        self.__master_char_dict ['a'] = 2
        self.__master_char_dict ['b'] = 4
        self.__master_char_dict ['c'] = 4
        self.__master_char_dict ['d'] = 3
        self.__master_char_dict ['e'] = 1
        self.__master_char_dict ['f'] = 4
        self.__master_char_dict ['g'] = 3
        self.__master_char_dict ['h'] = 4
        self.__master_char_dict ['i'] = 2
        self.__master_char_dict ['j'] = 4
        self.__master_char_dict ['k'] = 3
        self.__master_char_dict ['l'] = 4
        self.__master_char_dict ['m'] = 2
        self.__master_char_dict ['n'] = 2
        self.__master_char_dict ['o'] = 3
        self.__master_char_dict ['p'] = 4
        self.__master_char_dict ['q'] = 4
        self.__master_char_dict ['r'] = 3
        self.__master_char_dict ['s'] = 3
        self.__master_char_dict ['t'] = 1
        self.__master_char_dict ['u'] = 3
        self.__master_char_dict ['v'] = 4
        self.__master_char_dict ['w'] = 3
        self.__master_char_dict ['x'] = 4
        self.__master_char_dict ['y'] = 4
        self.__master_char_dict ['z'] = 4
    
    #method to read in audio file to __audio
    def readfile(self, filename):
        #TODO: proper exception handling? idk
        if not isinstance(filename, str):
            raise Exception('Invalid path for __readfile(self, path): not a str.')
        try:
            self.__audio, self.__sfreq = lr.load(filename)
        except Exception as e:
            print('Could not read audio file ({}).'.format(str(e)))
    
        
    #method to generate intermediate snippets after readfile has been called
    def gen_intermediate_snippets(self):
        #must already have audio
        if (self.__audio is None) or (self.__sfreq is None):
            return
        self.__intermediate_snippets = []
        new_audio = []

        #first we need to make sure that that sampling frequency of the data
        #is less than or equal to self.__INTERMEDIATE_DESIRED_SFREQ
        if self.__sfreq > self.__INTERMEDIATE_DESIRED_SFREQ:
            increment_length = int(self.__sfreq/self.__INTERMEDIATE_DESIRED_SFREQ)
            #cycle through each increment and then individually through each data point in that increment
            for i in range(int(len(self.__audio) / increment_length + 1)):
                #at start of increment now
                #find average magnitude of increment
                avgmag = 0.0
                j = 0
                while (j < increment_length) and (i * increment_length + j < len(self.__audio)):
                    avgmag += abs(self.__audio[(i * increment_length + j)])
                    j += 1
                #to normalize average, we delete by j, because the last increment could be 
                #shorter than increment_length
                avgmag = avgmag / j
                new_audio.append(avgmag)
        
        self.__audio = new_audio
        self.__sfreq = self.__INTERMEDIATE_DESIRED_SFREQ

        #now start clump work: want to clump together groups of increasing and decreasing magnitudes
        clump_global_avg = 0.0
        i = -1
        while i < len(self.__audio) - 1:
            i += 1
            clumplength = 1
            clumpavgmag = self.__audio[i]
            #we first increment through while the ones ahead are larger in magnitude (accounting for tolerance)
            while (i < len(self.__audio) - 1) and (self.__audio[i+1] >= self.__audio[i]*(1.0-self.__INTERMEDIATE_CLUMP_TOLERANCE)):
                i += 1
                clumplength += 1
                clumpavgmag += self.__audio[i]
            #only go through the smaller ones if we have not gone through larger ones
            if clumplength == 1:
                #TODO: include tolerance for decreasing ones?

                while (i < len(self.__audio) - 1) and (self.__audio[i+1] <= self.__audio[i]):
                    i += 1
                    clumplength += 1
                    clumpavgmag += self.__audio[i]
            
            #add to intermediate_snippets
            clump_global_avg += clumpavgmag
            clumpavgmag = clumpavgmag/clumplength
            self.__intermediate_snippets.append((clumplength, clumpavgmag))
        #divide global average by length of audio
        clump_global_avg = clump_global_avg / len(self.__audio)
        #clump work is done, now throw out isnips that are too short for global_clump_avg

        for isnip in self.__intermediate_snippets:
            if isnip[0] < self.__INTERMEDIATE_LENGTH_TOLERANCE * clump_global_avg:
                del(isnip)

    #method to generate snippets after gen_intermediate_snippets has been called
    def gen_snippets(self):
        #must have already generated intermediate_snippets
        if (self.__intermediate_snippets is None) or (len(self.__intermediate_snippets) == 0):
            return
        self.__snippets = []

        #first we want to determine if each intermediate_snippet is a beep or pause
        #we do this by finding the avgmag and medmag to obtain normal_mav = (avgmag + medmag)/2
        magslist = []
        avgmag = 0.0
        for isnip in self.__intermediate_snippets:
            avgmag += isnip[1]
            magslist.append(isnip[1])
        magslist.sort()
        medmag = magslist[int(len(magslist)/2)]
        avgmag /= len(self.__intermediate_snippets)
        normal_mag = (avgmag + medmag)/2
        #now go through intermediate_snippets and add a corresponding snippet to snippets
        for isnip in self.__intermediate_snippets:
            #check magnitude to determine if it is a beep or a pause
            mag = isnip[1]
            if mag > normal_mag:
                #a beep
                self.__snippets.append(Snippet(value = 'beep'))
            else:
                #a pause
                self.__snippets.append(Snippet(value = 'pause'))
        
        #exception check: snippets and intermediate_snippets must have same length
        if not (len(self.__snippets) == len(self.__intermediate_snippets)):
            raise Exception('Exception: different number of intermediate snippets and snippets.')

        #we now follow a similar procedure to determine if each is a beep or a pause
        beep_lengths = []
        avg_beep_length = 0.0
        pause_lengths = []
        avg_pause_length = 0.0
        for i in range(len(self.__snippets)):
            if self.__snippets[i].isbeep():
                #dealing with a beep
                beep_lengths.append(self.__intermediate_snippets[i][0])
                avg_beep_length += self.__intermediate_snippets[i][0]
            else:
                #dealing with a pause
                pause_lengths.append(self.__intermediate_snippets[i][0])
                avg_pause_length += self.__intermediate_snippets[i][0]

        beep_lengths.sort()
        try:
            avg_beep_length /= len(beep_lengths)
        except:
            avg_beep_length = 0.0
        try:
            med_beep_length = beep_lengths[int(len(beep_lengths)/2)]
        except:
            med_beep_length = 0.0

        pause_lengths.sort()
        try:
            avg_pause_length /= len(pause_lengths)
        except:
            avg_pause_length = 0.0
        try:
            med_pause_length = pause_lengths[int(len(pause_lengths)/2)]
        except:
            med_pause_length = 0.0

        normal_beep_length = (avg_beep_length + med_beep_length)/2
        normal_pause_length = (avg_pause_length + med_pause_length)/2
        #go through and add length info to snippets
        for i in range(len(self.__snippets)):
            snip = self.__snippets[i]
            length = self.__intermediate_snippets[i][0]
            if snip.isbeep():
                #dealing with a beep
                if length > normal_beep_length:
                    #long beep
                    snip.setvars(length = 'long')
                else:
                    #short beep
                    snip.setvars(length = 'short')
            else:
                #dealing with a pause
                if length > normal_pause_length:
                    #long pause
                    snip.setvars(length = 'long')
                else:
                    #short pause
                    snip.setvars(length = 'short')
        '''
        we now cleanup the snips
        basically there should never be two beeps or pauses in a row, we will replace these with a long beep or pause
        examples (assume that message is formatted correctly before issue):
            b,b,p --> long beep, pause
            b,b,b --> b, pause with same length as middle b, b
            p,p,b --> long pause, beep
            p,p,p --> p, beep with same length as middle p, p
        '''
        #only cycle through to len(self.__snippets) - 2, deal with end after
        for i in range(len(self.__snippets) - 2):
            s0 = self.__snippets[i]
            s1 = self.__snippets[i + 1]
            s2 = self.__snippets[i + 2]
           
            #check for possibility of error
            if s0.isbeep() == s1.isbeep():
                #s0 and s1 have the same value, check if s2 has the same also
                if s1.isbeep() == s2.isbeep():
                    #bad group of three, we change the middle one's value
                    if s1.isbeep():
                        #middle is a beep, make it a pause
                        s1.setvars(value = 'pause')
                    else:
                        #middle is a pause, make it a beep
                        s1.setvars(value = 'beep')
                else:
                    #first two are the bad group, make first one long and delete second one
                    s0.setvars(length = 'long')
                    del(self.__snippets[i + 1])
            #IMPORTANT: s1 and s2 being same value does not trigger error since it will happen on the next loop
        
        #now deal with the last three
        #only possible issue is if the last two are equal only
        if len(self.__snippets) >= 2:
            #we know that the third from the last will be fine thanks to our loop before hand
            s0 = self.__snippets[len(self.__snippets) - 2]
            s1 = self.__snippets[len(self.__snippets) - 1]
            if s0.isbeep() == s1.isbeep():
                #issue, set length of s0 to long and delete s1
                s0.setvars(length = 'long')
                del(self.__snippets[len(self.__snippets) - 1])
            
    #method to generate plaintext after gen_snippets has been called
    def gen_plain_text(self):
        self.__plaintext = ''
        #We go through snippets, trying to create a group for each letter
        i = 0
        while i < len(self.__snippets):
            #generate dictionary for possibilities
            possibilities = {}
            for ascii_num in range(97, 123):
                possibilities[chr(ascii_num)] = 0.0
            lettergroup = []
            #go through and add snippets until we hit a long pause
            #only add beeps because short pauses mean nothing
            while i < len(self.__snippets) and not (self.__snippets[i].ispause() and self.__snippets[i].islong()):
                if self.__snippets[i].isbeep():
                    lettergroup.append(self.__snippets[i])
                i += 1
            #now lettergroup has all snippets in (hopefully) letter except longpause at end
            #increment through and update possibilities
            overshot_word = False
            for j in range(len(lettergroup)):
                #only subtract by 1.0 from possibilities if wrong length
                #if go over length, subtract by 0.5
                s = lettergroup[j]
                if j == 0:
                    #first beep
                    if s.islong():
                        #subtract from letters where this is not the case
                        possibilities['a'] -= 1.0
                        possibilities['e'] -= 1.0
                        possibilities['f'] -= 1.0
                        possibilities['h'] -= 1.0
                        possibilities['i'] -= 1.0
                        possibilities['j'] -= 1.0
                        possibilities['l'] -= 1.0
                        possibilities['p'] -= 1.0
                        possibilities['r'] -= 1.0
                        possibilities['s'] -= 1.0
                        possibilities['u'] -= 1.0
                        possibilities['v'] -= 1.0
                        possibilities['w'] -= 1.0
                    else:
                        #subtract from letters where this is not the case (have long first character)
                        possibilities['b'] -= 1.0
                        possibilities['c'] -= 1.0
                        possibilities['d'] -= 1.0
                        possibilities['g'] -= 1.0
                        possibilities['k'] -= 1.0
                        possibilities['m'] -= 1.0
                        possibilities['n'] -= 1.0
                        possibilities['o'] -= 1.0
                        possibilities['q'] -= 1.0
                        possibilities['t'] -= 1.0
                        possibilities['x'] -= 1.0
                        possibilities['y'] -= 1.0
                        possibilities['z'] -= 1.0
                elif j == 1:
                    #second beep
                    #do normal subtraction, but also subtract for letters that are too short
                    #too short first
                    possibilities['e'] -= 0.5
                    possibilities['t'] -= 0.5
                    if s.islong():
                        #subtract from words where this is not true
                        possibilities['b'] -= 1.0
                        possibilities['c'] -= 1.0
                        possibilities['d'] -= 1.0
                        possibilities['f'] -= 1.0
                        possibilities['h'] -= 1.0
                        possibilities['i'] -= 1.0
                        possibilities['k'] -= 1.0
                        possibilities['n'] -= 1.0
                        possibilities['s'] -= 1.0
                        possibilities['u'] -= 1.0
                        possibilities['v'] -= 1.0
                        possibilities['x'] -= 1.0
                        possibilities['y'] -= 1.0
                    else:
                        #subtract from words where this is not true
                        possibilities['a'] -= 1.0
                        possibilities['g'] -= 1.0
                        possibilities['j'] -= 1.0
                        possibilities['l'] -= 1.0
                        possibilities['m'] -= 1.0
                        possibilities['o'] -= 1.0
                        possibilities['p'] -= 1.0
                        possibilities['q'] -= 1.0
                        possibilities['r'] -= 1.0
                        possibilities['w'] -= 1.0
                        possibilities['z'] -= 1.0
                elif j == 2:
                    #third beep
                    #do normal subtraction, but also subtract for letters that are too short
                    #too short first
                    possibilities['e'] -= 0.5
                    possibilities['t'] -= 0.5
                    possibilities['a'] -= 0.5
                    possibilities['i'] -= 0.5
                    possibilities['m'] -= 0.5
                    possibilities['n'] -= 0.5
                    if s.islong():
                        #subtract from letters where this is not true
                        possibilities['b'] -= 1.0
                        possibilities['d'] -= 1.0
                        possibilities['g'] -= 1.0
                        possibilities['h'] -= 1.0
                        possibilities['l'] -= 1.0
                        possibilities['q'] -= 1.0
                        possibilities['r'] -= 1.0
                        possibilities['s'] -= 1.0
                        possibilities['v'] -= 1.0
                        possibilities['x'] -= 1.0
                        possibilities['z'] -= 1.0
                    else:
                        #subtract from letters where this is not true
                        possibilities['c'] -= 1.0
                        possibilities['f'] -= 1.0
                        possibilities['j'] -= 1.0
                        possibilities['k'] -= 1.0
                        possibilities['o'] -= 1.0
                        possibilities['p'] -= 1.0
                        possibilities['u'] -= 1.0
                        possibilities['w'] -= 1.0
                        possibilities['y'] -= 1.0
                elif j == 3:
                    #fourth beep
                    #do normal suvtraction, but also subtract for letters that are too short
                    #too short first  
                    possibilities['e'] -= 0.5
                    possibilities['t'] -= 0.5
                    possibilities['a'] -= 0.5
                    possibilities['i'] -= 0.5
                    possibilities['m'] -= 0.5
                    possibilities['n'] -= 0.5
                    possibilities['d'] -= 0.5
                    possibilities['g'] -= 0.5
                    possibilities['k'] -= 0.5
                    possibilities['o'] -= 0.5
                    possibilities['r'] -= 0.5
                    possibilities['s'] -= 0.5
                    possibilities['u'] -= 0.5
                    possibilities['w'] -= 0.5
                    if s.islong():
                        #subtract from letters where this is not teh case.
                        possibilities['b'] -= 1.0
                        possibilities['c'] -= 1.0
                        possibilities['f'] -= 1.0
                        possibilities['h'] -= 1.0
                        possibilities['l'] -= 1.0
                        possibilities['p'] -= 1.0
                        possibilities['z'] -= 1.0
                    else:
                        possibilities['j'] -= 1.0
                        possibilities['q'] -= 1.0
                        possibilities['v'] -= 1.0
                        possibilities['x'] -= 1.0
                        possibilities['y'] -= 1.0
                else:
                    overshot_word = True
                    break
            maxes = []
            maximum = possibilities['a']
            for key, value in possibilities.items():
                if value > maximum:
                    maximum = value
            for key, value in possibilities.items():
                if value == maximum:
                    maxes.append(key)
            #we now have all characters that have an equal likelyhood, we will prioritize ones
            #that are shorter or equal but have the closest length to lettergroup
            mindist = 10
            for k in maxes:
                dist = len(lettergroup) - self.__master_char_dict[k]
                if dist < 0:
                    continue
                if dist < mindist:
                    mindist = dist
            actual_possibilities = []
            for k in maxes:
                dist = len(lettergroup) - self.__master_char_dict[k]
                if dist == mindist:
                    actual_possibilities.append(k)
            #add to plain text
            if len(actual_possibilities) == 1:
                self.__plaintext += actual_possibilities[0]
            else:
                self.__plaintext += '('
                for pos in actual_possibilities:
                    self.__plaintext += pos
                    self.__plaintext += '/'
                self.__plaintext += '?)'
            #increment to step over long pause
            i += 1
            #handle overstep
            overstep = len(lettergroup) - self.__master_char_dict[actual_possibilities[0]]
            if overstep > 0:
                i -= overstep

    def temptest(self):
        
        readtime = time.time()*1000
        self.readfile('~/Playground/MorseCode/morsetest.wav')
        readtime = time.time()*1000 - readtime
        intertime = time.time()*1000
        self.gen_intermediate_snippets()
        intertime = time.time()*1000 - intertime
        for isnip in self.__intermediate_snippets:
            print(str(isnip))
        gentime = time.time()*1000
        self.gen_snippets()
        gentime = time.time()*1000 - gentime
        for snip in self.__snippets:
            if snip.ispause() and snip.islong():
                print(snip.tostring())
                print('\n')
            else:
                print(snip.tostring())
        plaintexttime = time.time()*1000
        self.gen_plain_text()
        plaintexttime = time.time()*1000 - plaintexttime
        print('Time to read file: {} ms.'.format(readtime))
        print('Time to generate intermediate snippets: {} ms.'.format(intertime))
        print('Time to generate snippets: {} ms.'.format(gentime))
        print('Time to generate plain text: {} ms.'.format(plaintexttime))
        print(self.__plaintext)
        
    def bigtest(self):
        rootdir = '~/Playground/MorseCode/BigTestFiles'
        tests = {}
        for subdir, dirs, files in os.walk(rootdir):
            for file in files:
                if file[len(file) - 4: ] == '.wav':
                    tests[file[0: file.index('.wav')]] = file
        
        test_record_string = ''
        successes = 0
        
        keepgoing = True
        globindex = 1
        while keepgoing:
            try:
                index = 1
                for expected, filepath in tests.items():
                    if index < globindex:
                        index += 1
                        continue
                    self.__audio = None
                    self.__sfreq = None
                    self.__intermediate_snippets = None
                    self.__snippets = None
                    self.__plaintext = None
                    print('On file ({}/{})...'.format(index, len(tests)))
                    self.readfile('{}/{}'.format(rootdir, filepath))
                    self.gen_intermediate_snippets()
                    self.gen_snippets()
                    self.gen_plain_text()
                    if self.__plaintext == expected:
                        successes += 1
                    else:
                        test_record_string += 'Failed for string {}.\n'.format(expected)
                    index += 1
                    globindex = index
                keepgoing = False
            except Exception as e:
                print(e)
                globindex += 1
                if not str(e) == 'KeyboardInterupt':
                    test_record_string += 'Failed for string {}.\n'.format(expected)
                
        with open('~/Playground/MorseCode/BigTestResults.txt', 'w') as s:
            s.write('Successes: {}/{}.\n'.format(successes, len(tests)))
            s.write(test_record_string)
    
    def run(self):
        mainwin = tk.Tk()
        mainwin.minsize(200, 200)
        frame1 = tk.Frame(mainwin, width=200, height=70)
        frame1.pack_propagate(0)
        frame1.grid(row=0, column=0, columnspan=2)
        
        frame2a = tk.Frame(mainwin, width=100, height=65)
        frame2a.pack_propagate(0)
        frame2a.grid(row=1, column=0)

        frame2b = tk.Frame(mainwin, width=100, height=65)
        frame2b.pack_propagate(0)
        frame2b.grid(row=1, column=1)

        frame3 = tk.Frame(mainwin, width=200, height=65)
        frame3.pack_propagate(0)
        frame3.grid(row=2, column=0, columnspan=2)


        title_label = tk.Label(frame1, text='Morse Translator Beta', font=('Times New Roman', 30), borderwidth=2, relief=tk.SOLID)
        title_label.pack(fill=tk.BOTH, expand=1)

        read_label = tk.Label(frame2a, text=' Read in file: ', font=('Times New Roman', 15), anchor='w')
        read_label.pack(fill=tk.BOTH, expand=1)

        def read_button_func():
            self.__audio = None
            self.__sfreq = None
            filename = filedialog.askopenfilename(initialdir='/', title='Select file',
            filetypes=(('wav files', '*.wav')))
            self.readfile(filename)

        read_button = tk.Button(frame2b, text='Choose File...', font=('Times New Roman', 15), command=lambda: read_button_func)
        read_button.pack(fill=tk.BOTH, expand=1)

        def translate_button_func(mainwin):
            self.__intermediate_snippets = None
            self.__snippets = None
            self.__plaintext = None
            if not self.__audio is None:
                self.gen_intermediate_snippets()
                self.gen_snippets()
                self.gen_plain_text()
            else:
                return
            popup = tk.Toplevel(mainwin)
            popup.minsize(1000, 200)

            popupframe = tk.Frame(popup, width=1000, height=200)
            popupframe.pack_propagate(0)
            popupframe.grid(row=0, column=0)

            popuplabel = tk.Label(popupframe, text='Translated to: {}.'.format(self.__plaintext))
            popuplabel.pack(fill=tk.BOTH, expand=1)
            popup.mainloop()

        translate_button = tk.Button(frame3, text='Translate to Plaintext...', font=('Times New Roman', 15), command=lambda: translate_button_func(mainwin))
        translate_button.pack(fill=tk.BOTH, expand=1)
        mainwin.mainloop()

if __name__ == "__main__":
    t = MorseTranslator()


#TODO: deal with handling of last tone
#TODO: add digits
#TODO: add extra long spaces for between words
#TODO: make more elegant
#TODO: add different ways of evaluating which is on top or bottom

#write_test_math_code()