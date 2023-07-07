import pandas as pd
import os


data = pd.read_csv('data/train.csv')
sample_result = pd.read_csv('data/sample_submission.csv')
data['일자'] = data['일자'].astype('str')
sample_result.head()

