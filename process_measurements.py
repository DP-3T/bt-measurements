#!/usr/bin/python3

"""
Generate all the different figures and tables from the key experiments.
"""

from figures import *
from measurements import *

def create_heatmaps(exp, image_name, title, exp_title):
	all_data = []
	scenario_id = 1
	for scenario_name, dbname in exp:
		scenario = get_attenuations(dbname)
		heatmap(scenario,
			title + ": " + exp_title.format(scenario_id, scenario_name), 
			image_name.format(scenario_id, scenario_name.lower()))
		scenario_id += 1
		all_data += scenario

	heatmap(all_data,
		title + ": " + exp_title.format(scenario_id, "All combined"), 
		image_name.format(scenario_id, "all"))


def create_precision_recall(exp, image_name, exp_title):
	data_200530 = []
	data_200613 = []
	data_200813 = []
	data_our = []
	for _, dbname in exp:
		data_200530 += get_attenuations(dbname, compensation=MODEL_RX_TX_COMPENSATION_200530)
		data_200613 += get_attenuations(dbname, compensation=MODEL_RX_TX_COMPENSATION_200613)
		data_200813 += get_attenuations(dbname, compensation=MODEL_RX_TX_COMPENSATION)
		data_our += get_attenuations(dbname, compensation=MODEL_RX_TX_COMPENSATION_OUR)

	#precision_recall(data_200530, 30, 80, title=exp_title+": precision/recall for all scenarios (200530)", filename=image_name.format("200530"))
	precision_recall(data_200613, 30, 80, title=exp_title+": precision/recall for all scenarios (200613)", filename=image_name.format("200613"))
	precision_recall(data_200813, 30, 80, title=exp_title+": precision/recall for all scenarios (200813)", filename=image_name.format("200813"))
	precision_recall(data_our, 30, 80, title=exp_title+": precision/recall for all scenarios (our measurements)", filename=image_name.format("our"))
	precision_recall_table(data_200813, 30, 80)


def create_precision_recall_en(exp, image_name, exp_title):
	data_amin_gmin = []
	data_amin_gavg = []
	data_aavg_gmin = []
	data_aavg_gavg = []
	for _, dbname in exp:
		data_amin_gmin += get_attenuations_en(dbname, att='min', gtd='min')
		data_amin_gavg += get_attenuations_en(dbname, att='min', gtd='avg')
		data_aavg_gmin += get_attenuations_en(dbname, att='avg', gtd='min')
		data_aavg_gavg += get_attenuations_en(dbname, att='avg', gtd='avg')

	precision_recall(data_amin_gmin, 30, 80, title=exp_title+": prec./recall, all scenarios (att min/gtd min)", filename=image_name.format("amingmin"))
	precision_recall(data_amin_gavg, 30, 80, title=exp_title+": prec./recall, all scenarios (att min/gtd avg)", filename=image_name.format("amingavg"))
	precision_recall(data_aavg_gmin, 30, 80, title=exp_title+": prec./recall, all scenarios (att avg/gtd min)", filename=image_name.format("aavggmin"))
	precision_recall(data_aavg_gavg, 30, 80, title=exp_title+": prec./recall, all scenarios (att avg/gtd avg)", filename=image_name.format("aavggavg"))


if __name__ == "__main__":

	exp05 = [
		('Lunch', 'exp05-epfl-soldiers/scenario01-lunch.sqlite'),
		('Train', 'exp05-epfl-soldiers/scenario02-train.sqlite'),
		('Office', 'exp05-epfl-soldiers/scenario03-office.sqlite'),
		('Queue', 'exp05-epfl-soldiers/scenario04-queue.sqlite'),
		('Party', 'exp05-epfl-soldiers/scenario05-party.sqlite'),
	]
	#create_heatmaps(exp05, "figures/exp05s{:02d}-{}", "Experiment 05", "Social Experiment, Scenario {:02d} '{}' (EPFL)")
	#create_precision_recall(exp05, "figures/exp05-pr-{}", "Experiment 05")

	#data_e05_rounded = []
	#for att, gtd in data_e05:
	#	data_e05_rounded.append((att, round(gtd*2)/2))
	#boxplot(data_e05_rounded, title="Experiment 05: Attenuation vs. Distance", ylabel="Attenuation [dB]", xlabel="Distance [m]", filename="figures/exp05-box")


	exp34 = [
		('Lunch', 'exp34-epfl-soldiers/scenario01-lunch.sqlite'),
		('Train', 'exp34-epfl-soldiers/scenario02-train.sqlite'),
		('Office', 'exp34-epfl-soldiers/scenario03-office.sqlite'),
		('Queue', 'exp34-epfl-soldiers/scenario04-queue.sqlite'),
		('Party', 'exp34-epfl-soldiers/scenario05-party.sqlite'),
		('Movement', 'exp34-epfl-soldiers/scenario06-movement.sqlite'),
	]
	create_heatmaps(exp34, "figures/exp34s{:02d}-{}", "Experiment 34", "Social Experiment, Scenario {:02d} '{}' (EPFL)")
	create_precision_recall(exp34, "figures/exp34-pr-{}", "Experiment 34")

	exp34en = [
		('Lunch', 'exp34-epfl-soldiers/scenario01-lunch.json'),
		('Train', 'exp34-epfl-soldiers/scenario02-train.json'),
		('Office', 'exp34-epfl-soldiers/scenario03-office.json'),
		('Queue', 'exp34-epfl-soldiers/scenario04-queue.json'),
		('Party', 'exp34-epfl-soldiers/scenario05-party.json'),
		('Movement', 'exp34-epfl-soldiers/scenario06-movement.json'),
	]
	create_precision_recall_en(exp34en, "figures/exp34-pr-en-{}", "Exp34, EN data")
	#data_e34_rounded = []
	#for att, gtd in data_e34:
	#	data_e34_rounded.append((att, round(gtd*2)/2))
	#boxplot(data_e34_rounded, title="Experiment 34: Attenuation vs. Distance", ylabel="Attenuation [dB]", xlabel="Distance [m]", filename="figures/exp34-box")

