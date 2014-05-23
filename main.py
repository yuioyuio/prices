import os
import urllib2
import cgi
import time

from logging import Logger as log
from BeautifulSoup import BeautifulSoup
from django.utils import simplejson
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

class Seller(db.Model):
    name = db.StringProperty()
    pricere = db.StringProperty()
    pricesoup = db.StringProperty()
    picre = db.StringProperty()
    picsoup = db.StringProperty()
    shipre = db.StringProperty()
    shipsoup = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now_add=True)

class URL(db.Model):
    url = db.StringProperty()

class Price(db.Model):
    url = db.ReferenceProperty(URL)
    price = db.FloatProperty()
    timestamp = db.DateTimeProperty(auto_now_add=True)
    
    def IsValid(self):
        return self.price is not None and self.price != 0.0

class Target(db.Model):
    owner = db.UserProperty()
    url = db.ReferenceProperty(URL)
    seller = db.ReferenceProperty(Seller)
    name = db.StringProperty()
    description = db.StringProperty()
    prices = db.ListProperty( db.Key )
    timestamp = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
    def get(self):
        
        values = {}
        targets = Target.all()
        for target in targets:
            owner = target.owner
            url = target.url
            seller = target.seller
            name = target.name
            description = target.description
            key = str( target.key() )
            data = ( key, owner, url.url, name, description )
            values[ name ] = data
        
        #self.response.out.write( str( values ) )
        
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        template_values = {
            'values' : values,
            'url': url,
            'url_linktext': url_linktext,
        }
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class Results(webapp.RequestHandler):
    def get(self):
        
        key = self.request.get('key')
        target = Target.get( key )
        targets = [target]
        values = {}
        
        prices = set()
        
        for target in targets:
            for key in target.prices:
                price = Price.get( key )
                prices.add( price.price )
                data = ( price.price, time.mktime( price.timestamp.timetuple() ) * 1000 )
                values.setdefault( target.url.url, [] ).append( data )
        
        lastprice = ( price.price, price.timestamp.strftime('%H:%M - %d %b %Y') )
        lowprice = min( prices )
        highprice = max( prices )
        
                
        
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        template_values = {
            'values1' : simplejson.dumps( values ),
            'values2' : values,
            'low' : lowprice,
            'high' : highprice,
            'last' : lastprice,
            'url': url,
            'url_linktext': url_linktext,
        }
        
        path = os.path.join(os.path.dirname(__file__), 'results.html')
        self.response.out.write(template.render(path, template_values))

class Update(webapp.RequestHandler):
    def get(self):
        user_agent = "Mozilla/5.0 (Windows NT 7.1; rv:7.0.1) Gecko/20100101 Firefox/9.0.1"
        headers = {'User-Agent':user_agent}
        
        targets = Target.all()
        for target in targets:    
            req = urllib2.Request(url=target.url.url,headers=headers)
            site = urllib2.urlopen(req).read()
            soup = BeautifulSoup( site )
            
            price = Price()
            #price.price = EvalField( target.seller.pricesoup, None )
            price.price = float( eval( target.seller.pricesoup ) )
            #price.rrp = EvalField( target.seller.rrpsoup, None )
            #price.pic = EvalField( target.seller.picsoup )
            #price.shipping = EvalField( target.seller.shippingsoup, None )
            price.url = target.url
            price.put()
            
            target.prices.append( price.key() )
            target.put()

class AddTarget(webapp.RequestHandler):
    def get(self):
        template_values = { 'sellers' : Seller.all() }
        
        path = os.path.join(os.path.dirname(__file__), 'addtarget.html')
        self.response.out.write(template.render(path, template_values))
    
    def post(self):
        try:
            name = cgi.escape(self.request.get('name'))
            description = cgi.escape(self.request.get('description'))
            url = cgi.escape(self.request.get('url'))
            seller = cgi.escape(self.request.get('seller'))
        except:
            log.exception( "fail to get data from form" )
            print( "fail to get data from form" )
        
        seller = Seller.get( seller )
        
        if seller:
            turl = URL()
            turl.url = url
            turl.put()
            
            target = Target()
            target.name = name
            target.description = description
            target.url = turl
            target.seller = seller
            target.put()
        else:
            print( "no seller with specified name" )

class AddSeller(webapp.RequestHandler):
    def get(self):
        template_values = {}
        
        path = os.path.join(os.path.dirname(__file__), 'addseller.html')
        self.response.out.write(template.render(path, template_values))
    
    def post(self):
        try:
            name = cgi.escape(self.request.get('name'))
            pricesoup = cgi.escape(self.request.get('pricesoup'))
            picsoup = cgi.escape(self.request.get('picsoup'))
            shipsoup = cgi.escape(self.request.get('shipsoup'))
        except:
            log.exception( "fail to get data from form" )
            print( "fail to get data from form" )
        
        seller = Seller()
        seller.name = name
        seller.pricesoup = pricesoup
        seller.picsoup = picsoup
        seller.shipsoup = shipsoup
        seller.put()

def EvalField( expression, failure, *exceptions ):
    try:
        return eval( expression )
    except exceptions or Exception:
        return failure() if callable(failure) else failure

class TestAdd(webapp.RequestHandler):
    def get1(self):
        seller = Seller()
        seller.name = "Amazon.co.uk"
        seller.pricesoup = "soup.findAll(attrs={'class':'priceLarge'})[0].text.encode('ASCII','ignore')"
        #seller.rrpsoup = ""
        seller.picsoup = "soup.findAll(id='prodImageCell')[0].img['src']"
        seller.put()
        
        url = URL()
        url.url = "http://www.amazon.co.uk/Logitech-M570-Wireless-Trackball-Graphite/dp/B0042BBR2S/"
        url.put()
        
        target = Target()
        target.owner = users.get_current_user()
        target.url = url
        target.seller = seller
        target.name = 'logitech m570'
        target.description = 'new logitech m570 trackball'
        target.put()
    
    def get2(self):
        seller = Seller()
        seller.name = "Amazon.co.uk"
        seller.pricesoup = "soup.findAll(attrs={'class':'priceLarge'})[0].text.encode('ASCII','ignore')"
        #seller.rrpsoup = ""
        seller.picsoup = "soup.findAll(id='prodImageCell')[0].img['src']"
        seller.put()
        
        url = URL()
        url.url = "http://www.amazon.co.uk/Darkness-II-Limited-PC-DVD/dp/B005ULLEX6/"
        url.put()
        
        target = Target()
        target.owner = users.get_current_user()
        target.url = url
        target.seller = seller
        target.name = 'darkness 2 pc'
        target.description = 'the darkness 2 pc game'
        target.put()
        
        #price = Price()
        #price.url = url
        #price.seller = seller
        #price.put()

class Test(webapp.RequestHandler):
    def get(self):
        sellers = Seller.all()
        sellers = sellers.filter( "name ==", "Amazon.co.uk" )
        seller = sellers.get()
        self.response.out.write( str( seller.name ) )

class Fix(webapp.RequestHandler):
    def get(self):
        targets = Target.get('agpkZXZ-cHJpY2VzcgwLEgZUYXJnZXQYBQw')
        popped = targets.prices.pop(1)
        targets.put()
        
        self.response.out.write( str( popped ) )

class Data(webapp.RequestHandler):
    def get(self):
        target = self.request.get('id')
        
        values = {}
        target = Target.get( target )
        
        for key in target.prices:
            price = Price.get( key )
            tuple = ( price.price, price.timestamp )
            try:
                values[ target.name ].append( tuple )
            except:
                values[ target.name ] = [ tuple ]
        
        self.response.out.write( str( values ) )

application = webapp.WSGIApplication([
                                      ('/', MainPage),
                                      ('/results', Results),
                                      ('/add', TestAdd),
                                      ('/tasks/update', Update),
                                      ('/tasks/fix', Fix),
                                      ('/addtarget', AddTarget),
                                      ('/addseller', AddSeller),
                                      ('/test', Test),
                                      ('/data', Data ),
                                      ], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
