import sys
import pandas as pd
import csv
from tabulate import tabulate


__author__ = 'rlou@br.ibm.com'

### Read File CSV ###
def read_csv(csv_file):
    readers = pd.read_csv(csv_file)
    return readers

### Creating a new Filtered CSV File ###
def create_csv_file(filtered):
    df = pd.DataFrame(filtered)
    df.to_csv('CSV_Challenge.csv' , index=False)

### FILTER ###
def filter_csv(reader):
    for row in reader:
        if (row[9].isnull()):
            row[9] = "0.0"

        if row[7] == 'Nunavut' and float(row[9]) <= 0.7:           
            df.to_csv('CSV_Challenge.csv', mode='a')
    
    filtered = read_csv('CSV_Challenge.csv')
    return filtered 

### MAIN ###
def main():
        reader = read_csv('SampleCSVFile_556kb.csv')
        print(tabulate(reader, headers = 'keys', tablefmt = 'psql', showindex = False))

        filtered = filter_csv(reader)
        df = pd.DataFrame(filtered)

if __name__ == '__main__':
    main()