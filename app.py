from flask import Flask
from flask_restplus import Api, Resource, fields

app = Flask(__name__)
api = Api(app, title='Car Market API', description='API для рынка автомобилей')

# Основное пространство имён (как name_space в вашем примере)
ns_car = api.namespace('cars', description='Операции с автомобилями')

# Модель данных для автомобиля (аналог info в part.py)
car_model = api.model('Car', {
    'id': fields.String(required=True, description='ID автомобиля'),
    'brand': fields.String(required=True, description='Марка (Toyota, BMW)'),
    'model': fields.String(required=True, description='Модель (Camry, X5)'),
    'year': fields.Integer(description='Год выпуска'),
    'price': fields.Float(required=True, description='Цена ($)'),
    'mileage': fields.Integer(description='Пробег (км)'),
})

# "База данных" (аналог INFO в part.py)
CARS = [
    {'id': '1', 'brand': 'Toyota', 'model': 'Camry', 'year': 2020, 'price': 25000, 'mileage': 15000},
    {'id': '2', 'brand': 'BMW', 'model': 'X5', 'year': 2019, 'price': 45000, 'mileage': 30000},
]

# Эндпоинты для автомобилей (аналог InfoList и InfoId в part.py)
@ns_car.route('/')
class CarList(Resource):
    @ns_car.marshal_list_with(car_model)
    def get(self):
        """Список всех автомобилей"""
        return CARS

    @ns_car.expect(car_model)
    @ns_car.marshal_with(car_model, code=201)
    def post(self):
        """Добавить новый автомобиль"""
        new_car = api.payload
        CARS.append(new_car)
        return new_car, 201

@ns_car.route('/<string:id>')
@ns_car.param('id', 'ID автомобиля')
@ns_car.response(404, 'Автомобиль не найден')
class CarResource(Resource):
    @ns_car.marshal_with(car_model)
    def get(self, id):
        """Получить автомобиль по ID"""
        for car in CARS:
            if car['id'] == id:
                return car
        api.abort(404, "Автомобиль не найден")

    @ns_car.expect(car_model)
    @ns_car.marshal_with(car_model)
    def put(self, id):
        """Обновить данные автомобиля"""
        for car in CARS:
            if car['id'] == id:
                car.update(api.payload)
                return car
        api.abort(404, "Автомобиль не найден")

    def delete(self, id):
        """Удалить автомобиль"""
        global CARS
        CARS = [car for car in CARS if car['id'] != id]
        return {'message': 'Автомобиль удален'}, 200

# Подключение дополнительных модулей (как part.py и parttmpl.py)
from car_api.cars import api as cars_ns
from car_api.templates import templ as car_templ

api.add_namespace(cars_ns)
app.register_blueprint(car_templ, url_prefix='/car-templ')

if __name__ == "__main__":
    app.run(debug=True)