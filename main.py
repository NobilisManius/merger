import funcs
import copy

data_dir = "data"

key = ''
values = []

if __name__ == '__main__':

    # final_data = funcs.template_merge(data_dir)

    data_files = funcs.data_load(data_dir)

    for lib in data_files:
        for name, value in lib.cell.items():
            if len(key) == 0:
                key = name
            values.append(value)

    for item in values:
        keys_bus = []
        values_bus = []
        bus_data = {}
        for name, value in item.bus.items():
            keys_bus.append(name)                 # ???
            values_bus.append(value)

        for key in keys_bus:
            for value in values_bus:
                if value.name == key:
                    for item in value.pin.values():
                        if hasattr(item, 'timing') == True:
                            print(item.timing[0].cell_rise.items())
                            print(item.timing[0].cell_fall.items())
                            print(item.timing[0].fall_transition.items())
                            print(item.timing[0].rise_transition.items())






    print('a')


    # with open('results' + '/' + 'final_solution' + '.lib', 'w', encoding='utf-8') as final_solution:
    #     final_data.dump(final_solution, '')