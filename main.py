import bus_funcs
import pin_funcs
import misc_funcs
import axis_funcs

data_dir = "data"

cell_name = ''


def main():
    data_files = misc_funcs.data_load(data_dir)

    final_bus_data = bus_funcs.final_bus_data(data_files)

    data_files[0].cell[cell_name] = final_bus_data

    values = pin_funcs.final_pin_data(data_files)

    data_files[0].cell[cell_name] = values

    # TODO: Redo the merge. I need to use data_files[0] as sample not as main data template. (?)

    axis_funcs.add_axis(data_files)

    with open('results' + '/' + 'final_solution' + '.lib', 'w', encoding='utf-8') as final_solution:
        data_files[0].dump(final_solution, '')

    return 1


if __name__ == '__main__':
    main()
    input()
    print("The deed is done.", flush=True)
