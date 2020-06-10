##############################################
#Use BeautifulSoup for webscraping of Craigslist to get listing locations and prices
##############################################
from bs4 import BeautifulSoup
import urllib.request
import sys
import sqlite3
from math import cos, asin, sqrt, pi


def getMoreDetails(listingLink):
    thisFile = urllib.request.urlopen(listingLink).read()
    thisSoup = BeautifulSoup(thisFile,features='html.parser')
    moreDetails ={}
    if thisSoup is not None:
        latitude = thisSoup.find("div",attrs={"id":"map"})["data-latitude"]
        longitude = thisSoup.find("div",attrs={"id":"map"})["data-longitude"]
        bedBath = thisSoup.find("span",attrs={"shared-line-bubble"}).findAll("b")
        if bedBath is not None:
            try:
                numBeds = bedBath[0].text
            except:
                numBeds = "N/A"
            try:
                numBaths = bedBath[1].text
            except:
                numBaths = "N/A"
        else:
            numBeds = "N/A"
            numBaths = "N/A"
       
    else:
        print("This soup was empty: " + listingLink)
        latitute = 0
        longitude = 0
        numBeds = "N/A"
        numBaths = "N/A"
    moreDetails["Location"]={"latitude":latitude,"longitude":longitude}
    moreDetails["Beds"]=numBeds
    moreDetails["Baths"]=numBaths
    return moreDetails

def getAllListingsFromCraigslist(urlBase,urlSearch,listingInfo):
    webFile = urllib.request.urlopen(urlBase+urlSearch).read()
    soup = BeautifulSoup(webFile,features='html.parser')
    results = soup.findAll('li',attrs={"class":"result-row","data-repost-of":False})
    for row in results:
        try:
            dataPID = row["data-pid"]
            listingLink = row.find("a",href=True)["href"]
            listingPrice = row.find("span",attrs={"class":"result-price"}).text
            thisListing ={}
            thisListing["PID"] = dataPID
            thisListing["Link"] = listingLink
            thisListing["Price"]= listingPrice
            moreDetails = getMoreDetails(listingLink)
            thisListing["Location"] = moreDetails["Location"]
            thisListing["Beds"] = moreDetails["Beds"]
            thisListing["Baths"] = moreDetails["Baths"]
            print(thisListing)
            listingInfo.append(thisListing)
        except Exception as e:
            print(e)
            continue

    #get next page of listings
    try:
        newSearchString = soup.find("a",attrs={"title":"next page"})["href"]
        
        if newSearchString is not None and newSearchString !="":
            print("Starting Search for additional Listings at:\n"+urlBase+newSearchString)
            getAllListingsFromCraigslist(urlBase,newSearchString,listingInfo)
        
        return listingInfo
    except:
        print("Soup file empty for" + webFile+"\n Ending crawl early.")
        return listingInfo

def initializeDB(dbName):
    conn = sqlite3.connect(dbName)
    c = conn.cursor()

    #Check if Table Exitsts
    c.execute("SELECT count(name) FROM sqlite_master WHERE type = 'table' AND name = 'listings'")
    if c.fetchone()[0]==1:
        return
    #Create table
    c.execute("CREATE TABLE listings (PID text, LINK text, PRICE real, LATITUDE real, LONGITUDE real, BEDS text, BATHS text, PRIMARY KEY (PID))")
    conn.commit()

def insertDataToDB(dbName,data):
    conn = sqlite3.connect(dbName)
    c = conn.cursor()

    for row in data:
        oneRow = [str(row["PID"]), str(row["Link"]), float(row["Price"][1:]), float(row["Location"]["latitude"]), float(row["Location"]["longitude"]), str(row["Beds"]), str(row["Baths"])]
        c.execute("REPLACE INTO listings VALUES (?,?,?,?,?,?,?)",oneRow)
        print(oneRow)
    
    conn.commit()

def distanceInMiles(lat1, long1, lat2, long2):
    p = pi/180
    r = 3963
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat2*p) * cos(lat1*p) * (1-cos((long2-long1)*p))/2
    return 2*r*asin(sqrt(a))
    
def getListingsWithinDistance(lat,long,distance,db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    allListings = c.execute("SELECT PID, LINK, PRICE, BEDS, BATHS, LATITUDE, LONGITUDE FROM listings")
    qualifiedResults = []

    for row in allListings:
        thisRow = list(row)
        dist = distanceInMiles(lat, long, thisRow[5], thisRow[6])
        print(str(thisRow) + " distance: " + str(dist))
        if dist < distance:
            thisRow.append(dist)
            qualifiedResults.append(thisRow)
    
    return qualifiedResults


urlTestBase = "https://philadelphia.craigslist.org"
urlTestSearch = "/search/apa?"
#urlTestSearch = "/search/apa?availabilityMode=0&query=malvern+pa&sale_date=all+dates"
listingInfo = []
testDB = "Listings.db"
testLat = 40.0468
testLong = -75.531
testDistance = 10

results = getListingsWithinDistance(testLat,testLong,testDistance,testDB)
for row in results:
    print(row)

#updatedListingInfo = getAllListingsFromCraigslist(urlTestBase,urlTestSearch,listingInfo)
#initializeDB(testDB)
#insertDataToDB(testDB,updatedListingInfo)

#conn = sqlite3.connect(testDB)
#conn.row_factory=sqlite3.Row
#c = conn.cursor()

#summary = c.execute("Select Beds, Baths, MIN(Price) as MinPrice, MAX(Price) as MaxPrice, AVG(Price) as MeanPrice FROM Listings GROUP BY Beds, Baths ORDER BY Beds asc, Baths asc")
#summary = c.execute("SELECT Link, Price, Baths from Listings WHERE Price <= 1000 ORDER BY Price asc")

#Using row_factory
# rowList = summary.fetchall()
# print(rowList[0].keys())
# for row in rowList:
#     rowResult=""
#     for col in rowList[0].keys():
#         rowResult+=str(row[col]) + ", "
#     print(rowResult)

#for row in summary:
    #print(row)






##############################################
#Create the Listing Class
##############################################
