#!/usr/bin/env python3
"""Generate dark/light contribution heatmap SVGs for the profile README."""
import sys, os, json, random, urllib.request, datetime as dt
USER = sys.argv[1] if len(sys.argv) > 1 else "xAgesx"
SAMPLE = "--sample" in sys.argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
def fetch():
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not tok: sys.exit("Set GH_TOKEN (read:user) or use --sample")
    q = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""
    req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query":q,"variables":{"u":USER}}).encode(), headers={"Authorization":"bearer "+tok,"Content-Type":"application/json","User-Agent":"contrib-svg"})
    d=json.load(urllib.request.urlopen(req))
    if "errors" in d: sys.exit(str(d["errors"]))
    cal=d["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    lv={"NONE":0,"FIRST_QUARTILE":1,"SECOND_QUARTILE":2,"THIRD_QUARTILE":3,"FOURTH_QUARTILE":4}
    return [[(x["date"],x["contributionCount"],lv[x["contributionLevel"]]) for x in w["contributionDays"]] for w in cal["weeks"]],cal["totalContributions"]
def sample():
    random.seed(11); end=dt.date.today(); start=end-dt.timedelta(days=364); start-=dt.timedelta(days=(start.weekday()+1)%7)
    days=[]; d=start
    while d<=end:
        r=random.random(); n=0
        if d.weekday()<5 and r<.72: n=int(random.expovariate(1/2.6))+1
        elif r<.35: n=random.randint(1,4)
        days.append((d.isoformat(),n)); d+=dt.timedelta(days=1)
    mx=max(n for _,n in days)
    def L(n): return 0 if n==0 else 1 if n<=mx*.25 else 2 if n<=mx*.5 else 3 if n<=mx*.75 else 4
    return [[(a,n,L(n)) for a,n in days[i:i+7]] for i in range(0,len(days),7)],sum(n for _,n in days)
weeks,total=sample() if SAMPLE else fetch()
flat=[x for w in weeks for x in w]; today=dt.date.today().isoformat(); past=[x for x in flat if x[0]<=today]
cur=best=run=0
for _,n,_ in past: run=run+1 if n>0 else 0; best=max(best,run)
i=len(past)-1
if i>=0 and past[i][1]==0: i-=1
while i>=0 and past[i][1]>0: cur+=1; i-=1
busiest=max(past,key=lambda x:x[1]); active=sum(1 for _,n,_ in past if n>0)
THEMES={"dark":dict(fg="#e6edf3",mute="#8b949e",line="#30363d",lv=["#161b22","#0e4429","#006d32","#26a641","#39d353"]),"light":dict(fg="#1f2328",mute="#656d76",line="#d0d7de",lv=["#ebedf0","#9be9a8","#40c463","#30a14e","#216e39"])}
C,G,X0,Y0=11,3,44,118; W=X0+len(weeks)*(C+G)+20; H=Y0+7*(C+G)+46; FONT="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"; MON=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
def build(name,t):
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}" role="img" aria-label="{total} contributions in the last year">',f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="none" stroke="{t["line"]}"/>',f'<text x="24" y="44" font-size="26" font-weight="600" fill="{t["fg"]}">{total:,}</text>',f'<text x="24" y="64" font-size="13" fill="{t["mute"]}">contributions in the last year</text>']
    stats=[(str(cur),"day streak"),(str(best),"longest streak"),(str(busiest[1]),"busiest day"),(str(active),"active days")]
    for k,(v,l) in enumerate(stats):
        x=W-24-(len(stats)-k)*112+112
        s.extend([f'<text x="{x}" y="44" font-size="20" font-weight="600" fill="{t["fg"]}" text-anchor="end">{v}</text>',f'<text x="{x}" y="64" font-size="12" fill="{t["mute"]}" text-anchor="end">{l}</text>'])
    s.append(f'<line x1="24" x2="{W-24}" y1="84" y2="84" stroke="{t["line"]}"/>')
    last=-9
    for c,w in enumerate(weeks):
        d0=dt.date.fromisoformat(w[0][0])
        if d0.day<=7 and c-last>=3 and c<len(weeks)-1:
            s.append(f'<text x="{X0+c*(C+G)}" y="{Y0-10}" font-size="11" fill="{t["mute"]}">{MON[d0.month-1]}</text>'); last=c
    for r,lab in ((1,"Mon"),(3,"Wed"),(5,"Fri")): s.append(f'<text x="{X0-8}" y="{Y0+r*(C+G)+9}" font-size="10" fill="{t["mute"]}" text-anchor="end">{lab}</text>')
    for c,w in enumerate(weeks):
        for r,(d,n,l) in enumerate(w):
            if d>today: continue
            tip=f'{n} contribution{"s" if n!=1 else ""} on {d}'
            s.append(f'<rect x="{X0+c*(C+G)}" y="{Y0+r*(C+G)}" width="{C}" height="{C}" rx="2.5" fill="{t["lv"][l]}"><title>{tip}</title></rect>')
    ly=Y0+7*(C+G)+14; lx=W-24-5*(C+G)-62
    s.append(f'<text x="{lx}" y="{ly+9}" font-size="11" fill="{t["mute"]}" text-anchor="end">Less</text>')
    for k in range(5): s.append(f'<rect x="{lx+8+k*(C+G)}" y="{ly}" width="{C}" height="{C}" rx="2.5" fill="{t["lv"][k]}"/>')
    s.extend([f'<text x="{lx+14+5*(C+G)}" y="{ly+9}" font-size="11" fill="{t["mute"]}">More</text>','</svg>'])
    open(os.path.join(OUT,f"contrib-{name}.svg"),"w",encoding="utf8").write("\n".join(s))
for n,t in THEMES.items(): build(n,t)
print("ok",total,"contributions; streak",cur,"best",best)
