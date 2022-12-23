def data_pin_init(timing_data, key):
    cell_fall_data = []
    cell_rise_data = []
    fall_transition_data = []
    rise_transition_data = []

    for pin in timing_data[key]:
        if hasattr(pin[0], 'cell_fall'):
            for item in pin:
                cell_fall_data.append(item.cell_fall)
                cell_rise_data.append(item.cell_rise)
                fall_transition_data.append(item.fall_transition)
                rise_transition_data.append(item.rise_transition)
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
            if counter == len(value.split(sep= ',')):
                right_bracket = ')'
                line_feed = ''
            else:
                comma = ',' + '/'

            temp_value = temp_value + tab + left_bracket + quotes + value + quotes + comma + right_bracket + line_feed

            tab = ''
            left_bracket = ''
            right_bracket = ''
            comma = ''
            line_feed = '\n'

        all_data.append({name: temp_value})
    return all_data, list(data_name)


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

            cell_fall_data, cell_fall_names = table_merge(cell_fall_data)
            cell_rise_data, cell_rise_names = table_merge(cell_rise_data)
            fall_transition_data, fall_transition_names = table_merge(fall_transition_data)
            rise_transition_data, rise_transition_names = table_merge(rise_transition_data)

            for index, name in enumerate(cell_fall_names):
                if name in pins_final_data[key][index].cell_fall.keys():
                    pins_final_data[key][index].cell_fall[cell_fall_names[index]].values = cell_fall_data[index][name]
            for index, name in enumerate(cell_rise_names):
                if name in pins_final_data[key][index].cell_rise.keys():
                    pins_final_data[key][index].cell_rise[cell_rise_names[index]].values = cell_rise_data[index][name]
            for index, name in enumerate(fall_transition_names):
                if name in pins_final_data[key][index].fall_transition.keys():
                    pins_final_data[key][index].fall_transition[fall_transition_names[index]].values = fall_transition_data[index][name]
            for index, name in enumerate(rise_transition_names):
                if name in pins_final_data[key][index].rise_transition.keys():
                    pins_final_data[key][index].rise_transition[rise_transition_names[index]].values = rise_transition_data[index][name]

    for key in keys_pins:
        for obj in pins:
            if obj == values[0].pin[key].name:
                values[0].pin[key].timing[0] = pins_final_data[obj][0]

    final_data = values[0]

    return final_data
