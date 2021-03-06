from xml.dom import minidom
from scipy.stats.stats import pearsonr
import re
import numpy as np
import operator
from dateutil import parser

def getFifthTag():
    xmldoc = minidom.parse('overflow/Tags.xml')
    rows = xmldoc.getElementsByTagName('row')
    totals = dict()
    for row in rows:
        name = row.attributes['TagName'].value
        count = int(row.attributes['Count'].value)
        totals[name] = count

    sorted_x = sorted(totals.items(), key=operator.itemgetter(1), reverse=True)
    return sorted_x[4][0]

def getPosts():
    xmldoc = minidom.parse('overflow/Posts.xml')
    rows = xmldoc.getElementsByTagName('row')
    total = float(len(rows))
    matchString = '.*<' + getFifthTag() + '>.*'
    matchCount = 0
    for row in rows:
        try:
            tag = row.attributes['Tags'].value
            if  re.match(matchString, tag):
                matchCount += 1
        except KeyError:
            continue;
    percent = matchCount/total
    print('percent: %.10f' % percent)

def getAvgDiff():
    xmldoc = minidom.parse('overflow/Posts.xml')
    rows = xmldoc.getElementsByTagName('row')
    avgQ = list();
    avgA = list();
    for row in rows:
        typeID = int(row.attributes['PostTypeId'].value)
        score = float(row.attributes['Score'].value)
        if typeID == 1:
            avgQ.append(score)
        if typeID == 2:
            avgA.append(score)
    meanQ = np.mean(avgQ, dtype=np.float64)
    meanA = np.mean(avgA, dtype=np.float64)
    print(meanA - meanQ)

def getUserRep():
    xmldoc = minidom.parse('overflow/Users.xml')
    rows = xmldoc.getElementsByTagName('row')
    userRep = dict();
    for row in rows:
        userID = int(row.attributes['Id'].value)
        rep = float(row.attributes['Reputation'].value)
        if userID == -1:
            continue;
        userRep[userID] = rep
    return userRep

def getPostUserScore():
    xmldoc = minidom.parse('overflow/Posts.xml')
    rows = xmldoc.getElementsByTagName('row')
    userScore = dict();
    for row in rows:
        try:
            userID = int(row.attributes['OwnerUserId'].value)
            score = float(row.attributes['Score'].value)
            if userID in userScore:
                userScore[userID] += score
            else:
                userScore[userID] = score
        except KeyError:
            continue;
    return userScore

def getPearson():
    userRep = getUserRep()
    userScore = getPostUserScore()
    userRepList = list();
    userScoreList = list();
    for userID in userRep:
        if userID in userScore:
            userRepList.append(userRep[userID])
            userScoreList.append(userScore[userID])
    print pearsonr(userRepList, userScoreList)

def getPostUp():
    xmldoc = minidom.parse('overflow/Votes.xml')
    rows = xmldoc.getElementsByTagName('row')
    postVote = dict();
    for row in rows:
        postID = int(row.attributes['PostId'].value)
        voteType = int(row.attributes['VoteTypeId'].value)
        if postID in postVote:
            if voteType == 2:
                postVote[postID] += 1
        else:
            if voteType == 2:
                postVote[postID] = 1
    return postVote

def getUpAvgByQA():
    xmldoc = minidom.parse('overflow/Posts.xml')
    rows = xmldoc.getElementsByTagName('row')
    postVote = getPostUp()
    avgQ = list();
    avgA = list();
    for row in rows:
        ID = float(row.attributes['Id'].value)
        typeID = int(row.attributes['PostTypeId'].value)
        if typeID == 1:
            if ID in postVote:
                avgQ.append(postVote[ID])
        if typeID == 2:
            if ID in postVote:
                avgA.append(postVote[ID])
    meanQ = np.mean(avgQ, dtype=np.float64)
    meanA = np.mean(avgA, dtype=np.float64)
    print(meanA - meanQ)

def getQWithAccepted():
    #xmldoc = minidom.parse('overflow/PostsFixture.xml')
    xmldoc = minidom.parse('overflow/Posts.xml')
    rows = xmldoc.getElementsByTagName('row')
    timeQA = dict();
    for row in rows:
        typeID = int(row.attributes['PostTypeId'].value)
        if typeID == 1:
            qID = int(row.attributes['Id'].value)
            try:
                aID = int(row.attributes['AcceptedAnswerId'].value)
                aTime = False
                try:
                    answer = rows[aID - 1]
                    aTime = answer.attributes['CreationDate'].value
                except IndexError:
                    print("Not found")
                qTime = parser.parse(row.attributes['CreationDate'].value)
                if aTime:
                    aTime = parser.parse(aTime)
                    #print("(%s) A: %s Q: %s" % (qID, aTime, qTime))
                    timeQA[qID] = [qTime, aTime]
            except KeyError:
                continue;
    return timeQA

def makeTimeBuckets():
    timePairDict = getQWithAccepted()
    bucketDict = dict()
    for qID in timePairDict:
        h = timePairDict[qID][0].hour
        hourDiff = float((timePairDict[qID][1] - timePairDict[qID][0]).total_seconds())/3600
        if h in bucketDict:
            bucketDict[h].append(hourDiff)
        else:
            bucketDict[h] = [hourDiff]
    sortedBucket = dict(sorted(bucketDict.items(), key=operator.itemgetter(1), reverse=True))
    for hour in bucketDict:
        median = np.median(bucketDict[hour])
        mini = np.amin(bucketDict[hour])
        maxi = np.amax(bucketDict[hour])
        print('median for %s: %.10f, min: %s, max: %s, length: %s' % (hour, median, mini, maxi, len(bucketDict[hour])))

#getAvgDiff()
#getPosts()
#getPearson()
#getUpAvgByQA()
#getQWithAccepted()
makeTimeBuckets()
