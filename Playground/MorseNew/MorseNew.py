import librosa as lr
import time as time_

#fourier decomposition
#inverse fourier transform
class MorseChar:

    #A class to store a short or long beep or pause, including how much certainty we have about
    #the value (magnitude) of the MorseChar and the length.
    #TODO: add length implementation

    #Variables:
        #__mtext
            #the string of the MorseChar itself

            #initialized as None.
            #setting mag to beep or pause without length makes it 'b' or 'p'
            #setting length to long or short without mag makes it 'l' or 's'
            #once length is included, mtext is set as follows:
                #long beep: '-'
                #short beep: '.'
                #short pause: ','
                #long pause: ';'
                #extra long pause: ':'
                #TODO: add extra long pause implementation

        #__len_quart_dist:
            #distance of magnitude from the quartile of the magnitudes in a given message of many MorseChhar's
            #positive if the distance indicates more certainty, negative if increases uncertainty
                #example: if long and mag is 5.0 more than the upper quartile, then __len_quart_dist is 5.0
                #if long and 5.0 less than upper quartile, then __len_quart_dist is -5.0
            #intialized as None

        #__len_med_dist:
            #defined in a similar way to __len_quart_dist (positive means more certain, negative means less)
            #except, measures distance to median (med)
            #intialized as None

        #__len_avg_dist:
            #defined in a similar way to others (positive means more certain, negative means less)
            #except, measures distance to avg magnitude
            #intialized as None

        #__len_meavg_dist:
            #defined in a similar way to others (positive means more certain, negative means less)
            #except, measures distance to meavg
            #meavg is (med + avg)/2
            #intialized as None

        #__len_certainty:
            #calculated uncertainty
            #mag_uncertainty = len_meavg_dist + len_avg_dist + len_med_dist + (5 * len_quart_dist)
            #IMPORTANT: weighs quartile information more heavily. This is a magic value.
            #intialized as None

    #Methods:
        #set(self, **kargs)
            #method for setting all of the variables
            #can set mtext and all mag_d's
            #when all mag_d's are set, mag_uncertainty gets set
        
        #mtext(self)
            #method to return __mtext, a protected variable
        
        #len_certainty(self)
            #method to return __len_certainty, a protected variable

    def __init__(self, **kargs):
        self.__mtext = None
        self.__len_quart_dist = None
        self.__len_med_dist = None
        self.__len_avg_dist= None
        self.__len_meavg_dist = None
        self.__len_certainty = None

        self.set(**kargs)

    #method for setting the variables
    def set(self, **kargs):
        for k, v in kargs.items():
            #store original key and value for exception handling
            #then, make key and value lower case for simplicity
            o_k = k
            o_v = v

            k = k.lower()
            if isinstance(v, str):
                v = v.lower()

            #first for setting __mtext explicitly and directly
            if (k == 'mtext') or (k == 'text') or (k == 'char'):
                #value must be 'b', 'p', 'l', 's', '.', '-', ',', ';', or ':'.
                if (v == 'b') or (v == 'p') or (v == 'l') or (v == 's')                 \
                    or (v == '.') or (v == '-') or (v == ',') or (v == ';') or (v == ':'):
                    #correct value, set it
                    self.__mtext = v
                else:
                    #invalid value, raise Exception
                    raise Exception('Invalid value for mtext/text/char argument provided ({}).'.format(str(o_v)))
            #next for setting mag, which implicitly sets __mtext
            elif (k == 'magnitude') or (k == 'mag') or (k == 'm'):
                #value must be 'beep', 'pause', 'b', or 'p'.
                if (v == 'beep') or (v == 'b'):
                    #we can now set __mtext
                    #if __mtext is None, we only have the mag information and will set it accordingly (to b)
                    #if __mtext is 'l', we already have length and will set it to '-'
                    #if __mtext is 's', we already have length and will set it to '.'
                    if self.__mtext is None:
                        self.__mtext = 'b'
                    elif self.__mtext == 'l':
                        self.__mtext = '-'
                    elif self.__mtext == 's':
                        self.__mtext = '.'
                    elif self.__mtext == 'el':
                        #raise exception (because it will be extralong)
                        raise Exception('Tried to set an extra long MorseChar to a beep.')
                    else:
                        #raise exception (this should really not happen)
                        raise Exception('Tried to set a MorseChar with __mtext ({}) to beep.'.format(str(self.__mtext)))
                elif (v == 'pause') or (v == 'p'):
                    #we can now set __mtext
                    #if __mtext is None, we only have the mag information and will set it accordingly (to p)
                    #if __mtext is 'l', we already have length and will set it to ';'
                    #if __mtext is 's', we already have length and will set it to ','
                    #if __mtext is 'el', we already have length and will set it to ':'
                    if self.__mtext is None:
                        self.__mtext = 'p'
                    elif self.__mtext == 'l':
                        self.__mtext = ';'
                    elif self.__mtext == 's':
                        self.__mtext = ','
                    elif self.__mtext == 'el':
                        self.__mtext = ':'
                    else:
                        #raise exception (this should really not happen).
                        raise Exception('Tried to set a MorseChar with __mtext ({}) to pause'.format(str(self.__mtext)))
                else:
                    #invalid value, raise exception
                    raise Exception('Invalid value for magnitude/mag/m argument provided ({}).'.format(str(o_v)))
            #next for setting length, which implicitly sets __mtext
            elif (k == 'length') or (k == 'len') or (k == 'l'):
                #value must be 'long', 'short', 'extra long', 'extra_long', 'elong', 'l', 's', 'el'
                if (v == 'long') or (v == 'l'):
                    #we can now set __mtext
                    #if __mtext is None we set it to 'l'
                    #if __mtext is b we set it to '-'
                    #if __mtext is p we set it to ';'
                    if self.__mtext is None:
                        self.__mtext = 'l'
                    elif self.__mtext == 'b':
                        self.__mtext = '-'
                    elif self.__mtext == 'p':
                        self.__mtext = ';'
                    else:
                        #raise exception (this really should not happen)
                        raise Exception('Tried to set a MorseChar with __mtext({}) to long.'.format(str(self.__mtext)))
                elif (v == 'short') or (v == 's'):
                    #we can now set __mtext
                    #if __mtext is None we set it to 's'
                    #if __mtext is b we set it to '.'
                    #if __mtext is p we set it to ','
                    if self.__mtext is None:
                        self.__mtext = 's'
                    elif self.__mtext == 'b':
                        self.__mtext = '.'
                    elif self.__mtext == 'p':
                        self.__mtext = ','
                    else:
                        #raise exception (this really should not happen)
                        raise Exception('Tried to set a MorseChar with __mtext({}) to short.'.format(str(self.__mtext)))
                elif (v == 'extra long') or (v == 'extra_long') or (v == 'elong') or (v == 'el'):
                    #we can now set __mtext
                    #if __mtext is None we set it to 'el'
                    #if __mtext is b we raise an Exception, because there should be no extra long beeps.
                    #if __mtext is p we set it to ':'
                    if self.__mtext is None:
                        self.__mtext = 'el'
                    elif self.__mtext == 'p':
                        self.__mtext = ':'
                    elif self.__mtext == 'b':
                        #raise Exception
                        raise Exception('Tried to set a beep MorseChar to extra long.')
                    else:
                        #raise exception (this really should not happen)
                        raise Exception('Tried to set a MorseChar with __mtext({}) to extra long.'.format(str(self.__mtext)))
                else:
                    #invalid value, raise exception
                    raise Exception('Invalid value for length/len/l argument provided ({}).'.format(str(o_v)))
            #next for setting len_quart_dist
            elif (k == 'len_quart_dist') or (k == 'l_q_d') or (k == 'lqd'):
                #the value must be a float
                try:
                    self.__len_quart_dist = float(v)
                except Exception as e:
                    raise Exception('Tried to set len_quart_dist to nonfloat value ({}), throwing Exception: {}.').format(str(o_v), str(e))
            #next for setting len_med_dist
            elif (k == 'len_med_dist') or (k == 'l_m_d') or (k == 'lmd'):
                #the value must be a float
                try:
                    self.__len_med_dist = float(v)
                except Exception as e:
                    raise Exception('Tried to set len_med_dist to nonfloat value ({}), throwing Exception: {}.').format(str(o_v), str(e))
            #next for setting len_avg_dist
            elif (k == 'len_avg_dist') or (k == 'l_a_d') or (k == 'lad'):
                #the value must be a float
                try:
                    self.__len_avg_dist = float(v)
                except Exception as e:
                    raise Exception('Tried to set len_avg_dist to nonfloat value ({}), throwing Exception: {}.').format(str(o_v), str(e))
            #next for setting len_meavg_dist
            elif (k == 'len_meavg_dist') or (k == 'l_ma_d') or (k == 'lmad'):
                #the value must be a float
                try:
                    self.__len_meavg_dist = float(v)
                except Exception as e:
                    raise Exception('Tried to set len_meavg_dist to nonfloat value ({}), throwing Exception: {}.').format(str(o_v), str(e))
            #TODO: add length stuff
            else:
                #invalid key
                raise Exception('Invalid key ({}) provided.'.format(str(o_k)))

        #once all the vars are set, we calculate and set len_certainty (if we can)
        if not((self.__len_quart_dist is None) or (self.__len_med_dist is None) or (self.__len_avg_dist is None)\
            or (self.__len_meavg_dist is None)):
            #IMPORTANT: this formula is somewhat random.
            self.__len_certainty = (5 * self.__len_quart_dist) + self.__len_med_dist \
                + self.__len_avg_dist + self.__len_meavg_dist

    #method for accessing __mtext
    def mtext(self):
        return self.__mtext
    
    #method for accessing __len_certainty
    def len_certainty(self):
        return self.__len_certainty

class Translator:

    #A class to translate morse code and run the subsequent GUI
    
    #Variablaes:
        #__raw_audio
            #raw audio from the file that is opened
            #initialized as None and set to None in reset method
        #__clumps
            #list of clumps formed from raw audio
            #each clump is a tuple of a length and a boolean
            #True indicates a beep, False a pause
            #initialized as None and set to None in reset method
        #__morsechars
            #list of MorseChar's formed from the clumps
            #only works for single words, not spaces in between words yet
            #initialized as None and set to None in reset method
        #__plaintext
            #text that is generated from __morsechars
            #in method to generate this, we preform analysis on how sure we are of each char
            #initialized as None and set to None in reset method
        #__timing_storage
            #dictionary of time taken by certain methods to execute
            #intialized as {} and set to {} by reset method
        #__CLEANING_TOLERANCE
            #magic value for cleaning up __raw_audio into clumps
            #the absolute value of the numerical derivative plus the absolute value of the audio at that point
                #must be greater than 2 * __CLEANING_TOLERANCE * (med_mag_audio + avg_mag_audio)/2
        #__LETTERS_TO_DOTS_DITCT
            #dictionary with dots and dashes values for each character
            #initialized manually
        #__DOTS_TO_LETTERS_DICT
            #dictionary with character value for each string of dots and dashes
            #initialzed using __LETTERS_TO_DOTS_DICT
    
    #Methods:
        #__reset(self):
            #sets all variables to initialized value
        #__read_file(self, filename)
            #reads in audio using librosa, not much that can be done
            #adds a time to __timing_storage
        #__gen_clumps_quick(self)
            #generates clumps from raw_audio
            #raw_audio must be read in before hand, otherwise will throw an exception

            #quick only compares mag of audio and derivative with avg mag of audio
            #takes less time because requires no ordering or anything, but less accurate possibly
        #__gen_clumps_med(self)
            #generates clumps from raw_audio
            #raw_audio must be read in before hand, otherwise will throw an exception

            #med compares mag of audio with avg mag of audio and derivative with avg mag of derivative
            #takes more time because than quick because calculating two averages, but less accurate than slow because
            #derivative can blow up, swaying the avg.
        #__gen_clumps_long(self)
            #generates clumps from raw_audio
            #raw_audio must be read in before hand, otherwise will throw an exception

            #med compares mag of audio with meavg mag of audio and derivative with meavg mag of derivative
            #takes more time because than others because must reorder and copy lists to get median for meavg
        #__gen_morsechars(self)
            #generates morsechars from __clumps
            #__clumps must be finished before we start this method
            #basically a complicated if statement that determines the mtext and certainty of each morsechar
        #__gen_plaintext_simple(self)
            #generates plaintext from __morsechars
            #__morsechars must be finished before we start this method
            #assumes that data is nice, no mistake handling...
    @staticmethod
    def new_possibilities_dict():
        d = {}
        for i in range(97, 123):
            d[chr(i)] = 0.0
        return d
    
    def __init__(self):
        self.__raw_audio = None 
        self.__clumps = None
        self.__morsechars = None
        self.__plaintext = None
        self.__timing_storage = {}
        self.__CLEANING_TOLERANCE = 0.05
        self.__LETTERS_TO_DOTS_DICT = {}
        self.__DOTS_TO_LETTERS_DICT = {}

        #initialize big dictionaries
        self.__LETTERS_TO_DOTS_DICT['a'] = '.,-;'
        self.__LETTERS_TO_DOTS_DICT['b'] = '-,.,.,.;'
        self.__LETTERS_TO_DOTS_DICT['c'] = '-,.,-,.;'
        self.__LETTERS_TO_DOTS_DICT['d'] = '-,.,.;'
        self.__LETTERS_TO_DOTS_DICT['e'] = '.;'
        self.__LETTERS_TO_DOTS_DICT['f'] = '.,.,-,.;'
        self.__LETTERS_TO_DOTS_DICT['g'] = '-,-,.;'
        self.__LETTERS_TO_DOTS_DICT['h'] = '.,.,.,.;'
        self.__LETTERS_TO_DOTS_DICT['i'] = '.,.;'
        self.__LETTERS_TO_DOTS_DICT['j'] = '.,-,-,-;'
        self.__LETTERS_TO_DOTS_DICT['k'] = '-,.,-;'
        self.__LETTERS_TO_DOTS_DICT['l'] = '.,-,.,.;'
        self.__LETTERS_TO_DOTS_DICT['m'] = '-,-;'
        self.__LETTERS_TO_DOTS_DICT['n'] = '-,.;'
        self.__LETTERS_TO_DOTS_DICT['o'] = '-,-,-;'
        self.__LETTERS_TO_DOTS_DICT['p'] = '.,-,-,.;'
        self.__LETTERS_TO_DOTS_DICT['q'] = '-,-,.,-;'
        self.__LETTERS_TO_DOTS_DICT['r'] = '.,-,.;'
        self.__LETTERS_TO_DOTS_DICT['s'] = '.,.,.;'
        self.__LETTERS_TO_DOTS_DICT['t'] = '-;'
        self.__LETTERS_TO_DOTS_DICT['u'] = '.,.,-;'
        self.__LETTERS_TO_DOTS_DICT['v'] = '.,.,.,-;'
        self.__LETTERS_TO_DOTS_DICT['w'] = '.,-,-;'
        self.__LETTERS_TO_DOTS_DICT['x'] = '-,.,.,-;'
        self.__LETTERS_TO_DOTS_DICT['y'] = '-,.,-,-;'
        self.__LETTERS_TO_DOTS_DICT['z'] = '-,-,.,.;'
        #reverse dictionary for __DOTS_TO_LETTERS_DICT
        for key, val in self.__LETTERS_TO_DOTS_DICT.items():
            self.__DOTS_TO_LETTERS_DICT[val] = key
    
    def __reset(self):
        self.__raw_audio = None 
        self.__clumps = None
        self.__morsechars = None
        self.__plaintext = None
        self.__timing_storage = {}
        self.__CLEANING_TOLERANCE = 0.05
    
    def __read_file(self, filename):
        #TODO: proper exception handling? idk
        time = time_.time() * 1_000

        if not isinstance(filename, str):
            raise Exception('Invalid path for __read_file(self, filename): not a str.')
        try:
            self.__raw_audio, _ = lr.load(filename)
        except Exception as e:
            print('Could not read audio file ({}).'.format(str(e)))
        
        time = time_.time() * 1_000 - time
        self.__timing_storage['Reading in file'] = time
        
    #quickest method for generating clumps
    def __gen_clumps_quick(self):
        #TODO: integrate this in better with the MorseChar structure?
        #must already have our raw audio read in.
        if (self.__raw_audio is None) or (len(self.__raw_audio) == 0):
            raise Exception('Tried to run __gen_clumps_quick(self) without reading in audio.')
        
        #time for total time to gen clumps with quick method
        total_time = time_.time() * 1_000
        #time variable to be used recording times later
        time = 0

        #first we calculate the avg magnitude of __raw_audio
        #record this time
        time = time_.time() * 1_000
        avg_mag = 0.0
        for num in self.__raw_audio:
            avg_mag += abs(num)
        avg_mag /= len(self.__raw_audio)
        #put time in __timing_storage
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Calculating average magnitude in __gen_clumps_quick (sub-time)'] = time

        #new list for cleaned audio (just 1's and 0's)
        clean_audio = []
        #we now go through __raw_audio, calculating derivative and seeing if we add a 1 or 0 to clean_audio
        #record this time as well
        #TODO: think about whether it is ok to skip first and last index
        #TODO: think about whether smart to use simple computational derivative
        time = time_.time() * 1_000
        for i in range(1, len(self.__raw_audio) - 1):
            #calculate derivative at this point and grab mag
            deriv = (self.__raw_audio[i + 1] - self.__raw_audio[i - 1]) / 2
            mag = self.__raw_audio[i]
            #see if it satisfies requirement to be considered a tone for clean_audio
            if (abs(mag) + abs(deriv)) >= (2 * self.__CLEANING_TOLERANCE * avg_mag):
                clean_audio.append(1)
            else:
                clean_audio.append(0)
        #put time into __timing_storage
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Generating initial clean_audio in __gen_clumps_quick (sub-time)'] = time

        #next up, quick fix for clean_audio
        #should clean up noise, relying on previous and next elements
            #ex1 
                #'...101...' -> '...111...'
            #ex2
                #'...010...' -> '...000...'
            #basically cannot have single digits surrounded by not matching ones
            #if at beginning:
                #'011...' -> '111...'
                #'100...' -> '000...'
            #if at end:
                #'...110' -> '...111'
                #'...001' -> '...000'
        #TODO: determine if this makes sense? because I am very unsure
        #record time as well
        time = time_.time() * 1_000
        #deal with beginning first, but only if length is longer than 2
        if len(clean_audio) <= 2:
            raise Exception('Clean audio only length {} in __gen_clumps_quick.'.format(len(clean_audio)))
        if (clean_audio[1] == clean_audio[2]) and not (clean_audio[0] == clean_audio[1]):
            clean_audio[0] = clean_audio[1]
        #now iterate through all indexes except beginning and end
        for i in range(1, len(clean_audio) - 1):
            #check condition: if before and after are equal, but not to middle, then change middle
            before, current, after = clean_audio[i - 1: i+2]
            if (before == after) and not (before == current):
                #change the current one in the list
                clean_audio[i] = before
        #now deal with end
        if (clean_audio[-3] == clean_audio[-2]) and not (clean_audio[-2] == clean_audio[-1]):
            clean_audio[-1] = clean_audio[-2]
        #put time into __timing_storage now
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Executing dirty fix of clean_audio in __gen_clumps_quick (sub-time)'] = time

        #clean_audio should be nice and uniform now, we can begin generating the actual clumps
        #record this time as well
        time = time_.time() * 1_000
        self.__clumps = []
        i = 0
        while i < len(clean_audio):
            clump_length = 1
            val = clean_audio[i]
            #iterate through to end of clump
            while (i < len(clean_audio) - 1) and (clean_audio[i + 1] == val):
                clump_length += 1
                i += 1
            #add clump to __clumps (only if length is more than 1)
            if clump_length > 1:
                self.__clumps.append((clump_length, bool(val)))
            #iterate once more to get to start of next clump
            i += 1
        #put time into __timing_storage now
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Creating actual clumps from clean_audio in __gen_clumps_quick (sub-time)'] = time

        #now done, record total time
        total_time = time_.time() * 1_000 - total_time
        self.__timing_storage['Total generating clumps in __gen_clumps_quick (super-time)'] = total_time
    
    #medium method for generating clumps
    def __gen_clumps_med(self):
        #TODO: integrate this in better with the MorseChar structure?
        #must already have our raw audio read in.
        if (self.__raw_audio is None) or (len(self.__raw_audio) == 0):
            raise Exception('Tried to run __gen_clumps_med(self) without reading in audio.')
        
        #time for total time to gen clumps with quick method
        total_time = time_.time() * 1_000
        #time variable to be used recording times later
        time = 0

        #first we calculate the avg magnitude of __raw_audio and of derivatives
        derivs = []
        #record this time
        time = time_.time() * 1_000
        avg_mag = abs(self.__raw_audio[0])
        avg_d_mag = 0.0
        for i in range(1, len(self.__raw_audio) - 1):
            avg_mag += abs(self.__raw_audio[i])
            d = (self.__raw_audio[i + 1] - self.__raw_audio[i - 1])/2
            derivs.append(d)
            avg_d_mag += abs(d)
        avg_mag += abs(self.__raw_audio[-1])
        avg_mag /= len(self.__raw_audio)
        avg_d_mag /= len(derivs)
        #put time in __timing_storage
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Calculating average magnitude of BOTH in __gen_clumps_med (sub-time)'] = time

        #new list for cleaned audio (just 1's and 0's)
        clean_audio = []
        #we now go through __raw_audio, calculating derivative and seeing if we add a 1 or 0 to clean_audio
        #record this time as well
        #TODO: think about whether it is ok to skip first and last index
        #TODO: think about whether smart to use simple computational derivative
        time = time_.time() * 1_000
        for i in range(1, len(self.__raw_audio) - 1):
            #calculate derivative at this point and grab mag
            deriv = derivs[i - 1]
            mag = self.__raw_audio[i]
            #see if it satisfies requirement to be considered a tone for clean_audio
            if (abs(mag) + abs(deriv)) >= (self.__CLEANING_TOLERANCE*(avg_mag + avg_d_mag)):
                clean_audio.append(1)
            else:
                clean_audio.append(0)
        #put time into __timing_storage
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Generating initial clean_audio in __gen_clumps_med (sub-time), should be less...'] = time

        #next up, quick fix for clean_audio
        #should clean up noise, relying on previous and next elements
            #ex1 
                #'...101...' -> '...111...'
            #ex2
                #'...010...' -> '...000...'
            #basically cannot have single digits surrounded by not matching ones
            #if at beginning:
                #'011...' -> '111...'
                #'100...' -> '000...'
            #if at end:
                #'...110' -> '...111'
                #'...001' -> '...000'
        #TODO: determine if this makes sense? because I am very unsure
        #record time as well
        time = time_.time() * 1_000
        #deal with beginning first, but only if length is longer than 2
        if len(clean_audio) <= 2:
            raise Exception('Clean audio only length {} in __gen_clumps_med.'.format(len(clean_audio)))
        if (clean_audio[1] == clean_audio[2]) and not (clean_audio[0] == clean_audio[1]):
            clean_audio[0] = clean_audio[1]
        #now iterate through all indexes except beginning and end
        for i in range(1, len(clean_audio) - 1):
            #check condition: if before and after are equal, but not to middle, then change middle
            before, current, after = clean_audio[i - 1: i+2]
            if (before == after) and not (before == current):
                #change the current one in the list
                clean_audio[i] = before
        #now deal with end
        if (clean_audio[-3] == clean_audio[-2]) and not (clean_audio[-2] == clean_audio[-1]):
            clean_audio[-1] = clean_audio[-2]
        #put time into __timing_storage now
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Executing dirty fix of clean_audio in __gen_clumps_med (sub-time)'] = time

        #clean_audio should be nice and uniform now, we can begin generating the actual clumps
        #record this time as well
        time = time_.time() * 1_000
        self.__clumps = []
        i = 0
        while i < len(clean_audio):
            clump_length = 1
            val = clean_audio[i]
            #iterate through to end of clump
            while (i < len(clean_audio) - 1) and (clean_audio[i + 1] == val):
                clump_length += 1
                i += 1
            #add clump to __clumps (only if length is more than 1)
            if clump_length > 1:
                self.__clumps.append((clump_length, bool(val)))
            #iterate once more to get to start of next clump
            i += 1
        #put time into __timing_storage now
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Creating actual clumps from clean_audio in __gen_clumps_med (sub-time)'] = time

        #now done, record total time
        total_time = time_.time() * 1_000 - total_time
        self.__timing_storage['Total generating clumps in __gen_clumps_med (super-time)'] = total_time

    #long method for generating clumps
    def __gen_clumps_long(self):
        #TODO: integrate this in better with the MorseChar structure?
        #must already have our raw audio read in.
        if (self.__raw_audio is None) or (len(self.__raw_audio) == 0):
            raise Exception('Tried to run __gen_clumps_long(self) without reading in audio.')
        
        #time for total time to gen clumps with quick method
        total_time = time_.time() * 1_000
        #time variable to be used recording times later
        time = 0

        #first we calculate the avg magnitude of __raw_audio and of derivatives
        #also, copy over __raw_audio to a copy list so can find median
        derivs = []
        copy_raw = []
        #record this time
        time = time_.time() * 1_000
        avg_mag = abs(self.__raw_audio[0])
        avg_d_mag = 0.0
        copy_raw.append(abs(self.__raw_audio[0]))
        for i in range(1, len(self.__raw_audio) - 1):
            avg_mag += abs(self.__raw_audio[i])
            copy_raw.append(abs(self.__raw_audio[i]))
            d = (self.__raw_audio[i + 1] - self.__raw_audio[i - 1])/2
            derivs.append(abs(d))
            avg_d_mag += abs(d)
        avg_mag += abs(self.__raw_audio[-1])
        copy_raw.append(abs(self.__raw_audio[-1]))
        
        avg_mag /= len(self.__raw_audio)
        avg_d_mag /= len(derivs)
        #find median times by sorting
        derivs.sort()
        copy_raw.sort()
        med_mag = copy_raw[int(len(copy_raw)/2)]
        med_d_mag = derivs[int(len(derivs)/2)]

        meavg_mag = avg_mag + med_mag
        meavg_d_mag = avg_d_mag + med_d_mag
        #put time in __timing_storage
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Calculating average and median magnitude of BOTH in __gen_clumps_long (sub-time)'] = time

        #new list for cleaned audio (just 1's and 0's)
        clean_audio = []
        #we now go through __raw_audio, calculating derivative and seeing if we add a 1 or 0 to clean_audio
        #record this time as well
        #TODO: think about whether it is ok to skip first and last index
        #TODO: think about whether smart to use simple computational derivative
        time = time_.time() * 1_000
        for i in range(1, len(self.__raw_audio) - 1):
            #calculate derivative at this point and grab mag
            deriv = (self.__raw_audio[i + 1] - self.__raw_audio[i - 1])/2
            mag = self.__raw_audio[i]
            #see if it satisfies requirement to be considered a tone for clean_audio
            if (abs(mag) >= self.__CLEANING_TOLERANCE * meavg_mag) and (abs(deriv) >= self.__CLEANING_TOLERANCE * meavg_d_mag):
                clean_audio.append(1)
            else:
                clean_audio.append(0)
        #put time into __timing_storage
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Generating initial clean_audio in __gen_clumps_long (sub-time)'] = time

        #next up, quick fix for clean_audio
        #should clean up noise, relying on previous and next elements
            #ex1 
                #'...101...' -> '...111...'
            #ex2
                #'...010...' -> '...000...'
            #basically cannot have single digits surrounded by not matching ones
            #if at beginning:
                #'011...' -> '111...'
                #'100...' -> '000...'
            #if at end:
                #'...110' -> '...111'
                #'...001' -> '...000'
        #TODO: determine if this makes sense? because I am very unsure
        #record time as well
        time = time_.time() * 1_000
        #deal with beginning first, but only if length is longer than 2
        if len(clean_audio) <= 2:
            raise Exception('Clean audio only length {} in __gen_clumps_long.'.format(len(clean_audio)))
        if (clean_audio[1] == clean_audio[2]) and not (clean_audio[0] == clean_audio[1]):
            clean_audio[0] = clean_audio[1]
        #now iterate through all indexes except beginning and end
        for i in range(1, len(clean_audio) - 1):
            #check condition: if before and after are equal, but not to middle, then change middle
            before, current, after = clean_audio[i - 1: i+2]
            if (before == after) and not (before == current):
                #change the current one in the list
                clean_audio[i] = before
        #now deal with end
        if (clean_audio[-3] == clean_audio[-2]) and not (clean_audio[-2] == clean_audio[-1]):
            clean_audio[-1] = clean_audio[-2]
        #put time into __timing_storage now
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Executing dirty fix of clean_audio in __gen_clumps_long (sub-time)'] = time

        #clean_audio should be nice and uniform now, we can begin generating the actual clumps
        #record this time as well
        time = time_.time() * 1_000
        self.__clumps = []
        i = 0
        while i < len(clean_audio):
            clump_length = 1
            val = clean_audio[i]
            #iterate through to end of clump
            while (i < len(clean_audio) - 1) and (clean_audio[i + 1] == val):
                clump_length += 1
                i += 1
            #add clump to __clumps (only if length is more than 1)
            if clump_length > 1:
                self.__clumps.append((clump_length, bool(val)))
            #iterate once more to get to start of next clump
            i += 1
        #put time into __timing_storage now
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Creating actual clumps from clean_audio in __gen_clumps_long (sub-time)'] = time

        #now done, record total time
        total_time = time_.time() * 1_000 - total_time
        self.__timing_storage['Total generating clumps in __gen_clumps_long (super-time)'] = total_time
    
    #method for generating MorseChar's
    def __gen_morsechars(self):
        #TODO: deal with extra long pauses
        #first check that we have clumps already
        if (self.__clumps is None) or (len(self.__clumps) == 0):
            raise Exception('Tried to run __gen_morsechars without having __clumps present.')
        #time variables to keep track of time taken by method
        total_time = time_.time() * 1_000
        time = 0

        #create beep_lengths and pause_lengths to store lengths of all clumps to calculate statistical info
            #(med, quartiles)
        #record this time
        time = time_.time() * 1_000
        beep_lengths = []
        pause_lengths = []
        beep_len_avg = 0.0
        pause_len_avg = 0.0
        for clength, cval in self.__clumps:
            if cval:
                beep_len_avg += clength
                beep_lengths.append(clength)
            else:
                pause_len_avg += clength
                pause_lengths.append(clength)
        #avoid dividing by 0 when calculating averages
        if len(beep_lengths) > 0:
            beep_len_avg /= len(beep_lengths)
        else:
            beep_len_avg = 0.0
        
        if len(pause_lengths) > 0:
            pause_len_avg /= len(pause_lengths)
        else:
            pause_len_avg = 0.0
        #sort to find median and quartiles
        beep_lengths.sort()
        beep_len_med = beep_lengths[int(len(beep_lengths) / 2)]
        beep_len_uquart = beep_lengths[int((3/4) * len(beep_lengths))]
        beep_len_lquart = beep_lengths[int(len(beep_lengths) / 4)]
        beep_len_meavg = (beep_len_avg + beep_len_med) / 2
            #TODO: consider issue of quartiles for pauses...
        pause_lengths.sort()
        pause_len_med = pause_lengths[int(len(pause_lengths) / 2)]
        pause_len_uquart = pause_lengths[int((3/4) * len(pause_lengths))]
        pause_len_lquart = pause_lengths[int(len(pause_lengths) / 4)]
        pause_len_meavg = (pause_len_avg + pause_len_med) / 2
        #put time into timing_storage now
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Calculating statistical info about lengths in __gen_morsechars (sub-time)'] = time

        #now, initialize __morsechars and go through adding chars
            #making sure to update the distances from the expected result for each individual char
        #record this time as well
        time = time_.time() * 1_000
        self.__morsechars = []
        #first, check that beep_len_meavg and pause_len_meavg are not 0 to avoid dividing by 0 later
        if beep_len_meavg == 0:
            raise Exception('beep_len_meavg was 0 in __gen_morse_chars; this would cause a divide by 0 error later.')
        if pause_len_meavg == 0:
            raise Exception('pause_len_meavg was 0 in __gen_morse_chars; this would cause a divide by 0 error later.')
        #iterate through
        for clength, cval in self.__clumps:
            #we keep track of mtext initially, and keep margs as a dictionary with keyworded arguments to feed
                #to the character later
            mtext = ''
            margs = {}
            if cval:
                #a beep
                #we check conditions that indicate whether long or short
                #start with strongest
                if (clength > beep_len_uquart) and (clength > beep_len_avg):
                    #greater than the upper quartile and avg (fixes issue when upperquart is low)
                    #a long beep
                    mtext = '-'
                elif (clength < beep_len_lquart) and (clength < beep_len_avg):
                    #less than the bottom quartile and avg (fixes issue when lowerquart is high)
                    #a short beep
                    mtext = '.'
                elif (clength > beep_len_avg) and (clength > beep_len_med):
                    #greater than both the avg and med
                    #a long beep
                    mtext = '-'
                elif (clength < beep_len_avg) and (clength < beep_len_med):
                    #less than both the avg and med
                    #a short beep
                    mtext = '.'
                elif clength > beep_len_meavg:
                    #greater than the meavg
                    #a long beep
                    mtext = '-'
                else:
                    #less than the meavg
                    #a short beep
                    mtext = '.'
            else:
                #a pause
                #we check conditions that indicate whether long or short
                #start with strongest
                if (clength > pause_len_uquart) and (clength > pause_len_avg):
                    #greater than the upper quartile and avg (fixes issue when upperquart is low)
                    #a long pause
                    mtext = ';'
                elif (clength < pause_len_lquart) and (clength < pause_len_avg):
                    #less than the bottom quartile and avg (fixes issue when lowerquart is high)
                    #a short pause
                    mtext = ','
                elif (clength > pause_len_avg) and (clength > pause_len_med):
                    #greater than both the avg and med
                    #a long pause
                    mtext = ';'
                elif (clength < pause_len_avg) and (clength < pause_len_med):
                    #less than both the avg and med
                    #a short pause
                    mtext = ','
                elif clength > pause_len_meavg:
                    #greater than the meavg
                    #a long pause
                    mtext = ';'
                else:
                    #less than the meavg
                    #a short pause
                    mtext = ','
            #at this point, we know what mtext is and can add it to margs
            margs['mtext'] = mtext
            #we now add the rest of the args depending on what mtext
            #TODO: this is redundant, but easier to read
            if mtext == '-':
                #long beep
                #since a long beep, clength should be above beep_len_uquart
                #so, len_quart_dist = (clength - beep_len_uquart) / beep_len_meavg
                #(divide to normalize)
                margs['len_quart_dist'] = (clength - beep_len_uquart) / beep_len_meavg
                #for rest, since long beep we use beep info we already have and assume that clength is greater than
                    #each piece of info (that way, positive means more certain)
                margs['len_med_dist'] = (clength - beep_len_med) / beep_len_meavg
                margs['len_avg_dist'] = (clength - beep_len_avg) / beep_len_meavg
                margs['len_meavg_dist'] = (clength - beep_len_meavg) / beep_len_meavg
            elif mtext == ';':
                #long pause
                #since a long pause, clength should be above pause_len_uquart
                #so, len_quart_dist = (clength - pause_len_uquart) / pause_len_meavg
                #(divide to normalize)
                margs['len_quart_dist'] = (clength - pause_len_uquart) / pause_len_meavg
                #for rest, since long pause we use pause info we already have and assume that clength is greater
                    #than each piece of info (that way, positive means more certain)
                margs['len_med_dist'] = (clength - pause_len_med) / pause_len_meavg
                margs['len_avg_dist'] = (clength - pause_len_avg) / pause_len_meavg
                margs['len_meavg_dist'] = (clength - pause_len_meavg) / pause_len_meavg
            elif mtext == '.':
                #short beep
                #since a short beep, clength should be below beep_len_lquart
                #so, len_quart_dist = (beep_len_lquart - clength) / beep_len_meavg
                #(divide to normalize)
                margs['len_quart_dist'] = (beep_len_lquart - clength) / beep_len_meavg
                #for rest, since short beep we use beep info we already have and assume that clength is less
                    #than each pice of info (that way, positive means more certain)
                margs['len_med_dist'] = (beep_len_med - clength) / beep_len_meavg
                margs['len_avg_dist'] = (beep_len_avg - clength) / beep_len_meavg
                margs['len_meavg_dist'] = (beep_len_meavg - clength) / beep_len_meavg
            elif mtext == ',':
                #short pause
                #since a short pause, clength should be below pause_len_lquart
                #so, len_quart_dist = (pause_len_lquart - clength) / pause_len_meavg
                #(divide to normalize)
                margs['len_quart_dist'] = (pause_len_lquart - clength) / pause_len_meavg
                #for rest, since short pause we use pause info we already have and assume that clength is less
                    #than each pice of info (that way, positive means more certain)
                margs['len_med_dist'] = (pause_len_med - clength) / pause_len_meavg
                margs['len_avg_dist'] = (pause_len_avg - clength) / pause_len_meavg
                margs['len_meavg_dist'] = (pause_len_meavg - clength) / pause_len_meavg
            else:
                #this really should not happen, because there is nothing else it can be assinged to
                try:
                    mtext = str(mtext)
                except:
                    mtext = 'COULD NOT CONVERT MTEXT TO STR!'
                raise Exception(f'mtext of morsechar was \"{mtext}\".')
            
            #at this point, we can add a new MorseChar constructed with margs to the list
            self.__morsechars.append(MorseChar(**margs))
        #put time into timing_storage now
        time = time_.time() * 1_000 - time
        self.__timing_storage['     Constructing and adding morsechars based on statistical info in __gen_morsechars (sub-time).'] = time

        #put total time into timing_storage now
        total_time = time_.time() * 1_000 - total_time
        self.__timing_storage['Total time for executing __gen_morsechars (super-time).'] = total_time

    #method for generating plaintext
    def __gen_plaintext_simple(self):
        if (self.__morsechars is None) or (len(self.__morsechars) == 0):
            raise Exception('Tried to run __gen_plaintext without having __morsechars present.')
        
        #record this time
        total_time = time_.time() * 1_000
        #initiatilze ptext, then add all of the mtext's of the elements of __morsechars
        ptext = ''
        for m in self.__morsechars:
            ptext += m.mtext()

        #want to make sure that ptext starts at a beep
        #already know that ptext is alternating between pauses and beeps
        #so, only trim if first is a pause
        #know ptext is one long at least because we already required that len(self.__morsechars) != 0
        if (ptext[0] == ',') or (ptext[0] == ';') or (ptext[0] == ':'):
            ptext = ptext[1:]

        #this method assumes that ptext is pretty well formatted, with no mistakes
        #know that already to the point where ptext is alternating spaces and pauses
        #so, split by semicolons and continue from there
        ptext = ptext.split(';')
        for i, char in enumerate(ptext):
            #if we find char in our dict, then we make it what it corresponds to 
            char += ';'
            if char in self.__DOTS_TO_LETTERS_DICT:
                ptext[i] = self.__DOTS_TO_LETTERS_DICT[char]
            else:
                #did not find it, make it a '?'
                ptext[i] = '?'
        #join together ptext and set __plaintext to it
        self.__plaintext = ''.join(ptext)
        #put this time into __timing_storage now
        total_time = time_.time() * 1_000 - total_time
        self.__timing_storage['Executing __gen_plaintext_simple'] = total_time

    def __gen_plaintext_complicated():
        pass

    def temp_test(self):
        self.__read_file('~/Playground/MorseNew/morsetest.wav')
        self.__gen_clumps_quick()
        
        self.__gen_morsechars()
        self.__gen_plaintext_simple()
        print(self.__plaintext)
        
        



#t = Translator()
#t.temp_test()

#TODO: aesthetic reordering (reorder quart and stuff).., fixing string formatting