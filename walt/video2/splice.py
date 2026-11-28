import sys,soundfile as sf,numpy as np,json
bruta,novo,velho,t,lim,out=sys.argv[1],sys.argv[2],sys.argv[3],float(sys.argv[4]),float(sys.argv[5]),sys.argv[6]
y,sr=sf.read(bruta,dtype='float32'); n,_=sf.read(novo,dtype='float32'); dv=sf.info(velho).duration
if n.ndim>1: n=n.mean(1)
print('novo',len(n)/sr,'velho',dv,'limite',lim)
assert len(n)/sr<=lim, 'não cabe'
a=int(t*sr); y[a:a+int(dv*sr)]=0; y[a:a+len(n)]+=n*10**(3.1/20*0)  # mesma cadeia/nível da narração
sf.write(out,y,sr)
