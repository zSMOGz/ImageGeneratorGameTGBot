import peewee
from peewee import *

connection = SqliteDatabase('routes.db')
cursor = connection.cursor()


class BaseModel(Model):
    class Meta:
        database = connection


class PointMap(BaseModel):
    id = AutoField(column_name='id')
    name = CharField(column_name='name')
    description = TextField(column_name='description')
    ai_description = TextField(column_name='ai_description')

    class Meta:
        table_name = 'PointMaps'


class Route(BaseModel):
    point_map_id = IntegerField(column_name='point_map_id')
    another_point_map_id = ForeignKeyField(column_name='another_point_map_id',
                                           model=PointMap)


class Statistic(BaseModel):
    id = IntegerField(column_name='id')
    neural_network_name = CharField(column_name='neural_network_name')
    time_generated = DateTimeField(column_name='time_generated',
                                   null=True)
    time_loaded = DateTimeField(column_name='time_loaded',
                                null=True)


connection.create_tables([PointMap, Route, Statistic], )


def get_available_routes(point_map_id):
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
    try:
        point_map = PointMap.get(PointMap.id == point_map_id)

        return point_map
    except DoesNotExist as de:
        print(de)


def get_statistic():
    try:
        statistic = (Statistic.select(Statistic.neural_network_name,
                                     peewee.fn.AVG(Statistic.time_generated),
                                     peewee.fn.AVG(Statistic.time_loaded))
                              .group_by(Statistic.neural_network_name)
                              .order_by(Statistic.neural_network_name)
                              .objects())

        return statistic
    except DoesNotExist as de:
        print(de)


def add_statistic_generated(neural_network_name, time_generated):
    try:
        Statistic.create(neural_network_name=neural_network_name,
                         time_generated=time_generated)
    except IntegrityError as ie:
        print(ie)


def add_statistic_loaded(neural_network_name, time_loaded):
    try:
        Statistic.create(neural_network_name=neural_network_name,
                         time_loaded=time_loaded)
    except IntegrityError as ie:
        print(ie)
