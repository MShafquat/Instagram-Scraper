from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

import json
from time import sleep
import sys

class InstagramScraper:
    username_key = "username"
    password_key = "password"
    results = []

    def __init__(self, headless=False):
        # make browser headless
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("user-data-dir=/tmp/ig_cache")
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10) # set default timeout to 10 seconds

    def login_instagram(self, username, password):
        try:
            if not self.__load_login_page():
                self.__fill_login_form(username, password)
        except Exception as e:
            raise

    def __load_login_page(self):
        """
        Loads login page, if already logged in, returns True
        if not already logged in, the returns false
        if the page cannot be loaded, it raises an exception
        """
        try:
            self.driver.get("http://www.instagram.com")
            if not "Login" in self.driver.title:
                print("Already logged in")
                return True
            else:
                return False
        except Exception as e:
            print(f"Website cannot be reached: {e}")
            raise

    def __fill_login_form(self, username, password):
        """
        fills login form
        """
        try:
            username_element = self.driver.find_element(By.NAME, self.username_key)
            username_element.clear()
            username_element.send_keys(username)

            password_element = self.driver.find_element(By.NAME, self.password_key)
            password_element.clear()
            password_element.send_keys(password)
            password_element.send_keys(Keys.RETURN)
        except NoSuchElementException as e:
            print(f"Login form not found: {e}")
            raise

    def ignore_notifications(self):
        """
        dismissed the show notification dialog
        """
        try:
            notification_xpath = "//span[text()[contains(., 'notifications')]]"
            notification_popup_div = self.driver.find_element(By.XPATH, notification_xpath)
        except NoSuchElementException as e:
            # no need to raise here
            print("Notification popup not found")
            return
        try:
            notification_ignore_button_xpath = "//button[text() = 'Not Now']"
            notification_popup_parent_div = notification_popup_div.find_element(By.XPATH, './../..')
            notification_ignore_button = notification_popup_parent_div.find_element(By.XPATH, notification_ignore_button_xpath)
            notification_ignore_button.click()
        except NoSuchElementException as e:
            print("Notification popup turn off button not found")
            raise

    def start_stories(self):
        """
        finds the first story on homepage, and starts iterating
        """
        try:
            first_story_xpath = '/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/section/main/div[1]/div[1]/div/div[1]/div/div/div/div/div/div/ul/li[3]/div/button'
            first_story_element = self.driver.find_element(By.XPATH, first_story_xpath)
            first_story_element.click()
        except NoSuchElementException as e:
            print(f"Story element not found!: {e}")
            raise

    def iterate_stories(self):
        """
        Starts iterating stories until it returns to homepage
        """
        try:
            if self.__pause_current_story():
                sleep(2)
                self.__save_story()
                self.__go_to_next_story()
                self.iterate_stories()
            else:
                return
        except Exception as e:
            print(f"Error occurred {e}")
            raise

    def __pause_current_story(self):
        """
        Presses pause button on story page, and returns True
        returns False if button is not found, which means
        user is redirected back to homepage after completing stories
        """
        try:
            pause_story_button_svg_cs = "[aria-label='Pause']"
            pause_story_button_svg = self.driver.find_element(By.CSS_SELECTOR, pause_story_button_svg_cs)
            pause_story_button = pause_story_button_svg.find_element(By.XPATH, './../..')
            pause_story_button.click()
            return True
        except NoSuchElementException as e:
            print("Pause button not found")
            return False

    def __save_story(self):
        try:
            story_url = self.driver.current_url
            header_element = self.driver.find_element(By.CSS_SELECTOR, 'div header')
            author_xpath = './/div[2]/div[1]/div/div[2]/div/div[1]/a'
            author_element = header_element.find_element(By.TAG_NAME, 'a')
            author_url = author_element.get_attribute('href')
            author_username = author_element.text
            time_element = header_element.find_element(By.TAG_NAME, 'time')
            datetime = time_element.get_attribute('datetime')

            result = {
                'story_url': story_url,
                'author_url': author_url,
                'author_username': author_username,
                'datetime': datetime
            }
        except Exception as e:
            print("Header information not found")
            raise

        try:
            image_element = header_element.parent.find_element(By.TAG_NAME, 'img')
            image_png = image_element.screenshot_as_base64()
            print(image_png)
            result['image'] = image_png
            self.results.append(result)
            return
        except NoSuchElementException as e:
            print("Image element not found")
            print(e)
        except Exception as e:
            # other exception
            print(e)
            raise
        try:
            video_element = header_element.parent.find_element(By.TAG_NAME, 'video')
            result['video'] = video_element.screenshot_as_base64()
            self.results.append(result)
            return
        except Exception as e:
            print(e)
            print("Video or image element not found")
            raise

    def __go_to_next_story(self):
        """
        Presses next button on a story
        """
        try:
            next_story_button_cs = "[aria-label='Next']"
            next_story_button = self.driver.find_element(By.CSS_SELECTOR, next_story_button_cs)
            next_story_button.click()
        except NoSuchElementException as e:
            print("Next story button not found")
            raise

    def close(self):
        self.driver.close()

if __name__ == '__main__':
    with open("credentials.json", 'r') as f:
        credentials = json.load(f)
        username = credentials['username']
        password = credentials['password']
    try:
        instagramScraper = InstagramScraper(headless=False)
        instagramScraper.login_instagram(username, password)
        sleep(2)
        instagramScraper.ignore_notifications()
        sleep(1)
        instagramScraper.start_stories()
        instagramScraper.iterate_stories()
        instagramScraper.close()
    except Exception as e:
        print("Could not run program")
        print(e)
