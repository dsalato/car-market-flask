from flask_restplus import Namespace, Resource, fields

api = Namespace('extra', description='Дополнительные операции с автомобилями')

# Модель для статистики
stats_model = api.model('Stats', {
    'avg_price': fields.Float(description='Средняя цена'),
    'max_mileage': fields.Integer(description='Максимальный пробег'),
})

@api.route('/stats')
class CarStats(Resource):
    @api.marshal_with(stats_model)
    def get(self):
        """Статистика по автомобилям"""
        prices = [car['price'] for car in CARS]
        mileages = [car['mileage'] for car in CARS if car.get('mileage')]
        return {
            'avg_price': sum(prices) / len(prices) if prices else 0,
            'max_mileage': max(mileages) if mileages else 0,
        }