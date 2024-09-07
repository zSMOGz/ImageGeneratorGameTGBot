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


connection.create_tables([PointMap, Route], )


def get_available_routes(point_map_id):
    try:
        available_routes = (Route.select(PointMap.id, PointMap.name, PointMap.description).join(PointMap).
                            where(PointMap.id == point_map_id
                                  and Route.point_map_id == point_map_id).
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
