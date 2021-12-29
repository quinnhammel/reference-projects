
import os
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from pathlib import Path
import xlwt
import math
import datetime


class Fee:
    #has name, date, total cost, students (dict of names to events attended)
    def __init__(self, name=None, date=None, total_cost=None):
        if isinstance(name, str):
            self.__name = name
        else:
            self.__name = ''
        if Fee.is_valid_date(date):
            self.__date = Fee.get_ordered_date(date)
        else:
            self.__date = ''
        if isinstance(total_cost, float) or isinstance(total_cost, int):
            self.__total_cost = float(total_cost)
        else:
            self.__total_cost = 0.0
        self.__students = {}

    def add_student(self, student, events_attended=None):
        if not isinstance(student, str):
            return
        student = Fee.get_ordered_name(student)

        if isinstance(events_attended, int) and (events_attended >= 0):
            self.__students[student] = events_attended
        else:
            self.__students[student] = 1

    def set_events(self, student, events_attended):
        if (not isinstance(student, str)) or (not isinstance(events_attended, int)) or (events_attended < 0):
            return
        student = Fee.get_ordered_name(student)
        if not(student in self.__students):
            return
        self.__students[student] = events_attended

    def get_date(self):
        return self.__date

    def get_name(self):
        return self.__name

    def get_total_cost(self):
        return self.__total_cost

    def get_info(self, student):
        student_ordered = Fee.get_ordered_name(student)
        if student_ordered in self.__students:
            return (Fee.get_readable_name(student), self.__students[student_ordered])
        return (Fee.get_readable_name(student), 0)

    def get_students(self):
        return self.__students

    @staticmethod
    def is_valid_date(date):
        if isinstance(date, str):
            if (date.count('/') == 2) and (len(date) < 11) and (len(date) > 5):
                return True
            elif '-' in date:
                date = date.replace('-', '/')
                return Fee.is_valid_date(date)

        return False

    @staticmethod
    def get_readable_date(date):
        date_str = ''
        if isinstance(date, str):
            if not(Fee.is_valid_date(date)):
                return date_str
            #get month, day, and year and make the correct length
            if '-' in date:
                date = date.replace('-', '/')
            month = date[0: date.index('/')]
            day = date[date.index('/')+1: date.rfind('/')]
            year = date[date.rfind('/')+1:]
            
            if len(month) < 2:
                date_str += '0'
            date_str += month + '/'
            if len(day) < 2:
                date_str += '0'
            date_str += day + '/'
            if len(year) < 4:
                date_str += '20'
            date_str += year
        elif isinstance(date, int):
            date = str(date)
            if not (len(date) == 8):
                return date_str
            date_str += date[4:6] + '/'
            date_str += date[6:] + '/'
            date_str += date[0:4]
        return date_str

    @staticmethod
    def get_ordered_date(date):
        date_int = 0
        if not isinstance(date, str):
            return None
        date = Fee.get_readable_date(date)
        #add year digits, then month digits, then day digits
        date_int += int(date[date.rfind('/')+1: ])
        date_int *= 100
        date_int += int(date[0: date.index('/')])
        date_int *= 100
        date_int += int(date[date.index('/') + 1: date.rfind('/')])
        return date_int

    @staticmethod
    def get_ordered_name(name):
        ordered_name = ''
        if not isinstance(name, str):
            return ordered_name
        if '_' in name:
            return name
        name = name.lower()
        #last names go first, separated by dashes
        index = name.rfind(' ')
        while (index > 0):
           ordered_name += name[index + 1: ] + '_'
           name = name[0: index]
           index = name.rfind(' ')

        ordered_name += name
        return ordered_name

    @staticmethod
    def get_readable_name(name):
        name_readable = ''
        if not isinstance(name, str):
            return ''
        
        if (' ' in name):
            while ' ' in name:
                name_readable += name[0: 1].upper()
                name_readable += name[1: name.index(' ')]
                name_readable += ' '
                try:
                    name = name[name.index(' ') + 1:]
                except:
                    #should not happen, unless space at end of name
                    name = ''
            name_readable += name[0:1].upper()
            name_readable += name[1:]
        else:
            while '_' in name:
                try:
                    name_readable += name[name.rfind('_') + 1].upper()
                    name_readable += name[name.rfind('_')+2: ]
                    name_readable += ' '
                except:
                    #only happens if dash at end
                    pass
                name = name[0: name.rfind('_')]
            name_readable += name[0].upper()
            name_readable += name[1:]
        return name_readable
    

class Roster:
    #has student_list, fee_list
    def __init__(self):
        self.__student_list = []
        self.__fee_list = []

    def add_fee(self, fee_added):
        if isinstance(fee_added, Fee):
            self.__fee_list.append(fee_added)
            for student in fee_added.get_students():
                if not (student in self.__student_list):
                    self.__student_list.append(student)
    
    def order(self):
        self.__student_list.sort()
        self.__fee_list.sort(key=lambda f: f.get_date())

    def get_tabroom_info(self, username, password, start, end):
        #username and password should be strings
        if (not isinstance(username, str)) or (not isinstance(password, str)) or (not isinstance(start, str)) or (not 
         isinstance(end, str)):
            return
        #start and end should be dates
        try:
            start = Fee.get_readable_date(start)
            end = Fee.get_readable_date(end)
            if (len(start) < 10) or (len(end) < 10):
                raise Exception('Empty date.')
            if Fee.get_ordered_date(end) <= Fee.get_ordered_date(start):
                raise Exception('Invalid date: start not before end.')
        except:
            #invalid date, go for default
            d = datetime.datetime.today()
            start = '01/01/{}'.format(d.year)
            end = '12/31/{}'.format(d.year)
        #username should be an email
        if username.index('@') < 0:
            return

        user_home_link = 'https://www.tabroom.com/user/home.mhtml'
        login_link = 'https://www.tabroom.com/user/login/login_save.mhtml'
        tournaments_link = 'https://www.tabroom.com/user/results/index.mhtml?chapter_id=19398'
        #open session and login
        s = requests.Session()
        data = {'username':username, 'password':password}
        s.post(login_link, data=data)
        #get soup for page with tournaments
        try:
            tournaments = s.get(tournaments_link)
            
            #if tournaments.Response
            response_int = str(tournaments)
            response_int = int(response_int[response_int.index('[')+1: response_int.index(']')])
            if (400 <= response_int) and (response_int <= 499):
                raise Exception('Exception: Invalid link (tournamnets list).')
            soup_tournaments = BeautifulSoup(tournaments.content, 'html.parser')
        except Exception as e:
            #link could be broken, go old fashioned way
            try:
                user_home = s.get(user_home_link)
                soup_home = BeautifulSoup(user_home.content, 'html.parser')
                nav_choices = soup_home.findAll('li')
                link_end = nav_choices[13].a['href']
                tournaments = s.get('https://www.tabroom.com{}'.format(link_end))
                soup_tournaments = BeautifulSoup(tournaments.content, 'html.parser')
            except Exception as c:
                print('Encountered critical exception \'{}\' while handling exception {}.'.format(c, e))
        tournament_list = soup_tournaments.findAll('tr')
        #remove first one, as it is just formatting, then go through and remove right ones.
        del tournament_list[0]
        for tournament in tournament_list:
            options = tournament.findAll('td')
            try:
                date = ' '.join(options[0].text.split())
                date_int = Fee.get_ordered_date(date)
                #check if in range (start at top, so too far ahead means continue, too far behind means break)
                if (date_int >= Fee.get_ordered_date(start)) and (date_int <= Fee.get_ordered_date(end)):
                    #construct fee, enter it, and then begin populating with students
                    name = ' '.join(options[3].a.text.split())
                    fee = Fee(name, date)
                    link_end = options[4].a['href']
                    #(want roster, not tourn)
                    link_end = link_end.replace('tourn', 'roster')
                    ind_tourn = s.get('https://www.tabroom.com/user/results/{}'.format(link_end))
                    soup_ind_tourn = BeautifulSoup(ind_tourn.content, 'html.parser')
                elif date_int > Fee.get_ordered_date(end):
                    continue
                else:
                    break
            except Exception as e:
                print(e)
                continue

            #begin adding students... set up a map first.
            students = {}
            #find entry list, remove first as it is formatting
            entry_list = soup_ind_tourn.findAll('tr')
            try:
                del entry_list[0]
            except:
                #probably an empty list
                continue
            #go through entries
            for entry in entry_list:
                #special if we know that it is a hybrid or a judge
                ishybrid = False
                entry_data = entry.findAll('td')
                if len(entry_data) < 6:
                    ishybrid = True
                event = ' '.join(entry_data[0].text.split()).lower()
                reg_name = ' '.join(entry_data[3].text.split()).lower()
                if 'judge' in event:
                    #done with entries
                    break
                elif ('/' in event) or ('hybrid' in reg_name):
                    ishybrid = True
                #check if they dropped
                try:
                    code = ' '.join(entry_data[1].text.split()).lower()
                    if 'drop' in code:
                        continue
                except:
                    pass
                #grab students and then change numbers
                if ishybrid:
                    names = entry_data[4].contents
                else:
                    names = entry_data[5].contents
                for index in range(0, int(len(names)/2)):
                    student = Fee.get_readable_name(' '.join(names[2*index].split()))
                    if student in students:
                        #only change number if we are not dealing with a hybrid
                        if not ishybrid:
                            students[student] = students[student] + 1
                    else:
                        students[student] = 1
            for student in students:
                fee.add_student(student, students[student])
            self.add_fee(fee)
        
    def write_to_excel(self):
        self.order()
        excel_workbook = xlwt.Workbook()
        master_cost = excel_workbook.add_sheet('Master_cost')
        master_shares = excel_workbook.add_sheet('Master_shares')
        #set up fonts and styles
        font = xlwt.Font()
        font.name = 'Times New Roman'
        font.bold = False
        font_bold = xlwt.Font()
        font_bold.name = 'Times New Roman'
        font_bold.bold = True
        norm = xlwt.XFStyle()
        norm.font = font
        bold = xlwt.XFStyle()
        bold.font = font_bold

        #begin writing basic titles
        master_cost.write(0, 0, 'Finances', bold)
        master_shares.write(0, 0, 'Finances', bold)
        master_cost.write(1, 0, 'Master Sheet (costs)', bold)
        master_shares.write(1, 0, 'Master Sheet (shares)', bold)
        try:
            date_range = '({}-{})'.format(Fee.get_readable_date(self.__fee_list[0].get_date()),
            Fee.get_readable_date(self.__fee_list[len(self.__fee_list)-1].get_date()))
        except:
            #no fees
            date_range = '(-)'
        master_cost.write(2, 0, date_range, bold)
        master_shares.write(2, 0, date_range, bold)
        master_cost.write(7, 0, 'Student name', bold)
        master_shares.write(7, 0, 'Student name', bold)
        master_cost.write(7, 1, 'Total due', bold)
        
        #write students names and formula
        row_offset = 9
        col_offset = 3
        for student_index, student in enumerate(self.__student_list):
            master_cost.write(row_offset + student_index, 0, Fee.get_readable_name(student), norm)
            master_shares.write(row_offset + student_index, 0, Fee.get_readable_name(student), norm)
            content = 'SUM({}:{})'.format(Roster.get_excel_cell_name(row_offset+student_index, col_offset),
            Roster.get_excel_cell_name(row_offset+student_index, col_offset+len(self.__fee_list)+40))
            master_cost.write(row_offset+student_index, 1, xlwt.Formula(content), norm)
        
        #write fee info
        #titles first
        row_offset = 4
        col_offset = 2
        master_cost.write(row_offset, col_offset, 'Fee', bold)
        master_shares.write(row_offset, col_offset, 'Fee', bold)
        master_cost.write(row_offset+1, col_offset, 'Total cost:', bold)
        master_shares.write(row_offset+1, col_offset, 'Total shares:', bold)
        master_cost.write(row_offset, col_offset+1, 'Universal fee', norm)
        master_shares.write(row_offset, col_offset+1, 'Universal fee', norm)
        master_shares.write(row_offset+1, col_offset+1, 
        xlwt.Formula('SUM(D10:D{})'.format(40+len(self.__student_list))))
        for student_index, student in enumerate(self.__student_list):
            content = 'ROUND(Master_shares!{}*D6/Master_shares!D6, 2)'.format(
                Roster.get_excel_cell_name(row_offset+5+student_index, col_offset+1))
            master_cost.write(row_offset+5+student_index, col_offset+1, xlwt.Formula(content), norm)
            master_shares.write(row_offset+5+student_index, col_offset+1, 1, norm)
        for fee_index, fee in enumerate(self.__fee_list):
            master_cost.write(row_offset, col_offset+2+fee_index, '{} ({})'.format(fee.get_name(),
             Fee.get_readable_date(fee.get_date())), norm)
            master_shares.write(row_offset, col_offset+2+fee_index, '{} ({})'.format(fee.get_name(),
             Fee.get_readable_date(fee.get_date())), norm)
            master_cost.write(row_offset+1, col_offset+2+fee_index, fee.get_total_cost(), norm)
            master_cost.write(row_offset+3, col_offset+2+fee_index, 'Cost due', bold)
            master_shares.write(row_offset+3, col_offset+2+fee_index, 'Shares due', bold)
            #fee formula
            content = 'SUM({}:{})'.format(Roster.get_excel_cell_name(row_offset+5, col_offset+2+fee_index),
            Roster.get_excel_cell_name(40+len(self.__student_list), col_offset+2+fee_index))
            master_shares.write(row_offset+1, col_offset+2+fee_index, xlwt.Formula(content), norm)
            #now fee shares and individual cost formula
            for student_index, student in enumerate(self.__student_list):
                content = 'ROUND(Master_shares!{}*{}/Master_shares!{}, 2)'.format(
                    Roster.get_excel_cell_name(row_offset+5+student_index, col_offset+2+fee_index),
                    Roster.get_excel_cell_name(row_offset+1, col_offset+2+fee_index),
                    Roster.get_excel_cell_name(row_offset+1, col_offset+2+fee_index))
                master_cost.write(row_offset+5+student_index, col_offset+2+fee_index, xlwt.Formula(content), norm)
                master_shares.write(row_offset+5+student_index, col_offset+2+fee_index, fee.get_info(student)[1], norm)
        
        #now do error work
        master_cost.write(0, 1, 'Total needed:', bold)
        master_cost.write(1, 1, 'Total expected:', bold)
        master_cost.write(2, 1, 'Error:', bold)
        content = 'SUM({}:{})'.format(Roster.get_excel_cell_name(row_offset+1, col_offset+1),
        Roster.get_excel_cell_name(row_offset+1, col_offset+1+5+len(self.__fee_list)))
        master_cost.write(0, 2, xlwt.Formula(content), bold)
        content = 'SUM({}:{})'.format(Roster.get_excel_cell_name(row_offset+5, 1),
        Roster.get_excel_cell_name(row_offset+5+5+len(self.__student_list), 1))
        master_cost.write(1, 2, xlwt.Formula(content), bold)
        master_cost.write(2, 2, xlwt.Formula('C2-C1'), bold)

        excel_workbook.save('{}/Desktop/Finances{}.xls'.format(os.path.expanduser('~'), date_range.replace('/', ':')))


    @staticmethod
    def get_excel_cell_name(row, col):
        if (not isinstance(row, int)) or (not isinstance(col, int)):
            return ''
        cell_name = ''
        while (col > 25):
            cell_name = chr(65 + col%26) + cell_name
            col = int(col/26)
            col -= 1
        cell_name = chr(65 + col%26) + cell_name
        cell_name += str(row + 1)
        return cell_name

def beta():
    print('Beta test for finance program.')
    username = input('Enter username for tabroom: ')
    password = input('Enter password for tabroom: ')
    start = input('Enter start date for tournaments (mm/dd/yyyy): ')
    end = input('Enter end date for tournaments (mm/dd/yyyy): ')
    roster = Roster()
    print('     Getting tabroom info...')
    roster.get_tabroom_info(username, password, start, end)
    print('     Saving file...')
    roster.write_to_excel()
    print('     Done!')

if __name__ == "__main__":
    beta()