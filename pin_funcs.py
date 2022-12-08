def data_pin_init(timing_data, key):
    cell_fall_data = []
    cell_rise_data = []
    fall_transition_data = []
    rise_transition_data = []


    if hasattr(timing_data[key][0][0], 'cell_fall'):
        for item in timing_data[key]:
            cell_fall_data.append(item[0].cell_fall)
            cell_rise_data.append(item[0].cell_rise)
            fall_transition_data.append(item[0].fall_transition)
            rise_transition_data.append(item[0].rise_transition)
    return cell_fall_data, cell_rise_data, fall_transition_data, rise_transition_data


def table_merge(data):
    temp_data = []
    temp_value = ''
    for item in data:
        for name, value in item.items():
            data_name = name
            temp_data.append(value.values)

    for value in temp_data:
        temp_value = temp_value + value + '\n'

    # TODO: There gonna be a condition for choose a tab.
    # smth like if (cycle > 0) -> tab_string = '\t'
    #           else -> tab_string = ''
    return temp_value, data_name


def final_pin_data(data_files):
    timing_pin_names = []
    timing_data = {}
    pins = []
    values = []
    cell_name = ''


    for lib in data_files:
        for name, value in lib.cell.items():
            if len(cell_name) == 0:
                cell_name = name
            values.append(value)

    for item in values:
        keys_pins = []
        values_pins = []
        pins_final_data = {}

        for name, value in item.pin.items():
            keys_pins.append(name)
            values_pins.append(value)

        for key in keys_pins:
            for value in values_pins:
                if value.name == key:
                    if hasattr(value, 'timing'):
                        timing_pin_names.append(value.name)
                timing_pin_names = list(set(timing_pin_names))

        for pin in values_pins:
            if pin.name in timing_pin_names:
                if pin.name not in timing_data.keys():
                    pins.append(pin.name)
                    timing_data[pin.name] = []
                if pin.name in timing_data.keys():
                    timing_data[pin.name].append(pin.timing)

        for key in pins:
            pins_final_data[key] = timing_data[key][0]

    for key in pins:
        if hasattr(timing_data[key][0][0], 'cell_fall'):
            cell_fall_data, cell_rise_data, fall_transition_data, rise_transition_data = data_pin_init(timing_data, key)

            cell_fall_data, cell_fall_name = table_merge(cell_fall_data)
            cell_rise_data, cell_rise_name = table_merge(cell_rise_data)
            fall_transition_data, fall_transition_name = table_merge(fall_transition_data)
            rise_transition_data, rise_transition_name = table_merge(rise_transition_data)

            pins_final_data[key][0].cell_fall[cell_fall_name].values = cell_fall_data
            pins_final_data[key][0].cell_rise[cell_rise_name].values = cell_rise_data
            pins_final_data[key][0].fall_transition[fall_transition_name].values = fall_transition_data
            pins_final_data[key][0].rise_transition[rise_transition_name].values = rise_transition_data

    for key in keys_pins:
        for obj in pins:
            if obj == values[0].pin[key].name:
                values[0].pin[key].timing[0] = pins_final_data[obj][0]

    final_data = values[0]

    return final_data
