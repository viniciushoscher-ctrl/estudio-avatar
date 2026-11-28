"""Iguala timbre (EQ suave por 1/3 de oitava, ±6 dB) e nível de cada trecho do início ao corpo do vídeo."""
import json,sys,numpy as np,soundfile as sf,librosa
wav,lj,out,ate=sys.argv[1],sys.argv[2],sys.argv[3],float(sys.argv[4])
y,sr=sf.read(wav,dtype='float32'); L=json.load(open(lj))
F=librosa.fft_frequencies(sr=sr,n_fft=4096)
def ltas(s):
    S=np.abs(librosa.stft(s,n_fft=4096,hop_length=1024))**2; e=S.sum(0); return S[:,e>0.05*e.max()].mean(1)
def ativo(s):
    r=librosa.feature.rms(y=s,frame_length=2048,hop_length=1024)[0]; return 20*np.log10(np.median(r[r>0.1*r.max()]))
corpo=y[int(60*sr):int(600*sr)]; Lc=ltas(corpo); Ac=ativo(corpo)
cent=np.array([63*2**(i/3) for i in range(int(3*np.log2(16000/63))+1)])
def bandas(lt):
    return np.array([10*np.log10(lt[(F>=c/2**(1/6))&(F<c*2**(1/6))].mean()+1e-12) for c in cent])
Bc=bandas(Lc)
z=y.copy()
for lg in L['legendas']:
    if lg['ini']>ate: break
    a=max(0,int((lg['ini']-0.2)*sr)); b=int((lg['fim']+0.2)*sr); s=y[a:b]
    d=Bc-bandas(ltas(s)); d-=np.median(d[(cent>=300)&(cent<=1200)])   # só a forma do espectro
    LIM=float(__import__('os').environ.get('LIM',6)); d=np.clip(np.convolve(d,np.ones(3)/3,'same'),-LIM,LIM); d[cent<70]=np.minimum(d[cent<70],0)
    n=len(s); X=np.fft.rfft(s); fr=np.fft.rfftfreq(n,1/sr)
    g=10**(np.interp(np.log2(np.maximum(fr,20)),np.log2(cent),d)/20)
    s2=np.fft.irfft(X*g,n).astype(np.float32)
    s2*=10**((Ac-ativo(s2))/20)
    w=np.ones(n,np.float32); f=int(0.05*sr); w[:f]=np.linspace(0,1,f); w[-f:]=np.linspace(1,0,f)
    z[a:b]=z[a:b]*(1-w)+s2*w
    print(f"{lg['ini']:5.1f} ganho {Ac-ativo(s):+.1f} dB  EQ máx {np.abs(d).max():.1f} dB  {lg['txt'][:30]}")
pk=np.abs(z).max(); z*=min(1,0.97/pk); sf.write(out,z,sr)
