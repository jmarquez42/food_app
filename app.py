#/mnt/c/Users/User/PycharmProjects/food_app
#source /mnt/c/Users/User/flask_app/Scripts/activate

from flask import Flask, render_template, g, request
import sqlite3
from _datetime import datetime

app = Flask(__name__)


def connect_db():
    sql = sqlite3.connect(b'food_log.db')
    sql.row_factory = sqlite3.Row
    return sql


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    print(g)
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()
    if request.method == 'POST':
        date = request.form['date']
        dt = datetime.strptime(date, '%Y-%m-%d')
        try:
            database_date = datetime.strftime(dt, '%Y%m%d')
            db.execute('INSERT INTO log_date (entry_date) values (?)', [database_date])
            db.commit()
        except Exception as e:
            close_db(e)

    cur = db.execute("SELECT entry_date FROM log_date ORDER BY entry_date DESC ")
    result = cur.fetchall()

    pretty_results = []
    for i in result:
        single_date = {}
        d = datetime.strptime(str(i['entry_date']), '%Y%m%d')
        single_date['entry_date'] = datetime.strftime(d, '%B %d, %Y')

        pretty_results.append(single_date)
    print(pretty_results)
    return render_template('home.html', results=pretty_results)


@app.route('/view/<date>', methods=['GET', 'POST'])
def view(date):
    db = get_db()
    qry_date = db.execute("SELECT id, entry_date FROM log_date WHERE entry_date = ?", [date])
    result_date = qry_date.fetchone()

    if request.method == 'POST':
        try:
            value = request.form['food-select']
            db.execute('INSERT INTO food_date (food_id, log_date_id) values ( ?,?)', [value, result_date['id']])
            db.commit()
        except Exception as e:
            print(e)
            db.rollback()


    qry_foods = db.execute("SELECT id, name FROM food")
    list_foods = qry_foods.fetchall()
    print(list_foods)

    d = datetime.strptime(str(result_date['entry_date']), '%Y%m%d')
    pretty_date = datetime.strftime(d, '%B %d, %Y')

    log_cur = db.execute('\
                        SELECT food.name, food.protein, food.carbohydrates, food.fat, food.calories \
                        FROM log_date  JOIN food_date ON food_date.log_date_id = log_date.id JOIN food ON food.id = food_date.food_id \
                        WHERE log_date.entry_date = ?', [date])

    log_result = log_cur.fetchall()
    print(log_result)

    totals = {}
    totals['protein'] = 0
    totals['carbohydrates'] = 0
    totals['fat'] = 0
    totals['calories'] = 0

    for t in log_result:
        totals['protein'] += t['protein']
        totals['carbohydrates'] += t['carbohydrates']
        totals['fat'] += t['fat']
        totals['calories'] += t['calories']
    print(totals)
    return render_template('day.html', dates=pretty_date, foods=list_foods, log_results=log_result, total=totals)


@app.route('/food', methods=['GET', 'POST'])
def food():
    db = get_db()
    if request.method == 'POST':
        name = request.form['food-name']
        protein = int(request.form['protein'])
        carbohydrates = int(request.form['carbohydrates'])
        fat = int(request.form['fat'])
        calories = protein * 4 + carbohydrates * 4 + fat * 9
        insert = 'INSERT INTO food (name, protein, carbohydrates, fat, calories) values (' + '?,' * 4 + '?)'
        db.execute(insert, [name, protein, carbohydrates, fat, calories])
        db.commit()
        del request.form['food-name']

    cur = db.execute('SELECT name, protein, carbohydrates, fat, calories FROM food')
    results = cur.fetchall()
    return render_template('add_food.html', results=results)


if __name__ == '__main__':
    app.run(debug=True)