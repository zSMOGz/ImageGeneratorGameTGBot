import peewee
import datetime as dt

from peewee import *


connection = SqliteDatabase('routes.db')
cursor = connection.cursor()


class BaseModel(Model):
    class Meta:
        database = connection


class PointMap(BaseModel):
    """
    Точка на карте, к которой может переместиться игрок
    """
    name = CharField(column_name='name')
    description = TextField(column_name='description')
    ai_description = TextField(column_name='ai_description')

    class Meta:
        table_name = 'PointMaps'


class Route(BaseModel):
    """
    Список соединений между точками на карте
    """
    point_map_id = IntegerField(column_name='point_map_id')
    another_point_map_id = ForeignKeyField(column_name='another_point_map_id',
                                           model=PointMap)


class Statistic(BaseModel):
    """
    Статистика по времени генерации изображений и времени загрузки нейронных сетей
    """
    neural_network_name = CharField(column_name='neural_network_name')
    time_generated = DateTimeField(column_name='time_generated',
                                   null=True)
    time_loaded = DateTimeField(column_name='time_loaded',
                                null=True)


connection.create_tables([PointMap, Route, Statistic], )


def get_available_routes(point_map_id):
    """
    Возвращает список доступных точек на карте из указанной точки
    :param point_map_id: Точка на карте, из которой нужно искать доступные маршруты
    :return: Список доступных маршрутов из указанной точки
    """
    try:
        join_condition = ((Route.point_map_id == PointMap.id)
                          | (Route.another_point_map_id == PointMap.id))

        available_routes = (Route.select(PointMap.id,
                                         PointMap.name,
                                         PointMap.description).
                            join(PointMap, on=join_condition).
                            where((PointMap.id != point_map_id)
                                  & ((Route.point_map_id == point_map_id)
                                     | (Route.another_point_map_id == point_map_id))).
                            objects())
        return available_routes
    except DoesNotExist as de:
        print(de)


def get_point_map(point_map_id):
    """
    Возвращает точку на карте по ее id
    :param point_map_id: id точки на карте
    :return: Точка на карте
    """
    try:
        point_map = PointMap.get(PointMap.id == point_map_id)

        return point_map
    except DoesNotExist as de:
        print(de)


def get_statistic():
    """
    Возвращает статистику по времени генерации изображений и времени загрузки нейронных сетей
    :return: Статистика по времени генерации изображений и времени загрузки нейронных сетей
    """
    try:
        statistic = (Statistic.select(Statistic.neural_network_name,
                                      peewee.fn.AVG(Statistic.time_generated).alias('time_generated'),
                                      peewee.fn.AVG(Statistic.time_loaded).alias('time_loaded'))
                              .group_by(Statistic.neural_network_name)
                              .order_by(Statistic.neural_network_name)
                              .objects())

        return statistic
    except DoesNotExist as de:
        print(de)


def get_statistic_detailed():
    """
    Возвращает детальную статистику по времени генерации изображений и времени загрузки нейронных сетей.
    Время генерации каждого изображения, и время загрузки каждой нейронной сети
    :return: Детальная статистика по времени генерации изображений и времени загрузки нейронных сетей
    """
    try:
        statistic = (Statistic.select(Statistic.neural_network_name,
                                      Statistic.time_generated,
                                      Statistic.time_loaded)
                     .order_by(Statistic.neural_network_name)
                     .objects())

        return statistic
    except DoesNotExist as de:
        print(de)


def add_statistic_generated(neural_network_name: str,
                            time_generated: float):
    """
    Добавляет статистику по времени генерации изображений
    :param neural_network_name: Название нейронной сети
    :param time_generated: Время генерации изображения
    """
    try:
        Statistic.create(neural_network_name=neural_network_name,
                         time_generated=time_generated)
    except IntegrityError as ie:
        print(ie)


def add_statistic_loaded(neural_network_name: str,
                         time_loaded: float):
    """
    Добавляет статистику по времени загрузки нейронной сети
    :param neural_network_name: Название нейронной сети
    :param time_loaded: Время загрузки нейронной сети
    """
    try:
        Statistic.create(neural_network_name=neural_network_name,
                         time_loaded=time_loaded)
    except IntegrityError as ie:
        print(ie)
