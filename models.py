from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id_, name, email, role):
        self.id = id_
        self.name = name
        self.email = email
        self.role = role
