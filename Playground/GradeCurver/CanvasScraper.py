import os
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
#from Rewrite import AssingmentGrade

class CanvasScraper:
    #has username, password, session
    def __init__(self):
        self.__sess = requests.Session()
        self.__soupgrades = None
        #exceptions and links
        self.INVALIDLOGINEXCEPTION = Exception('Login failed: invalid username or password data.')
        self.INCORRECTLOGINEXCEPTION = Exception('Login failed: incorrect username or password.')
        self.INVALIDGRADELINKEXCEPTION = Exception('Fetching grades failed: invalid link.')

        self.MAINLINK = 'https://sequoia.instructure.com'
        self.LOGINLINK = 'https://sequoia.instructure.com/login/ldap'
        self.GRADELISTLINK = 'https://sequoia.instructure.com/grades'
        self.GETASSINGMENTSLINK = '/api/v1/courses/:course_id/assignments?per_page=10000'


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

    def get_assingments(self, ind_grade_link):
        #returns dictionary of assingments to their numbers
        assingmentsdict = {}
        #link is either actual link or just number
        if isinstance(ind_grade_link, int):
            ind_grade_link = str(ind_grade_link)
        if 'https' in ind_grade_link:
            ind_grade_link = ind_grade_link[ind_grade_link.index('s/') + 2: ind_grade_link.index('/g')]
        ind_grade_link = self.MAINLINK + self.GETASSINGMENTSLINK.replace(':course_id', ind_grade_link)
        
        #we try to get the link
        try:
            assingmentscomplex = str(self.__sess.get(ind_grade_link).content)
        except:
            return
        numassingments = assingmentscomplex.count('e}')
        for index in range(numassingments):
            indcomplex = assingmentscomplex[assingmentscomplex.index('{'):assingmentscomplex.index('e}') + 2]
            #name then date
            assingmentname = indcomplex[indcomplex.index('\"name\":\"') + 8: indcomplex.index('\",\"submission_types\"')]
            assingmentdate = indcomplex[indcomplex.index('\"due_at\":\"') + 10: indcomplex.index('\"due_at\":\"')+20]
            assingmentdate = CanvasScraper.date_format(assingmentdate)
            assingmentid = indcomplex[indcomplex.index('\"id\":') + 5: indcomplex.index(',\"description\"')]
            print(assingmentid)
            assingmentsdict['{} {}'.format(assingmentname, assingmentdate)] = assingmentid
        return assingmentsdict
    
    

    @staticmethod
    def date_format(date):
        try:
            return '({}/{}/{})'.format(date[date.index('-')+1:date.rfind('-')],
            date[date.rfind('-')+1:],
            date[0:date.index('-')])
        except:
            return ''



