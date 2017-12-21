from pylab import *
def freq_calc(y_mask):
	HIGH = 0
	LOW = 0
	prev = None
	T = []
	duty_cycle = []
	start = y_mask[0]==0
	for i in y_mask:
		print(i,HIGH,LOW)
		if prev == int(start) and i==int(not start):
			if HIGH>4 and LOW>4:
				T.append(HIGH+LOW)
				duty_cycle.append(HIGH/(HIGH+LOW))
				HIGH=0
				LOW=1
				print(T,duty_cycle)
		elif i==0:
			LOW+=1
		elif i==1:
			HIGH+=1
		prev = i
	print(T,duty_cycle)
	T_mean = np.mean(T)
	duty_cycle_mean = np.mean(duty_cycle)
	return 1/T_mean, duty_cycle_mean

def peak2peak(ref,signal,smooth_ref=3,mean_calc=np.median, ref_mode='triangle'):
	if ref_mode == 'triangle':
		y_df1 = np.insert(np.diff(medfilt(ref,smooth_ref)), 0, 0)
	else:
		#d = ref.max()-ref.mean()
		d=np.insert(np.diff(medfilt(ref,smooth_ref)), 0, 0)
		#y_df1 = ref-ref.mean()+d/5
		y_df1_ = ((d>0)+(d==0))&(ref>max(ref)*0.9)
		y_df1 = y_df1_.astype(int) - np.mean(y_df1_)
	#print(y_df1,type(y_df1))
	HIGH=np.mean(signal[y_df1>0])
	LOW=np.mean(signal[y_df1<0])
	res = abs(mean_calc(HIGH)-mean_calc(LOW))
	STD = np.sqrt(np.std(signal[y_df1>0])**2 )#+ np.std(signal[y_df1<0])**2)
	f,duty_cycle = freq_calc(y_df1_)
	#print(STD)
	return res,HIGH,LOW,STD,f,duty_cycle