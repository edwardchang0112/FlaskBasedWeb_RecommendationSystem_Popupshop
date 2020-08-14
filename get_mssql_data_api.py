import pymssql
from load_input_mssql_data import historical_oneUserData_preprocessing

def mssql_connection_setting():
    mssql_server = 'instance-mssql.XXXXXXXXXXXX.XXXXXXXXX.rds.amazonaws.com'
    mssql_port = 1234
    mssql_user = 'XXXdb'
    mssql_password = 'XXXXXXXX'
    mssql_database = 'XXXdb'
    conn = pymssql.connect(server=mssql_server, port=mssql_port, user=mssql_user, password=mssql_password, database=mssql_database, charset="utf8")
    return conn

def access_mssql_oneUser_historical_data(mssql_conn, UserEmail, historic_day_count):
    conn = mssql_connection_setting()
    #conn = mssql_conn
    cursor = conn.cursor(as_dict=True)
    cursor.execute('SELECT UserID FROM icidb.dbo.[User] WHERE Email='+"'"+str(UserEmail)+"'")
    UserID_mssql = cursor.fetchall()
    UserID = UserID_mssql[0]['UserID']
    cursor.execute('SELECT top '+str(historic_day_count)+' * FROM icidb.dbo.Record WHERE (UserID='+str(UserID)+') AND (DeleteDate IS NULL) order by uploadTime DESC')
    user_data_dict = {}
    dict_index_count = 0
    user_data = cursor.fetchall()
    for sub_user_data in user_data:
        user_data_dict[dict_index_count] = sub_user_data
        dict_index_count += 1
    conn.commit()
    cursor.close()
    #conn.close()
    return user_data_dict, dict_index_count # check if there is enough historical data for the user in our database

