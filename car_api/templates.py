from flask import Blueprint
from flask_restplus import Api

templ = Blueprint('car_templ', __name__, template_folder='templates', static_folder='static')
api = Api(templ)

@templ.route("/")
def index():
    return "Car Market Template Page"