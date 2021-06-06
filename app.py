import datetime
import os
import sqlite3
import peewee
import bcrypt
import schedule
from apscheduler.schedulers.background import BackgroundScheduler
from secrets import secret_key
from models import (database, User, Goals, UserGoal, Roles, UserRole,
                    UserDelete)

from flask import (Flask, render_template, abort, session
, request, flash, redirect, url_for)

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = secret_key

@app.before_request
def _db_connect():
    database.connect()

@app.teardown_request
def _db_close(_ecex):
    if not database.is_closed():
        database.close()

@app.route('/goal/<int:goal_id>')
def get_goal(goal_id): 
    if session.get('username') is None:
        return abort(403, "You must be logged in to view your goals.")
    try:
        goal = Goals.select().where(Goals.id == goal_id).dicts().get()
        return render_template("goal.j2", **goal)
    except peewee.DoesNotExist:
        abort(404, f'goal no.{goal_id} doesnt exist.')

@app.route('/user_goals/<string:user_name>', methods = ['GET','POST'])
def get_user_goals(user_name): 
    if request.method == 'GET':
        if session.get('username') is None:
            return abort(403, "You must be logged in to view your goals.")
        if session.get('username') != user_name:
            return abort(403, f"You are not logged in as {user_name}")
        try:
            query = (Goals.select(Goals).join(UserGoal,
                        peewee.JOIN.LEFT_OUTER)
                        .where(UserGoal.user_id == session.get("user_id")).order_by(Goals.id)
                        .execute())
            goals = [i for i in query]
            now = datetime.datetime.now()
            time_diffs = [str(round(((now - i.start)/(i.end - i.start)) * 100)) + "%"
             if ((i.start < now) & (i.end > now)) else "100%" if i.end < now else "0%" 
              for i in query]
            goals_diffs = zip(goals, time_diffs)
            return render_template("get_user_goals.j2", goals = goals_diffs)
        except peewee.DoesNotExist:
            abort(404, f"user {user_name} doesn't have any goals yet")
    if request.method == 'POST':
        action = request.form["btn"]
        goal_ids = [int(i) for i in request.form.getlist("action")]
        if action == 'delete':
            UserGoal.delete().where(UserGoal.goal_id.in_(goal_ids)).execute()
            Goals.delete().where(Goals.id.in_(goal_ids)).execute()
            goals = [i for i in Goals.select(Goals).join(UserGoal,
                        peewee.JOIN.LEFT_OUTER)
                        .where(UserGoal.user_id == session.get("user_id"))
                        .execute()]
            return render_template("get_user_goals.j2", goals = goals_diffs)
        if action == 'edit':
            session["edit_list"] = goal_ids
            return redirect(url_for("update_goals"))
        if action == 'add-goal':
            try:
                max_goal_id = Goals.select(peewee.fn.MAX(Goals.id)).dicts().get()
                if max_goal_id["max"] == None:
                    max_goal_id = 0
                else:
                    max_goal_id = int(max_goal_id["max"])
                subject = request.form["subject"]
                description = request.form["description"]
                start = request.form["start"]
                end = request.form["end"]
                if end < start:
                   return abort(403, "End date must be after start date.")
                goal_id =  int(max_goal_id + 1)
                Goals.create(id = goal_id,
                            active = 1,
                            description = description,
                            subject = subject,
                            start = start,
                            end = end,
                            created = datetime.datetime.now())

                max_user_goal_id = UserGoal.select(peewee.fn.MAX(UserGoal.id)).dicts().get()
                if max_user_goal_id["max"] == None:
                    max_user_goal_id = 0
                else:
                    max_user_goal_id = int(max_user_goal_id["max"])
                user_goal_id =  int(max_user_goal_id + 1)
                UserGoal.create(id = user_goal_id,
                                goal_id = goal_id,
                                user_id = session["user_id"])
                return redirect(url_for("get_user_goals", user_name = session.get('username')))
            except peewee.IntegrityError:
                abort(400, "Bad goal Input")
            except  peewee.DataError:
                flash("Bad data Input")
                return redirect(url_for("get_user_goals", user_name = session.get('username')))

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.j2")
    try:
        max_user_id = User.select(peewee.fn.MAX(User.id)).get().max
        if max_user_id is None:
            max_user_id = 0
        else:
            max_user_id = int(max_user_id)
        
        salt = bcrypt.gensalt()
        username = request.form["name"]
        email = request.form["mail"]
        User.create(id = int(max_user_id + 1),
        name = username,
        password = bcrypt.hashpw(request.form["password"].encode('utf-8'), salt),
        salt = salt,
        mail = email,
        created = datetime.datetime.now())
        UserRole.create(user_id = int(max_user_id + 1), role_id = 2)
        return "User created successfully"
    except peewee.IntegrityError:
        abort(400, "Username or Email already exist")

@app.route('/edit_user', methods = ['GET', 'POST'])
def edit_user():
    if request.method == 'GET':
        return render_template("edit_user.j2")
    try:
        user = User.select().where(User.id == session["user_id"]).get()
        if ((request.form['first-password'] == request.form['second-password'])
         & (request.form['first-password'] != "password")):
            salt = bcrypt.gensalt()
            password = bcrypt.hashpw(request.form['first-password'].encode('utf-8'), salt)
        elif (request.form['first-password'] != request.form['second-password']):
            flash("The Passwords Don't Match")
            return render_template("edit_user.j2")
        else:
            password = User.password
        username = request.form["name"]
        email = request.form["mail"]
        User.update(name = username, 
        password = password,
        mail = email).where(User.id == session.get("user_id")).execute()
        UserRole.update(role_id = 2).where(UserRole.user_id == session.get("user_id")).execute()
        if session["type"] == "guest":
            session["type"] = "user"
            UserDelete.delete().where(UserDelete.user_id == session.get("user_id")).execute()
        flash("Changes Applied Successfully")
        return redirect(url_for("get_user_goals", user_name = session.get('username')))
    except peewee.IntegrityError:
        abort(400, "Username or Email already exist")

@app.route('/', methods = ['GET'])
def default():
    return redirect(url_for("login"))

@app.route('/guest', methods = ['GET', 'POST'])
def guest():
    if request.method == 'GET':
        if 'username' in session:
            return f"{session['username']} is already loggen in!"
    try:
        max_user_id = User.select(peewee.fn.MAX(User.id)).get().max
        if max_user_id is None:
            max_user_id = 0
        else:
            max_user_id = int(max_user_id)
        salt = bcrypt.gensalt()
        username = "Guest-" + str(max_user_id + 1)
        email = f"guest-{str(max_user_id + 1)}@myemail.com"
        User.create(id = int(max_user_id + 1),
        name = username,
        password = bcrypt.hashpw(("Guest-" + str(max_user_id + 1)).encode('utf-8'), salt),
        salt = salt,
        mail = email,
        created = datetime.datetime.now())
        UserRole.create(user_id = int(max_user_id + 1), role_id = 3)
        UserDelete.create(user_id = int(max_user_id + 1))
        session['username'] = username
        session['user_id'] = int(max_user_id + 1)
        session['now'] = datetime.datetime.now()
        session["mail"] = email
        session["type"] = "guest"
        flash("Enjoy your stay! Notice: guest data will be lost if not converted registered user")
        return redirect(url_for("get_user_goals", user_name = username))
    except peewee.IntegrityError:
        abort(400, "Username or Email already exist")


    return redirect(url_for("login"))

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'username' in session:
            #flash(f"{session['username']} is already loggen in!")
            return redirect(url_for("get_user_goals", user_name = session.get('username')))
        else:
            return render_template("login.j2", showcase = get_showcase_goals())
    try:
        username = request.form["name"]
        user = User.select().where(User.name == username).get()
        user_id = user.id
        user_mail = user.mail
        given_pw = request.form["password"].encode('utf-8')
        stored_hashpw =  User.select(User.password).where(User.name == username).dicts().get()["password"]
        if bcrypt.checkpw(given_pw, stored_hashpw.encode('utf-8')):  
            session['username'] = username
            session['user_id'] = user_id
            session['now'] = datetime.datetime.now()
            session["mail"] = user_mail
            session["type"] = "user"
            flash(f"{username} logged in successfully!")
            return redirect(url_for("get_user_goals", user_name = session.get('username')))
        else:
            flash("Bad username/password")
            return render_template("login.j2")
    except peewee.DoesNotExist:
      #  flash("User doesn't exist")
        return render_template("login.j2")

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    session.pop('now', None)
    session.pop('mail', None)
    session.pop('type', None)
    return redirect(url_for("login"))

@app.route('/add_goal', methods = ['GET', 'POST'])
def add_goal():
    if session.get('username') is None:
        return abort(403, "You must be logged in to view your goals.")
    if request.method == 'GET':
        return render_template("add_goal.j2")
    try:
        max_goal_id = Goals.select(peewee.fn.MAX(Goals.id)).dicts().get()
        if max_goal_id["max"] == None:
            max_goal_id = 0
        else:
            max_goal_id = int(max_goal_id["max"])
        subject = request.form["subject"]
        description = request.form["description"]
        start = request.form["start"]
        end = request.form["end"]
        goal_id =  int(max_goal_id + 1)
        Goals.create(id = goal_id,
                    active = 1,
                    description = description,
                    subject = subject,
                    start = start,
                    end = end,
                    created = datetime.datetime.now())

        max_user_goal_id = UserGoal.select(peewee.fn.MAX(UserGoal.id)).dicts().get()
        if max_user_goal_id["max"] == None:
            max_user_goal_id = 0
        else:
            max_user_goal_id = int(max_user_goal_id["max"])
        user_goal_id =  int(max_user_goal_id + 1)
        UserGoal.create(id = user_goal_id,
                        goal_id = goal_id,
                        user_id = session["user_id"])
        return redirect(url_for("get_user_goals", user_name = session.get('username')))
    except peewee.IntegrityError:
        abort(400, "Bad goal Input")

@app.route('/update_goals', methods = ['GET', 'POST'])
def update_goals():
    goals = session.get('edit_list')
    if session.get('username') is None:
        return abort(403, "You must be logged in to edit goals.")
    if request.method == 'GET':
        try:
            goal_list = [i for i in Goals.select()
                    .where(Goals.id.in_(goals))
                    .execute()]
            return render_template("update_goals.j2", goals = goal_list)
        except peewee.IntegrityError:
            abort(400, "Bad goal Input")
    if request.method == 'POST':
        descriptions = request.form.getlist("description")
        starts = request.form.getlist("start")
        ends = request.form.getlist("end")
        if ends < starts:
            return abort(403, "End date must be after start date.")
        subjects = request.form.getlist("subject")
        for i in range(len(descriptions)):
            Goals.update(description = descriptions[i],
                         start = starts[i],
                         end = ends[i],
                         subject = subjects[i]).where(Goals.id == goals[i]).execute()
        return redirect(url_for("get_user_goals", user_name = session.get('username')))

@app.route('/showcase_goals')
def showcase_goals():
    return render_template("showcase_goals.j2",
     goals = get_showcase_goals())

def get_showcase_goals():
    query = Goals.select().order_by(Goals.created.desc()).limit(10).execute()
    now = datetime.datetime.now()
    goals = [i.subject for i in query]
    time_diffs = [str(round(((now - i.start)/(i.end - i.start)) * 100)) + "%"
        if ((i.start < now) & (i.end > now)) else "100%" if i.end < now else "0%" 
        for i in query]
    goals_diffs = zip(goals, time_diffs)
    return goals_diffs

def delete_users():
    database.connect()
    query = UserDelete.select(UserDelete)
    delete_users = [user.user_id.id for user in query]
    delete_goals = [i.id for i in Goals.select(Goals).join(UserGoal,
            peewee.JOIN.LEFT_OUTER)
            .where(UserGoal.user_id.in_(delete_users))
            .execute()]
    UserGoal.delete().where(UserGoal.goal_id.in_(delete_goals)).execute()
    Goals.delete().where(Goals.id.in_(delete_goals)).execute()
    UserRole.delete().where(UserRole.user_id.in_(delete_users)).execute()
    UserDelete.delete().where(UserDelete.user_id.in_(delete_users)).execute()
    User.delete().where(User.id.in_(delete_users)).execute()
    database.close()
    print(f"delete users ran at: {datetime.datetime.now()}")

sched = BackgroundScheduler(daemon=True)
sched.add_job(delete_users,'interval',hours = 12)
sched.start()


if __name__ == '__main__':
    #app.run(threaded = True, port=5000)
    app.run()



