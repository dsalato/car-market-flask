from flask import Flask, render_template, request, url_for, redirect, Blueprint
from flask_restplus import Api, Resource, fields

app = Flask(__name__)


api = Api(app,
          title='Car Market API',
          description='API для рынка автомобилей',
          doc='/api/docs',
          prefix='/api',
          endpoint='api')
# Модель данных
car_model = api.model('Car', {
    'id': fields.String(required=True, description='ID автомобиля'),
    'brand': fields.String(required=True, description='Марка (Toyota, BMW)'),
    'model': fields.String(required=True, description='Модель (Camry, X5)'),
    'year': fields.Integer(description='Год выпуска'),
    'price': fields.Float(required=True, description='Цена ($)'),
    'mileage': fields.Integer(description='Пробег (км)'),
})

# Начальные данные
CARS = [
    {'id': '1', 'brand': 'Toyota', 'model': 'Camry', 'year': 2020, 'price': 25000, 'mileage': 15000},
    {'id': '2', 'brand': 'BMW', 'model': 'X5', 'year': 2019, 'price': 45000, 'mileage': 30000},
]

# Создание Blueprint для веб-интерфейса
web = Blueprint('web', __name__, template_folder='templates')

@web.route('/')
def index():
    return redirect(url_for('web.list_cars'))

@web.route('/cars')
def list_cars():
    return render_template('cars.html', cars=CARS)

@web.route('/cars/add', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        new_car = {
            'brand': request.form['brand'],
            'model': request.form['model'],
            'year': int(request.form.get('year', 0)),
            'price': float(request.form['price']),
            'mileage': int(request.form.get('mileage', 0))
        }
        new_id = str(max(int(car['id']) for car in CARS) + 1) if CARS else '1'
        new_car['id'] = new_id
        CARS.append(new_car)
        return redirect(url_for('web.list_cars'))
    return render_template('edit_car.html', car=None)

@web.route('/cars/edit/<id>', methods=['GET', 'POST'])
def edit_car(id):
    car = next((car for car in CARS if car['id'] == id), None)
    if not car:
        return "Car not found", 404

    if request.method == 'POST':
        car.update({
            'brand': request.form['brand'],
            'model': request.form['model'],
            'year': int(request.form.get('year', 0)),
            'price': float(request.form['price']),
            'mileage': int(request.form.get('mileage', 0))
        })
        return redirect(url_for('web.list_cars'))
    return render_template('edit_car.html', car=car)

@web.route('/cars/delete/<id>')
def delete_car(id):
    global CARS
    CARS = [car for car in CARS if car['id'] != id]
    return redirect(url_for('web.list_cars'))

# Регистрация Blueprint для веб-интерфейса
app.register_blueprint(web, url_prefix='/web')

# API Namespace
ns_car = api.namespace('cars', description='Операции с автомобилями')

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
        if CARS:
            max_id = max(int(car['id']) for car in CARS)
            new_id = str(max_id + 1)
        else:
            new_id = '1'
        new_car['id'] = new_id
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


from car_api.cars import api as cars_ns
from car_api.templates import templ as car_templ
api.add_namespace(cars_ns)
app.register_blueprint(car_templ, url_prefix='/car-templ')

if __name__ == '__main__':
    app.run(debug=True)