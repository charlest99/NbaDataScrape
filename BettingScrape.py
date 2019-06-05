import pandas as pd
from bs4 import BeautifulSoup
from requests import get
from time import sleep
import random
import sys

def query_site(url, dat_tag, num_cols): #send url, tag that the data (not headers) is under, number of columns
    website = get(url).text 
    swoop = BeautifulSoup(website, 'html.parser') #turns website into html beautiful soup object 
    dataBin = swoop.find_all(dat_tag) #, class_ = 'data' (optional paramater if necessary)
    data = list()
    for i in range(len(dataBin)):
        data.append(dataBin[i].text) #makes a list with the raw text from the website's table
    new_list = [data[i:i+num_cols] for i in range(0, len(data), num_cols)] #copies the list into an array
    return new_list

def data_to_df(data, col_names):
    return pd.DataFrame(data, columns=col_names)

cols = ["Start", "Away", "AwayPts", "Home", "HomePts", "miscOne", "miscTwo", "miscThree", "miscFour"]

def getBoxScoresforYear(year):
    data = query_site('https://www.basketball-reference.com/leagues/NBA_' + str(year) + '_games-november.html', 'td', len(cols))
    df = data_to_df(data, cols)
    months = ["december", "january", "february", "march"]
    for month in months:
        site = 'https://www.basketball-reference.com/leagues/NBA_' + str(year) + '_games-' + month + '.html'
        y = query_site(site, 'td', len(cols))
        dfx = pd.DataFrame(y, columns=df.columns)
        df = df.append(dfx)
    return df

def getDatesforYear(year):
    data = query_site('https://www.basketball-reference.com/leagues/NBA_' + str(year) + '_games-november.html', 'th', 1)
    data = data[10:]
    listData = list()
    listData.append(data)
    months = ["december", "january", "february", "march"]
    for month in months:
        site = 'https://www.basketball-reference.com/leagues/NBA_' + str(year) + '_games-' + month + '.html'
        y = query_site(site, 'th', 1)
        y = y[10:]
        listData.append(y)

    dateList = []
    for x in listData:
        for y in x:
            dateList.append(y)

    datesFinal = []
    for x in dateList:
        for y in x:
            datesFinal.append(y[5:])
            
    return datesFinal
        
def getDfforYear(year):
    box = getBoxScoresforYear(year)
    dates = getDatesforYear(year)
    box["Date"] = dates
    box = box.drop('Start', 1)
    box = box.drop('miscOne', 1)
    box = box.drop('miscTwo', 1)
    box = box.drop('miscThree', 1)
    box = box.drop('miscFour', 1)
    box['Date'] =  pd.to_datetime(box['Date'], format='%b %d, %Y')
    return box

