import datetime
import os
import sqlite3
import bcrypt

Host = "ec2-54-87-112-29.compute-1.amazonaws.com"
Database_name = "dbi8jtb4fm82j6"
Username = "wjsdqozngyzbip"
Port = 5432
Password = "a9f7dafc9543e3e003cea2d6d8a1dff06fff47fb4817db61d1d91540b56e7dd8"

from peewee import (Model, TextField, IntegerField,
                    FloatField, BooleanField, CharField,
                    DateTimeField,ForeignKeyField,
                    PostgresqlDatabase, fn, JOIN)

database = PostgresqlDatabase(Database_name, user = Username, 
password = Password, host = Host, port = Port)

class UnknownField(object):
    def __init__(self, *_, **__):
         pass

class BaseModel(Model):
    class Meta:
        database = database

class Goals(BaseModel):
    active = BooleanField(null=True)
    created = DateTimeField(null=True)
    description = TextField(null=True)
    end = DateTimeField()
    start = DateTimeField()
    steps = IntegerField(null=True)
    subject = TextField(null=True)

    class Meta:
        table_name = 'goals'

class User(BaseModel):
    created = DateTimeField(null=True)
    mail = TextField(unique = True)
    name = TextField(unique = True)
    password = TextField()
    class Meta:
        table_name = 'user'

class UserGoal(BaseModel):
    goal_id = ForeignKeyField(Goals)
    user_id = ForeignKeyField(User)

    class Meta:
        table_name = 'user_goal'

class Roles(BaseModel):
    user_id = ForeignKeyField(User)
    role_name = TextField(null=True)

    class Meta:
        table_name = 'roles'

class UserRole(BaseModel):
    user_id = ForeignKeyField(User)
    role_id = ForeignKeyField(Roles)
    class Meta:
        table_name = 'user_role'

class UserDelete(BaseModel):
    user_id = ForeignKeyField(User)
    class Meta:
        table_name = 'user_delete'


# database.connect()

#query = Goals.select(Goals).join(UserGoal,
# JOIN.LEFT_OUTER).where(UserGoal.user_id == 1).dicts().execute()

#for i in query:
#    print(i)

# query = Goals.select().where(Goals.id == 4)
# time_diff = str(round(((query.get().start - datetime.datetime.now())/(query.get().start - query.get().end)) * 100)) + "%"
# print(time_diff)
# #

# query = (Goals.select(Goals).join(UserGoal,
#             JOIN.LEFT_OUTER)
#             .where(UserGoal.user_id == 1)
#             .execute())
# goals = [i for i in query]
# now = datetime.datetime.now()
# time = [((now - i.start)/(i.end - i.start)) if i.start < now else 0
# for i in query]

# print(list(zip(goals, time)))


def get_showcase_goals():
    query = Goals.select().order_by(Goals.created).limit(10).execute()
    now = datetime.datetime.now()
    goals = [i.subject for i in query]
    time_diffs = [str(round(((now - i.start)/(i.end - i.start)) * 100)) + "%"
        if ((i.start < now) & (i.end > now)) else "100%" if i.end < now else "0%" 
        for i in query]
    goals_diffs = zip(goals, time_diffs)
    return goals_diffs

# showcase_goals = get_showcase_goals()

# print(list(showcase_goals))

# database.close()
#on=(Goals.id == UserGoal.goal_id)

# populate tables
database.connect()

# for i in range(6, 12):
#     UserDelete.create(user_id = i)

#UserGoal.delete().where(UserGoal.user_id.in_(delete_users)).execute()
# Goals.delete().where(Goals.id.in_(goal_ids)).execute()

database.close()
