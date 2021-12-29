from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)


def log_error(e):

    """
    It is always a good idea to log errors. 
    This function just prints them, but you can
    make it do anything.
    """
    print(e)

def simple_tab_tester(n=None):
    #displays the entries for the n most recent tournaments
    if not isinstance(n, int):
        n = 10

    raw_html = simple_get('https://www.tabroom.com/index/index.mhtml')
    html = BeautifulSoup(raw_html, 'html.parser')

    data_index = 0
    string = ''
    date = ''
    link = ''
    #tournament_list = html.find(id='tournlist').tbody.select('tr')
        #.findAll('tr')
        #select('tr')
    tournament_list = html.select('tr')
    for i in range(1, n+1):
        tournament = ''
        try:
            tournament = tournament_list[i]
            data_index += 1
        except:
            continue
        name_and_date = tournament.select('td')
        date = ' '.join(name_and_date[0].text.split())
        date = ' '.join(date[10: ].split())
        date = ' '.join(date[0:5].split()) + ' ' + ' '.join(date[5: ].split())
        name = ' '.join(name_and_date[1].text.split())
        print('{} ({})'.format(name, date))
        #get link for tournament
        link = 'https://www.tabroom.com/index/{}'.format(name_and_date[1].a['href'])
        #enter the tournament
        tournament_html = BeautifulSoup(simple_get(link), 'html.parser')

        #enter the entries page
        menues = tournament_html.select('ul')
        menu_options = menues[1].select('li')
        try:
            entries_option = menu_options[1]
        except:
            continue
        #should be entries, not anything else
        if not(entries_option.a.text.strip().lower() == 'entries'):
            print('     (No entries)')
            continue
        link = 'https://www.tabroom.com' + entries_option.a['href'].strip()
        tournament_html = BeautifulSoup(simple_get(link), 'html.parser')

        #go through the events now
        j = tournament_html.find(id='content') #.select('div')
        event_menu = tournament_html.find(class_='sidenote')
        for event in event_menu.select('a'):
            event_name = ' '.join(event.text.split())
            #get link to enter the event
            link = 'https://www.tabroom.com' + event['href']
            tournament_html = BeautifulSoup(simple_get(link), 'html.parser')
            #get number in event
            event_num = ' '.join(tournament_html.find(class_='fifth nospace bluetext semibold').h5.text.split())
            event_num = event_num[0: event_num.index('e') - 1]
            event_num = int(event_num)
            print('     {} ({} entries)'.format(event_name, event_num))
            #loop over students
            test = tournament_html.findAll('table', id='fieldsort')
            entry_table = tournament_html.find('table', id='fieldsort').tbody
            for entry in entry_table.select('tr'):
                entry_data = entry.select('td')
                try:
                    print('          {} ({})'.format(' '.join(entry_data[2].text.split()), ' '.join(entry_data[3].text.split())))
                except:
                    pass
    print(data_index)


if __name__ == "__main__":
	simple_tab_tester(90)
