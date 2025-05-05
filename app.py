from flask import Flask, render_template, request, url_for, redirect, Blueprint
from flask_restplus import Api, Resource, fields, reqparse
import statistics

app = Flask(__name__)

# Инициализация API
api = Api(app,
          doc='/api/docs',
          title='Car Market API',
          description='API для управления автомобилями с сортировкой и статистикой',
          prefix='/api')

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
# Парсеры для API
sort_parser = reqparse.RequestParser()
sort_parser.add_argument('sort_by', type=str, help='Поле для сортировки (brand, model, year, price, mileage)')
sort_parser.add_argument('order', type=str, choices=['asc', 'desc'], default='asc', help='Порядок сортировки')

# API Namespace
ns_car = api.namespace('cars', description='Операции с автомобилями')


@ns_car.route('/')
class CarList(Resource):
    @ns_car.expect(sort_parser)
    @ns_car.marshal_list_with(car_model)
    def get(self):
        """Список всех автомобилей с возможностью сортировки"""
        args = sort_parser.parse_args()
        cars = CARS.copy()

        if args['sort_by'] and args['sort_by'] in ['brand', 'model', 'year', 'price', 'mileage']:
            reverse = args['order'] == 'desc'
            cars.sort(key=lambda x: x.get(args['sort_by'], ''), reverse=reverse)

        return cars

    @ns_car.expect(car_model)
    @ns_car.marshal_with(car_model, code=201)
    def post(self):
        """Добавить новый автомобиль"""
        new_car = api.payload
        new_id = str(max(int(car['id']) for car in CARS) + 1) if CARS else '1'
        new_car['id'] = new_id
        CARS.append(new_car)
        return new_car, 201


@ns_car.route('/stats')
class CarStats(Resource):
    def get(self):
        """Статистика по всем автомобилям"""
        if not CARS:
            return {'message': 'Нет данных для анализа'}, 404

        prices = [car['price'] for car in CARS]
        years = [car['year'] for car in CARS if car.get('year') is not None]
        mileages = [car['mileage'] for car in CARS if car.get('mileage') is not None]

        return {
            'count': len(CARS),
            'price': {
                'avg': round(statistics.mean(prices), 2) if prices else None,
                'max': max(prices) if prices else None,
                'min': min(prices) if prices else None
            },
            'year': {
                'avg': round(statistics.mean(years), 1) if years else None,
                'max': max(years) if years else None,
                'min': min(years) if years else None
            },
            'mileage': {
                'avg': round(statistics.mean(mileages), 1) if mileages else None,
                'max': max(mileages) if mileages else None,
                'min': min(mileages) if mileages else None
            }
        }


@ns_car.route('/<string:id>')
@ns_car.param('id', 'ID автомобиля')
@ns_car.response(404, 'Автомобиль не найден')
class CarResource(Resource):
    @ns_car.marshal_with(car_model)
    def get(self, id):
        """Получить информацию о конкретном автомобиле"""
        car = next((car for car in CARS if car['id'] == id), None)
        if car:
            return car
        api.abort(404, "Автомобиль не найден")

    @ns_car.expect(car_model)
    @ns_car.marshal_with(car_model)
    def put(self, id):
        """Обновить информацию об автомобиле"""
        car = next((car for car in CARS if car['id'] == id), None)
        if car:
            car.update(api.payload)
            return car
        api.abort(404, "Автомобиль не найден")

    def delete(self, id):
        """Удалить автомобиль"""
        global CARS
        CARS = [car for car in CARS if car['id'] != id]
        return {'message': 'Автомобиль удален'}, 200


# Веб-интерфейс
web = Blueprint('web', __name__, template_folder='templates', static_folder='static')


@web.route('/')
def index():
    return redirect(url_for('web.list_cars'))


@web.route('/cars')
def list_cars():
    sort_by = request.args.get('sort_by')
    order = request.args.get('order', 'asc')

    cars = CARS.copy()
    if sort_by in ['brand', 'model', 'year', 'price', 'mileage']:
        reverse = order == 'desc'
        try:
            cars.sort(key=lambda x: float(x.get(sort_by, 0)), reverse=reverse)
        except (ValueError, TypeError):
            cars.sort(key=lambda x: str(x.get(sort_by, '')).lower(), reverse=reverse)

    return render_template('cars.html',
                           cars=cars,
                           sort_by=sort_by,
                           order=order)


@web.route('/cars/<id>')
def car_detail(id):
    car = next((car for car in CARS if car['id'] == id), None)
    if not car:
        return "Автомобиль не найден", 404

    # Статистика для этого автомобиля
    stats = {
        'price_comparison': {
            'avg': round(statistics.mean([c['price'] for c in CARS]), 2),
            'max': max([c['price'] for c in CARS]),
            'min': min([c['price'] for c in CARS])
        },
        'mileage_comparison': {
            'avg': round(statistics.mean([c['mileage'] for c in CARS if c.get('mileage')]), 2),
            'max': max([c['mileage'] for c in CARS if c.get('mileage')]),
            'min': min([c['mileage'] for c in CARS if c.get('mileage')])
        } if any(c.get('mileage') for c in CARS) else None,
        'age': 2025 - car['year'] if car.get('year') else None
    }

    return render_template('car_detail.html',
                           car=car,
                           stats=stats)


@web.route('/cars/add', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        new_car = {
            'brand': request.form['brand'],
            'model': request.form['model'],
            'year': int(request.form['year']) if request.form['year'] else None,
            'price': float(request.form['price']),
            'mileage': int(request.form['mileage']) if request.form['mileage'] else None
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
        return "Автомобиль не найден", 404

    if request.method == 'POST':
        car.update({
            'brand': request.form['brand'],
            'model': request.form['model'],
            'year': int(request.form['year']) if request.form['year'] else None,
            'price': float(request.form['price']),
            'mileage': int(request.form['mileage']) if request.form['mileage'] else None
        })
        return redirect(url_for('web.list_cars'))
    return render_template('edit_car.html', car=car)


@web.route('/cars/delete/<id>')
def delete_car(id):
    global CARS
    CARS = [car for car in CARS if car['id'] != id]
    return redirect(url_for('web.list_cars'))


app.register_blueprint(web, url_prefix='/web')

if __name__ == '__main__':
    app.run(debug=True)