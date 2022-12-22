from logic import Liberty
import os


def data_load(data_dir):
    data_files = []
    data = os.listdir(data_dir)

    for count, file in enumerate(data):
        lib = Liberty.load(data_dir + '/' + data[count])
        data_files.append(lib)
    return data_files


def table_merge(data):
    temp_data = []
    temp_value = ''

    left_bracket = ''
    right_bracket = ''
    tab = ''
    quotes = '\"'
    comma = ''
    line_feed = '\n'

    for item in data:
        for name, value in item.items():
            data_name = name
            temp_data.append(value.values)

    for counter, value in enumerate(temp_data):
        if counter == 0:
            left_bracket = '('
        else:
            tab = '\t\t\t\t\t'
        if counter == len(value.split(',')) - 1:
            right_bracket = ')'
            line_feed = ''
        else:
            comma = ','

        temp_value = temp_value + tab + left_bracket + quotes + value + quotes + comma + right_bracket + line_feed

        tab = ''
        left_bracket = ''
        right_bracket = ''
        comma = ''
        line_feed = '\n'
    return temp_value, data_name


def data_bus_init(timing_data, key):
    cell_fall_data = []
    cell_rise_data = []
    fall_transition_data = []
    rise_transition_data = []

    for item in timing_data[key]:
        cell_fall_data.append(item[0].cell_fall)
        cell_rise_data.append(item[0].cell_rise)
        fall_transition_data.append(item[0].fall_transition)
        rise_transition_data.append(item[0].rise_transition)
    return cell_fall_data, cell_rise_data, fall_transition_data, rise_transition_data

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

        cell_fall_data, cell_fall_name = table_merge(cell_fall_data)
        cell_rise_data, cell_rise_name = table_merge(cell_rise_data)
        fall_transition_data, fall_transition_name = table_merge(fall_transition_data)
        rise_transition_data, rise_transition_name = table_merge(rise_transition_data)

        bus_final_data[key][0].cell_fall[cell_fall_name].values = cell_fall_data
        bus_final_data[key][0].cell_rise[cell_rise_name].values = cell_rise_data
        bus_final_data[key][0].fall_transition[fall_transition_name].values = fall_transition_data
        bus_final_data[key][0].rise_transition[rise_transition_name].values = rise_transition_data

    for key in keys_bus:
        for item in pins:
            if item in values[0].bus[key].pin:
                values[0].bus[key].pin[item].timing[0] = bus_final_data[item][0]

    final_data = values[0]

    return final_data
