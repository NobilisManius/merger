from logic import Liberty
import os
def data_load(data_dir):
    data_files = []
    data = os.listdir(data_dir)

    for count, file in enumerate(data):
        lib = Liberty.load(data_dir + '/' + data[count])
        data_files.append(lib)
    return data_files
