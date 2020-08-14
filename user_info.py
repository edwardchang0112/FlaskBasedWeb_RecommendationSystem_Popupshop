import datetime

"""User info class"""
class User:
    def __init__(self, name, age, user_email, phone, time, product, hydration_avg, oxygen_avg, score, ba_email):
        self.name = name
        self.age = age
        self.user_email = user_email
        self.phone = phone
        self.time = time
        self.product = product
        self.hydration_avg = hydration_avg
        self.oxygen_avg = oxygen_avg
        self.score = score
        self.ba_email = ba_email

    def name(self):
        return '{}'.format(self.name)

    def age(self):
        return '{}'.format(self.age)

    def user_email(self):
        return '{}'.format(self.user_email)

    def phone(self):
        return '{}'.format(self.phone)

    def time(self):
        return '{}'.format(self.time)

    def product(self):
        return '{}'.format(self.product)

    def hydration_avg(self):
        return '{}'.format(self.hydration_avg)

    def oxygen_avg(self):
        return '{}'.format(self.oxygen_avg)

    def score(self):
        return '{}'.format(self.score)

    def ba_email(self):
        return '{}'.format(self.ba_email)

    def __repr__(self):
        return "User('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(self.name, self.age, self.user_email, self.phone, self.time, self.product, self.hydration_avg, self.oxygen_avg, self.score, self.ba_email)

if __name__ == '__main__':
    user_1 = User('John', 'a123456@gmail.com', '0912345678', str(datetime.datetime.now()), str([1, 2, 3]))
    #user_2 = User('Mary', 'b123456@gmail.com', str(datetime.datetime.now()), str([1, 2, 3]))
    print(user_1.time)


