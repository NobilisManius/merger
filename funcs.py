from logic import Liberty
import copy
import os



def data_load(data_dir):
    data_files = []
    data = os.listdir(data_dir)

    for count, file in enumerate(data):
        lib = Liberty.load(data_dir + '/' + data[count])
        data_files.append(lib)
    return data_files


def template_merge(data_dir):
    data_files = data_load(data_dir)

    keys = []
    values = []
    tables = []
    final_data = {}

    for lib in data_files:
        for name, value in lib.lu_table_template.items():
            keys.append(name)
            values.append(value)

    for key in keys:
        data_table = ''
        for value in values:
            if value.name == key:
                data_table = data_table + value.index_1 + '\n' + '      '
        final_data[key] = data_table[0:len(data_table) - 1]

    final_lib = data_files[0]
    for key, table in final_data.items():
        final_lib.lu_table_template[key].index_1 = copy.deepcopy(table)

    return final_lib


def cell_merge(data_dir):
    data_files = data_load(data_dir)

    for lib in data_files:
        for name, value in lib.lu_table_template.items():
            keys = []
            values = []
            keys.append(name)
            values.append(value)