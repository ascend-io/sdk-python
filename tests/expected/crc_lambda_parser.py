# import package needed
# Please add them to install list below,
# if they are not pre-built
import csv
import datetime
import time

# main function
def parser_function(reader, onNext):
    # Use reader to read in data, and pass a python map to onNext function as parsing result.
    csv_reader = csv.reader((b.decode('utf-8') for b in reader))
    header = next(csv_reader)
    times = [time.strptime(d, '%m/%d/%y') for d in header[4:]]
    dates = [datetime.date(year=t.tm_year, month=t.tm_mon, day=t.tm_mday).isoformat() for t in times]
    for line in csv_reader:
        country = line[1]
        state = line[0]
        for i, count in enumerate(line[4:]):
            try:
                onNext({'Country_Region': country, 'Province_State': state, 'Date': dates[i], 'Deaths': count})
            except:
                raise Exception(f'error for {i}: {line}')
