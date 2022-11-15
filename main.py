import funcs
import copy

data_dir = "data"

key = ''
values = []
timing_pin_names = []

timing_data = {}

pins = []
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
            keys_bus.append(name)
            values_bus.append(value)

        for key in keys_bus:
            for value in values_bus:
                if value.name == key:
                    for item in value.pin.values():
                        if hasattr(item, 'timing') == True:
                            timing_pin_names.append(item.name)
                timing_pin_names = list(set(timing_pin_names))

        for key in keys_bus:
            for value in values_bus:
                for pin_instance in value.pin:
                    if pin_instance in timing_pin_names:
                        if pin_instance not in timing_data:
                            pins.append(pin_instance)
                            timing_data[pin_instance] = []

                        if pin_instance in timing_data:
                            timing_data[pin_instance].append(value.pin[pin_instance].timing)

        for pin in timing_data:
            cell_fall_data = []
            cell_rise_data = []
            fall_transition_data = []
            rise_transition_data = []
            temp_keys = []
            for item in timing_data[pin]:
                for instance in item:
                    cell_fall_data.append(instance.cell_fall)
                    cell_rise_data.append(instance.cell_rise)
                    fall_transition_data.append(instance.fall_transition)
                    rise_transition_data.append(instance.rise_transition)

            # TODO: Cringe. I'll change it later.
            #       Redo it as func.
            for template in cell_fall_data:
                temp_keys.append(list(template.keys()))

            temp = []
            for item in temp_keys:
                temp.append(item[0])

            temp_keys = list(set(temp))
            temp = []
            # Cringe.

            # TODO:     Пересобирать temp, этот вариант неправильный
            for key in temp_keys:
                for item in cell_fall_data:
                    if key in item:
                        temp.append(item[key].values)

            # TODO:     В общем
            #           всё это создано для распихивания всех вещей по спискам для дальнейшего объединения
            #           Сейчас все данные лежат в temp, надо их объединять в одно и передавать куда то дальше
            #           Скорее всего в какой-то дикт и потом по ссылке на него получать обратно всё
            #           Dict должен так выглядеть
            #           pin_instance -> template_name -> final_values
            #           Он будет вложен, да


            print('sas')

    print('sas')

    # with open('results' + '/' + 'final_solution' + '.lib', 'w', encoding='utf-8') as final_solution:
    #     final_data.dump(final_solution, '')
