import bus_funcs
import pin_funcs

data_dir = "data"

cell_name = ''
if __name__ == '__main__':
    data_files = bus_funcs.data_load(data_dir)

    final_bus_data = bus_funcs.final_bus_data(data_files)

    data_files[0].cell[cell_name] = final_bus_data

    values = pin_funcs.final_pin_data(data_files)

    data_files[0].cell[cell_name] = values

    with open('results' + '/' + 'final_solution' + '.lib', 'w', encoding='utf-8') as final_solution:
        data_files[0].dump(final_solution, '')
