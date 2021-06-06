from peewee import (Model, TextField, IntegerField,
                    FloatField, BooleanField, CharField,
                    DateTimeField,ForeignKeyField,
                    PostgresqlDatabase)

from secrets import (Database_name, User,
 Password, Host, Port)

database = PostgresqlDatabase(Database_name, user = User, 
password = Password, host = Host, port = Port)

#database = SqliteDatabase('goals.db')
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



TABLES = [Goals, User, UserGoal, Roles, UserRole, UserDelete]

with database.connection_context():
    database.create_tables(TABLES, safe = True)
