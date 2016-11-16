#coding:utf-8
import os

from flask import Flask
from flask import redirect
from flask import render_template
from flask import session
from flask import url_for
from flask.ext.bootstrap import Bootstrap
from flask.ext.mail import Mail, Message
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager, Shell
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

secret_key = 'wobuzhidao'
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# 防止攻击，保证安全
app.config['SECRET_KEY'] = secret_key

#配置邮箱
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] = 'Flasky Admin <flasky@example.com>'
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:////' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)

# 如果不添加会有Warming
track_modifications = app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', True)

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
mail = Mail()

#数据迁移
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    mail.send(msg)


class NameForm(FlaskForm):
    name = StringField('你的名字？', validators=[DataRequired()])
    submit = SubmitField('提交')


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    users = db.relationship('User', backref='role')

    def __repr__(self):
        return '<Role %r>' % self.name  # ％r为repr方法输出  ％s为str方法输出


# 自动导入数据库实例和模型
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


manager.add_command("shell", Shell(make_context=make_shell_context))


@app.route('/', methods=['GET', 'POST'])
def index():
    # name = None
    # nameForm = NameForm()
    #
    # if nameForm.validate_on_submit():
    #     nameForm.name.data = ''

    form = NameForm()
    if form.validate_on_submit():
        # old_name =session.get('name')
        user = User.query.filter_by(username=form.name.data).first()
        # if old_name is not None and old_name != form.name.data:
        #     flash('Looks like you have changed your name!')

        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False

            if app.config['FLASKY_ADMIN']:
                send_email(app.config['FLASKY_ADMIN'], 'New User',
                           'mail/new_user', user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))

    # return render_template('index.html', current_time=datetime.utcnow())
    return render_template('index.html',
                           form=form,
                           name=session.get('name'),
                           known=session.get('known', False))


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404  # 状态码


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    # db.create_all()
    manager.run()
