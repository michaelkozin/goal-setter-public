import sqlite3
import os
import datetime
from flask import Flask, render_template, request

project = r"C:\Users\Michael\Documents\Python\web-projects\goal-setter"

os.chdir(project)

db = sqlite3.connect("goals.db")

def refresh_db(db):
    db.executescript("""
    DROP TABLE IF EXISTS goals;

    CREATE TABLE IF NOT EXISTS goals
    (
    id          INT      NOT NULL,
    start       DATETIME NOT NULL,
    end         DATETIME NOT NULL,
    description VARCHAR  NULL    ,
    steps       INT      NULL    ,
    active      BOOL     NULL    ,
    subject     VARCHAR  NULL    ,
    created     DATETIME NULL    ,
    PRIMARY KEY (id)
    );

    DROP TABLE IF EXISTS user;

    CREATE TABLE IF NOT EXISTS user
    (
    id       INT     NOT NULL,
    name     VARCHAR NOT NULL,
    password VARCHAR NOT NULL,
    mail     VARCHAR NOT NULL,
    created  DATETIME NULL,
    PRIMARY KEY (id)
    );

    DROP TABLE IF EXISTS user_goal;

    CREATE TABLE IF NOT EXISTS user_goal
    (
    id      INT NOT NULL,
    goal_id INT NOT NULL,
    user_id INT NOT NULL,
    PRIMARY KEY (id)
    );""")
    db.commit()


def gen_random_values_in_db(db):
    db.executescript("""
    INSERT INTO user
    VALUES (1, "first", "1111", "one@gmail.com", date('now')),
    (2, "second", "2222",  "two@gmail.com", date('now')),
    (3, "third", "3333",  "three@gmail.com", date('now')),
    (4, "fourth", "4444",  "four@gmail.com", date('now')),
    (5, "fifth", "5555",  "five@gmail.com", date('now'));

    INSERT INTO goals (id , start, end, description, created)
    VALUES (1, date("now"), date("now"), "one@gmail.com", date('now')),
    (2, date("now"), date('now',
    'start of month',
    '+3 month','-1 day'), "me@gmail.com", date('now'));

    INSERT INTO user_goal
    VALUES (1, 1, 1),
    (2, 2, 2),
    (3, 3, 3);
    """)
    db.commit()
    print("random values generated")

cur = db.cursor()

def check_user_exist(name_check):
    query = ("SELECT name FROM USER WHERE name = :name")
    cur.execute(query, {"name": name_check})
    if len(cur.fetchall()) == 0:
        return False
    else:
        return True

def get_new_id(table = "user"):
    query = (f"SELECT MAX(id) FROM {table}")
    cur.execute(query)
    result = cur.fetchall()
    if ((len(result) == 0) | (result[0][0] == None)):
        return 1
    else:
        return int(result[0][0]) + 1


def add_user(name, password, email):
    if check_user_exist(name) == False:
        query = "INSERT INTO user (id, name, password, mail, created) VALUES (:id, :name, :password, :email, date('now'))"
        cur.execute(query, {"id": get_new_id(table = 'user'), 
        "name": name, 
        "password": password,
        "email": email})
        print(f"user: {name}, added successfully, timestamp: {datetime.datetime.now()}")
        db.commit()
        return True
    else:
        raise Exception("user already exists")
        


def get_user_id(name):
    query = ("SELECT id FROM USER WHERE name = :name")
    cur.execute(query, {"name": name})
    result = cur.fetchall()
    if len(result) == 0:
        raise Exception("User doesn't exist")
    else:
        return result[0][0]

date_format = "%Y-%m-%d"

def check_valid_time(time):
    try:
        result = isinstance(datetime.datetime.strptime(time, date_format), datetime.datetime)
        return result
    except ValueError:
        return False
    

def add_goal(user_name, start, end, description = None, steps = None, active = True, subject = None):
    query = ("INSERT INTO goals VALUES (:id, date(:start), date(:end), :description, :steps, :active, :subject, date('now'))")
    if (check_valid_time(start) & check_valid_time(end)):
        goal_id =  get_new_id(table = "goals")
        res = cur.execute(query, {"id": goal_id,
        "start": start,
        "end": end,
        "description": description,
        "steps": steps,
        "active": active,
        "subject": subject})
        cur.execute("INSERT INTO user_goal VALUES (:id, :goal_id, :user_id)",
         {"id": get_new_id(table = "user_goal"), "goal_id": goal_id, "user_id": get_user_id(user_name)})
        print(f"user: {user_name}, goal id: {goal_id}, start: {start}, end: {end}. - succesfull")
        db.commit()
    else:
        print("bad date fomat, try the format: YYYY-MM-DD")

def remove_goal(goal_id):
    query = "DELETE FROM goals where id = :goal_id"
    cur.execute(query, {"goal_id": goal_id})
    query = "DELETE FROM user_goal where goal_id = :goal_id"
    cur.execute(query, {"goal_id": goal_id})
    print(f"goal no.{goal_id} deleted succefully")
    db.commit()

def remove_user(user_id):
    query = "DELETE FROM goals where id = (SELECT goal_id FROM user_goal where user_id = :user_id)"
    cur.execute(query, {"user_id": user_id})
    query = "DELETE FROM user where id = :user_id"
    cur.execute(query, {"user_id": user_id})
    query = "DELETE FROM user_goal where user_id = :user_id"
    cur.execute(query, {"user_id": user_id})
    print(f"user no.{user_id} and his goals deleted succefully")
    db.commit()


def update_value(table_name, id, column, new_value):
    if ((table_name == "goals") & (column in ["start", "end"])):
        if check_valid_time(new_value):
            query = f"UPDATE {table_name} SET {column} = :new_value WHERE id = {id}"
            cur.execute(query, {"new_value": new_value})
            print(f"{column} was updated to {new_value}")
            db.commit()
        else:
            print("bad date fomat, try the format: YYYY-MM-DD")
    else:
        query = f"UPDATE {table_name} SET {column} = :new_value WHERE id = {id}"
        cur.execute(query, {"new_value": new_value})
        print(f"{column} was updated to {new_value}")
        db.commit()
        db.close()

def get_goal(goal_id):
      query = ("SELECT *  FROM goals where id = :goal_id")
      res = cur.execute(query, {"goal_id": goal_id}).fetchall()
      keys = [i[0] for i in cur.description]
      values = res[0]
      return dict(zip(keys, values))

refresh_db(db)

gen_random_values_in_db(db)


add_user("david", 1234, 1111)

add_goal(user_name = "david", start = "2020-12-21", end = "2021-06-06")

print(cur.execute("SELECT * FROM goals where id = 3;").fetchall())

update_value("goals", 3, "end", "2020-01-01")

print(cur.execute("SELECT * FROM goals where id = 3;").fetchall())

get_goal(2)

db.close()