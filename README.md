This is a short script to parse through feeding/drinking data collected in Coulborn machines. Drinking data is collected through a simple voltage-based lico-meter. Feeding data uses a slightly more complex method of having the sensor detect a lack of food for 10 seconds before despensing the next pellet. Therefore, a simple binary check on the food sensor data does not work for parsing feeding data. 

Since this is a custom script written for a mouse lab at UCSF, there are a few quirks about data organization and naming that needs to be followed. These are as follows:
1. Files need to be organized by experiment. All experiments must be placed into subdirectorys in the format of Treatment1_Treatment2. For example, for water deprived mice given CNO (a drug), the subdirectory would be named wd_cno.
2. Relevant mouse information needs to be added to a excel spreadsheet called config_file.csv You can find a sample copy in the github. Place this config file with the subdirectories above into a new root directory
3. There are a few global variables you can change to match your own needs. Note that a few of the parameters must be changed for the code to work
4. The script has a few dependencies - numpy, matplotlib, tkinter

The file outputs a number of files described below:
1. In each experiment folder (Treatment1_Treatment2), each individual experiment with name NAME will generate a file titled a_NAME which is an excel sheet which generates 3 sets of data. In column A is the timestamps of all the feeding/licking activity. In column B, the feeding/licking data is organized into histographic bins customized in the global variables of the script. In column C, the bins are organized to be cumulative and allows for easy plotting in another software. This file will also note the total licks/pellets dispensed, the average bout size, and the number of bouts.
2. Each individual experiment will also generate a file named f_NAME. This is a rough figure of the feeding/licking data. This should not be used in a professional setting and is just meant as a quick way to see if the experiment worked. 
3. A file called analysis_report.csv This contains summarized information from all the experiments including average calculations grouped by genotype/experiment/treatments. This will be automatically generated in the same directory as the config file.

Known issues:
1. Some figures are not showing up properly (there is sometimes a trailing line. Main figure should still be accurate)