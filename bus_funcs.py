def data_bus_init(timing_data, key):
    cell_fall_data = []
    cell_rise_data = []
    fall_transition_data = []
    rise_transition_data = []

    for bus in timing_data[key]:
        for item in bus:
            cell_fall_data.append(item.cell_fall)
            cell_rise_data.append(item.cell_rise)
            fall_transition_data.append(item.fall_transition)
            rise_transition_data.append(item.rise_transition)
        print(f"Data for {key} have been collected.")
    return cell_fall_data, cell_rise_data, fall_transition_data, rise_transition_data


def table_merge(data):
    all_data = []
    temp_data = []
    names = []
    temp_dict = {}

    data_name = set()

    left_bracket = ''
    right_bracket = ''
    tab = ''
    quotes = '\"'
    comma = ''
    line_feed = '\n'

    for item in data:
        for name, value in item.items():
            data_name.add(name)
            all_data.append({name: value.values})

    for item in all_data:
        for name, values in item.items():
            names.append(name)

    names = list(set(names))

    for name in names:
        for item in all_data:
            if name in item.keys():
                temp_data.append(item[name])
        temp_dict[name] = temp_data
        temp_data = []

    all_data.clear()

    for name, values in temp_dict.items():
        temp_data = temp_dict[name]
        temp_value = ''

        for counter, value in enumerate(temp_data):
            if counter == 0:
                left_bracket = '('
            else:
                tab = '\t\t\t\t\t'
            if counter == len(value.split(sep=',')) - 1:
                #TODO: Cringe
                right_bracket = ')'
                line_feed = ''
                temp_value = temp_value + tab + left_bracket + quotes + value + quotes + comma + right_bracket + \
                             line_feed
                tab = ''
                left_bracket = ''
                right_bracket = ''
                comma = ''
                line_feed = '\n'
                break
            else:
                comma = ',' + '\\'

            temp_value = temp_value + tab + left_bracket + quotes + value + quotes + comma + right_bracket + line_feed

            tab = ''
            left_bracket = ''
            right_bracket = ''
            comma = ''
            line_feed = '\n'

        all_data.append({name: temp_value})
        print(f"The bus data of {name} have been merged.")
    return all_data, list(data_name)


def final_bus_data(data_files):
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
        keys_bus = []
        values_bus = []
        bus_final_data = {}

        for name, value in item.bus.items():
            keys_bus.append(name)
            values_bus.append(value)

        for key in keys_bus:
            for value in values_bus:
                if value.name == key:
                    for item in value.pin.values():
                        if hasattr(item, 'timing'):
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
        cell_fall_data, cell_rise_data, fall_transition_data, rise_transition_data = data_bus_init(timing_data, key)

        cell_fall_data, cell_fall_names = table_merge(cell_fall_data)
        cell_rise_data, cell_rise_names = table_merge(cell_rise_data)
        fall_transition_data, fall_transition_names = table_merge(fall_transition_data)
        rise_transition_data, rise_transition_names = table_merge(rise_transition_data)

        for index, name in enumerate(cell_fall_names):
            if name in bus_final_data[key][index].cell_fall.keys():
                bus_final_data[key][index].cell_fall[cell_fall_names[index]].values = cell_fall_data[index][name]

        for index, name in enumerate(cell_rise_names):
            if name in bus_final_data[key][index].cell_rise.keys():
                bus_final_data[key][index].cell_rise[cell_rise_names[index]].values = cell_rise_data[index][name]

        for index, name in enumerate(fall_transition_names):
            if name in bus_final_data[key][index].fall_transition.keys():
                bus_final_data[key][index].fall_transition[fall_transition_names[index]].values = \
                    fall_transition_data[index][name]

        for index, name in enumerate(rise_transition_names):
            if name in bus_final_data[key][index].rise_transition.keys():
                bus_final_data[key][index].rise_transition[rise_transition_names[index]].values = \
                    rise_transition_data[index][name]

    for key in keys_bus:
        for item in pins:
            if item in values[0].bus[key].pin:
                values[0].bus[key].pin[item].timing[0] = bus_final_data[item][0]

    final_data = values[0]
    print(f"All the buses have been combined.")
    return final_data
