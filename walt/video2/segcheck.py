import sys,json,numpy as np,soundfile as sf,librosa,tempfile,os
sys.path.insert(0,'/tmp/w2'); from qual import q
wav,lj=sys.argv[1],sys.argv[2]; L=json.load(open(lj)); y,sr=sf.read(wav,dtype='float32')
tmp=tempfile.mktemp(suffix='.wav'); R=[]
for lg in L['legendas']:
    a=max(0,int((lg['ini']-0.25)*sr)); b=int((lg['fim']+0.25)*sr); sf.write(tmp,y[a:b],sr)
    r=q(tmp); r['t']=round(lg['ini'],1); r['txt']=lg['txt'][:40]; R.append(r)
json.dump(R,open(sys.argv[3],'w'),indent=0)
H=np.array([r['hz'] for r in R]); print('hz mediana',np.median(H),'p10',np.percentile(H,10),'| sig mediana',np.median([r['sig'] for r in R]),'| sim mediana',np.median([r['sim'] for r in R]))
for r in R:
    if r['nota']>1.5 or r['hz']<0.88*np.median(H) or r['fry']>0.1 or r['sig']<3.3: print('ATENÇÃO',r)
