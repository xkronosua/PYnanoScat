# IPython log file

get_ipython().magic('cd work/PYnanoScat/')
get_ipython().magic('ls ')
y=[]
for i in range(5):
    y+=[0,1]
    
y
x=arange(len(y))
plot(x,y)
from scipy.interpolate import iterp1d
from scipy.interpolate import interp1d
x1=linspace(x.min(),x.max(),256)
x1
y1=interp1d(x,y)(x1)
plot(x1,y1)
k=rand(len(x1))
y1+=k/5
plot(x1,y1)
y1=interp1d(x,y)(x1)
y1+=k/8
plot(x1,y1)
y1=interp1d(x,y)(x1)
y1+=k/10
y1=interp1d(x,y)(x1)
y1+=k/10
plot(x1,y1)
x=x1
y=y1
y_df1 = np.insert(np.diff(y), 0, 0)
y_df2 = np.insert(np.diff(y_df1), 0, 0) 
y_df1
plot(y_df1)
plot(y_df2)
plot(x1,y1)
y
def find_ranges(y):
    y=medfilt(y,21)
    # calculate second derivative
    y_df1 = np.insert(np.diff(y), 0, 0)
    y_df2 = np.insert(np.diff(y_df1), 0, 0) 

    # points where the decrease starts and ends
    # (where the second derivative is minimum and maximum)
    x_dec = np.where(y_df2 == min(y_df2))[0][0]
    x_inc = np.where(y_df2 == max(y_df2))[0][0]
    return x_dec,x_inc
y
y_df1
plot(y1)
plot(y_df1)
plot(y_df2)
y_df1 = np.insert(np.diff(y), 0, 0)
y_df2 = np.insert(np.diff(y_df1), 0, 0) 
plot(y_df2)
y_df1 = np.insert(np.diff(medfilt(y,10)), 0, 0)
y_df2 = np.insert(np.diff(y_df1), 0, 0)
 
from scipy.signal import medfilt
y_df1 = np.insert(np.diff(medfilt(y,10)), 0, 0)
y_df2 = np.insert(np.diff(y_df1), 0, 0)
 
y_df1 = np.insert(np.diff(medfilt(y,11)), 0, 0)
y_df2 = np.insert(np.diff(y_df1), 0, 0)
 
plot(y)
plot(y_df1)
plot(y_df2)
plot(y_df1)
plot(y_df1>0)
plot(y_df2>0)
plot(y)
y_df1 = np.insert(np.diff(y), 0, 0)
y_df2 = np.insert(np.diff(y_df1), 0, 0)
 
plot(y_df1>0)
y_df1 = np.insert(np.diff(medfilt(y,5)), 0, 0)
y_df2 = np.insert(np.diff(y_df1), 0, 0)
 
plot(y)
plot(y_df1>0)
plot(y)
plot(y_df1>0)
s=(y_df1>0)*1
s
s+=k/10+k/8
k
s
k
s+=k/10+k/8
s+=k/10.+k/8.
s
s=(y_df1>0)*1.
s
s+=k/10.+k/8.
s
plot(s)
top=np.mean(s[y_dif1>0])
top=np.mean(s[y_df1>0])
low=np.mean(s[y_df1<0])
HIGH=np.mean(s[y_df1>0])
LOW=np.mean(s[y_df1<0])
plot([0,256],[HIGH]*2,'-r')
plot([0,256],[LOW]*2,'-b')
LOW=np.median(s[y_df1<0])
HIGH=np.median(s[y_df1>0])
plot([0,256],[HIGH]*2,'-r')
plot([0,256],[LOW]*2,'-b')
d=(y_df1>0)*1.
d
medfilt(d,10)
medfilt(d,11)
medfilt(d,21)
sin(d)
medfilt(d+k,11)
plot(medfilt(d+k,11))
plot(medfilt(d+k,3))
plot(medfilt(d+k/5,3))
average
get_ipython().magic('pinfo average')
def peak2peak(ref,signal,smooth=3,mean_calc=np.median):
    y_df1 = np.insert(np.diff(medfilt(ref,smooth)), 0, 0)
    HIGH=np.mean(signal[y_df1>0])
    LOW=np.mean(signal[y_df1<0])
    res = mean_calc(HIGH)-mean_calc(LOW)
    return res
plot(y)
plot(s)
def peak2peak(ref,signal,smooth=3,mean_calc=np.median):
    y_df1 = np.insert(np.diff(medfilt(ref,smooth)), 0, 0)
    HIGH=np.mean(signal[y_df1>0])
    LOW=np.mean(signal[y_df1<0])
    res = mean_calc(HIGH)-mean_calc(LOW)
    return res,(HIGH,LOW)
peak2peak(y,s)
peak2peak(y,s)
peak2peak(y,s)
import time
start=time.time();peak2peak(y,s);print(time.time()-start)
start=time.time();peak2peak(y,s);print(time.time()-start)
fourier = np.fft.fft(s)
plot(d)
fourier = np.fft.fft(d)
n=d.size
n
timestep=0.05*8/256
timestep
freq = np.fft.fftfreq(n, d=timestep)
freq
plot(freq)
get_ipython().magic('paste')
get_ipython().magic('paste')
freq_from_crossings(d,1)
freq_from_crossings(s,1)
get_ipython().magic('paste')
freq_from_fft(d,1)
from scipy.signal import blackmanharris, fftconvolve
freq_from_fft(d,1)
from parabolic import parabolic
u=d
u=y
t=x
t
t=linspace(256,len(y))
t
t=linspace(0,256,len(y))
t
plot(t,u)
t=arange(256)
len(t)
len(u)
t
dt=1
FFT = sy.fft(u)
freqs = syfp.fftfreq(len(u), dt)
FFT = np.fft(u)
freqs = np.fftfreq(len(u), dt)
fft
FFT = fft(u)
freqs = fftfreq(len(u), dt)
fft
fft(u)
import scipy as sy
import scipy.fftpack as syfp
FFT = sy.fft(u)
freqs = syfp.fftfreq(len(u), dt)
FFT
plot(FFT)
plot(freqes)
plot(freqs)
FFT = sy.fft(u)
freqs = syfp.fftfreq(len(u), dt)
u
plot(t,u)
FFT = sy.fft(u)
freqs = syfp.fftfreq(len(u), dt)
plot(freqs, sy.log10(abs(FFT)), '.')
figure(2)
plot(t,u)
get_ipython().magic('logstart')
112-57
w = np.fft.fft(y)
freqs = np.fft.fftfreq(len(y))
plot(freqs,w)
plot(freqs,abs(w))
plot(freqs,abs(w))
plot(freqs,abs(w))
1/55
