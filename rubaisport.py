import urllib2

url = "http://rubaisport.com/r/olympics/Medals.aspx?date=10&thread=https://www.reddit.com/r/olympics/comments/4x0rww/day_five_megathread/d6bkhhq"
req = urllib2.Request(url)
c = urllib2.urlopen(req).read()

