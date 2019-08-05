import numpy as np
import pandas as pd
from pandas import DataFrame

from bs4 import BeautifulSoup
import requests
from requests import get

import random
import sys
import datetime
from datetime import date
import time
import os
from time import sleep

from selenium import webdriver
from selenium.webdriver.firefox.options import Options


def mergeDfs(betting, teamstats):
    teamstats_df = teamstats
    betting_df = betting

    #text cleaning to ensure the teamnames match
    teamstats_df["teamnames"] =  teamstats_df['teamnames'].replace('Charlotte Bobcats', 'Charlotte Hornets')
    teamstats_df["teamnames"] =  teamstats_df['teamnames'].replace('New Orleans Hornets', 'New Orleans Pelicans')
    teamstats_df["teamnames"] =  teamstats_df['teamnames'].replace('LA Clippers', 'Los Angeles Clippers')
    teamstats_df["teamnames"] =  teamstats_df['teamnames'].replace('New Jersey Nets', 'Brooklyn Nets')

    #ensuring both columns are in datatime
    teamstats_df['date'] = pd.to_datetime(teamstats_df['date'])
    betting_df['Date'] = pd.to_datetime(betting_df['Date'])
    
    #first, split on home team to be able to merge one set of team stats at a time
    hcolumns = list(teamstats_df.columns.values)
    hhcolumns = ['h' + s for s in hcolumns]
    hometeamstats_df = teamstats_df.copy()
    hometeamstats_df.columns = hhcolumns
    
    # next, split on away
    acolumns = list(teamstats_df.columns.values)
    aacolumns = ['a' + s for s in acolumns]
    awayteamstats_df = teamstats_df.copy()
    awayteamstats_df.columns = aacolumns

    #merge the home and away stats onto the box scores
    complete_df1 = pd.merge(betting_df, hometeamstats_df,  how='left', left_on=['Date','HomeTeam'], right_on = ['hdate','hteamnames'])
    complete_df = pd.merge(complete_df1, awayteamstats_df, how='left', left_on=['Date', 'AwayTeam'], right_on = ['adate', 'ateamnames'])
    return complete_df

#CLEAN THE RETURNED DF WITH STATS AND BOXS COMBINED
def cleanDf(df):
    complete_df = df

    #this allows us to get the columns to begin further cleaning
    hCols = list(complete_df.columns)
    hCols = hCols[15:29]

    #we do not care about the individual home and away stats, but rather the differences between the two teams for each stat
    newCols = [i[1:] for i in hCols]
    aCols = ['a' + i[1:] for i in hCols]
    for (col, hcol, acol) in zip(newCols, hCols, aCols):
        complete_df[col] = complete_df[hcol] - complete_df[acol]

    #we can now drop the home and away columns
    complete_df.drop(hCols, axis=1, inplace=True)
    complete_df.drop(aCols, axis=1, inplace=True)
    complete_df.drop(['Date', 'AwayTeam', 'HomeTeam', 'AwayPts', 'HomePts', 'FinalHomeMinusAway', 'AwayCoveredSpread', 'hdate', 'adate'], axis=1, inplace=True)
    complete_df.drop(['hteamnames', 'hgp', "hwincnt", 'hlosscnt', 'hminutes', 'ateamnames', 'agp', "awincnt", 'alosscnt', 'aminutes'], axis=1, inplace=True)


    #reorder the columns to have our target as the final column
    cols = list(complete_df.columns)
    y = cols.pop(1)
    cols.append(y)
    complete_df = complete_df[cols]
    complete_df.dropna(inplace=True)

    #recode the target column as an int
    complete_df['HomeCoveredSpread'] = complete_df['HomeCoveredSpread'].astype('int')
    return complete_df

#MERGE AND CLEAN TO CREATE THE FINAL DF
def mergeAndClean(betting, teamstats):
    complete_df = mergeDfs(betting, teamstats)
    df = cleanDf(complete_df)
    return df

#RETURNS A DATA FRAME WITH BOXSCORES FROM A SINGLE DAY
def getBoxScoresForDay(month, day, year):
    website = get("https://www.basketball-reference.com/boxscores/index.fcgi?month=" + month +"&day=" + day +"&year=" + year).text
    swoop = BeautifulSoup(website, 'html.parser') #turns website into html beautiful soup object 

    #This loops through the html on the site, pulls out the necessary info, cleans it, and properly puts it into a data frame
    dataBin = swoop.findAll("table", {"class": "teams"})
    data = list()
    for item in dataBin:
        temp = list()
        for x in item.stripped_strings:
            temp.append(x)
        data.append(temp)
    df = pd.DataFrame(data, columns=['Away', 'AwayPts', 'Date', 'Home', 'HomePts'])
    
    #This generates a proper column for the game date and ensures data types are right
    dates = list()
    for i in range(df.shape[0]):
        dates.append(month + '/' + day + '/' + year)    
    df['AwayPts'] = df['AwayPts'].astype(int)
    df['HomePts'] = df['HomePts'].astype(int)
    df['Date'] = dates
    df['Date'] =  pd.to_datetime(df['Date'])
    df['RealSpread'] = df['AwayPts'] - df['HomePts']
    df = cleanTeamNames(df)
    return df

#CLEANS THE DAILY BOX SCORE DATA
def cleanTeamNames(temp):
    temp['Away'] = np.where(temp['Away'] == 'LA Clippers', 'Los Angeles Clippers', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Oklahoma City', 'Oklahoma City Thunder', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'New Orleans', 'New Orleans Pelicans', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Houston', 'Houston Rockets', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Indiana', 'Indiana Pacers', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Denver', 'Denver Nuggets', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'New York', 'New York Knicks', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Memphis', 'Memphis Grizzlies', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Toronto', 'Toronto Raptors', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Minnesota', 'Minnesota Timberwolves', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Detroit', 'Detroit Pistons', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Boston', 'Boston Celtics', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Cleveland', 'Cleveland Cavaliers', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Miami', 'Miami Heat', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Utah', 'Utah Jazz', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'LA Lakers', 'Los Angeles Lakers', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Philadelphia', 'Philadelphia 76ers', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Orlando', 'Orlando Magic', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Chicago', 'Chicago Bulls', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Atlanta', 'Atlanta Hawks', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Washington', 'Washington Wizards', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Brooklyn', 'Brooklyn Nets', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'San Antonio', 'San Antonio Spurs', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Dallas', 'Dallas Mavericks', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Charlotte', 'Charlotte Hornets', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Phoenix', 'Phoenix Suns', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Golden State', 'Golden State Warriors', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Portland', 'Portland Trail Blazers', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Milwaukee', 'Milwaukee Bucks', temp['Away'])
    temp['Away'] = np.where(temp['Away'] == 'Sacramento', 'Sacramento Kings', temp['Away'])
    
    temp['Home'] = np.where(temp['Home'] == 'LA Clippers', 'Los Angeles Clippers', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Oklahoma City', 'Oklahoma City Thunder', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'New Orleans', 'New Orleans Pelicans', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Houston', 'Houston Rockets', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Indiana', 'Indiana Pacers', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Denver', 'Denver Nuggets', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'New York', 'New York Knicks', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Memphis', 'Memphis Grizzlies', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Toronto', 'Toronto Raptors', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Minnesota', 'Minnesota Timberwolves', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Detroit', 'Detroit Pistons', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Boston', 'Boston Celtics', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Cleveland', 'Cleveland Cavaliers', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Miami', 'Miami Heat', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Utah', 'Utah Jazz', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'LA Lakers', 'Los Angeles Lakers', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Philadelphia', 'Philadelphia 76ers', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Orlando', 'Orlando Magic', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Chicago', 'Chicago Bulls', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Atlanta', 'Atlanta Hawks', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Washington', 'Washington Wizards', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Brooklyn', 'Brooklyn Nets', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'San Antonio', 'San Antonio Spurs', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Dallas', 'Dallas Mavericks', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Charlotte', 'Charlotte Hornets', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Phoenix', 'Phoenix Suns', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Golden State', 'Golden State Warriors', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Portland', 'Portland Trail Blazers', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Milwaukee', 'Milwaukee Bucks', temp['Home'])
    temp['Home'] = np.where(temp['Home'] == 'Sacramento', 'Sacramento Kings', temp['Home'])
    return temp

#GETS BETTING URL
def soup_url(type_of_line, tdate):
    if type_of_line == 'Spreads':
        url_addon = ''
    elif type_of_line == 'ML':
        url_addon = 'money-line/'
    elif type_of_line == 'Totals':
        url_addon = 'totals/'
    else:
        print("Wrong url_addon")
    url_addon = ''
    url = 'https://classic.sportsbookreview.com/betting-odds/nba-basketball/' + url_addon + '?date=' + str(tdate)
    now = datetime.datetime.now()
    raw_data = requests.get(url)
    soup_big = BeautifulSoup(raw_data.text, 'html.parser')
    soup = soup_big.find_all('div', id='OddsGridModule_5')[0]
    timestamp = time.strftime("%H:%M:%S")
    return soup, timestamp

#GETS BETTING DATA
def parse_and_write_data(soup, date, time, not_ML = True):
    def book_line(book_id, line_id, homeaway):
        line = soup.find_all('div', attrs = {'class':'el-div eventLine-book', 'rel':book_id})[line_id].find_all('div')[homeaway].get_text().strip()
        return line
    '''
    BookID  BookName
    238     Pinnacle
    19      5Dimes
    93      Bookmaker
    1096    BetOnline
    169     Heritage
    123     BetDSI
    999996  Bovada
    139     Youwager
    999991  SIA
    '''
    if not_ML:
        df = DataFrame(
                columns=('key','date','time',
                         'team','opp_team','pinnacle_line','pinnacle_odds',
                         '5dimes_line','5dimes_odds',
                         'heritage_line','heritage_odds',
                         'bovada_line','bovada_odds',
                         'betonline_line','betonline_odds'))
    else:
        df = DataFrame(
            columns=('key','date','time',
                     'team',
                     'opp_team',
                     'pinnacle','5dimes',
                     'heritage','bovada','betonline'))
    counter = 0
    number_of_games = len(soup.find_all('div', attrs = {'class':'el-div eventLine-rotation'}))
    for i in range(0, number_of_games):
        A = []
        H = []
        info_A =         soup.find_all('div', attrs = {'class':'el-div eventLine-team'})[i].find_all('div')[0].get_text().strip()
        team_A =                info_A
        try:
            pinnacle_A =     book_line('238', i, 0)
        except IndexError:
            pinnacle_A = ''
        try:
            fivedimes_A =     book_line('19', i, 0)
        except IndexError:
            fivedimes_A = ''
        try:
            heritage_A =        book_line('169', i, 0)
        except IndexError:
            heritage_A = ''
        try:
            bovada_A =     book_line('999996', i, 0)
        except IndexError:
            bovada_A = ''
        try:
            betonline_A = book_line('1096', i, 0)
        except IndexError:
            betonline_A = ''
        info_H =         soup.find_all('div', attrs = {'class':'el-div eventLine-team'})[i].find_all('div')[1].get_text().strip()
        team_H =                info_H
        try:
            pinnacle_H =     book_line('238', i, 1)
        except IndexError:
            pinnacle_H = ''
        try:
            fivedimes_H =     book_line('19', i, 1)
        except IndexError:
            fivedimes_H = ''
        try:
            heritage_H =     book_line('169', i, 1)
        except IndexError:
            heritage_H = '.'
        try:
            bovada_H =     book_line('999996', i, 1)
        except IndexError:
            bovada_H = '.'
        try:
            betonline_H = book_line('1096', i, 1)
        except IndexError:
            betonline_H = ''
        if team_H ==   'Detroit':
            team_H =   'Detroit'
        elif team_H == 'Indiana':
            team_H =   'Indiana'
        elif team_H == 'Brooklyn':
            team_H =   'Brooklyn'
        elif team_H == 'L.A. Lakers':
            team_H =   'L.A. Lakers'
        elif team_H == 'Washington':
            team_H =   'Washington'
        elif team_H == 'Miami':
            team_H =   'Miami'
        elif team_H == 'Minnesota':
            team_H =   'Minnesota'
        elif team_H == 'Chicago':
            team_H =   'Chicago'
        elif team_H == 'Oklahoma City':
            team_H =   'Oklahoma City'
        if team_A ==   'New Orleans':
            team_A =   'New Orleans'
        elif team_A == 'Houston':
            team_A =   'Houston'
        elif team_A == 'Dallas':
            team_A =   'Dallas'
        elif team_A == 'Cleveland':
            team_A =   'Cleveland'
        elif team_A == 'L.A. Clippers':
            team_A =   'L.A. Clippers'
        elif team_A == 'Golden State':
            team_A =   'Golden State'
        elif team_A == 'Denver':
            team_A =   'Denver'
        elif team_A == 'Boston':
            team_A =   'Boston'
        elif team_A == 'Milwaukee':
            team_A =   'Milwaukee'            
       # A.append(str(date) + '_' + team_A.replace(u'\xa0',' ') + '_' + team_H.replace(u'\xa0',' '))
        A.append(date)
        A.append(time)
        A.append('away')
        A.append(team_A)
        A.append(team_H)
        if not_ML:
            pinnacle_A = pinnacle_A.replace(u'\xa0',' ').replace(u'\xbd','.5')
            pinnacle_A_line = pinnacle_A[:pinnacle_A.find(' ')]
            pinnacle_A_odds = pinnacle_A[pinnacle_A.find(' ') + 1:]
            A.append(pinnacle_A_line)
            A.append(pinnacle_A_odds)
            fivedimes_A = fivedimes_A.replace(u'\xa0',' ').replace(u'\xbd','.5')
            fivedimes_A_line = fivedimes_A[:fivedimes_A.find(' ')]
            fivedimes_A_odds = fivedimes_A[fivedimes_A.find(' ') + 1:]
            A.append(fivedimes_A_line)
            A.append(fivedimes_A_odds)
            heritage_A = heritage_A.replace(u'\xa0',' ').replace(u'\xbd','.5')
            heritage_A_line = heritage_A[:heritage_A.find(' ')]
            heritage_A_odds = heritage_A[heritage_A.find(' ') + 1:]
            A.append(heritage_A_line)
            A.append(heritage_A_odds)
            bovada_A = bovada_A.replace(u'\xa0',' ').replace(u'\xbd','.5')
            bovada_A_line = bovada_A[:bovada_A.find(' ')]
            bovada_A_odds = bovada_A[bovada_A.find(' ') + 1:]
            A.append(bovada_A_line)
            A.append(bovada_A_odds)
            betonline_A = betonline_A.replace(u'\xa0',' ').replace(u'\xbd','.5')
            betonline_A_line = betonline_A[:betonline_A.find(' ')]
            betonline_A_odds = betonline_A[betonline_A.find(' ') + 1:]
            A.append(betonline_A_line)
            A.append(betonline_A_odds)
        else:
            A.append(pinnacle_A.replace(u'\xa0',' ').replace(u'\xbd','.5'))
            A.append(fivedimes_A.replace(u'\xa0',' ').replace(u'\xbd','.5'))
            A.append(heritage_A.replace(u'\xa0',' ').replace(u'\xbd','.5'))
            A.append(bovada_A.replace(u'\xa0',' ').replace(u'\xbd','.5'))
            A.append(betonline_A.replace(u'\xa0',' ').replace(u'\xbd','.5'))
        H.append(date)
        H.append(time)
        H.append('home')
        H.append(team_H)
        H.append(team_A)
        if not_ML:
            pinnacle_H = pinnacle_H.replace(u'\xa0',' ').replace(u'\xbd','.5')
            pinnacle_H_line = pinnacle_H[:pinnacle_H.find(' ')]
            pinnacle_H_odds = pinnacle_H[pinnacle_H.find(' ') + 1:]
            H.append(pinnacle_H_line)
            H.append(pinnacle_H_odds)
            fivedimes_H = fivedimes_H.replace(u'\xa0',' ').replace(u'\xbd','.5')
            fivedimes_H_line = fivedimes_H[:fivedimes_H.find(' ')]
            fivedimes_H_odds = fivedimes_H[fivedimes_H.find(' ') + 1:]
            H.append(fivedimes_H_line)
            H.append(fivedimes_H_odds)
            heritage_H = heritage_H.replace(u'\xa0',' ').replace(u'\xbd','.5')
            heritage_H_line = heritage_H[:heritage_H.find(' ')]
            heritage_H_odds = heritage_H[heritage_H.find(' ') + 1:]
            H.append(heritage_H_line)
            H.append(heritage_H_odds)
            bovada_H = bovada_H.replace(u'\xa0',' ').replace(u'\xbd','.5')
            bovada_H_line = bovada_H[:bovada_H.find(' ')]
            bovada_H_odds = bovada_H[bovada_H.find(' ') + 1:]
            H.append(bovada_H_line)
            H.append(bovada_H_odds)
            betonline_H = betonline_H.replace(u'\xa0',' ').replace(u'\xbd','.5')
            betonline_H_line = betonline_H[:betonline_H.find(' ')]
            betonline_H_odds = betonline_H[betonline_H.find(' ') + 1:]
            H.append(betonline_H_line)
            H.append(betonline_H_odds)
        else:
            H.append(pinnacle_H.replace(u'\xa0',' ').replace(u'\xbd','.5'))
            H.append(fivedimes_H.replace(u'\xa0',' ').replace(u'\xbd','.5'))
            H.append(heritage_H.replace(u'\xa0',' ').replace(u'\xbd','.5'))
            H.append(bovada_H.replace(u'\xa0',' ').replace(u'\xbd','.5'))
            H.append(betonline_H.replace(u'\xa0',' ').replace(u'\xbd','.5'))

        df.loc[counter]   = ([A[j] for j in range(len(A))])
        df.loc[counter+1] = ([H[j] for j in range(len(H))])
        counter += 2
    return df

def select_and_rename(df, text):
    if text[-2:] == 'ml':
        df = df[['key','time','team','opp_team',
                 'pinnacle','5dimes','heritage','bovada','betonline']]
        df.columns = ['key',text+'_time','team','opp_team',
                      text+'_PIN',text+'_FD',text+'_HER',text+'_BVD',text+'_BOL']
    else:
        df = df[['key','time','team','opp_team',
                 'pinnacle_line','pinnacle_odds',
                 '5dimes_line','5dimes_odds',
                 'heritage_line','heritage_odds',
                 'bovada_line','bovada_odds',
                 'betonline_line','betonline_odds']]
        df.columns = ['key',text+'_time','team','opp_team',
                      text+'_PIN_line',text+'_PIN_odds',
                      text+'_FD_line',text+'_FD_odds',
                      text+'_HER_line',text+'_HER_odds',
                      text+'_BVD_line',text+'_BVD_odds',
                      text+'_BOL_line',text+'_BOL_odds']
    return df

#USES ABOVE FUNCTIONS TO CREATE BETTING DF    
def createDf(todays_date):
    soup_ml, time_ml = soup_url('ML', todays_date)
    soup_rl, time_rl = soup_url('Spreads', todays_date)
    soup_tot, time_tot = soup_url('Totals', todays_date)
    df_ml = parse_and_write_data(soup_ml, todays_date, time_ml, not_ML = False)
    df_ml.columns = ['key','date','ml_time','team',
                         'opp_team',
                         'ml_PIN','ml_FD','ml_HER','ml_BVD','ml_BOL']    

    df_rl = parse_and_write_data(soup_rl, todays_date, time_rl)
    df_rl = select_and_rename(df_rl, 'rl')


    df_tot = parse_and_write_data(soup_tot, todays_date, time_tot)
    df_tot = select_and_rename(df_tot, 'tot')
    write_df = df_ml
    write_df = write_df.merge(
                    df_rl, how='left', on = ['key','team','opp_team'])
    write_df = write_df.merge(
                    df_tot, how='left', on = ['key','team','opp_team'])
    return write_df

#ERROR HANDLING FOR MISSING DATA
def getBettingLine(date):
    try:
        df = createDf(date)
        cleanedDf = cleanBets(df)
        return cleanedDf
    except IndexError:
        return 0

#CLEANS THE BETTING DATAFRAME
def cleanBets(bets):
    bets = bets[bets["ml_time"] == "away"]
    bets = bets[['key','team', 'opp_team', 'tot_BVD_line']]
    bets['key'] =  pd.to_datetime(bets['key'], format='%Y%m%d')
    temp = bets
    temp['team'] = np.where(temp['team'] == 'L.A. Clippers', 'Los Angeles Clippers', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Oklahoma City', 'Oklahoma City Thunder', temp['team'])
    temp['team'] = np.where(temp['team'] == 'New Orleans', 'New Orleans Pelicans', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Houston', 'Houston Rockets', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Indiana', 'Indiana Pacers', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Denver', 'Denver Nuggets', temp['team'])
    temp['team'] = np.where(temp['team'] == 'New York', 'New York Knicks', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Memphis', 'Memphis Grizzlies', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Toronto', 'Toronto Raptors', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Minnesota', 'Minnesota Timberwolves', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Detroit', 'Detroit Pistons', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Boston', 'Boston Celtics', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Cleveland', 'Cleveland Cavaliers', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Miami', 'Miami Heat', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Utah', 'Utah Jazz', temp['team'])
    temp['team'] = np.where(temp['team'] == 'L.A. Lakers', 'Los Angeles Lakers', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Philadelphia', 'Philadelphia 76ers', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Orlando', 'Orlando Magic', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Chicago', 'Chicago Bulls', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Atlanta', 'Atlanta Hawks', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Washington', 'Washington Wizards', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Brooklyn', 'Brooklyn Nets', temp['team'])
    temp['team'] = np.where(temp['team'] == 'San Antonio', 'San Antonio Spurs', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Dallas', 'Dallas Mavericks', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Charlotte', 'Charlotte Hornets', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Phoenix', 'Phoenix Suns', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Golden State', 'Golden State Warriors', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Portland', 'Portland Trail Blazers', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Milwaukee', 'Milwaukee Bucks', temp['team'])
    temp['team'] = np.where(temp['team'] == 'Sacramento', 'Sacramento Kings', temp['team'])
    return temp


#MERGES THE BETTING DF AND BOX SCORE DF
def mergeBetsAndBox(bets, box):
    new_df = pd.merge(box, bets,  how='left', left_on=['Date','Away'], right_on = ['key','team'])
    new_df = new_df[["Date", "Away", "Home", "AwayPts", "HomePts", "tot_BVD_line"]]
    new_df = new_df.dropna()
    return new_df

#RETURNS A DF WITH A DAILY BOX SCORE AND BETTING LINE
def getPreviousDayGames(month, day, year):
    dateString = year+month+day
    boxs = getBoxScoresForDay(month, day, year)
    bets = getBettingLine(dateString)
    betting = mergeBetsAndBox(bets, boxs)
    return betting


def get_stats_table(url, date):
    # initialize Firefox headless browser
    options = Options()
    #options.headless = True
    driver = webdriver.Firefox(options=options, executable_path='/Users/ctananbaum/Desktop/charlesWork/geckodriver')
    driver.get(url)
    time.sleep(3)
    # get stats table
    table = driver.find_elements_by_css_selector('td')
    teamnames = []
    for elem in table[1::20]:
        teamnames.append(elem.text)
    gp = []
    for elem in table[2::20]:
        gp.append(elem.text)
    wincnt = []
    for elem in table[3::20]:
        wincnt.append(elem.text)
    losscnt = []
    for elem in table[4::20]:
        losscnt.append(elem.text)
    minutes = []
    for elem in table[5::20]:
        minutes.append(elem.text)
    offrtg = []
    for elem in table[6::20]:
        offrtg.append(elem.text)
    defrtg = []
    for elem in table[7::20]:
        defrtg.append(elem.text)
    netrtg = []
    for elem in table[8::20]:
        netrtg.append(elem.text)
    astpct = []
    for elem in table[9::20]:
        astpct.append(elem.text)
    ast_to = []
    for elem in table[10::20]:
        ast_to.append(elem.text)
    astratio = []
    for elem in table[11::20]:
        astratio.append(elem.text)
    orebpct = []
    for elem in table[12::20]:
        orebpct.append(elem.text)
    drebpct = []
    for elem in table[13::20]:
        drebpct.append(elem.text)
    rebpct = []
    for elem in table[14::20]:
        rebpct.append(elem.text)
    tovpct = []
    for elem in table[15::20]:
        tovpct.append(elem.text)
    efgpct = []
    for elem in table[16::20]:
        efgpct.append(elem.text)
    tspct = []
    for elem in table[17::20]:
        tspct.append(elem.text)
    pace = []
    for elem in table[18::20]:
        pace.append(elem.text)
    pie = []
    for elem in table[19::20]:
        pie.append(elem.text)
    driver.close()  # quit the process
    data = {'teamnames': teamnames, 'gp': gp, 'wincnt': wincnt, 'losscnt': losscnt, 'minutes': minutes, 'offrtg': offrtg,
            'defrtg': defrtg, 'netrtg': netrtg, 'astpct': astpct, 'ast_to': ast_to, 'astratio': astratio,
            'orebpct': orebpct, 'drebpct': drebpct, 'rebpct': rebpct, 'tovpct': tovpct, 'efgpct': efgpct, 'tspct': tspct,
            'pace': pace, 'pie': pie}
    statsdf = pd.DataFrame(data)
    statsdf = statsdf.drop_duplicates('teamnames')
    statsdf['date'] = date
    statsdf['teamnames'].replace('', np.nan, inplace=True)
    statsdf.dropna(subset=['teamnames'], inplace=True)
    return statsdf


# RETURNS A DF WITH STATS FROM ALL YEARS USED TO TRAIN THE INITIAL MODEL
def create_stats_df_train():
    seasons = ['2009-10', '2010-11', '2011-12', '2012-13', '2013-14', '2014-15', '2015-16', '2016-17', '2017-18', '2018-19']
    months = ['11', '12', '1', '2', '3'] # nov - mar for a given season

    # initialize dataframe
    allstats_df = pd.DataFrame(columns=['date', 'teamnames', 'gp', 'wincnt', 'losscnt', 'minutes', 'offrtg',
                'defrtg', 'netrtg', 'astpct', 'ast_to', 'astratio',
                'orebpct', 'drebpct', 'rebpct', 'tovpct', 'efgpct', 'tspct', 'pace', 'pie'])

    # loop through all days and get cumulative stats for each team on a given day
    for season in seasons:
        for month in months:
            # get year
            if (month == '11' or month == '12'):
                year = season.split('-')[0]
            else:
                yrlist = season.split('-')
                year = '20' + yrlist[1]

            if (month == '11'):
                days = 30
            elif (month == '2'):
                days = 28
            else: # 12, 1, 3
                days = 31

            for i in range(1, days + 1):
                url = 'https://stats.nba.com/teams/advanced/?sort=W&dir=-1&Season=' + season + '&SeasonType=Regular%20Season&DateTo=' + month + '%2F' + str(i) + '%2F' + year
                date = year + '-' + month + '-' + str(i)
                try:
                    allstats_df = allstats_df.append(get_stats_table(url, date), sort=False)
                except ValueError:
                    print('ValueError: ' + date)
                    continue
                
# GET TEAM STATS FOR A GIVEN DAY
def create_stats_df(month, day, year):
    # loop through all days and get cumulative stats for each team on a given day
    url = 'https://stats.nba.com/teams/advanced/?sort=W&dir=-1&Season=18-19&SeasonType=Regular%20Season&DateTo=' + month + '%2F' + day + '%2F' + year
    date = year + '-' + month + '-' + day
    try:
        allstats_df = get_stats_table(url, date)
        return allstats_df
    except ValueError:
        print('ValueError: ' + date)
        return 0
    
#RETURNS A DF WITH ALL INFO FOR THE DAY'S GAMES
def getDailyDf(month, day, year):
	betting = getPreviousDayGames(month, day, year)
	stats = create_stats_df(month, day, year)
	df = mergeAndClean(betting, stats)
	return df
