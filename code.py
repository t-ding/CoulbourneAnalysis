'''
Version 1.2
Runs through Coulborne data and extracts information:
- Timestamps of drinking + licking
- Custom defined bouts of drinking + licking (bout = uninterrupted time of drinking/eating)
	interruption = custom defined length of time
- Outputs figures of feeding + drinking for each experiment
- Outputs excels of feeding + drinking for each experiment
- Outputs summarized data over genotype, treatment, other treatment, drug

TO RUN THE CODE:
1. Organized the files into appropriate directories
	- Organize by experiment (OtherTreatment_Drug) format
	- E.g. fd_cno and wd_cno and wd_sal
2. Add relevant mouse information to a excel spreadsheet and name this config_file.csv
	- See example config_file.csv
	- Must match characters to folder names and index list in code below
3. Edit global variables below as appropriate
4. Execute the file code.py using any version of Python3
	- E.g. in the command line: "py code.py"
5. You will be prompted to select the directory that contains the data
	- This must contain the fd_cno, etc folders from step 1
	- This must contain the config_file.csv from step 2

*Note1 all text is character sensitive*

OUTPUTS:
1. In each experiment folder (fd_cno), each experiment titled FILE will generate a file called a_FILE
	- This is the excel sheet of the timestamps in 3 different formats
2. In each experiment folder (fd_cno), each experiment titled FILE will generate a file called f_FILE
	- This is the pdf figure of the plotted timestamps
3. A file called analysis_report.csv
	- This contains all the summarized information from all the experiments
	- This will be automatically generated in the same directory as the config_file.csv

WIP:
- WD not clearing figure

Tom Ding 2021
tom.ding@ucsf.edu
'''
import numpy as np
from numpy import mean
import csv
import os
import matplotlib.pyplot as plt
import tkinter as tk

bout_break_feed = 30 #30 seconds between feeding = new bout
bout_break_lico = 30
resolution = 10 #seconds per bin
index_list = ["cck", "grp"], ["hm3"], ["wd", "fd"], ["cno", "sal"] #please fill this out. Must be consistent with config_file.csv
#Format is genotype, treatment, deprivation/other treatment, drug, this order is also important.
start = 1800 #start time in seconds of analysis
stop = 5400 #end time in seconds of analysis
bout_start = 1800 #start time in seconds of analysis for bouts
bout_stop = 5400 #end time in seconds of analysis for bouts
feed_min_bout = 5 #min number of pellets to be considered a bout
lico_min_bout = 10 #min number of licks to be considered a bout

class Experiment:
	def __init__(self, genotype, treatment, deprivation, drug):
		self.genotype = genotype
		self.treatment = treatment
		self.deprivation = deprivation
		self.drug = drug
		self.feed = [] #list of all timecodes
		self.lico = [] #list of all timecodes
		self.feed_bouts = [] #list of length of each bout
		self.lico_bouts = [] #list of length of each bout
		self.ID = str(self.genotype) + str(self.treatment) + str(self.deprivation) + str(self.drug)
		self.mouseID = ""

	def find_feed_bouts(self, brk, bout_start, bout_stop):
		if len(self.feed_bouts) == 0:
			current = -99999
			for time_pt in self.feed:
				f_time_pt = float(time_pt)
				if f_time_pt >= bout_start and f_time_pt <= bout_stop:
					if f_time_pt - current < brk:
						self.feed_bouts[-1] = self.feed_bouts[-1] + 1
						current = f_time_pt
					else:
						self.feed_bouts += [1]
						current = f_time_pt
		else:
			print ("Feed bouts already analyzed")

	def find_lico_bouts(self, brk, bout_start, bout_stop):
		if len(self.lico_bouts) == 0:
			current = -99999
			for time_pt in self.lico:
				f_time_pt = float(time_pt)
				if f_time_pt >= bout_start and f_time_pt <= bout_stop:
					if f_time_pt - current < brk:
						self.lico_bouts[-1] = self.lico_bouts[-1] + 1
						current = f_time_pt
					else:
						self.lico_bouts += [1]
						current = f_time_pt
		else:
			print ("Lick bouts already analyzed")

	def trim_bouts_by_min(self, feed_min_size, lico_min_size):
		i = 0
		while i < len(self.feed_bouts):
			if self.feed_bouts[i] < feed_min_size:
				self.feed_bouts.pop(i)
			else:
				i+=1
		i = 0
		while i < len(self.lico_bouts):
			if self.lico_bouts[i] < lico_min_size:
				self.lico_bouts.pop(i)
			else:
				i+=1

class Data_sets:
	def __init__(self, genotype, treatment, deprivation, drug):
		self.genotype = genotype
		self.treatment = treatment
		self.deprivation = deprivation
		self.drug = drug
		self.feed_totals = []
		self.lico_totals = []
		self.feed_bout_totals = [] #number of bouts
		self.lico_bout_totals = []
		self.feed_bout_lengths = [] #size of bouts in seconds
		self.lico_bout_lengths = []
		self.ID = str(self.genotype) + str(self.treatment) + str(self.deprivation) + str(self.drug)

#takes the times of lick/feed, outputs a set of x-labels with labels
#increment of x-axis labels is 300
def make_xticks(times):
	x_ticks = []
	x_ticks_label = []
	res = 0
	max_val = 999
	while max_val > 15:
		res += 5
		max_val = (times[-1] // (60 * res)) + 2
		max_val = int(max_val)
	for i in range(max_val):
		x_ticks += [i*60*res]
		x_ticks_label += [i*res]
	return [x_ticks, x_ticks_label]

#Takes list of event times as array [2, 5.5, 830.44] and resolution (bin size) and outputs list in bin form [2,3]
def make_bins(event_times, res):
	binned_events = []
	binned_events2 = []
	bin_limit = res
	bin_count = 0
	i = 0
	while i < len(event_times):
		if event_times[i] > bin_limit:
			binned_events += [bin_count]
			binned_events2 += [i]
			bin_limit += res
			bin_count = 0
		else:
			bin_count += 1
			i += 1
	binned_events += [bin_count]
	binned_events2 += [i]
	return (binned_events, binned_events2)

#takes 6 lists of variable length and "zip"s them
#a2 and a3 must be same length
#a4 is of different length
#a5,a6 must be same length of 3
def custom_zip(a1, a2, a3, a4, a5, a6):
	zipped_list = []
	max_len = max(len(a1), len(a2))
	for i in range(max_len):
		if i >= len(a1):
			zipped_list += [["", a2[i], a3[i]]]
		elif i >= len(a2):
			zipped_list += [[a1[i], "", ""]]
		else:
			zipped_list += [[a1[i], a2[i], a3[i]]]
			i += 1
	i = -1
	for i in range(0, len(a4)):
		zipped_list[i] += [a4[i]]
	while i < 2:
		i+=1
		zipped_list[i] += [""]
	for i in [0, 1, 2]:
		zipped_list[i] += [a5[i], a6[i]]
	return zipped_list

def individual_analysis(experiment, file_name, directory):
	plt.clf()
	y_feed = list(range(0, len(experiment.feed) + 1))
	y_lico = list(range(0, len(experiment.lico) + 1))
	plt.plot([0] + experiment.feed, y_feed)
	x_ticks = make_xticks([0] + experiment.feed)
	plt.xticks(x_ticks[0], x_ticks[1])
	plt.savefig(os.path.join(str(directory), "f_feed_" + str(file_name)[:-4] + ".pdf"))
	plt.clf()
	plt.plot([0] + experiment.lico, y_lico)
	x_ticks = make_xticks([0] + experiment.lico)
	plt.xticks(x_ticks[0], x_ticks[1])
	plt.savefig(os.path.join(str(directory), "f_lico_" + str(file_name)[:-4] + ".pdf"))
	plt.clf()
	feed_bins = make_bins(experiment.feed, resolution)
	lico_bins = make_bins(experiment.lico, resolution)
	average_labels = ["total:", "avg bout:", "num_bout:"]
	feed_average_values = [len(experiment.feed), np.mean(experiment.feed_bouts), len(experiment.feed_bouts)]
	lico_average_values = [len(experiment.lico), np.mean(experiment.lico_bouts), len(experiment.lico_bouts)]
	#INSERT CODE HERE FOR BOUT SIZES (INDIVIDUAL), AND AVERAGES
	feed_to_write = custom_zip(experiment.feed, feed_bins[0], feed_bins[1], experiment.feed_bouts, average_labels, feed_average_values)
	lico_to_write = custom_zip(experiment.lico, lico_bins[0], lico_bins[1], experiment.lico_bouts, average_labels, lico_average_values)
	with open(os.path.join(str(directory), "a_feed_" + str(file_name)), mode='w', newline='') as output_file:
		data_writer = csv.writer(output_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for i in range(len(experiment.feed)):
			data_writer.writerow(feed_to_write[i])
	with open(os.path.join(str(directory), "a_lico_" + str(file_name)), mode='w', newline='') as output_file:
		data_writer = csv.writer(output_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for i in range(len(experiment.lico)):
			data_writer.writerow(lico_to_write[i])


#reads config file to translate mouse ID to genotype/treatment
#output: dictionary[mouseID] = (genotype, treatment)
def decode(config_file):
	index = {}
	with open(config_file) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		line_count = 0
		for row in csv_reader:
			if line_count == 0:
				line_count += 1
			else:
				index[row[0]] = (row[1], row[2])
	return index

#reads a file and inputs food timestamps into Experiment, returns Experiment
def parse_file(directory, file_name, index, deprivation, drug, start, stop):
	feed_times = []
	lico_times = []
	mouseID = file_name.split('_')[7].split('-')[0]
	decoded = index[mouseID]
	new_exp = Experiment(decoded[0], decoded[1], deprivation, drug)
	with open(os.path.join(directory, file_name)) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		line_count = 0
		for row in csv_reader:
			if line_count == 0:
				line_count += 1
			else:
				if row[8] == '5' and row[9] == '2' and float(row[7]) >= start and float(row[7]) <= stop:
					feed_times += [float(row[7])]
				if row[11] == '1' and float(row[7]) >= start and float(row[7]) <= stop:
					lico_times += [float(row[7])]
					line_count += 1
	new_exp.feed = feed_times
	new_exp.lico = lico_times
	new_exp.mouseID = mouseID
	return new_exp

#goes through directory of choice and creates index dictionary with the config file
#goes through subdirectories (wd/FILENAME) and parses each FILENAME in wd
#returns a list of all experiments, unorganized
def process_all(directory, start, stop):
	experiments = []
	index = decode(os.path.join(directory, "config_file.csv"))
	for item in os.listdir(directory):
		params = item.split('_')
		if os.path.isdir(os.path.join(directory, item)):
			dir_list = os.listdir(os.path.join(directory, item))
			for exp in dir_list:
				if exp[0] != "a" and exp[0] != "f":
					new_exp = parse_file(os.path.join(directory, item), exp, index, params[0], params[1], start, stop)
					experiments += [new_exp]
					individual_analysis(new_exp, exp, os.path.join(directory, item))
	return experiments

#update Data_sets with a single new Experiment
def update_data_sets(data_sets, experiment, break_feed, break_lico, bout_start, bout_stop, feed_min_bout, lico_min_bout):
	data_sets.feed_totals += [len(experiment.feed)]
	data_sets.lico_totals += [len(experiment.lico)]
	experiment.find_feed_bouts(break_feed, bout_start, bout_stop)
	experiment.find_lico_bouts(break_lico, bout_start, bout_stop)
	experiment.trim_bouts_by_min(feed_min_bout, lico_min_bout)
	data_sets.feed_bout_totals += [len(experiment.feed_bouts)]
	data_sets.lico_bout_totals += [len(experiment.lico_bouts)]
	data_sets.feed_bout_lengths += [mean(experiment.feed_bouts)]
	data_sets.lico_bout_lengths += [mean(experiment.lico_bouts)]

#go through list of experiments to update a dict of data_sets[exp_ID] = Data_sets
def analyze(experiments, break_feed, break_lico, bout_start, bout_stop, feed_min_bout, lico_min_bout):
	data_sets = {}
	for exp in experiments:
		cur_ID = exp.ID
		if cur_ID not in data_sets:
			data_sets[exp.ID] = Data_sets(exp.genotype, exp.treatment, exp.deprivation, exp.drug)
		update_data_sets(data_sets[exp.ID], exp, break_feed, break_lico, bout_start, bout_stop, feed_min_bout, lico_min_bout)
	return data_sets

#indexes: [gene1, gene2], [treatment1, treatment2], [wd, fd], [cno, sal]
def make_output(data_sets, indexes, directoryy):
	titles = []
	feed_output = []
	lico_output = []
	feed_bout_count_output = []
	lico_bout_count_output = []
	feed_bout_length_output = []
	lico_bout_length_output = []
	for genotype in indexes[0]:
		for treatment in indexes[1]:
			cur = [[], [], [], [], [], []]
			cur_title = [genotype, treatment]
			for deprivation in indexes[2]:
				for drug in indexes[3]:
					ID = str(genotype) + str(treatment) + str(deprivation) + str(drug)
					if ID not in data_sets.keys():
						continue
					data_set = data_sets[ID]
					cur[0] += [mean(data_set.feed_totals)]
					cur[1] += [mean(data_set.lico_totals)]
					cur[2] += [mean(data_set.feed_bout_totals)]
					cur[3] += [mean(data_set.lico_bout_totals)]
					cur[4] += [mean(data_set.feed_bout_lengths)]
					cur[5] += [mean(data_set.lico_bout_lengths)]
					cur_title += [deprivation + "-" + drug]
			feed_output += [cur[0]]
			lico_output += [cur[1]]
			feed_bout_count_output += [cur[2]]
			lico_bout_count_output += [cur[3]]
			feed_bout_length_output += [cur[4]]
			lico_bout_length_output += [cur[5]]
			titles += [cur_title]
	analysis_location = os.path.join(directoryy, "analysis_report.csv")
	with open(analysis_location, mode='w', newline = '') as output_file:
		data_writer = csv.writer(output_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for i in range(len(titles)):
			data_writer.writerow(titles[i])
			data_writer.writerow(['Feeding', ''] + feed_output[i])
			data_writer.writerow(['Num Feed Bouts', ''] + feed_bout_count_output[i])
			data_writer.writerow(['Len Feed Bouts', ''] + feed_bout_length_output[i])
			data_writer.writerow(['Lico', ''] + lico_output[i])
			data_writer.writerow(['Num Lico Bouts', ''] + lico_bout_count_output[i])
			data_writer.writerow(['Len Lico Bouts', ''] + lico_bout_length_output[i])
			data_writer.writerow([''])

def run_all():
	index_test = ["cck", "grp"], ["hm3"], ["wd", "fd"], ["cno", "sal"]
	x = tk.filedialog.askdirectory(title="please select directory of datasets")
	experiments_list = process_all(x, start, stop)
	list_data_sets = analyze(experiments_list, bout_break_feed, bout_break_lico, bout_start, bout_stop, feed_min_bout, lico_min_bout)
	make_output(list_data_sets, index_list, x)
	print ("ran successfully")

run_all()
