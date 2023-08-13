# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 13:03:03 2023

@author: gabri
"""

#%%
import os
os.chdir("C:/Users/gabri/Desktop/Selenium scraping/Selenium__Duckduckgo/2023")

#%%
from selenium import webdriver
import time
# set chrome driver

options = webdriver.ChromeOptions()
# options.add_argument('--headless') # hidden mode
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
#%%
slp_time1 = 2
slp_time2 = 0.001


#%%
import pandas as pd
Media = pd.read_csv("Media.txt")["Media"]
Keywords = pd.read_csv("Keywords.txt")["KW"]
Date = pd.read_csv("Date.txt")["Date"]


url = Media[0]

# query = 'site:'+url+" "+Keywords[0]

#%%
# from selenium.webdriver.common.keys import Keys
#launch URL
driver = webdriver.Chrome("C:/Users/gabri/Desktop/Selenium scraping/chromedriver.exe", options=options)
time.sleep(slp_time1)
#%%

dfTot = pd.DataFrame()

for kw in Keywords:

    for j,m in enumerate(Media[:]):
        tmpdf0 = pd.DataFrame()
        
        for k,d in enumerate(Date[:]):
            query = 'https://duckduckgo.com/?q=site%3Ahttps%3A%2F%2F' + m + "%2F+" + kw + "&va=b&t=hc&df=" + d + ".." + d + "&ia=web"
            print(j)
            print(k)
            print(query)
     
            driver.get(query)
            time.sleep(slp_time2)
     
            # Fetch MOST of urls and headings
            
            links = driver.find_elements_by_xpath('/html/body/div[2]/div[5]/div[4]/div/div/section[1]/ol/li[*]/article/div[2]/h2/a')
            urls_text = [l.get_attribute('href') for l in links]
                  
            try:    
                driver.find_element_by_xpath('//*[@id="links"]/div/form/input[1]').click()
            except: 
                print('Next.')
            
            # create a new dataframe for each loop and concatenate them to tmpdf0
            tmpdf = pd.DataFrame({
                "Url": urls_text,
                "Media": m,
                "Date": d
            })
            
            tmpdf0 = pd.concat([tmpdf0, tmpdf])
            
        dfTot = pd.concat([dfTot, tmpdf0])
    
#%%
# dfTot['Title'] = dfTot['Title'].str.split("\n",expand=True)[1]

dfTot['Date'] = pd.to_datetime(dfTot['Date'])

Wave = []

for d in dfTot['Date']:
    if d < pd.Timestamp('2022-03-01'):
        Wave.append('1')
    elif d > pd.Timestamp('2022-03-01') and d < pd.Timestamp('2023-06-01'):
        Wave.append('2')
    else:
        Wave.append('3')
        
dfTot['Wave'] = Wave

# dfTot.to_excel("News_selenium_Urls.xlsx",index_label='ID')

#%%
import pandas as pd

# dfTot = pd.read_excel('News_selenium_Urls.xlsx')
Headers = []

# j = 107
# k = 257

for i,u in enumerate(dfTot['Url'][:]):
    print(i)
    print(u)
    
    
    try:
        driver.get(u)
        # time.sleep(slp_time1)
        
        
        try:
            h1 = driver.find_elements_by_tag_name('h1')
            
            
            h1_text = [h.text for h in h1]
            
            # h1_text = h1.text
            
            # title_text = title.text
            title = max(h1_text, key=len)
            Headers.append(title)
            print(title)
            print('\n')
        except:
            Headers.append("99")
            print('99')
            print('\n')
            continue
    except:
        Headers.append("99")
        print('99')
        print('\n')
        continue

# pd.Series(Headers).to_excel('MediaCheck_Headers_'+str(j) +'_' +str(k) +'.xlsx')
dfTot['Title'] = Headers

# dfTot.to_excel("WarNews_selenium_Headlines.xlsx",index_label='ID')
