import pandas as pd
import time
import geocoder
import googlemaps
import math
import gender_guesser.detector as gender
from pprint import pprint
from requests_oauthlib import OAuth2Session
import requests


class CountryReader:
    def __init__(self):
        self.country_mapping = self.read_csv_mapping_to_dict(
            "country_bing_to_genderguesser.csv")
        self.country_mapping_google = self.read_csv_mapping_to_dict(
            "country_google_to_genderguesser.csv")

    def read_csv_mapping_to_dict(self, file_name=''):
        df = pd.read_csv(file_name, index_col=0)
        d = df.to_dict("split")
        d = dict(zip(d["index"], d["data"]))
        
        country_mapping = {}
        for i in d:
            country_mapping[i] = d[i][0]
        # print(country_mapping)

        return country_mapping

    def get_country_geocode(self, location):
        g = geocoder.bing(location, key="")
        time.sleep(3)
        geocoder_country = g.json['country']
        return geocoder_country

    def get_country_geocode_google(self, location):
        gmaps = googlemaps.Client(key='')
        time.sleep(0.1)
        geocode_result = gmaps.geocode(location)
        geocoder_country = ''
        if len(geocode_result) > 0:
            for i in geocode_result[0]['address_components']:
                try:
                    if i['types'][0] == 'country':
                        geocoder_country = i['long_name']
                except:
                    geocoder_country = 'other_countries'
        # print('gcot:', geocoder_country)
        return geocoder_country
    
    def find_gg_location(self, country_name):
        gg_location = self.country_mapping[self.get_country_geocode(country_name)]
        return gg_location

    def find_gg_location_google(self, user_location):
        gg_location = ''
        possible_country_name = user_location.split(',')[-1]
        if possible_country_name in self.country_mapping_google.keys():
            gg_location = self.country_mapping_google[possible_country_name]
        else:
            country_name = self.get_country_geocode_google(user_location)
            if country_name in self.country_mapping_google.keys():
                gg_location = self.country_mapping_google[country_name]            
        # print(gg_location)
        return gg_location


# print(cr.find_gg_location('New York, United States'))


# stack exchange crawler
# put your application information here
class Crawler:
    def __init__(self):
        # self.client_id = '' # client_id
        # self.client_secret = '' # client_secret
        # self.key = '' # key
       

        self.redirect_uri = 'https://stackexchange.com/oauth/login_success'
        scope = 'no_expiry'
        # oauth = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri, scope=scope)
        # self.authorization_url, self.state = oauth.authorization_url('https://stackexchange.com/oauth/dialog')
        self.BASEURL = "https://api.stackexchange.com/2.2/users"
        self.site = 'stackoverflow'
        self.page = 1
        self.pagesize = 100  # the maximum pagesize is 100
        self.order = 'desc'
        self.sort = 'reputation'
        self.filter_param = '!)69QNaSIwI-L8npwI6YUwd1oloC2'
        self.access_token = self.get_token()

        # print("Please click in this link:", self.authorization_url)

    # copy the link from the browser and put in the 'response_url' below

    def get_token(self):
        response_url = 'https://stackexchange.com/oauth/login_success#access_token=zLYApYSBKGHlCj5orSoVtA))&state=S9jkaaE7LaM8Z35MTiiwu8lUAgBWf4'
        access_token = response_url.split('=')[1].split('&')[0]
        return access_token

    def get_users_json(self):
        # https://api.stackexchange.com/2.2/users?order=desc&sort=reputation&site=stackoverflow&filter=!)69QNaSIwI-L8npwI6YUwd1oloC2
        params = {
            "site": self.site,
            "page": self.page,
            "pagesize": self.pagesize,
            "order": self.order,
            "sort": self.sort,
            "filter": self.filter_param,
            "access_token": self.access_token,
            "key": self.key  # change the key to your
        }

        r = requests.get(self.BASEURL, params=params)
        return r.json()

    def get_user_list(self):
        users_json = self.get_users_json()
        return users_json['items']

    def get_user_list_pages(self, start_page, end_page):
        user_list = []
        for page in range(start_page, end_page+1):
            self.page = page
            users_json = self.get_users_json()
            if 'backoff' in users_json.keys():
                sleep_time = users_json['backoff']
                print('backoff:', sleep_time)
                time.sleep(sleep_time)
            print('page:', page, 'quota_remaining',users_json['quota_remaining'])
            user_list += users_json['items']
        return user_list

    def get_user_by_index(self, index):
        users_json = self.get_users_json()
        users_items = users_json['items']
        return users_items[index]


class UserDataGetter:
    def get_first_name(self, name):
        return name.split()[0]

    def get_name_and_location(self, user):
        name = user['display_name']
        location = user.get('location')
        return self.get_first_name(name), location

    def save_as_csv(self, user_list, filename):
        pd.DataFrame(user_list).to_csv(filename, index=False)


# Main below
detector = gender.Detector()
crawler = Crawler()
country_reader = CountryReader()
udg = UserDataGetter()

# user_list = crawler.get_user_list()

# user_list = crawler.get_user_list_pages(1, 1000)
# udg.save_as_csv(user_list, 'page_1_to_1000_no_gender.csv')

df = pd.read_csv('page_1_to_1000_no_gender.csv')
user_list = df.to_dict('records')
# pprint(country_reader.country_mapping_google)

###### Google map method
index = 0
for user in user_list:
    try:
        user_name, user_location = udg.get_name_and_location(user)
        user_gg_location = 'other_countries'
        if user_location is not None and type(user_location) == str:
            user_gg_location = country_reader.find_gg_location_google(user_location)
        # print('o:',user_location,'n:',user_gg_location)
        user_gender = detector.get_gender(user_name, user_gg_location)
        user["gender"] = user_gender
        print(str(index) + '/' + str(len(user_list)),'o:',user_location,'n:',user_gg_location)
    except:
        print(str(index) + '/' + str(len(user_list)),'error in above try')
    index+=1
    # print(user_name,user_gender)

###### Bing map method
# for user in user_list:
#     user_name, user_location = udg.get_name_and_location(user)
#     try:
#         user_gg_location = country_reader.find_gg_location(user_location)
#     except:
#         # print("Country was not able to be found, country name was: " + str(user_location.split()))
#         if user_location is not None:
#             location_arr = user_location.split(',')
#             if len(location_arr) > 1:
#                 location = location_arr[-1]
#             else:
#                 location = location_arr[0]
#             try:
#                 user_gg_location = country_reader.find_gg_location(location)
#             except:
#                 user_gg_location = 'other_countries'
#         else:
#             user_gg_location = 'other_countries'

#     user_gender = detector.get_gender(user_name, user_gg_location)
#     user["gender"] = user_gender

# pprint(user_list)

# udg.save_as_csv(user_list, 'user_list.csv')
udg.save_as_csv(user_list, 'page_1_to_1000.csv')
