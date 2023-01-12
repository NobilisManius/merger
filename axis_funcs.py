class BasicAxis:
    index_1 = ""
    name = ""
    variable_1 = ""
    index_2 = ""
    variable_2 = ""

    def __init__(self):
        self.index_1 = "0"
        self.name = "None"
        self.variable_1 = "0"
        self.index_2 = "0"
        self.variable_2 = "0"

    def axis(self, name, index, value):
        self.name = name
        self.index_1 = index
        self.variable_1 = value

    def add_axis(self, index, value):
        self.index_2 = index
        self.variable_2 = value


# , indexes, values, names
def add_axis(data_files):
    templates = []
    basic_data_array = []
    final_data = []
    for item in data_files[0].lu_table_template.items():
        templates.append(item)

    for index, item in enumerate(templates):
        basic_data_array.append(BasicAxis())
        basic_data_array[index].axis(item[0], item[1].index_1, item[1].variable_1)

    print('Axis have been added. (In theory)')
    return 1
