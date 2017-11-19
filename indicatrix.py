from pylab import *
import json
import pandas as pd
import scipy as sp
import sys
import traceback

fname = sys.argv[1]

Lambda = "532"
filters = ["1","op06", "op09", "op18", "op09,op18"]

def filtCalc(filters, filtTable=None):
	if filters:
		if not filtTable is None:
			filters = filters.replace(' ', '').replace(' ', '').replace('+', ',').replace(';', ',').replace('.', ',')
			res = 1.
			try:
				res = sp.multiply.reduce( [ filtTable[Lambda][i.upper()] for i in filters.split(",")] ) 
			except KeyError:
				traceback.print_exc()
				res = 1.
			return res
		else:
			return	
	else:
		return 1. 

filtTable = json.load(open('filters.dict'))


df = pd.read_csv(fname,comment='#',names=['angle','ref','signal','filt'],sep='\t')
filt = [filtCalc(filters[i],filtTable) for i in df.filt]

a = []
for i in df.angle:
	r = 0
	try:
		r = float(i)
	except:
		pass
	a.append(r)

df['angle1'] = array(a)
df['scat'] = df.signal/filt
plot(df.angle1/2, df.scat)
show(1)
df.to_csv(fname+"_res.dat",sep='\t',comment='#')