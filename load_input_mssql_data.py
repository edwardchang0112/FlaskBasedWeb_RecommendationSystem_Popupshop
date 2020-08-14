import requests
import numpy as np

def access_mssql_api(UserID):
    url = "http://XX.XXX.XX.XX:XXXX/Download_mssql_data"
    headers = {'Content-type': 'application/json'}
    body = {
        "UserID": UserID
    }
    response = requests.post(url, json=body, headers=headers)
    return response.status_code, response.json()

def date_tanslation(user_mssql_date):
    day = str(user_mssql_date)[8:10]
    month = str(user_mssql_date)[5:7]
    year = str(user_mssql_date)[:4]
    #print("year = ", year)
    trans_date = str(year)+str('-')+str(month)+str('-')+str(day)
    time_h = str(user_mssql_date)[11:13]
    trans_time_h = time_h
    return trans_date, trans_time_h

def oneUserData_preprocessing(oneUser_response_data):
    user_data_all = []
    for sub_data_index in oneUser_response_data:
        user_date = oneUser_response_data[sub_data_index]['UpdateDate']
        trans_date, trans_time_h = date_tanslation(user_date)
        user_temperature = oneUser_response_data[sub_data_index]['temperature']
        user_humidity = oneUser_response_data[sub_data_index]['humidity']
        user_hydrationAvg = oneUser_response_data[sub_data_index]['hydrationAvg']
        user_skinHealthAvg = oneUser_response_data[sub_data_index]['skinHealthAvg']
        user_data_all.append([trans_date, trans_time_h, user_temperature, user_humidity, float(user_hydrationAvg), float(user_skinHealthAvg)])
    remove_index = []
    remove_count = 0
    for sub_list in user_data_all:
        if None in sub_list:
            remove_index.append(remove_count)
        remove_count += 1
    for index in sorted(remove_index, reverse=True): # reverse the remove_index to avoid the index changes while deleting the lower index value
        del user_data_all[index]
    return user_data_all

# change the features of user data in your application
def historical_oneUserData_preprocessing(oneUser_response_data):
    user_data_all = []
    user_data_date_all = []
    user_data_numerical_all = []
    temperatue_default = 25.0 # the default value for Taiwanese use
    humidity_default = 60.0 # the default value for Taiwanese use
    user_longitude = None
    user_latitude = None
    #print("oneUser_response_data = ", oneUser_response_data)
    for sub_data_index in oneUser_response_data:
        #print("sub_data_index = ", sub_data_index)
        user_date = oneUser_response_data[sub_data_index]['UpdateDate']
        trans_date, trans_time_h = date_tanslation(user_date)
        user_temperature = oneUser_response_data[sub_data_index]['temperature']
        if user_temperature == None:
            user_temperature = temperatue_default # default value when access failed.
        user_humidity = oneUser_response_data[sub_data_index]['humidity']
        if user_humidity == None:
            user_humidity = humidity_default # default value when access failed.
        user_hydrationAvg = oneUser_response_data[sub_data_index]['hydrationAvg']
        user_skinHealthAvg = oneUser_response_data[sub_data_index]['skinHealthAvg']
        user_skincareRatio = oneUser_response_data[sub_data_index]['product']
        user_score = oneUser_response_data[sub_data_index]['score']

        user_data = [trans_date, trans_time_h, np.float(user_temperature), np.float(user_humidity), np.float(user_hydrationAvg), np.float(user_skinHealthAvg), np.int(user_skincareRatio)]
        user_data_all.append(user_data)

        # collect the info of location, which inclueds longitude and latitude, only need the newest location
        if user_longitude == None or user_latitude == None:
            if oneUser_response_data[sub_data_index]['longitude'] != None:
                user_longitude = oneUser_response_data[sub_data_index]['longitude']
            if oneUser_response_data[sub_data_index]['latitude'] != None:
                user_latitude = oneUser_response_data[sub_data_index]['latitude']
        else:
            pass

    # if user don't allow GPS to access their APP, then use default longitude and latitude (default:(121, 25) for Taiwan)
    if user_longitude == None or user_latitude == None:
        user_longitude = 121
        user_latitude = 25
    else:
        pass

    user_data_all = np.stack((user_data_all))

    for user_data_all_index in range(len(user_data_all[:])):
        if user_data_all[user_data_all_index, 2] != None and user_data_all[user_data_all_index, 3] != None:
            continue # skip loop of this round
        else: # if there is no temerature or humidity data, then use default value
            if user_data_all[user_data_all_index, 2] == None:
                user_data_all[user_data_all_index, 2] = temperatue_default
            else:
                continue # skip loop of this round

            if user_data_all[user_data_all_index, 3] == None:
                user_data_all[user_data_all_index, 3] = humidity_default
            else:
                continue # skip loop of this round

    return user_data_all, user_score, user_longitude, user_latitude

def data_aggregate(UserID):
    response_status, response_data = access_mssql_api(UserID)
    if UserID != 'ALL':
        user_data_all = oneUserData_preprocessing(response_data['data'])
        user_data_all = np.vstack((user_data_all))
        return user_data_all
    else:
        all_user_data_all = []
        #print(response_data['data'])
        for oneUser_data in response_data['data']:
            user_data_all = oneUserData_preprocessing(oneUser_data)
            all_user_data_all.append(user_data_all)
        return all_user_data_all

if __name__ == '__main__':
    user_data_all = data_aggregate('ALL')
    print(user_data_all)
