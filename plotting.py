import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

class Plotter:
    def __init__(self):
        pass
    
    def gettime(time_assign, timepoints):
        realt = time_assign[timepoints]
        return (realt)

    def plt_heatmap(self, tgap, barcode_number, df_dict, sample_list, assay_list, tp):
        # Create a dictonary for timepoints
        time_assign = {}

        for cycle in range(1,len(tp)+1):
            tpoint = "t" + str(cycle)
            time_assign[tpoint] = tgap + 3 + (cycle-1) * 5
        
        fig_timepoints = {}
        for i in tqdm(tp):
            df_dict[i] = df_dict[i].transpose()
            frame = df_dict[i][sample_list].reindex(assay_list)
            fig, axes = plt.subplots(1,1,figsize=(len(frame.columns.values)*0.5,len(frame.index.values)*0.5))
            ax = sns.heatmap(frame,cmap='Reds',square = True,cbar_kws={'pad':0.002}, annot_kws={"size": 20})

            # calculate the real timing of the image
            rt = time_assign[i]

            plt.title('Heatmap for 'f'{barcode_number} at '+str(rt)+' minutes', size = 28)
            plt.xlabel('Samples', size = 14)
            plt.ylabel('Assays', size = 14)
            bottom, top = ax.get_ylim()
            ax.set_ylim(bottom + 0.5, top - 0.5)
            ax.tick_params(axis="y", labelsize=16)
            ax.tick_params(axis="x", labelsize=16)
            plt.yticks(rotation=0)

            tgt_num = len(sample_list)
            gd_num = len(assay_list)
            bottom, top = ax.get_ylim()
            ax.set_ylim(bottom + 0.5, top - 0.5)
            h_lines = np.arange(3,gd_num,3)
            v_lines = np.arange(3,tgt_num,3)
            axes.hlines(h_lines, colors = 'silver',alpha=0.9,linewidths = 0.35,*axes.get_xlim())
            axes.vlines(v_lines, colors = 'silver',alpha=0.9,linewidths = 0.35,*axes.get_ylim())
            fig_timepoints[i] = fig

        return fig_timepoints