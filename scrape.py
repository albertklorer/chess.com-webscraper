import pandas as pd
import numpy as np
import time
from urllib.request import urlopen, Request
from urllib.error import URLError
from bs4 import BeautifulSoup
from socket import timeout
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By

# club urls to scrape member data from
club_urls = [
    'https://www.chess.com/clubs/members/chess-university',
    'https://www.chess.com/clubs/members/chess-school',
    'https://www.chess.com/clubs/members/nm-coach-bills-free-video-lessons',
    'https://www.chess.com/clubs/members/chess-com-en-espanol',
    'https://www.chess.com/clubs/members/dan-heisman-learning-center',
    'https://www.chess.com/clubs/members/team-india',
    'https://www.chess.com/clubs/members/chess-com-em-portugues',
    'https://www.chess.com/clubs/members/pro-chess-league',
    'https://www.chess.com/clubs/members/uschess',
    'https://www.chess.com/clubs/members/4-player-chess',
    'https://www.chess.com/clubs/members/we-chat-global',
    'https://www.chess.com/clubs/members/chess-unlimited',
    'https://www.chess.com/clubs/members/the-power-of-chess',
    'https://www.chess.com/clubs/members/chessbrahs',
    'https://www.chess.com/clubs/members/chess-champ',
    'https://www.chess.com/clubs/members/marianczello-club',
    'https://www.chess.com/clubs/members/reydamayt',
    'https://www.chess.com/clubs/members/chess-com-po-russki',
    'https://www.chess.com/clubs/members/gm-ben-finegold-club',
    'https://www.chess.com/clubs/members/botez-live-fan-club-formerly-alexandras-club',
    'https://www.chess.com/clubs/members/polski-zwiazek-szachowy'
]

# header to trick server into granting access
headers = {
    'User-Agent': 
        'Chrome/23.0.1271.64',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'
}

# create set to store links of members
member_links = set()

# iterate through club urls
for club_url in club_urls:
    # send request
    request = Request(url=club_url, headers=headers) 
    page = urlopen(request)

    # create beutiful soup object
    soup_page = BeautifulSoup(page, 'html.parser')
    
    # find all member links on initial page
    for a in soup_page.find_all('a', class_='post-view-meta-avatar clubs-members-list-avatar v-user-popover'):
        member_links.add(a['href'])

    # iterate to next page
    i = 1
    club_url_mod = club_url + '?&page=' + str(i)
    request = Request(url=club_url_mod, headers=headers) 
    page = urlopen(request)
    soup_page = BeautifulSoup(page, 'html.parser')

    # as long as members appear on page continute to iterate
    while len(soup_page.find_all('a', class_='post-view-meta-avatar clubs-members-list-avatar v-user-popover')) is not 0:
        # iterate page count
        i = i + 1

        try:
            # send request
            club_url_mod = club_url + '?&page=' + str(i)
            request = Request(url=club_url_mod, headers=headers) 

            # attempt to open request
            page = urlopen(request, timeout=5)

            # create beautiful soup object
            soup_page = BeautifulSoup(page, 'html.parser')

            # find all member links on page
            for a in soup_page.find_all('a', class_='post-view-meta-avatar clubs-members-list-avatar v-user-popover'):
                member_links.add(a['href'])
        
        # continue to next page if request times out
        except timeout:
            print(f'Request for url {club_url_mod} timed out')
            continue

        # sleep and continue to next page if server rate limit is reached
        except URLError:
            print(f'Server rate limit reached at url {club_url_mod}')
            time.sleep(300)
            continue

# load chrome web driver
driver = Chrome(executable_path='/Users/albertklorer/Desktop/chess.com-webscraper/chromedriver')

# create dataframe to store member information
members = pd.DataFrame(columns=['id', 'bullet_rating', 'bullet_wins', 'bullet_losses', 'bullet_draws', 'blitz_rating', 'blitz_wins', 'blitz_losses', 'blitz_draws',
    'rapid_rating', 'rapid_wins', 'rapid_losses', 'rapid_draws', 'daily_rating', 'daily_wins', 'daily_losses', 'daily_draws'])

# iterate through member links
for member_link in member_links:
    # attempt to load member page
    try:
        driver.get(member_link)
    
    # handle case where broser crashes
    except Exception:
        driver = Chrome(executable_path='/Users/albertklorer/Desktop/chess.com-webscraper/chromedriver')
        driver.get(member_link)

    # wait until page is loaded
    try:
        WebDriverWait(driver, 5).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, 'chess-board')))
    
    except TimeoutException:
        print(f'Member page {member_link} took too long to load')
        continue
    

    # collapse expanded stats div
    try:
        driver.find_element_by_xpath('//*[contains(@class, "stat-section-expanded")]/a').click()
    
    except NoSuchElementException: 
        print(f'No statistics present on page {member_link}')
        continue

    # bullet stats
    try:
        # expand bullet stats
        driver.find_element_by_xpath('//*[@title="Bullet"]').click()

        # find stats
        bullet_rating = driver.find_element_by_xpath('//*[@title="Bullet"]/div/div[1]/span').get_attribute('innerHTML')
        bullet_wins = int(driver.find_element_by_xpath('//*[contains(text(),"W/L/D")]/aside/span[1]').get_attribute('innerHTML').split()[0])
        bullet_losses = int(driver.find_element_by_xpath('//*[contains(text(),"W/L/D")]/aside/span[2]').get_attribute('innerHTML').split()[0])
        bullet_draws = int(driver.find_element_by_xpath('//*[contains(text(),"W/L/D")]/aside/span[3]').get_attribute('innerHTML').split()[0])

        driver.find_element_by_xpath('//*[contains(@class, "stat-section-expanded")]/a').click()

    except NoSuchElementException:
        bullet_rating = np.nan
        bullet_wins = np.nan
        bullet_losses = np.nan
        bullet_draws = np.nan

    # blitz stats
    try:
        # expand blitz stats
        driver.find_element_by_xpath('//*[@title="Blitz"]').click()

        # find stats
        blitz_rating = driver.find_element_by_xpath('//*[@title="Blitz"]/div/div[1]/span').get_attribute('innerHTML')
        blitz_wins = int(driver.find_element_by_xpath('//*[contains(text(),"W/L/D")]/aside/span[1]').get_attribute('innerHTML').split()[0])
        blitz_losses = int(driver.find_element_by_xpath('//*[contains(text(),"W/L/D")]/aside/span[2]').get_attribute('innerHTML').split()[0])
        blitz_draws = int(driver.find_element_by_xpath('//*[contains(text(),"W/L/D")]/aside/span[3]').get_attribute('innerHTML').split()[0])

        driver.find_element_by_xpath('//*[contains(@class, "stat-section-expanded")]/a').click()

    except NoSuchElementException:
        blitz_rating = np.nan
        blitz_wins = np.nan
        blitz_draws = np.nan
        blitz_losses = np.nan

    # rapid stats
    try:
        # expand rapid stats
        driver.find_element_by_xpath('//*[@title="Rapid"]').click()

        # find stats
        rapid_rating = driver.find_element_by_xpath('//*[@title="Rapid"]/div/div[1]/span').get_attribute('innerHTML')
        rapid_wins = int(driver.find_element_by_xpath('//*[contains(text(),"W/L/D")]/aside/span[1]').get_attribute('innerHTML').split()[0])
        rapid_losses = int(driver.find_element_by_xpath('//*[contains(text(),"W/L/D")]/aside/span[2]').get_attribute('innerHTML').split()[0])
        rapid_draws = int(driver.find_element_by_xpath('//*[contains(text(),"W/L/D")]/aside/span[3]').get_attribute('innerHTML').split()[0])

        driver.find_element_by_xpath('//*[contains(@class, "stat-section-expanded")]/a').click()

    except NoSuchElementException:
        rapid_rating = np.nan
        rapid_wins = np.nan
        rapid_losses = np.nan
        rapid_draws = np.nan

    # daily stats
    try:
        # expand rapid stats
        driver.find_element_by_xpath('//*[@title="Daily"]').click()

        # find stats
        daily_rating = driver.find_element_by_xpath('//*[@title="Daily"]/div/div[1]/span').get_attribute('innerHTML')
        daily_wins = int(driver.find_element_by_xpath('//*[contains(text(),"W/L/D")]/aside/span[1]').get_attribute('innerHTML').split()[0])
        daily_losses = int(driver.find_element_by_xpath('//*[contains(text(),"W/L/D")]/aside/span[2]').get_attribute('innerHTML').split()[0])
        daily_draws = int(driver.find_element_by_xpath('//*[contains(text(),"W/L/D")]/aside/span[3]').get_attribute('innerHTML').split()[0])

        driver.find_element_by_xpath('//*[contains(@class, "stat-section-expanded")]/a').click()

    except NoSuchElementException:
        daily_rating = np.nan
        daily_wins = np.nan
        daily_losses = np.nan
        daily_draws = np.nan
    
    members = members.append({'bullet_rating': bullet_rating, 'bullet_wins':bullet_wins, 'bullet_losses':bullet_losses, 'bullet_draws':bullet_draws,
        'blitz_rating': blitz_rating, 'blitz_wins': blitz_wins, 'blitz_losses': blitz_losses, 'blitz_draws': blitz_draws,'rapid_rating': rapid_rating, 
        'rapid_wins': rapid_wins, 'rapid_losses': rapid_losses, 'rapid_draws': rapid_draws, 'daily_rating': daily_rating, 'daily_wins': daily_wins, 
        'daily_losses': daily_losses, 'daily_draws': daily_draws}, ignore_index=True)

members.to_csv('chess.csv', index=False)

driver.close()
