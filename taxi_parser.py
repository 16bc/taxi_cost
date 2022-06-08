import requests
from json import loads
import pymysql
from datetime import datetime
from config import db_params, clid, apikey, point1, point2


def get_price(latlon1, latlon2):

    response = requests.get(f'https://taxi-routeinfo.taxi.yandex.net/taxi_info?clid={clid}&apikey={apikey}&rll={latlon1}~{latlon2}&class=econom')
    data = loads(response.text)
    result = {
        'price': data['options'][0]['price'],
        'wait': data['options'][0]['waiting_time'],
        'duration': data['time'],
    }
    return result


if __name__ == '__main__':
        data_to = get_price(point1, point2)
        data_from = get_price(point2, point1)
        res_item = {
            "ts": datetime.now(),
            "to_price": data_to.get('price'),
            "from_price": data_from.get('price'),
            "to_wait": data_to.get('wait'),
            "from_wait": data_from.get('wait'),
            "to_duration": data_to.get('duration'),
            "from_duration": data_from.get('duration'),
        }
        keys = [*res_item.keys()]
        vals = [*res_item.values()]

        with pymysql.connect(**db_params, cursorclass=pymysql.cursors.DictCursor) as connection:
            with connection.cursor() as cursor:
                # Create a new record
                sql = "INSERT INTO `taxi_stats` ({})".format(', '.join(f'{k}' for k in res_item)) + \
                    "VALUES ({})".format(', '.join('%s' for k in res_item))
                print(sql)
                cursor.execute(sql, (*res_item.values(),))
            connection.commit()
