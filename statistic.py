import matplotlib.pyplot as plt

STATS_PATH = "images/stats/"
GRAPH_NAME = "graph.png"
AVG_TIME_GENERATED_NAME = "Среднее время генерации изображения: "
AVG_TIME_LOADED_NAME = "Среднее время загрузки модели: "
TIME_GENERATED_NAME = "Время генерации изображения"
TIME_LOADED_NAME = "Время загрузки нейросети"
INDEX_NAME = "Номер измерения"


async def get_lists_by_neural_networks(statistics_detailed_data):
    lists_by_neural_networks = []
    current_neural_network_list = []
    last_neural_network_name = None
    last_neural_network = None

    for stat in statistics_detailed_data:
        if (last_neural_network_name != stat.neural_network_name
                or last_neural_network_name is None):
            current_neural_network_list = []
            lists_by_neural_networks.append(current_neural_network_list)
            last_neural_network_name = stat.neural_network_name

        last_neural_network = (stat.neural_network_name,
                               stat.time_loaded,
                               stat.time_generated)

        current_neural_network_list.append(last_neural_network)

    return lists_by_neural_networks


async def get_time_generated_list_and_indexes(lists_by_neural_networks):
    lists_time_generated = []
    lists_time_generated_indexes = []
    lists_time_loaded = []
    lists_time_loaded_indexes = []
    for split_lists_by_neural_networks in lists_by_neural_networks:
        list_time_generated = []
        list_time_generated_indexes = []
        current_time_generated_index = 0

        list_time_loaded = []
        list_time_loaded_indexes = []
        current_time_loaded_index = 0

        for stat in split_lists_by_neural_networks:
            name, time_loaded, time_generated = stat
            if time_generated is not None:
                list_time_generated.append(time_generated)
                current_time_generated_index += 1
                list_time_generated_indexes.append(current_time_generated_index)

            if time_loaded is not None:
                list_time_loaded.append(time_loaded)
                current_time_loaded_index += 1
                list_time_loaded_indexes.append(current_time_loaded_index)

        lists_time_generated.append(list_time_generated)
        lists_time_generated_indexes.append(list_time_generated_indexes)
        lists_time_loaded.append(list_time_loaded)
        lists_time_loaded_indexes.append(list_time_loaded_indexes)

    return (lists_time_generated,
            lists_time_generated_indexes,
            lists_time_loaded,
            lists_time_loaded_indexes)


async def get_create_graph(list_indexes,
                           lists_values,
                           title,
                           xlabel,
                           ylabel,
                           xticks,
                           yticks):
    plt.plot(list_indexes,
             lists_values)
    plt.title(TIME_GENERATED_NAME)
    plt.xlabel(INDEX_NAME)
    plt.ylabel(TIME_GENERATED_NAME)
    plt.xticks(list_indexes)
    plt.yticks(lists_values)
    plt.savefig(STATS_PATH + GRAPH_NAME)
    plt.clf()

    return STATS_PATH + GRAPH_NAME
