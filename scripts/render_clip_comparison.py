"""Create a compact annotated drawing comparing the reconstructed clip to the drawing."""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs/kicad'; OUT.mkdir(parents=True,exist_ok=True)
fig=plt.figure(figsize=(12,7),dpi=180); gs=fig.add_gridspec(2,3,height_ratios=[2.1,1],hspace=.38,wspace=.28)
ax=fig.add_subplot(gs[0,0]); ax.set_title('Front / formed spring (mm)',weight='bold')
ax.plot([-3.95,-3.95,-3.4,-2.7,-2.0,-1.3,-.5,0,.5,1.3,2.0,2.7,3.4,3.95,3.95],[.5,1.05,2.2,3.45,4.7,5.5,6.4,7.2,8.0,9.0,9.8,10.35,10.7,10.9,.5],color='#174f79',lw=2)
ax.plot([3.45,3.45,3.0,2.3,1.6,1.0,.5,0,-.5,-1.0,-1.6,-2.3,-3.0,-3.45,-3.45],[.5,1.25,2.5,3.8,4.9,5.8,6.7,7.2,6.7,5.8,4.9,3.8,2.5,1.25,.5],color='#174f79',lw=2)
ax.annotate('7.9 base width',xy=(3.95,.5),xytext=(0,-1.2),ha='center',arrowprops=dict(arrowstyle='<->')); ax.annotate('10.9 overall',xy=(4.4,10.9),xytext=(4.4,.5),va='center',arrowprops=dict(arrowstyle='<->'))
ax.text(0,7.2,'R3.2\ncentre z=7.2',ha='center',va='center',fontsize=8); ax.text(0,10.45,'4.5 mouth\n3.5 throat',ha='center',fontsize=8)
ax.set(xlim=(-5,5),ylim=(-1.8,12),aspect='equal'); ax.axis('off')
ax=fig.add_subplot(gs[0,1]); ax.set_title('Side / axial width and tails',weight='bold')
ax.add_patch(Rectangle((-3.5,0),7,.5,fc='#c5d1db',ec='#174f79')); ax.add_patch(Rectangle((-3.5,-3.6),.5,3.6,fc='#c5d1db',ec='#174f79')); ax.add_patch(Rectangle((3,-3.6),.5,3.6,fc='#c5d1db',ec='#174f79')); ax.add_patch(Rectangle((-3.5,.5),7,10.4,fc='#eaf1f5',ec='#174f79',alpha=.45))
ax.annotate('7.0 body width',xy=(-3.5,11.2),xytext=(3.5,11.2),ha='right',arrowprops=dict(arrowstyle='<->')); ax.annotate('3.6 below PCB',xy=(4,-3.6),xytext=(4,0),va='center',arrowprops=dict(arrowstyle='<->')); ax.text(0,-.8,'PCB top / 1.6 mm FR-4',ha='center',fontsize=8)
ax.set(xlim=(-5,5),ylim=(-5,13),aspect='equal'); ax.axis('off')
ax=fig.add_subplot(gs[0,2]); ax.set_title('Tail pattern / hole reference',weight='bold')
for x in (-3.8,3.8): ax.add_patch(plt.Circle((x,0),1,fill=False,color='#174f79',lw=2))
ax.annotate('7.6 pitch',xy=(-3.8,1.4),xytext=(3.8,1.4),ha='right',arrowprops=dict(arrowstyle='<->')); ax.text(0,-1.8,'Ø2.0 ±0.1 holes\nclip is DNP at JLC',ha='center',fontsize=9)
ax.set(xlim=(-6,6),ylim=(-3,3),aspect='equal'); ax.axis('off')
ax=fig.add_subplot(gs[1,:]); ax.axis('off'); ax.set_title('Datasheet comparison — nominal dimensions',loc='left',weight='bold')
rows=[('Overall height', '10.9', '10.900', '0.000'),('Base transverse width','7.9','7.900','0.000'),('Body axial width','7.0','7.000','0.000'),('Tail pitch','7.6','7.600','0.000'),('Tail below PCB','3.6','3.600','0.000'),('Sheet thickness','0.5','0.5 nominal','0.000'),('Hole diameter','2.0 ±0.1','2.0 pad / hole','see fab')]
t=ax.table(cellText=rows,colLabels=['Feature','Drawing / datasheet','CAD reconstruction','Difference'],loc='center',cellLoc='center',colWidths=[.28,.22,.22,.18]); t.auto_set_font_size(False); t.set_fontsize(10); t.scale(1,1.55)
fig.suptitle('C142864 / Littelfuse 10207101009 — sheet-metal reconstruction',fontsize=15,weight='bold'); fig.text(.01,.01,'Source: local C142864 datasheet and supplied 102071 Clip drawing. Bend transitions and stamping details are not dimensioned.',fontsize=8)
fig.savefig(OUT/'C142864-annotated-comparison.png',bbox_inches='tight'); fig.savefig(OUT/'C142864-annotated-comparison.pdf',bbox_inches='tight'); print(OUT/'C142864-annotated-comparison.png')
