import sqlite3

def insert_user(user, conn, c):
    with conn:
        c.execute("INSERT INTO users VALUES (:name, :age, :user_email, :phone, :time, :product, :hydration_avg, :oxygen_avg, :score, :ba_email)", {'name': user.name, 'age': user.age, 'user_email': user.user_email, 'phone': user.phone, 'time': user.time, 'product': user.product, 'hydration_avg': user.hydration_avg, 'oxygen_avg': user.oxygen_avg, 'score': user.score, 'ba_email': user.ba_email})

def get_users_by_email(ba_email, user_email, c):
    c.execute("SELECT * FROM users WHERE ba_email= :ba_email AND user_email= :user_email", {'ba_email': ba_email, 'user_email': user_email})
    return c.fetchall()

def get_users_name_by_email(ba_email, user_email, c):
    c.execute("SELECT name FROM users WHERE ba_email= :ba_email AND user_email= :user_email", {'ba_email': ba_email, 'user_email': user_email})
    return c.fetchall()[0][0]

def get_all_users(c):
    c.execute("SELECT * FROM users")
    return c.fetchall()

def remove_user(user):
    with conn:
        c.execute("DELETE from users WHERE name= :name AND email= :email",
                  {'name': user.name, 'email': user.email})

def remove_all_users():
    with conn:
        c.execute("DELETE from users")

if __name__ == '__main__':
    conn = sqlite3.connect('user.db')

    c = conn.cursor()

    # create new table in DB
    c.execute("""CREATE TABLE users (
                name text,
                age text,
                user_email text,
                phone text,
                time text,
                product text, 
                hydration_avg text,
                oxygen_avg text,
                score text,
                ba_email text
                )""")

    #remove_all_users()

    #user_1 = User('John', 'a123456@gmail.com', '0912345678', str(datetime.datetime.now()), str([1, 2, 3]))
    #user_2 = User('Mary', 'b123456@gmail.com', '0987654321', str(datetime.datetime.now()), str([1, 2, 3]))

    #insert_user(user_1)
    #insert_user(user_2)

    #users = get_all_users()
    #print(users)

    #users = get_users_by_email('b123456@gmail.com')
    #print(users)

    ##update(emp_2, 95000)
    #remove_user(user_2)
    #users = get_all_users()
    #print(users)

    conn.close()
