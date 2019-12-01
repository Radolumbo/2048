from flask import Flask, render_template
import os
from flask_socketio import SocketIO, emit
from mysql.connector import pooling
from mysql.connector import errors as sqlerr
from mysql.connector import errorcode as sqlerrcode
import json
from flask import request

SECRET_CONFIG_FILE = '/config/smashbot/super_secret_config.prod.json'
NSA_IS_WATCHING = {}

with open(SECRET_CONFIG_FILE) as json_file:  
    NSA_IS_WATCHING = json.load(json_file)

(host, name, user, password) = (NSA_IS_WATCHING["db_host"], NSA_IS_WATCHING["db_name"], NSA_IS_WATCHING["db_user"], NSA_IS_WATCHING["db_pass"])

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

socketio = SocketIO(app)
pool = pooling.MySQLConnectionPool(pool_name = "furry_pool",
                                    pool_size = pooling.CNX_POOL_MAXSIZE,
                                    database = name,
                                    host = host,
                                    user = user,
                                    passwd = password)

def get_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR'] # if behind a proxy
                                    

@app.route('/')
def hello():
    return render_template('index.html')

@socketio.on('score')
def score_handle(json):
    cursor = None
    conn = None
    try: 
        score = json["new_score"]
        name = json["name"]
        hash_id = get_ip()
        conn = pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT score FROM beard_score WHERE hash_id = %(hash_id)s"
        cursor.execute(query, {"hash_id": hash_id})
        row = cursor.fetchone()
        if(row is not None and score < row["score"]):
            pass
        else:
            query = "REPLACE INTO beard_score VALUES (%(hash_id)s, %(name)s, %(score)s)"
            cursor.execute(query, {"score": score, "name": name, "hash_id": hash_id})
        conn.commit()

        query = "select player_name, score from beard_score order by score desc limit 20"
        cursor.execute(query)

        html = ""

        for row in cursor.fetchall():
            html += f"<tr><td>{row['player_name']}</td><td>{row['score']}</td></tr>\n"

        emit("leaderboard",html)
    except Exception as e:
        print(e)
        raise
    finally:
        if cursor is not None:
            cursor.close()
        # returns connection back to pool
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    socketio.run(app,
        host=os.getenv('LISTEN', '0.0.0.0'),
        port=int(os.getenv('PORT', '8080'))
    )