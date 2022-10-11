import os, sys
import table

data_dir = "data"
data_lines = []
data_tables = []
indexes = []

if __name__ == '__main__':

    data = os.listdir(data_dir)

    f1 = open(data_dir + '/' + data[0], mode='r')
    f2 = open(data_dir + '/' + data[1], mode='r')

    temp_data_1 = []

    temp_data_2 = []

    for line in f1.readlines():
        temp_data_1.append(line)

    for line in f2.readlines():
        temp_data_2.append(line)

    for i in range(0, len(temp_data_1)):
        if temp_data_1[i] != temp_data_2[i]:
            indexes.append(i)

    temp_data_1.clear()
    temp_data_2.clear()

    i = 0
    for file in data:
        data_lines.append([])
        f = open(data_dir + '/' + file, mode='r')
        current_file_data = f.readlines()
        j = 0
        for line in current_file_data:
            if j in indexes:
                data_lines[i].append(line)
            j = j + 1
        i = i + 1
        f.close()
    i = 0

    temp = ''
    for j in range(0, len(data_lines[0])):
        for i in range(len(data_lines)):
            temp = temp + data_lines[i][j]
        data_tables.append(temp)
        temp = ''

for item in data_tables:
    print(item)
    print('---------------')