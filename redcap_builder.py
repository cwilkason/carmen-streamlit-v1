import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import re

class RedCapper:
    def __init__(self):
        pass
    
    # method
    def build_redcap(self, fl_t13_hit_binary_output_2, date, barcode_assignment):
       
        ### convert 0 to 2 (negative)
        redcap_t13_hit_binary_output = fl_t13_hit_binary_output_2.replace(0, 2)

         ### drop any rows incl and below 'Summary' row
        if 'Summary' in redcap_t13_hit_binary_output.index:
            idx = redcap_t13_hit_binary_output.index.get_loc('Summary')
            redcap_t13_hit_binary_output = redcap_t13_hit_binary_output.iloc[:idx]

        ### convert any cell val with a dagger † to 6 (NTC contaminated)
        redcap_t13_hit_binary_output = redcap_t13_hit_binary_output.replace(r'.*†.*', 6, regex=True)

        ### convert col vals for invalid assays to 5 (invalid)
        # for all invalid samples
        redcap_t13_hit_binary_output.loc[redcap_t13_hit_binary_output['SAMPLE VALID? Y/N'] == 'N***', :] = 5

        # for all invalid assays
        assay_valid_cols = redcap_t13_hit_binary_output.columns[redcap_t13_hit_binary_output.loc['Assay Valid?'] == 'INVALID ASSAY']
        for col in assay_valid_cols:
            redcap_t13_hit_binary_output[col] = 5

        ### drop the 'SAMPLE VALID? Y/N' col
        redcap_t13_hit_binary_output = redcap_t13_hit_binary_output.drop('SAMPLE VALID? Y/N', axis=1)

        ### drop the 'Assay Valid?' row
        redcap_t13_hit_binary_output = redcap_t13_hit_binary_output.drop('Assay Valid?', axis=0)

        ### drop any columns containing no_crRNA
        redcap_t13_hit_binary_output = redcap_t13_hit_binary_output.loc[:, ~redcap_t13_hit_binary_output.columns.str.lower().str.contains('no_crrna')]

        ### strip all _ and asterisks from the column names
        for i, col in enumerate(redcap_t13_hit_binary_output.columns):
            if not re.search(r'rnasep|no_crrna', col, re.IGNORECASE):
                new_col = re.split(r'[_*]', col)[0]
                redcap_t13_hit_binary_output.columns.values[i] = new_col
            if  re.search(r'rnasep|no_crrna', col, re.IGNORECASE):
                new_col = re.split(r'[*]', col)[0]
                redcap_t13_hit_binary_output.columns.values[i] = new_col

        ### add columns for the assay that wasn't run with since REDCAP format needs all assays (RVP and BBP) headers in 
        bbp_assays = ['CCHFV', 'CHI', 'DENV', 'EBOV', 'HBV_DNA', 'HCV', 'HIV_1', 'HIV_2', 'HTV', 'LASV', 'MBV', 'MMV', 
                    'MPOX_DNA', 'ONN', 'PF_3_DNA', 'RBV', 'RVFV', 'SYPH_DNA', 'WNV', 'YFV', 'ZIKV']
        rvp_assays = ['SARS-COV-2', 'HCOV-HKU1', 'HCOV-NL63', 'HCOV-OC43', 'FLUAV', 'FLUBV', 'HMPV', 'HRSV', 'HPIV-3']
        # set column order
        column_order = bbp_assays + rvp_assays + ['RNASEP_P1','RNASEP_P2']
        # when adding the new columns, enter the value as 4 (not run)
        for col in column_order:
            if col not in redcap_t13_hit_binary_output.columns:
                redcap_t13_hit_binary_output[col] = 4
        
        ### reorder cols
        redcap_t13_hit_binary_output = redcap_t13_hit_binary_output[column_order]

        ### add in the metadata columns
        sampleid = []
        for idx in redcap_t13_hit_binary_output.index:
            cleaned_idx = re.sub(r'[\*\|†\s]', '', idx)
            sampleid.append(cleaned_idx)
        
        redcap_t13_hit_binary_output.insert(0, "date", date)
        redcap_t13_hit_binary_output.insert(1, "ifc", barcode_assignment)
        redcap_t13_hit_binary_output.insert(2, "sampleid", sampleid)

        record_id = []
        for row in redcap_t13_hit_binary_output.itertuples():
            samp_id = row.sampleid 
            record_id_val = barcode_assignment + '_' + samp_id 
            record_id.append(record_id_val)

        redcap_t13_hit_binary_output.insert(0, "record_id", record_id)

        ### merge same samples ran on different panels 
        # extract sampleid before panel 
        redcap_t13_hit_binary_output['sampleid_prefix'] = redcap_t13_hit_binary_output['sampleid'].str.replace(r'(_P1|_P2|_RVP)$', '', regex=True)
       
        # merge rows with the same sampleid_prefix - keep assay results unique, combine record_ids, update sampleid
        def merge_group(group):
            # select first row in subset of redcap_t13_hit_binary_output grouped by sampleid_prefix
            merged_row = pd.DataFrame(columns=group.columns)
            merged_row.loc[0] = group.iloc[0]

            # the group is the unique sampleid_prefix - each group should have max 2 rows
            for col in group.columns:
                if col not in ["record_id", "date", "ifc", "sampleid", "sampleid_prefix"]:
                    # if merged_row['cchfv'] = [5,4], then lambda fn will produce [5,None]
                    # dropna will make it merged_row['cchfv'] = [5]
                    # .unique ensures that only unique vals are retained
                   
                    if all(group[col] == 4):
                        merged_row[col] = 4
                    else: # if group[col] = [5,4] or [3, 4] - there's no world where it would be [5,3]
                        filtered_values = group.loc[group[col] != 4, col].dropna().unique()
                        merged_row[col] = filtered_values[0] 
                     
            # each record_id is split and the two panel suffixes are added to the record_id - the .unique ensures that that all distinct splits are added tg
            merged_row['record_id'] = '_'.join(group['record_id'].apply(lambda x: x.split('_')[-1]).unique())

            # assign a sampleid to the merged_row (doesn't matter as sampleid col will be dropped later)
            merged_row['sampleid'] = group['sampleid'].iloc[0]

            return merged_row
        
        # apply the merge_group function to each group in the groupby obj (which is a df)
        redcap_t13_hit_binary_output = redcap_t13_hit_binary_output.groupby('sampleid_prefix').apply(merge_group).reset_index(drop=True)

        # make record_id col be ifc + sample_id_prefix + record_id (which is just _P1_P2)
        record_id_fix = []
        for row in redcap_t13_hit_binary_output.itertuples():
            record_id = row.record_id 
            sampleid_prefix = row.sampleid_prefix
            sampleid = row.sampleid
            if not any(control in sampleid_prefix for control in ['NTC', 'CPC', 'NDC']):
                record_id_val = barcode_assignment + '_' + sampleid_prefix + '_' + record_id
                record_id_fix.append(record_id_val)
            else:
                record_id_val = barcode_assignment + '_' + sampleid + '_' + record_id

        redcap_t13_hit_binary_output['record_id'] = record_id_fix

        ### drop sampleid
        redcap_t13_hit_binary_output = redcap_t13_hit_binary_output.drop(columns=['sampleid'])

        ### rename sampleid_prefix as sampleid and insert it as the 4th col
        redcap_t13_hit_binary_output = redcap_t13_hit_binary_output.rename(columns={'sampleid_prefix': 'sampleid'})
        cols = list(redcap_t13_hit_binary_output.columns)
        cols.remove('sampleid')
        cols.insert(3, 'sampleid')
        redcap_t13_hit_binary_output = redcap_t13_hit_binary_output[cols]

        ### lowercase all columns in redcap_t13_hit_binary_output for REDCAP data entry
        redcap_t13_hit_binary_output.columns = redcap_t13_hit_binary_output.columns.str.lower()

        ### reset index
        redcap_t13_hit_binary_output = redcap_t13_hit_binary_output.reset_index(drop=True)

        return redcap_t13_hit_binary_output

