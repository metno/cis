#!/bin/env python
from Plotting.Plotter import plot1D, heatmap
from Parser import parse_args
from Reading.DataReader import read_variable
from Exceptions.InvalidDimensionError import InvalidDimensionError

plot_types = {'line_plot' : plot1D, 
                'heatmap' : heatmap }

if __name__ ==  '__main__':
    try:
        arguments = Parser.parse_args()
    except InvalidFilenameError:
        print "Please enter a valid filename"
        exit(1)
    
    try:
        data = read_variable(arguments.filenames, arguments.variable)
    except:
        pass
        # Think about what to catch here
    
    try:
        plot_types[arguments.type](data, *arguments.formating)
    except KeyError:
        print "Invalid plot type"
        exit(1)
    
    