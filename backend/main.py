from flask import Flask, jsonify
from flask_security import Security, SQLAlchemyUserDatastore
from flask_cors import CORS
from models import db, datastore
from resources import api
from werkzeug.security import generate_password_hash, check_password_hash
from instances import cache
from worker import celery_init_app

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "thisissecter"
app.config['SECURITY_PASSWORD_SALT'] = "thisissaltt"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = False
app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Authentication-Token'
app.config['CACHE_TYPE'] = "RedisCache"
app.config['CACHE_REDIS_HOST'] = "localhost"
app.config['CACHE_REDIS_PORT'] = 6379
app.config.from_mapping(
    CELERY=dict(
        broker_url="redis://localhost:6379/1",
        result_backend="redis://localhost:6379/2",
        task_ignore_result=True,
        timezone="Asia/kolkata"
    ),
)
db.init_app(app)
api.init_app(app)
cache.init_app(app)
celery_app = celery_init_app(app)

CORS(app, resources={r"/*" : {'origins' : "*"}})

app.security = Security(app, datastore)

with app.app_context():
    import views
    db.create_all()
    if not datastore.find_role("admin"):
        datastore.create_role(name="admin")
    if not datastore.find_role("user"):
        datastore.create_role(name="user")
    if not datastore.find_role("manager"):
        datastore.create_role(name="manager")
    if not datastore.find_user(email="admin@grocery.com"):
        datastore.create_user(email="admin@grocery.com", password=generate_password_hash("admin"), roles=["admin"], name="admin", address="admin", phone=1234567890, active=True)
    datastore.commit()
    

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")