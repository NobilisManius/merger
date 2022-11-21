import funcs
import copy

data_dir = "data"

cell_name = ''
values = []
timing_pin_names = []

timing_data = {}

pins = []
if __name__ == '__main__':

    # final_data = funcs.template_merge(data_dir)

    data_files = funcs.data_load(data_dir)

    for lib in data_files:
        for name, value in lib.cell.items():
            if len(cell_name) == 0:
                cell_name = name
            values.append(value)

    for item in values:
        keys_bus = []
        values_bus = []
        bus_data = {}
        bus_final_data = {}

        for name, value in item.bus.items():
            keys_bus.append(name)
            values_bus.append(value)

        for key in keys_bus:
            for value in values_bus:
                if value.name == key:
                    for item in value.pin.values():
                        if hasattr(item, 'timing') == True:
                            timing_pin_names.append(item.name)
                timing_pin_names = list(set(timing_pin_names))


        for value in values_bus:
            for pin_instance in value.pin:
                if pin_instance in timing_pin_names:
                    if pin_instance not in timing_data:
                        pins.append(pin_instance)
                        timing_data[pin_instance] = []
                    if pin_instance in timing_data:
                        timing_data[pin_instance].append(value.pin[pin_instance].timing)


        for key in pins:
            bus_final_data[key] = timing_data[key][0]


    for key in pins:
        cell_fall_data = []
        cell_rise_data = []
        fall_transition_data = []
        rise_transition_data = []

        temp_cell_fall_data = []
        temp_cell_rise_data = []
        temp_fall_transition_data = []
        temp_rise_transition_data = []

        cell_fall_name = ''
        cell_rise_name = ''
        fall_transition_name = ''
        rise_transition_name = ''

        temp_value = ''

        for item in timing_data[key]:
            cell_fall_data.append(item[0].cell_fall)
            cell_rise_data.append(item[0].cell_rise)
            fall_transition_data.append(item[0].fall_transition)
            rise_transition_data.append(item[0].rise_transition)

        # TODO: Redo everything as func

        for item in cell_fall_data:
            for name, value in item.items():
                cell_fall_name = name
                temp_cell_fall_data.append(value.values)

        for item in cell_rise_data:
            for name, value in item.items():
                cell_rise_name = name
                temp_cell_rise_data.append(value.values)

        for item in fall_transition_data:
            for name, value in item.items():
                fall_transition_name = name
                temp_fall_transition_data.append(value.values)

        for item in rise_transition_data:
            for name, value in item.items():
                rise_transition_name = name
                temp_rise_transition_data.append(value.values)

        for value in temp_cell_fall_data:
            temp_value = temp_value + value + '\n'
        cell_fall_data.clear()
        cell_fall_data = temp_value
        temp_value = ''

        for value in temp_cell_rise_data:
            temp_value = temp_value + value + '\n'
        cell_rise_data.clear()
        cell_rise_data = temp_value
        temp_value = ''

        for value in temp_fall_transition_data:
            temp_value = temp_value + value + '\n'
        fall_transition_data.clear()
        fall_transition_data = temp_value
        temp_value = ''

        for value in temp_rise_transition_data:
            temp_value = temp_value + value + '\n'
        rise_transition_data.clear()
        rise_transition_data = temp_value
        temp_value = ''



        bus_final_data[key][0].cell_fall[cell_fall_name].values = cell_fall_data
        bus_final_data[key][0].cell_rise[cell_rise_name].values = cell_rise_data
        bus_final_data[key][0].fall_transition[fall_transition_name].values = fall_transition_data
        bus_final_data[key][0].rise_transition[rise_transition_name].values = rise_transition_data

    for key in keys_bus:
        for item in pins:
            if item in values[0].bus[key].pin:
                values[0].bus[key].pin[item].timing[0] = bus_final_data[item][0]

    final_bus_data = values[0]

    data_files[0].cell[cell_name] = final_bus_data

    with open('results' + '/' + 'final_solution' + '.lib', 'w', encoding='utf-8') as final_solution:
        data_files[0].dump(final_solution, '')
