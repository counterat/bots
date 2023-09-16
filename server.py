from flask import Flask, request, render_template
import requests
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__ , template_folder="templates")
# Настройка базы данных SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workers.db'
db = SQLAlchemy(app)




class Worker(db.Model):
    telegram_id = db.Column(db.String, primary_key=True)
    balance = db.Column(db.Float, default=0.0)
    profit = db.Column(db.Float, default=0.0)
    warnings = db.Column(db.Integer, default=0)
    payment_method = db.Column(db.String, default='Crypto USDT')

    def __init__(self, telegram_id, balance=0.0, profit=0.0, warnings=0, payment_method=''):
        self.telegram_id = telegram_id
        self.balance = balance
        self.profit = profit
        self.warnings = warnings
        self.payment_method = payment_method

with app.app_context():
    db.create_all()


@app.route('/verify', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        id = request.form.get('user_id')
        ip_address = '93.170.53.32'
        response = requests.get(f'https://ipinfo.io/{ip_address}/country')
        if response.status_code == 200:
            if response.text.strip() == 'UA':
                is_ukrainian = True
            else:
                is_ukrainian = False

            new_worker = Worker(id, is_ukrainian)
            db.session.add(new_worker)
            db.session.commit()



            return "верифицирован"
        else:
            return 'не верифицрован'

    return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=True)