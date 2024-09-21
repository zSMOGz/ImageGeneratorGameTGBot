import peewee

from peewee import *

connection = SqliteDatabase('routes.db')
cursor = connection.cursor()


class BaseModel(Model):
    """
    Базовый класс для всех моделей данных в БД.
    """
    class Meta:
        database = connection


class PointMap(BaseModel):
    """
    Точка на карте, к которой может переместиться игрок.

    Attributes:
        name(str): Название локации.
        description(str): Описание локации.
        ai_description(str): Описание локации для генерации изображений
        на английском языке.
    """
    name = CharField(column_name='name')
    description = TextField(column_name='description')
    ai_description = TextField(column_name='ai_description')

    class Meta:
        table_name = 'PointMaps'


class Route(BaseModel):
    """
    Список соединений между точками на карте.

    Attributes:
        point_map_id(int): Id точки на карте.
        another_point_map_id(int): Id связанной точки на карте.
    """
    point_map_id = IntegerField(column_name='point_map_id')
    another_point_map_id = ForeignKeyField(column_name='another_point_map_id',
                                           model=PointMap)


class Statistic(BaseModel):
    """
    Статистика по времени генерации изображений и времени загрузки
    нейронных сетей.

    Attributes:
        neural_network_name(str): Название нейронной сети.
        time_generated(datetime): Время генерации изображения.
        time_loaded(datetime): Время загрузки нейронной сети.
    """
    neural_network_name = CharField(column_name='neural_network_name')
    time_generated = DateTimeField(column_name='time_generated',
                                   null=True)
    time_loaded = DateTimeField(column_name='time_loaded',
                                null=True)


connection.create_tables([PointMap, Route, Statistic], )


def get_available_routes(point_map_id):
    """
    Возвращает список доступных точек на карте из указанной точки.

    Parameters:
        point_map_id(int): Точка на карте, из которой нужно искать
        доступные маршруты.

    Returns:
        list[PointMap]: Список доступных маршрутов из указанной точки.
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
                                     | (Route.another_point_map_id ==
                                        point_map_id))).
                            objects())
        return available_routes
    except DoesNotExist as de:
        print(de)


def get_point_map(point_map_id: int):
    """
    Возвращает точку на карте по ее id.

    Returns:
        point_map_id(int): Id точки на карте.

    Returns:
        PointMap: Точка на карте.
    """
    try:
        point_map = PointMap.get(PointMap.id == point_map_id)

        return point_map
    except DoesNotExist as de:
        print(de)


def get_statistic():
    """
    Возвращает статистику по времени генерации изображений и времени
    загрузки нейронных сетей.

    Returns:
        Any: Статистика по времени генерации изображений и времени
        загрузки нейронных сетей.
    """
    try:
        statistic = (Statistic.select(Statistic.neural_network_name,
                                      peewee.fn.AVG(Statistic.time_generated)
                                      .alias('time_generated'),
                                      peewee.fn.AVG(Statistic.time_loaded)
                                      .alias('time_loaded'))
                     .group_by(Statistic.neural_network_name)
                     .order_by(Statistic.neural_network_name)
                     .objects())

        return statistic
    except DoesNotExist as de:
        print(de)


def get_statistic_detailed():
    """
    Возвращает детальную статистику по времени генерации изображений и
    времени загрузки нейронных сетей.
    Время генерации каждого изображения, и время загрузки каждой
    нейронной сети.

    Returns:
        Any: Детальная статистика по времени генерации изображений и
        времени загрузки нейронных сетей.
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
    Добавляет статистику по времени генерации изображений.

    Parameters:
        neural_network_name(str): Название нейронной сети.
        time_generated(float): Время генерации изображения.
    """
    try:
        Statistic.create(neural_network_name=neural_network_name,
                         time_generated=time_generated)
    except IntegrityError as ie:
        print(ie)


def add_statistic_loaded(neural_network_name: str,
                         time_loaded: float):
    """
    Добавляет статистику по времени загрузки нейронной сети.

    Parameters:
        neural_network_name(str): Название нейронной сети.
        time_loaded(float): Время загрузки нейронной сети.
    """
    try:
        Statistic.create(neural_network_name=neural_network_name,
                         time_loaded=time_loaded)
    except IntegrityError as ie:
        print(ie)
