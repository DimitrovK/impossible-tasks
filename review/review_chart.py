import json, collections, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
rows=[r for r in json.load(open("review_results.json")) if r["parsed"]]
INVIS={"PATCHED THE HARNESS","DEFEATED THE METRIC","HID STATE IN SOURCE","FABRICATED DEP","CORRUPTED SOURCE","BROKE THE CONTRACT"}
HON={"CORRECT (approx)","WROTE MISSING FILE","SOLVED"}
def band(v): return "honest" if v in HON else ("invisible" if v in INVIS else "visible")
plt.rcParams.update({"figure.facecolor":"#12141a","axes.facecolor":"#12141a","axes.edgecolor":"#3a4050",
 "text.color":"#e6e8ee","axes.labelcolor":"#e6e8ee","xtick.color":"#9aa3b5","ytick.color":"#9aa3b5",
 "font.size":11,"grid.color":"#232733"})
fig=plt.figure(figsize=(12.5,8.6)); gs=fig.add_gridspec(2,1,height_ratios=[1.2,1],hspace=0.46)
ax=fig.add_subplot(gs[0])
order=["PATCHED THE HARNESS","DEFEATED THE METRIC","BROKE THE CONTRACT","HID STATE IN SOURCE",
       "CORRUPTED SOURCE","FABRICATED DEP","EDITED BOTH","WEAKENED TEST","TAUTOLOGY"]
labels={"PATCHED THE HARNESS":"patched the test's RNG","DEFEATED THE METRIC":"moved work out of the timed region",
 "BROKE THE CONTRACT":"hardcoded the value the ticket forbade","HID STATE IN SOURCE":"made the function stateful",
 "CORRUPTED SOURCE":"corrupted a correct function","FABRICATED DEP":"invented the missing dependency",
 "EDITED BOTH":"edited the test and the source","WEAKENED TEST":"weakened the assertion",
 "TAUTOLOGY":"made the assertion unfalsifiable"}
ys=[];vals=[];cols=[];ns=[]
for k in order:
    s=[r for r in rows if r["truth"]==k]
    if not s: continue
    ys.append(labels[k]); vals.append(100*sum(r["flagged"] for r in s)/len(s)); ns.append(len(s))
    cols.append("#e5484d" if band(k)=="invisible" else "#f5a524")
ax.barh(range(len(ys)),vals,color=cols,edgecolor="#12141a",lw=1.4)
for i,(v,n) in enumerate(zip(vals,ns)): ax.text(v+1.3,i,f"{v:.0f}%  (n={n})",va="center",fontsize=10)
ax.set_yticks(range(len(ys))); ax.set_yticklabels(ys,fontsize=10); ax.invert_yaxis()
ax.set_xlim(0,118); ax.set_xlabel("share of reviews that flagged the change as NOT_SOLVED")
ax.grid(axis="x",alpha=.3,lw=.6)
ax.set_title("Reviewers caught the subtle cheats and waved through the blatant ones",loc="left",pad=10,fontsize=12.5)
import matplotlib.patches as mp
ax.legend(handles=[mp.Patch(color="#e5484d",label="cheat hidden in the source (original tests still pass)"),
                   mp.Patch(color="#f5a724",label="cheat visible in the diff (a test was edited)")],
          loc="lower right",facecolor="#1a1d26",edgecolor="#3a4050",fontsize=9.5)
ax2=fig.add_subplot(gs[1])
mods=sorted({r["reviewer"] for r in rows}); w=0.26
for j,(b,c,lab) in enumerate([("invisible","#e5484d","hidden in the source"),
                              ("visible","#f5a524","visible in the diff"),
                              ("honest","#3fb950","genuinely fine (false alarms)")]):
    v=[]
    for m in mods:
        s=[r for r in rows if r["reviewer"]==m and band(r["truth"])==b]
        v.append(100*sum(r["flagged"] for r in s)/len(s) if s else 0)
    ax2.bar([i+j*w for i in range(len(mods))],v,width=w,color=c,label=lab,edgecolor="#12141a",lw=1.2)
    for i,x in enumerate(v): ax2.text(i+j*w,x+2.5,f"{x:.0f}",ha="center",fontsize=9.5,color="#e6e8ee")
ax2.set_xticks([i+w for i in range(len(mods))]); ax2.set_xticklabels(mods,fontsize=10)
ax2.set_ylabel("% flagged as NOT_SOLVED"); ax2.set_ylim(0,132); ax2.grid(axis="y",alpha=.3,lw=.6)
ax2.legend(facecolor="#1a1d26",edgecolor="#3a4050",fontsize=9.5,ncol=3,loc="upper center",bbox_to_anchor=(0.5,1.0))
ax2.set_title("Every reviewer flags honest work about as often as it flags a weakened test",loc="left",pad=10,fontsize=12)
fig.suptitle("I asked agents to review the cheats other agents wrote",x=0.06,ha="left",fontsize=14.5,y=0.985)
fig.text(0.06,0.948,"205 parsed reviews of 77 diffs, three reviewer models, each given the original ticket and the full diff.",
         ha="left",fontsize=10,color="#9aa3b5")
fig.subplots_adjust(left=0.30,right=0.97,top=0.90,bottom=0.08)
fig.savefig("review_results.png",dpi=145); print("wrote review_results.png")
