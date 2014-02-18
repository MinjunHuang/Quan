# -*- coding: utf-8 -*-
from datetime import datetime

from core import exceptions as local_exc
from core.views import AppHandler
from core.models.subjects import Circle, User, Status, Membership

from permissions import CirclePermission


class LoginHandler(AppHandler):

    def json_validate(self):

        self.validate_field_exist('cell_phone')
        self.validate_field_exist('password')

    def post(self):
        cell_phone = self.request_json['cell_phone']
        password = self.request_json['password']
        user = self.db.query(User).filter_by(cell_phone=cell_phone).first()
        if user:
            if user.check_password(password):
                user.last_login = datetime.now()
                user.access_token = user.generate_key()
                token_dict = {'access_token': user.access_token}
                self.db.commit()
                self.write(token_dict)
            else:
                raise local_exc.LoginError
        else:
            raise local_exc.UserNotExistError


class UserListHandler(AppHandler):

    def json_validate(self):

        self.validate_field_exist('cell_phone')
        self.validate_field_exist('password')

    def post(self):
        cell_phone = self.request_json['cell_phone']
        password = self.request_json['password']
        user = User(cell_phone=cell_phone, password=password)
        self.db.add(user)
        self.db.commit()
        token_dict = {'access_token': user.generate_key(),
                      'url': user.url}
        self.write(token_dict)

    def get(self):
        users = self.db.query(User).all()
        self.write({'list': [user.json for user in users]})


class UserDetailHandler(AppHandler):

    def prepare(self):
        super(UserDetailHandler, self).prepare()
        user_id = self.path_kwargs['uid']
        self.query_user = self.db.query(User).get(user_id)
        if not self.query_user:
            raise local_exc.UserNotExistError

    def get(self, **kwargs):
        self.write(self.query_user.json)

    def put(self, **kwargs):
        password = self.request_json.get('password', None)
        if password:
            self.query_user.generate_password(password)
            del self.request_json['password']
        self.query_user.update(self.request_json)
        self.db.commit()
        self.write(self.query_user.json)


class CircleListHandler(AppHandler):

    def json_validate(self):
        self.validate_field_exist('name')
        self.validate_field_exist('description')

    def get(self):
        circles = self.db.query(Circle).all()
        self.write({'list': [circle.json for circle in circles]})

    def post(self):
        name = self.request_json['name']
        description = self.request_json['description']
        circle = Circle(name=name, description=description)
        self.db.add(circle)
        membership = Membership(status=0, member=self.current_user,
                                circle=circle)
        self.db.add(membership)
        self.write(circle.json)
        self.db.commit()


class CircleHandler(AppHandler):

    def prepare(self):
        cirlce_id = self.path_kwargs['cid']
        self.query_circle = self.db.query(Circle).get(cirlce_id)
        if not self.query_circle:
            raise local_exc.CircleNotExistError
        super(CircleHandler, self).prepare()


class CircleDetailHandler(CircleHandler):

    permission_class = CirclePermission

    def get(self, **kwargs):
        self.write(self.query_circle.json)

    def json_validate(self):
        valide_keys = ['name', 'description']
        self.validate_fields_scope(self.request_json.keys(), valide_keys)

    def put(self, **kwargs):
        self.query_circle.update(self.request_json)
        self.db.commit()
        self.write(self.query_circle.json)


class CircleStatusHandler(CircleHandler):

    def get(self, **kwargs):
        self.write({'list': [status.json for status in self.query_circle.status]})

    def json_validate(self):
        self.validate_field_exist('content')

    def post(self, **kwargs):
        status = Status(content=self.request_json['content'])
        status.user = self.current_user
        status.cirlce = self.query_circle
        self.db.add(status)
        self.db.commit()
        self.write(status.json)
