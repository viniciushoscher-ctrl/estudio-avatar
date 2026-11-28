import sys,json,glob,numpy as np,librosa,torch,re
from speechbrain.inference.speaker import EncoderClassifier
enc=EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",savedir="/tmp/w2/ecapa",run_opts={"device":"cpu"})
def emb(f):
    y,_=librosa.load(f,sr=16000)
    with torch.no_grad(): e=enc.encode_batch(torch.tensor(y)[None]).squeeze().numpy()
    return e/np.linalg.norm(e)
A=np.array([emb(f) for f in sorted(glob.glob('/mnt/project-files/canal-walt/walt-15min-audio-hd/clipes/*.wav'))])
C=A.mean(0);C/=np.linalg.norm(C)
sa=A@C; print('aprovados vs centro: min %.2f p10 %.2f med %.2f'%(sa.min(),np.percentile(sa,10),np.median(sa)))
np.save('centro.npy',C)
N=sorted(glob.glob(sys.argv[1]+'/fala-*.wav')); E=np.array([emb(f) for f in N]); s=E@C
json.dump({f.split('/')[-1]:round(float(v),3) for f,v in zip(N,s)},open(sys.argv[2],'w'),indent=0)
print('narração vs centro: min %.2f p10 %.2f med %.2f'%(s.min(),np.percentile(s,10),np.median(s)))
for f,v in zip(N,s):
    if v<np.percentile(sa,5): print(f.split('/')[-1],round(float(v),3))
