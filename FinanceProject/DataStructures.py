import time
import os
import requests
from pathlib import Path

class Student:
    #four variables: name, schol_cap, fees, is_highlighted
    #name is student's name, schol_cap is the max amount they can pay, fees is a list of fees they owe for, is_highlighted is whether they are highlighted
    def __init__ (self, name=None, schol_cap=None, fees=None):
        self.__name = ''
        self.__schol_cap = 0.0
        self.__fees = {}
        self.__is_highlighted = False
        
        self.set_name(name)
        self.set_schol_cap(schol_cap)
        if isinstance(fees, list):
            for fee in fees:
                self.add_fee(fee)
        else:
            self.add_fee(fees)

    #setters for the four variables
    def set_name (self, name):
        if isinstance(name, str):
            self.__name = name
        else:
            self.__name = None

    def set_schol_cap (self, schol_cap):
        try:
            self.__schol_cap = round(float(schol_cap), 2)
        except:
            self.__schol_cap = None
    
    #for fees we have add and del instead of set
    def add_fee (self, fee_added, events=None):
        #adder will only be able to add one fee, as it is only called in a Fee object
        if isinstance(fee_added, Fee):
            if not(fee_added in self.__fees):
                self.__fees[fee_added] = 1
            else:
                self.__fees[fee_added] += 1
            if isinstance(events, int) and (events > 0):
                self.__fees[fee_added] = events

            #want to order the fees in here by date, do this using a helper from Roster class
            #sort by date then name
    
    def del_fee (self, fee_del):
        #del will only be able to del one fee, as it is only called in a Fee object
        #no need to check if it is a Fee, as there is no way to add a non-Fee
        if fee_del in self.__fees:
            del(self.__fees[fee_del])

    def get_events_attended(self, fee):
        if isinstance(fee, Fee):
            try:
                return self.__fees[fee]
            except:
                return 0

    #for is_highlighted we have toggle instead of set
    def toggle_highlight (self):
        self.__is_highlighted = not(self.__is_highlighted)

    #getters for the three variables
    def get_name (self):
        return self.__name
    
    def get_schol_cap (self):
        return self.__schol_cap

    def get_fees (self):
        return self.__fees

    def get_is_highlighted (self):
        return self.__is_highlighted

    #function for getting total that a student owes
    def get_total_owed (self):
        total = 0.0
        for fee in self.__fees:
            try:
                total += fee.get_cost()
            except:
                try:
                    #this is for if a str gets returned on accident, should not happen
                    total += float(fee.get_cost())
                except:
                    #just in case
                    pass
            if isinstance(self.__schol_cap, float) and total > self.__schol_cap:
                #can break out of the loop
                return self.__schol_cap
        return round(total, 2)

    #to_string(s)

    def to_writing_string (self, beg=None, end=None):
        #returns the str that will be written to save file
        #if '<' is beg and '>' is end, should be:
        #<student_save_file<student_name><student_schol_cap>>

        #handle cases for beg and end (should not really happen, as is passed in later)
        if not(isinstance(beg, str)) or not(len(beg) == 1):
            beg = chr(2)
        if not(isinstance(end, str)) or not(len(end) == 1):
            end = chr(3)
        #beg and end cannot be same
        if beg == end:
            beg = chr(2)
            end = chr(3)
        #begin the file and add the identifier
        output = beg
        output += 'student_save_file'
        #add the name inside of beg and end cell (should be defined)
        output += beg
        try:
            output += self.__name
        except:
            #want empty cell if None
            pass
        output += end

        #add the schol_cap inside of beg and end cell (is often None, so use if statement instead of try)
        output += beg
        if not (self.__schol_cap is None):
            #want empty cell if None
            output += str(self.__schol_cap)
        output += end

        #end student file and return
        output += end
        return output

    @staticmethod
    def float_to_dollar_string (cost_in_float):
        #just useful for converting floats to a useable dollar amount
        if isinstance(cost_in_float, float) or isinstance(cost_in_float, int):
            if cost_in_float < 0:
                return '-$%.2f' %float(cost_in_float)
            return '$%.2f' %float(cost_in_float)
        #at this point, probably None:
        return str(cost_in_float)



class Fee:
    #four variables: name, date, total_cost, students
    #name is the fee name, date is the date of the fee, total_cost is the total cost of the fee
    #students is the list of students who owe part of the fee
    #date requires some work to format because 1/1/11 and 01/01/2011 are equivalent
    def __init__ (self, name=None, date=None, total_cost=None, students=None):
        self.__name = ''
        self.__date = ''
        self.__total_cost = 0.0
        self.__students = []

        self.set_name(name)
        self.set_date(date)
        self.set_total_cost(total_cost)
        if isinstance(students, dict):
            self.__students = students
    
    #setters for variables
    def set_name (self, name):
        if isinstance(name, str):
            self.__name = name
        else:
            self.__name = None
    
    def set_date (self, date):
        #have to check if it is a valid date, and format it if it is
        if isinstance(date, str):
            if (date.count("/") == 2) and (len(date) >= 6 and len(date) <= 10):
                month = date[0: date.index("/")]
                if len(month) == 1:
                    month = '0' + month
                day = date[date.index("/") + 1: date.rfind("/")]
                if len(day) == 1:
                    day = '0' + day
                year = date[date.rfind("/") + 1: ]
                if len(year) == 2:
                    year = '20' + year
                self.__date = month + "/" + day + "/" + year
            else:
                self.__date = None

    def set_total_cost (self, total_cost):
        try:
            self.__total_cost = round(float(total_cost), 2)
        except:
            self.__total_cost = None
    
    #for students, there is only an add and del method
    def add_student (self, student_added, events=None):
        if isinstance(student_added, Student):
            self.__students.append(student_added)
            student_added.add_fee(self, events)
            #now sort using helper from Roster class
            self.__students.sort(key=lambda s: Roster.name_ordering_helper(s.get_name()))
        

    def del_students (self, students_del):
        #can be multiple students or one
        if isinstance(students_del, Student):
            students_del = [students_del]
				# return if not a list or iterable...
        try:
            iter(students_del)
        except:
            #not iterable
            return
				
        				
        for student in students_del:
            #IMPORTANT: FIRST DELETE THE FEE FROM THE STUDENT, THEN DELETE STUDENT FROM FEE
            if student in self.__students:
                student.del_fee(self)
                self.__students.remove(student)
        #order should be maintained

    #getters for variables
    def get_name (self):
        return self.__name

    def get_date (self):
        return self.__date

    def get_total_cost (self):
        return self.__total_cost

    def get_students (self):
        return self.__students

    #methods for getting individual cost and the rounding error that will be present
    def get_cost (self):
        try:
            events_attended = 0
            for student in self.__students:
                events_attended += student.get_events_attended(self)
            
            return round(self.__total_cost/events_attended)
        except:
            #if students is empty or the total cost is None
            return None

    def get_rounding_error (self):
        try:
            return round(self.__total_cost - len(self.__students)*self.get_cost(), 2)
        except:
            #same factors cause as cause exception for get_cost
            return None

    #to_string(s)
    def to_writing_string(self, students, beg=None, end=None):
        #returns the str that will be used for writing to save file
        #if '<' is beg and '>' is end, should be:
        #<fee_save_file<fee_name><fee_date><fee_total_cost><indexes_of_students>>

        #handle cases of beg and end (should not occurr, as they will be passed in)
        if not(isinstance(beg, str)) or not(len(beg) == 1):
            beg = chr(2)
        if not(isinstance(end, str)) or not(len(end) == 1):
            end = chr(3)
        #beg and end cannot be same
        if beg == end:
            beg = chr(2)
            end = chr(3)
        
        #begin file and add identifier
        output = beg
        output += 'fee_save_file'

        #add name in between cell (should be defined most of the time)
        output += beg
        try:
            output += self.__name
        except:
            #want empty cell if None
            pass
        output += end

        #add date in between cell (should be defined most of the time)
        output += beg
        try:
            output += self.__date
        except:
            #want empty cell if None
            pass
        output += end

        #add total_cost in between cell (should be defined most of the time)
        output += beg
        try:
            output += str(self.__total_cost)
        except:
            #want empty cell if None
            pass
        output += end
        
        #add all student indexes in a big cell
        output += beg
        for student in self.__students:
            #add index of the student in the list passed in (this makes it quicker later, only have to write indexes)
            output += beg
            try:
                output += str(students.index(student))
                #THIS IS AN ISSUE ********
            except:
                #want empty cell if not found (this REALLY should not happen)
                pass
            output += end
        output += end

        #end the file and return
        output += end
        return output



class Roster:
    #five variables: fees, students_display, students_search, poss_duplicates, ok_duplicates
    #fees is a list of Fees (ordered) for the roster
    #students_display is a list of all the Students in alphabetical order
    #students_search is a list of all the Students in order by tournaments attended, then alphabetical order
    #poss_duplicates is a list duples that are possible duplicates that are found (both Fees and Students)
    #ok_duplicates is a list of duples that gets written; it contains duplicates that the user says are ok, so that they do not get flagged later.
    #helper methods for ordering are present

    def __init__ (self):
        self.__fees = []
        self.__students_display = []
        self.__students_search = []
        self.__poss_duplicates = []
        self.__ok_duplicates = []

    def add_fees(self, fees_added):
        #can add one or multiple, should raise exception if not a list
        if isinstance(fees_added, Fee):
            fees_added = [fees_added]
        elif not isinstance(fees_added, list):
            raise Exception('Invalid parameters; tried to add a non-Fee with add_fees().')
        
        for fee in fees_added:
            #add fee if Fee and not already there (will sort later)
            if isinstance(fee, Fee) and not(fee in self.__fees):
                self.__fees.append(fee)
            #cycle through students and add them if not present (will sort later)
            for student in fee.get_students():
                if not(student in self.__students_display):
                    self.__students_display.append(student)
                if not(Student in self.__students_search):
                    self.__students_search.append(student)
        #sort fees by date helper (more recent is higher up, and unknown is highest), then by Fee name
        self.__fees.sort(key=lambda f: (Roster.date_ordering_helper(f.get_date()), f.get_name()))
        #sort students in display by name helper (alphabetical, last more important than first)
        self.__students_display.sort(key=lambda s: Roster.name_ordering_helper(s.get_name()))
        #sort students in search by num of fees helper (more fees means higher) and then by name helper (alphabetical, last more important than first)
        self.__students_search.sort(key=lambda s: (Roster.num_of_fees_ordering_helper(len(s.get_fees())), Roster.name_ordering_helper(s.get_name())))
    
    def del_fees(self, fees_del):
        #can be one or multiple
        if isinstance(fees_del, Fee):
            fees_del = [fees_del]
        for fee in fees_del:
            #delete students first, then remove fee from list
            if fee in self.__fees:
                fee.del_students(fee.get_students())
                self.__fees.remove(fee)

    #reading and writing functions
    
    def read_save_data(self, file_name):
        self.__fees = []
        self.__students_display = []
        self.__students_search = []
        #modify file_name possibly
        if os.path.exists('Finance Save Files') and not ('Finance Save Files' in file_name):
            file_name = os.path.join('Finance Save Files', file_name)
        with open(file_name, 'r') as s:
            beg = ''
            end = ''
            char = ''
            preview_char = ''
            #preview_char will be used to look one character ahead at certain points...
            #this is so that we can tell when (for example) the students list is finished (because preview_char will be end)
            #lots of Exceptions

            #ensure correct file type
            if s.read(16) != 'roster_save_file':
                raise Exception('Invalid file type; non-roster_save_file was attempted to be read.')
            #now know following format.
            beg = s.read(1)
            end = s.read(1)

            #read the Student(s) list
            if s.read(1) != beg:
                raise Exception('Invalid file format; beginning was not found where expected (beginning of students list).')
            #make preview char next (because it being end would mean an empty list), then seek back s so can reread
            preview_char = s.read(1)
            s.seek(s.tell() - 1)
            while preview_char != end:
                #loop will cover all Student(s)
                student = ''
                student_name = ''
                student_schol_cap = ''
                #ensure following file type
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of student in list).')
                if s.read(17) != 'student_save_file':
                    raise Exception('Invalid file type; non-student_save_file was attempted to be read in the students list.')
                
                #read in name
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of name of student in list).')
                char = s.read(1)
                while char != end:
                    student_name += char
                    char = s.read(1)
                if student_name == '':
                    #empty cell indicates None
                    student_name = None
                
                #read in schol_cap
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of schol_cap of student in list).')
                char = s.read(1)
                while char != end:
                    student_schol_cap += char
                    char = s.read(1)
                try:
                    student_schol_cap = float(student_schol_cap)
                except:
                    #handles empty cell and other exceptions
                    student_schol_cap = None

                #read end of student, then make and add to both lists (will order later)
                s.read(1)
                student = Student(student_name, student_schol_cap)
                self.__students_display.append(student)
                self.__students_search.append(student)

                #preview_char work (to stop loop after students list is done)
                preview_char = s.read(1)
                s.seek(s.tell() - 1)
            #read end of students list
            s.read(1)

            #read the Fee(s) list
            if s.read(1) != beg:
                raise Exception('Invalid file format; beginning was not found where expected (beginning of fees list).')
            #nake preview char next (same reasoning)
            preview_char = s.read(1)
            s.seek(s.tell() - 1)
            while preview_char != end:
                #loop will cover all Fee(s)
                fee = ''
                fee_name = ''
                fee_date = ''
                fee_total_cost = ''
                #ensure following the file type
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of fee in list).')
                if s.read(13) != 'fee_save_file':
                    raise Exception('Invalid file type; non-fee_save_file was attempted to be read in the fees list.')
                
                #read in name
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of name of fee in list).')
                char = s.read(1)
                while char != end:
                    fee_name += char
                    char = s.read(1)
                if fee_name == '':
                    #empty cell indicates None
                    fee_name = None
                
                #read in date
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of date of fee in list).')
                char = s.read(1)
                while char != end:
                    fee_date += char
                    char = s.read(1)
                if fee_date == '':
                    #empty cell indicates None
                    fee_date = None
                
                #read in total_cost
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of total_cost of fee in list).')
                char = s.read(1)
                while char != end:
                    fee_total_cost += char
                    char = s.read(1)
                try:
                    fee_total_cost = float(fee_total_cost)
                except:
                    #catches empty cell and other exceptions
                    fee_total_cost = None
                #make Fee without students
                fee = Fee(fee_name, fee_date, fee_total_cost)

                #read in all the students (will require another loop using preview_char)
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of index list of fee in list).')
                #make preview_char next (don't know how many indexes we are expecting)
                preview_char = s.read(1)
                s.seek(s.tell() - 1)
                while preview_char != end:
                    index = ''
                    if s.read(1) != beg:
                        raise Exception('Invalid file format; beginning was not found where expected (beginning of index in index list of fee in list).')
                    #read in index
                    char = s.read(1)
                    while char != end:
                        index += char
                        char = s.read(1)
                    #exception of having an empty cell is a pain, so update the preview_char before checking
                    preview_char = s.read(1)
                    s.seek(s.tell() - 1)
                    try:
                        index = int(index)
                        fee.add_students(self.__students_display[index])
                    except:
                        #handles empty cell or out of range index, both of which are bad to deal with/should not happen at all
                        pass
                #read in the end of the list of indexes and end of Fee
                s.read(1)
                s.read(1)
                #add fee to Roster
                self.__fees.append(fee)
                #make preview_char next
                preview_char = s.read(1)
                s.seek(s.tell() - 1)
            s.read(1)
            #go through duplicates now
            if s.read(1) != beg:
                raise Exception('Invalid file format; beginning was not found where expected (beginning of student dup_list).')
            #preview_char
            preview_char = s.read(1)
            s.seek(s.tell() - 1)
            while preview_char != end:
                index_one = ''
                index_two = ''
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of student dup).')
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of first index of student dup).')
                char = s.read(1)
                while char != end:
                    index_one += char
                    char = s.read(1)
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of second index of student dup).')
                char = s.read(1)
                while char != end:
                    index_two += char
                    char = s.read(1)
                #close tuple
                s.read(1)
                #do preview char work
                preview_char = s.read(1)
                s.seek(s.tell() - 1)
                try:
                    index_one = int(index_one)
                    index_two = int(index_two)
                except:
                    #should not happen
                    continue
                self.__ok_duplicates.append((self.__students_display[index_one], self.__students_display[index_two]))
            #read end
            s.read(1)
            if s.read(1) != beg:
                raise Exception('Invalid file format; beginning was not found where expected (beginning of fee dup_list).')
            preview_char = s.read(1)
            s.seek(s.tell() - 1)
            while preview_char != end:
                #open tuple
                index_one = ''
                index_two = ''
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of student dup).')
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of first index of fee dup).')
                char = s.read(1)
                while char != end:
                    index_one += char
                    char = s.read(1)
                if s.read(1) != beg:
                    raise Exception('Invalid file format; beginning was not found where expected (beginning of second index of fee dup).')
                char = s.read(1)
                while s.read(1) != end:
                    index_two += char
                    char = s.read(1)
                #close tuple
                s.read(1)
                #do preview work
                preview_char = s.read(1)
                s.seek(s.tell() - 1)
                try:
                    index_one = int(index_one)
                    index_two = int(index_two)
                except:
                    #should not happen
                    continue
                self.__ok_duplicates.append((self.__fees[index_one], self.__fees[index_two]))
                
                    
            #now need to reorder the fees and lists
            #sort fees by date helper (more recent is higher up, and unknown is highest), then by Fee name
            self.__fees.sort(key=lambda f: (Roster.date_ordering_helper(f.get_date()), f.get_name()))
            #sort students in display by name helper (alphabetical, last more important than first)
            self.__students_display.sort(key=lambda s: Roster.name_ordering_helper(s.get_name()))
            #sort students in search by num of fees helper (more fees means higher) and then by name helper (alphabetical, last more important than first)
            self.__students_search.sort(key=lambda s: (Roster.num_of_fees_ordering_helper(len(s.get_fees())), Roster.name_ordering_helper(s.get_name())))
            #search for duplicates
            self.reset_duplicates()

    def write_save_data(self, file_name, beg=None, end=None):
        #writes save data down in a file
        #if '<' is beg and '>' is end should be:
        #roster_save_file<><students_from_students_display><fees_with_students_list_passed_in><duples_of_dups_ignored_students><duples_of_dups_ignored_fees>>

        #handle cases of beg and end
        if not(isinstance(beg, str)) or not (len(beg) == 1):
            beg = chr(2)
        if not(isinstance(end, str)) or not (len(end) == 1):
            end = chr(3)
        #beg and end cannot be the same
        if beg == end:
            beg = chr(3)
            end = chr(3)
        #modify file_name before opening it
        if not os.path.exists('Finance Save Files'):
            os.mkdir('Finance Save Files')
        if not 'Finance Save Files' in file_name:
            file_name = os.path.join('Finance Save Files', file_name)
        
        with open(file_name, 'w') as s:
            #write file identifier and beg and end for identification purposes
            s.write('roster_save_file')
            s.write(beg)
            s.write(end)
        

            #write all students in students_display within a cell
            s.write(beg)
            for student in self.__students_display:
                s.write(student.to_writing_string(beg, end))
            s.write(end)

            #write all fees in fees within a cell, passing in students_display to to_writing_string()
            s.write(beg)
            for fee in self.__fees:
                s.write(fee.to_writing_string(self.__students_display, beg, end))
            s.write(end)
            #write all tuples of students and each other
            s.write(beg)
            first_fee_dup_index = 0
            for student_dup_index in range(0, len(self.__ok_duplicates)):
                first_fee_dup_index += 1
                
                if isinstance(self.__ok_duplicates[student_dup_index][0], Student):
                    #open cell for tuple
                    s.write(beg)
                    #write both indexes
                    s.write(beg)
                    s.write(str(self.__students_display.index(self.__ok_duplicates[student_dup_index][0])))
                    s.write(end)
                    s.write(beg)
                    s.write(str(self.__students_display.index(self.__ok_duplicates[student_dup_index][1])))
                    s.write(end)
                    s.write(end)
                elif isinstance(self.__ok_duplicates[student_dup_index][0], Fee):
                    #no indexes, but must end the tuple
                    break
            s.write(end)

            #write all tuples of fees and eachother
            s.write(beg)
            for fee_dup_index in range(first_fee_dup_index, len(self.__ok_duplicates)):
                #open cell for tuple
                s.write(beg)
                if isinstance(self.__students_display.index(self.__ok_duplicates[fee_dup_index][0]), Fee):
                    s.write(beg)
                    s.write(str(self.__fees.index(self.__ok_duplicates[fee_dup_index][0])))
                    s.write(end)
                    s.write(beg)
                    s.write(str(self.__fees.index(self.__ok_duplcates[fee_dup_index][1])))
                    s.write(end)
                s.write(end)
            s.write(end)
            #end list (no need to end file)
            s.write(end)
    
    #search functions
    def get_student_search_list(self, query):
        student_search_list = []
        for student in self.__students_search:
            if query in student.get_name():
                student_search_list.append(student)
        return student_search_list

    def get_fee_search_list(self, query):
        fee_search_list = []
        for fee in self.__fees:
            if query in fee.get_name():
                fee_search_list.append(fee)
        return fee

    #get functions for editting (need to return a Student or Fee to edit)
    #should be intimately related to ui design
        
    #functions to deal with duplicate students and fees (check helper later)
    def reset_duplicates(self, char_req_prob=None):
        try:    
            char_req_prob = float(char_req_prob)
        except:
            char_req_prob = 0.8
        #students first
        for student_index in range(0, len(self.__students_display)):
            student_one = self.__students_display[student_index]
            for alt_index in range(student_index + 1, len(self.__students_display)):
                student_two = self.__students_display[alt_index]
                #check if not in ignore list, and then check Roster function
                if not((student_one, student_two) in self.__ok_duplicates) and not((student_two, student_one) in self.__ok_duplicates):
                    if Roster.check_dup_helper(student_one, student_two, char_req_prob):
                        self._Roster__poss_duplicates.append((student_one, student_two))
        #now fees
        for fee_index in range(0, len(self.__fees)):
            fee_one = self.__fees[fee_index]
            for alt_index in range(fee_index + 1, len(self.__fees)):
                fee_two = self.__fees[alt_index]
                #check if not in ignore list, then check Roster function
                if not((fee_one, fee_two) in self.__ok_duplicates) and not((fee_two, fee_one) in self.__ok_duplicates):
                    if Roster.check_dup_helper(fee_one, fee_two, char_req_prob):
                        self.__poss_duplicates.append((fee_one, fee_two))

    def ignore_duplicate(self, dup_ignored):
        #only will have to do one
        if dup_ignored in self.__poss_duplicates:
            self.__poss_duplicates.remove(dup_ignored)
            self.__ok_duplicates.append(dup_ignored)
            
    def get_duplicates(self):
        return self.__poss_duplicates

    def merge(self, obj_sub, obj_sup):
        #should only get called by user confirmation
        #fails if not the same type
        if not(type(obj_sub) == type(obj_sup)):
            return
        if isinstance(obj_sub, Student):    
            for fee in obj_sub.get_fees():
                if not(fee in obj_sup.get_fees()):
                    obj_sup.add_fee(fee)
                fee.del_students(obj_sub)
            #copy over greater schol cap
            if obj_sup.get_schol_cap() is None:
                if not(obj_sub.get_schol_cap() is None):
                    obj_sup.set_schol_cap(obj_sub.get_schol_cap())
            elif not(obj_sub.get_schol_cap() is None):
                if (obj_sub.get_schol_cap() < obj_sup.get_schol_cap()):
                    obj_sup.set_schol_cap()
            #redo this part***^^^
            #delete student from student lists
            self.__students_display.remove(obj_sub)
            self.__students_search.remove(obj_sub)
        elif isinstance(obj_sub, Fee):
            for student in obj_sub.get_students():
                if not(student in obj_sup.get_students()):
                    obj_sup.add_students(student)
                obj_sub.del_students(student)
            #copy over greater cost
            try:
                if (obj_sub.get_total_cost() > obj_sup.get_total_cost()):
                    obj_sup.set_total_cost(obj_sub.get_total_cost())
            except:
                #None exception (only matters if sup exists but sub does not)
                if (obj_sup.get_total_cost() is None) and not(obj_sub.get_total_cost()):
                    obj_sup.set_total_cost(obj_sub.get_total_cost())
            self.__fees.remove(obj_sub)


    #helpers
    @staticmethod
    def date_ordering_helper (date):
        #returns date as a big int so that the order works easily
        #assumes formatted correctly
        if isinstance(date, str):
            year = date[date.rfind("/") + 1:]
            if len(year) == 2:
                year = "20" + year
            day = date[date.index("/")+1:date.rfind("/")]
            if len(day) == 1:
                day = "0" + day
            month = date[0: date.index("/")]
            if len(month) == 1:
                month = "0" + month
            return -1*(int(year + month + day))
        return -30000000

    @staticmethod
    def name_ordering_helper (name):
        #returns name split so that it is last+'_'+first, makes it easier to order
        if isinstance(name, str):
            return name[name.index(" ")+1:] + "_" + name[0:name.index(" ")]
        
    @staticmethod
    def num_of_fees_ordering_helper (num):
        #orders numbers of tournaments so that more is less. 
        if isinstance(num, int):
            if num > 0:
                return 1/num
            #2 is bigger than all other so 0 have lowest priority
            return 2

    @staticmethod
    def check_dup_helper(obj_one, obj_two, char_req_prob=None):
        #returns True of False depending on whether a possible duplicate
        if not(type(obj_one) == type(obj_two)):
            #must be same type
            return False
        #set char_req_prob
        try:
            char_req_prob = float(char_req_prob)
        except:
            #None and non-int or float exception
            char_req_prob = 0.8
        if isinstance(obj_one, Fee):
            #if not the same date, we say it is not a possible duplicate (name requirement too loose otherwise)
            #***issue: might mess up with big vs. small names, maybe add another condition
            try:
                if not(obj_one.get_date() == obj_two.get_date()):
                    return False
            except:
                #None exception
                pass
            #get smaller and bigger names for counting
            smaller_name = ''
            bigger_name = ''
            try:
                if (len(obj_one.get_name()) < len(obj_two.get_name())):
                    smaller_name = obj_one.get_name()
                    bigger_name = obj_two.get_name()
                else:
                    smaller_name = obj_two.get_name()
                    bigger_name = obj_one.get_name()
            except:
                #None exception (None will trigger because date already true)
                if obj_one.get_date() is None:
                    #if date is None, then the equality does not really tell us much if name is also None
                    #so we check total_cost
                    if obj_one.get_total_cost() == obj_two.get_total_cost():
                        return True
                    else:
                        return False
                return True                
            #count through chars. Goes through smaller_name and sees if its chars appear in same order in bigger_name.
            #then in enough correct (>=0.8?) will return true
            correct_char_counter = 0
            for char in smaller_name:
                if char in bigger_name:
                    bigger_name = bigger_name[bigger_name.index(char) + 1: ]
                    correct_char_counter += 1
            #if it is greater than like .8 or .9 or something
            if (correct_char_counter/len(smaller_name) >= char_req_prob):
                return True

        elif isinstance(obj_one, Student):
            try:
                one_first = obj_one.get_name()[0: obj_one.get_name().index(' ')]
                one_last = obj_one.get_name()[obj_one.get_name().index(' ') + 1: ]
                two_first = obj_two.get_name()[0: obj_two.get_name().index(' ')]
                two_last = obj_two.get_name()[obj_two.get_name().index(' ') + 1: ]
            except:
                #one of the students does not have a first and last or one of the names is None
                #None case returns False (whereas fee None case returns True) because there is no Date to check
                return False

            #first case of equality is if the last names are the same and first initial is same
            if (one_last == two_last) and (one_first[0:1] == two_first[0:1]):
                return True
            #second case of equality is if the charcounter holds
            correct_char_counter = 0
            smaller_comp_name = ''
            bigger_comp_name = ''
            #smaller_comp_name is smaller_first + smaller_last, bigger_comp_name is defined similarly
            if len(one_first) < len(two_first):
                smaller_comp_name += one_first
                bigger_comp_name += two_first
            else:
                smaller_comp_name += two_first
                bigger_comp_name += one_first

            if len(one_last) < len(two_last):
                smaller_comp_name += one_last
                bigger_comp_name += two_last
            else:
                smaller_comp_name += two_last
                bigger_comp_name += one_last
            #check count now
            for char in smaller_comp_name:
                if char in bigger_comp_name:
                    bigger_comp_name = bigger_comp_name[bigger_comp_name.index(char) + 1: ]
                    correct_char_counter += 1
                if (correct_char_counter/(len(smaller_comp_name) + len(bigger_comp_name)) >= char_req_prob):
                    return True
        return False

