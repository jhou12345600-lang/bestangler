import json, numpy as np
from PIL import Image
from scipy import ndimage
X0,Y0,X1,Y1=255,770,530,1266
def place(png):
    m=json.load(open(png+'.json')); c=Image.new('RGBA',(X1-X0,Y1-Y0)); c.alpha_composite(Image.open(png).convert('RGBA'),(m['x']-X0,m['y']-Y0)); return np.array(c).astype(float)
idle=place('work/girl_idle.png'); top=place('work/girl_fight_top.png')
H,W=idle.shape[:2]; yy=np.arange(H)[:,None]+Y0+np.zeros((1,W)); xx=np.arange(W)[None,:]+X0+np.zeros((H,1))
low=idle.copy()
low[...,3]=np.where(((xx>406)&~((xx<422)&(yy<1008)))|((xx<306)&(yy<1000)),0,low[...,3])
fight=top.copy()
fight[...,3]=np.where(yy<989,top[...,3],np.where(yy>994,low[...,3],np.maximum(top[...,3],low[...,3])))
fight[...,:3]=np.where((top[...,3:]>0)&(yy[...,None]<994),top[...,:3],np.where(low[...,3:]>0,low[...,:3],top[...,:3]))
def fill_small(m,maxa=150):
    filled=ndimage.binary_fill_holes(m); holes=filled&~m
    lab,n=ndimage.label(holes); sz=ndimage.sum(holes,lab,range(1,n+1))
    return m|np.isin(lab,[i+1 for i,s in enumerate(sz) if s<=maxa])
def clean(a):
    a=a.copy(); r,g,b,al=a[...,0],a[...,1],a[...,2],a[...,3]
    water=((g-r>27)&(g>80)&(yy>845)) | ((g-r>18)&(g>=b-8)&(r<115)&(yy>880)&(yy<1000)&((xx>396)|(xx<318))) | ((yy<850)&(g-r>18)&(r<135)&~((xx>336)&(xx<388)&(yy<824))) | ((yy<800)&(xx>384)&(g-r>8))
    grass=(yy>1110)&(b<0.72*np.minimum(r,g))&(r+g>150)
    al=np.where(water|grass,0,al)
    m=ndimage.binary_opening(al>20,iterations=1)
    bot=yy>1150
    m=np.where(bot,ndimage.binary_opening(m,structure=np.ones((1,5))),m)
    lab,n=ndimage.label(m); sz=ndimage.sum(m,lab,range(1,n+1))
    keep=np.isin(lab,[i+1 for i,s in enumerate(sz) if s>300])
    keep=fill_small(keep)
    al=np.where(keep,np.maximum(al,np.where(ndimage.binary_erosion(keep,iterations=2),255,0)),0)
    near=(al>0)&~ndimage.binary_erosion(al>250,iterations=3)
    a[...,1]=np.where(near&(g>r+4),np.minimum(g,(r+b)/2+4),g)
    a[...,3]=ndimage.gaussian_filter(al,0.6)*(al>0)
    return np.clip(a,0,255).astype(np.uint8)
Image.fromarray(clean(idle)).save('work/girl-idle.png')
Image.fromarray(clean(fight)).save('work/girl-fight.png')
s=Image.new('RGBA',((X1-X0)*2+10,Y1-Y0),(190,70,60,255))
s.alpha_composite(Image.open('work/girl-idle.png'),(0,0)); s.alpha_composite(Image.open('work/girl-fight.png'),(X1-X0+10,0)); s.convert('RGB').save('work/girl_pair.jpg')
