import os, sys
import table
from logic import Liberty

data_dir = "data"
data_files = []
values = []
tables = []
keys = []
final_data = {}

if __name__ == '__main__':

    data = os.listdir(data_dir)

    for count, file in enumerate(data):
        lib = Liberty.load(data_dir + '/' + data[count])
        data_files.append(lib)

    for lib in data_files:
        for name, value in lib.lu_table_template.items():
            keys.append(name)                   # It supposed to work in a different way but,,,
            values.append(value)

    for key in keys:
        data_table = ''
        for value in values:
            if value.name == key:
                data_table = data_table + value.index_1 + '\n'
        final_data[key] = data_table



    final_lib = data_files[0]
    final_lib.lu_table_template.clear()
    for key, table in final_data.items():
        final_lib.lu_table_template[key] = table

    # with open('results' + '/' + 'final_solution' + '.lib', 'w', encoding='utf-8') as final_solution:
    #     final_lib.dump(final_solution, '')