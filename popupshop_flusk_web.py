#!flask/bin/python
from flask import Flask, request, render_template
from gevent.pywsgi import WSGIServer
from user_DB import *
from get_mssql_data_api import *
import numpy as np
from random import choice
import pymssql
from OpenWeatherAPI import *
from datetime import timedelta
import xgboost as xgb

app = Flask(__name__)

def DB_connect(db_name):
    db_conn = sqlite3.connect(db_name)
    db_cursor = db_conn.cursor()
    return db_conn, db_cursor

def XGB_model_Load(filename):
    #with open(filename, 'rb') as f_XGB_model:
    #    XGB_model_fit = pickle.load(f_XGB_model)
    bst = xgb.Booster()
    bst.load_model(filename)
    return bst

def input_normalization(input):
    input_nor = input / 100
    bias = np.stack((0.1*np.ones((len([input_nor]), 1))), axis=0)
    input_nor_bias = np.hstack(([input_nor], bias))
    return input_nor_bias

# change this recommendation function to fit your application
def _choose_customized_skincare_ratio(input_data, hydration_model, oxygen_model, pre_skincare_ratio, pre_date, cur_date, pre_time_h, cur_time_h):
    skincare_options = [1, 2, 3, 4, 5, 6, 7]
    skincare_normalized_scale = 0.1
    skincare_options_normalized = [i*skincare_normalized_scale for i in skincare_options]
    input_data_nor = input_normalization(input_data)[0]
    #print("input_data_nor = ", input_data_nor)
    #input("===")
    all_skincare_hydration_pred = []
    all_skincare_oxygen_pred = []
    for skincare_option in skincare_options_normalized:
        input_data_nor[-2] = skincare_option # because sub_X[-1] is the bias term, sub_X[-2] is the skincare ratio term, change skincare ratio from 1~7
        #print("sub_X = ", sub_X)
        hydration_pred = hydration_model.predict(xgb.DMatrix((np.asarray((input_data_nor)).reshape(1, -1))))
        all_skincare_hydration_pred.append(hydration_pred)
        oxygen_pred = oxygen_model.predict(xgb.DMatrix((np.asarray((input_data_nor)).reshape(1, -1))))
        all_skincare_oxygen_pred.append(oxygen_pred)

    max_oxygen_skincare_pred = max(all_skincare_oxygen_pred)
    #best_skincare_option = choice([index for index, sk in enumerate(all_skincare_oxygen_pred) if sk == max_oxygen_skincare_pred])+1
    # For estimating wrong area which is not on face, and get significant variation compare to previous estimation
    if input_data_nor[10] >= input_data_nor[11]+0.1: # skin is significantly less hydrated (<10) than previous day
        best_skincare_option = pre_skincare_ratio+3
    elif input_data_nor[10] <= input_data_nor[11]-0.1: # skin is significantly less hydrated (<10) than previous day
        best_skincare_option = pre_skincare_ratio-3
    else: # For estimating right area which is on face
        #print("pre_time_h = ", pre_time_h)
        #print("cur_time_h = ", cur_time_h)
        if pre_date == cur_date: # For estimation in the same day
            # for every 6 hours, keep the same skincare ratio
            if cur_time_h - pre_time_h < 6 and ((cur_time_h < 18 and cur_time_h >= 8 and pre_time_h < 18 and pre_time_h >= 8) or (cur_time_h >= 18 and cur_time_h < 24 and pre_time_h >= 18 and pre_time_h < 24) or (cur_time_h >= 0 and cur_time_h < 8 and pre_time_h >= 0 and pre_time_h < 8)):
                if input_data_nor[10] > input_data_nor[11] + 0.05:
                    best_skincare_option = pre_skincare_ratio + 1
                elif input_data_nor[10] < input_data_nor[11] - 0.05:
                    best_skincare_option = pre_skincare_ratio - 1
                else:
                    best_skincare_option = pre_skincare_ratio
            else:
                if input_data_nor[10] > input_data_nor[11] or input_data_nor[4] > input_data_nor[5]: # skin is less hydrated or the weather is cooler than previous day
                    best_skincare_option = max([index for index, sk in enumerate(all_skincare_oxygen_pred) if sk == max_oxygen_skincare_pred])+1
                    best_skincare_option = int(round((best_skincare_option + pre_skincare_ratio)/2))
                else:
                    best_skincare_option = min([index for index, sk in enumerate(all_skincare_oxygen_pred) if sk == max_oxygen_skincare_pred])+1
                    best_skincare_option = int((best_skincare_option + pre_skincare_ratio)/2)
        else:
            if input_data_nor[10] > input_data_nor[11] or input_data_nor[4] > input_data_nor[5]: # # skin is less hydrated or the weather is cooler than previous day
                best_skincare_option = max([index for index, sk in enumerate(all_skincare_oxygen_pred) if sk == max_oxygen_skincare_pred])+1
                best_skincare_option = int(round((best_skincare_option + pre_skincare_ratio)/2))
                # For the two estimations which are not execute in a short time, add a random coeficient to keep the results different, while getting even the same results from the above calculation.
                if best_skincare_option == pre_skincare_ratio:
                    best_skincare_option += choice([0, 1])
                else:
                    pass
            else:
                best_skincare_option = min([index for index, sk in enumerate(all_skincare_oxygen_pred) if sk == max_oxygen_skincare_pred])+1
                best_skincare_option = int((best_skincare_option + pre_skincare_ratio)/2)
                # For the two estimations which are not execute in a short time, add a random coeficient to keep the results different, while getting even the same results from the above calculation.
                if best_skincare_option == pre_skincare_ratio:
                    best_skincare_option -= choice([0, 1])
                else:
                    pass

    if best_skincare_option >= 7:
        best_skincare_option = 7
    elif best_skincare_option <= 1:
        best_skincare_option = 1
    else:
        pass

    return best_skincare_option, all_skincare_hydration_pred[best_skincare_option-1], all_skincare_oxygen_pred[best_skincare_option-1]

def date_diff(ts_date_win):
    date_diff_list = []
    for date_row in ts_date_win:
        date_row = [date_row]
        date_a = datetime.date(int(str(ts_date_win[-1])[:4]), int(str(ts_date_win[-1])[5:7]), int(str(ts_date_win[-1])[8:10]))
        date_diff_sublist = []
        for date in date_row:
            date_diff_sublist.append(0.1*(date_a - datetime.date(int(str(date)[:4]), int(str(date)[5:7]), int(str(date)[8:10]))).days + 0.1) # + 1*0.1(normalization term) for predicting 1 day future
        date_diff_list.append(date_diff_sublist)
    date_diff_list = np.stack((date_diff_list), axis=1)[0]
    return date_diff_list

# extract user's history data from AWS RDS(MSSQL)
def hisrory_data_collection(user_email, historical_data_count): # make sure getting the data from MSSQL successfully
    historical_data_count = historical_data_count # for aggregating historical 2 data, and the current data
    connection_status = None
    reconnect_iter_counts = 10
    mssql_connection = None
    for i in range(reconnect_iter_counts):
        try: # if successfully connect to MSSQL
            oneUser_historical_data_dict, oneUser_historical_data_count = access_mssql_oneUser_historical_data(mssql_connection, user_email, historical_data_count)
            if oneUser_historical_data_count < historical_data_count: # if there is not enough historical data for the user, use the defult value, use the previous one to filled up (For the website use there must be one data for the user in mssql, since the user must get one detection from our APP)
                for i in range(historical_data_count-oneUser_historical_data_count): # see how many data is needed
                    oneUser_historical_data_dict[oneUser_historical_data_count] = oneUser_historical_data_dict[oneUser_historical_data_count-1]
                    oneUser_historical_data_count += 1
            else:
                pass
            connection_status = 'Connection is successful.'
            break
        except (pymssql.InterfaceError, pymssql.OperationalError) as e: # avoid connection is closed in sudden.
            connection_status = e
            print("connection_status = ", connection_status) # connection_status will be 'Connection is closed.'
            mssql_connection_setting()
    if connection_status != 'Connection is successful.': # when connection is closed and cannot be reconnected, use default value.
        print("connection_status = ", connection_status)
        hisrory_data_collection(user_email, historical_data_count)
    else:
        print("connection_status = ", connection_status)
        pass

    return oneUser_historical_data_dict


def _future_skincare_predict(user_email, user_age):
    skincare_ratio_default = choice([3, 4, 5])
    historical_data_count = 3
    oneUser_historical_data_dict = hisrory_data_collection(user_email, historical_data_count)
    oneUser_historical_data_list, user_score, user_longitude, user_latitude = historical_oneUserData_preprocessing(oneUser_historical_data_dict)
    historical_oneUser_data = oneUser_historical_data_list[::-1] # reverse all list for setting the oldest one at the first element
    ts_date_win = np.hstack((historical_oneUser_data[:, 0])) # [oldest date, ..., newest date]
    ts_date_diff = date_diff(ts_date_win)
    ts_temperature_win = np.hstack((historical_oneUser_data[:, 2]))
    ts_humidity_win = np.hstack((historical_oneUser_data[:, 3]))
    ts_avg_hydration_win = np.hstack((historical_oneUser_data[:, 4]))
    ts_avg_oxygen_win = np.hstack((historical_oneUser_data[:, 5]))
    pre_skincare_ratio = int(historical_oneUser_data[-2][-1])
    pre_time_h = int(historical_oneUser_data[-2][1])
    cur_time_h = int(historical_oneUser_data[-1][1])
    pre_date = historical_oneUser_data[-2][0]
    cur_date = historical_oneUser_data[-1][0]

    input_data_str = np.hstack((ts_date_diff, ts_temperature_win, ts_humidity_win, ts_avg_hydration_win, ts_avg_oxygen_win, [user_age], [skincare_ratio_default]))
    input_data_list = [float(element) for element in input_data_str]
    input_data = np.stack((input_data_list))
    # replace with your pre-trained model to fit your applications
    hydration_model_name = 'XGBmodel_Hyd.model'
    oxygen_model_name = 'XGBmodel_Oxy.model'
    hydration_model = XGB_model_Load(hydration_model_name)
    oxygen_model = XGB_model_Load(oxygen_model_name)
    pred_day_num = 3
    all_customized_skincare_ratio = []
    logitude = user_longitude
    latitude = user_latitude
    future_weather_info = get_future_weather(logitude, latitude)
    for pred_iter in range(pred_day_num):
        customized_skincare_ratio, hydration_pred, oxygen_pred = _choose_customized_skincare_ratio(input_data, hydration_model, oxygen_model, pre_skincare_ratio, pre_date, cur_date, pre_time_h, cur_time_h)
        all_customized_skincare_ratio.append(customized_skincare_ratio)
        temperature_next = future_weather_info[pred_iter][0]
        humidity_next = future_weather_info[pred_iter][1]
        # input data for the next day based on the prediction
        input_data_new = [input_data[1]+0.1, input_data[2]+0.1, 0.1, input_data[4], input_data[5], temperature_next, input_data[7], input_data[8], humidity_next, input_data[10], input_data[11], float(hydration_pred)*100, input_data[13], input_data[14], float(oxygen_pred)*100, input_data[15], customized_skincare_ratio]
        # date + 1
        pre_date = cur_date
        cur_date_datetimeForm = datetime.date(int(str(cur_date[:4])), int(str(cur_date[5:7])), int(str(cur_date[8:10])))
        cur_date_datetimeForm += timedelta(days=1)
        cur_date = cur_date_datetimeForm.strftime("%Y-%m-%d")
        input_data_new = np.stack((input_data_new))
        input_data = input_data_new
    response_data = str(all_customized_skincare_ratio)
    return response_data, oneUser_historical_data_list, user_score, user_longitude, user_latitude

@app.route('/popupshop', methods=['GET'])
def Base_getdata():
    return render_template('Base.html')

@app.route('/popupshop/NewUser', methods=['GET'])
def NewUser_getdata():
    return render_template('NewUser.html')

@app.route('/popupshop/CheckHistory', methods=['GET'])
def CheckHistory_getdata():
    return render_template('CheckHistory.html')

@app.route('/popupshop/CheckHistory/OneHistory', methods=['GET'])
def CheckHistoryOne_getdata():
    return render_template('CheckHistoryOne.html')

#In .html, when submit is pressed, then trigger following functions
@app.route('/popupshop/NewUser/Submit', methods=['POST'])
def submit():
    user_name = request.form.get('username')
    user_age = request.form.get('userage')
    user_email = request.form.get('useremail')
    user_phone = request.form.get('userphone')
    ba_email = request.form.get('baemail')
    # Check if there is any data of this user in SQLite
    db_name = 'user.db'
    db_conn, db_cursor = DB_connect(db_name)
    user_info_DB = get_users_by_email(ba_email, user_email, db_cursor)
    print("Hello, "+user_name)

    # Get history data from MSSQL by User's email
    oneUser_historical_data_dict = access_mssql_oneUser_historical_data(None, str(ba_email), 1)
    response_data, oneUser_historical_data_list, user_score, user_longitude, user_latitude = _future_skincare_predict(ba_email, user_age)
    hydration_avg = oneUser_historical_data_list[0, 4]
    oxygen_avg = oneUser_historical_data_list[0, 5]
    user_info_new = User(user_name, user_age, user_email, user_phone, str(datetime.datetime.now()), response_data, hydration_avg, oxygen_avg, user_score, ba_email)
    #print("user_info_new = ", user_info_new)
    insert_user(user_info_new, db_conn, db_cursor)
    recent_histories = user_info_DB
    #return response_data
    return render_template(
        'NewUserSubmit.html',
        recent_histories=recent_histories,
        username=user_name,
        skincare=response_data,
    )

@app.route('/popupshop/CheckHistory/AllHistory', methods=['GET'])
def history_all():
    db_name = 'user.db'
    db_conn, db_cursor = DB_connect(db_name)
    recent_histories = get_all_users(db_cursor)
    return render_template(
        'CheckHistoryAll.html',
        recent_histories=recent_histories
    )

@app.route('/popupshop/CheckHistory/CheckHistoryOne/Submit', methods=['POST'])
def history_one():
    user_email = request.form.get('useremail')
    ba_email = request.form.get('baemail')
    db_name = 'user.db'
    db_conn, db_cursor = DB_connect(db_name)
    recent_histories = get_users_by_email(ba_email, user_email, db_cursor)
    user_name = get_users_name_by_email(ba_email, user_email, db_cursor)
    return render_template(
        'CheckHistoryOneSubmit.html',
        username=user_name,
        recent_histories=recent_histories
    )

if __name__ == '__main__':
    app.debug = True
    http_server = WSGIServer(('0.0.0.0', 8888), app)
    http_server.serve_forever()
