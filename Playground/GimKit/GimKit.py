#fix log in
#store
#issues with sleep time?

# FOLLOWING PROGRAM WAS FOR GAMING A QUIZ SITE USED IN CLASS. 
# I did this as a project for  a class in high school. 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

class StoreManager:
    def __init__(self):
        self.__money = 0
        self.__store = {}
        #initialize all the prices
        self.__store[11] = 10
        self.__store[12] = 100
        self.__store[13] = 1000
        self.__store[14] = 10000
        self.__store[15] = 75000
        self.__store[16] = 300000
        self.__store[17] = 1000000
        self.__store[18] = 10000000
        self.__store[19] = 100000000

        self.__store[21] = 15
        self.__store[22] = 150
        self.__store[23] = 1500
        self.__store[24] = 15000
        self.__store[25] = 115000
        self.__store[26] = 450000
        self.__store[27] = 1500000
        self.__store[28] = 15000000
        self.__store[29] = 200000000

        self.__store[31] = 50
        self.__store[32] = 300
        self.__store[33] = 2000
        self.__store[34] = 12000
        self.__store[35] = 85000
        self.__store[36] = 700000
        self.__store[37] = 6500000
        self.__store[38] = 65000000
        self.__store[39] = 1000000000

    def change_money (self, new_money):
        self.__money = new_money
        for item_no in self.__store:
            if (self.__store[item_no] <= self.__money):
                return item_no
        return None
        
    def buy_good(self, item_no):
        if (self.__money >= self.__store[item_no]):
            self.__money -= self.__store[item_no]
            del(self.__store[item_no])




class GimKitGame:
    def __init__(self, game_pin, user_name, persistence=None, driver_directory=None):
        #check if only driver_directory and not persistence passed in
        #persistence is duple with time slept in first position, times to attempt stuff in second
        if isinstance(game_pin, int):
            game_pin = str(game_pin)
        if not isinstance(game_pin, str):
            raise Exception('Invalid game_pin input (not a str).')
        if len(game_pin) != 5:
            raise Exception('Invalid game_pin input (should have length 5, instead had length {}).'.format(len(game_pin)))

        if not isinstance(user_name, str):
            raise Exception('Invaild user_name input (not a str).')
        
        #in case inputs switch:
        if isinstance(persistence, str):
            driver_directory = persistence
            persistence = None
        if not isinstance(persistence, tuple) or len(persistence) != 2:
            persistence = (1, 10)
        else:
            if (not isinstance(persistence[0], int)) and (not isinstance(persistence[0], float)) or persistence[0] < 0:
                persistence[0] = 1
            if (not isinstance(persistence[1], int)) or (persistence[1] < 1):
                persistence[1] = 10
        if not isinstance(driver_directory, str):
            driver_directory = '~/Playground/GimKit/chromedriver'
        
        options = Options()
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")

        self.sleep_time = persistence[0]
        self.attempts_max = persistence[1]
        self.driver = webdriver.Chrome(options=options, executable_path=driver_directory)
        self.driver.set_page_load_timeout(10)
        self.driver.get('https://www.gimkit.com/play')
        self.game_pin = game_pin
        self.user_name = user_name
        self.__answer_key = {}
        self.__store_manager = StoreManager()
        
    def login(self):
        #enter in the number pin, join game, then enter name
        times_attempted = 0
        while (times_attempted < self.attempts_max):
            try:
                box = self.driver.find_element_by_class_name('sc-VigVT')
                #enter game pin
                box.send_keys(self.game_pin)
                #click
                self.driver.find_element_by_class_name('sc-bdVaJa').click()
                time.sleep(3)
                #enter name
                box.send_keys(self.user_name)
                #click
                self.driver.find_element_by_class_name('sc-bdVaJa').click()

                #we now look for an element only found in a valid entered game
                self.driver.find_element_by_class_name('sc-kEYyzF')
                
                times_attempted = self.attempts_max
            except:
                self.driver.refresh()
                time.sleep(self.sleep_time)
                times_attempted += 1
        
    def answer_question(self):
        time.sleep(1.5*self.sleep_time)
        answers = self.driver.find_elements(By.CLASS_NAME, 'gbnVhw')
        if (len(answers) < 5):
            print('No answers...')
            self.driver.refresh()
            time.sleep(4*self.sleep_time)
            answers = self.driver.find_elements(By.CLASS_NAME, 'gbnVhw')
            if (len(answers) < 5):
                return
        
        question = answers[0].get_attribute("textContent")
        answers.remove(answers[0])
        for index in range(0, 4):
            answers[index] = answers[index].get_attribute("textContent")
        buttons = self.driver.find_elements(By.CLASS_NAME, 'jywpvk')

        if question in self.__answer_key:
            correct = self.__answer_key[question]
            right_button = -1
            for index in range(0, 4):
                if answers[index] == correct:
                    right_button = index
                    break
            if right_button > -1:
                buttons[right_button].click()
                time.sleep(1.3*self.sleep_time)
                continue_buttons = self.driver.find_elements(By.CLASS_NAME, 'caXxao')
                if len(continue_buttons) < 2:
                    print('Not enough continues...')
                    time.sleep(2*self.sleep_time)
                    continue_buttons = self.driver.find_elements(By.CLASS_NAME, 'caXxao')
                continue_buttons[1].click()
        else:
            buttons[0].click()
            time.sleep(1.3*self.sleep_time)
            continue_buttons = self.driver.find_elements(By.CLASS_NAME, 'caXxao')
            indicator = continue_buttons[0].get_attribute("textContent")
            #either shop or view correct answer
            if indicator == 'Shop':
                self.__answer_key[question] = answers[0]
                continue_buttons[1].click()
            else:
                continue_buttons[0].click()
                correct = self.driver.find_element_by_class_name('ifBkBM').get_attribute("textContent")
                self.__answer_key[question] = correct
                #continue now
                self.driver.find_element_by_class_name('iZlxJU').click()
        #we now check if we can buy an item
        money = self.driver.find_elements(By.CLASS_NAME, 'jss45')[1].get_attribute("textContent")
        money = money[0:money.index('$')] + money[money.index('$') + 1:]
        money = money.replace(',', '')
        money = int(money)
        store_suggestion = self.__store_manager.change_money(money)
        if not (store_suggestion is None):
            self.buy_item(store_suggestion)
   
    def buy_item(self, item_no):
        time.sleep(2*self.sleep_time)
        dollar_button = self.driver.find_elements(By.CLASS_NAME, 'jss45')[1]
        dollar_button.click()
        store_buttons = self.driver.find_elements(By.CLASS_NAME, 'sc-tilXH')
        try:
            store_buttons[int(item_no/10)-1].click()
        except:
            pass
        time.sleep(2*self.sleep_time)
        level_buttons = self.driver.find_elements(By.CLASS_NAME, 'sc-jtRfpW')
        try:
            level_buttons[item_no%10].click()
        except:
            pass
        #we now buy it
        time.sleep(2*self.sleep_time)
        self.driver.find_element_by_class_name('sc-cmTdod').click()
        #we now continue
        time.sleep(2*self.sleep_time)
        self.driver.find_element_by_class_name('sc-bdVaJa').click()
        self.__store_manager.buy_good(item_no)

     

