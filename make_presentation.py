"""Generate an editable SentinelUPI project overview PowerPoint.

Customize PROJECT_NAME, TAGLINE, and TEAM below, then run this script.
Requires: python-pptx (python -m pip install python-pptx)
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml import parse_xml
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import nsdecls

PROJECT_NAME = "SentinelUPI"  # Main title: replace this text to rename the project
TAGLINE = "Adaptive UPI fraud detection with explainable decisions"
TEAM_NAME = "Callidus"
TEAM = [("Team Leader", "Pradyumn Kr. Singh"), ("Member", "Sddhant Arya"),
        ("Member", "Manas Dungriyal"), ("Member", "Mayank Dungriyal"),
        ("Member", "Aayush Dhami")]
OUT = "SentinelUPI_Project_Overview.pptx"

# Mint glass theme; orange is reserved for the corner triangle.
ORANGE = "F47721"  # Reserved exclusively for the corner triangle.
ACCENT = "65A987"; AMBER = ACCENT; INK = "17352A"; MUTED = "526D60"
PAPER = "F6FFF9"; WHITE = "FFFFFF"; PALE = "E6F6EC"; GREEN = "398267"
W, H = 13.333, 7.5
prs = Presentation(); prs.slide_width = Inches(W); prs.slide_height = Inches(H)
prs.core_properties.title = f"{PROJECT_NAME} | Project Overview"
prs.core_properties.subject = "Editable overview of project architecture, features, and team"
prs.core_properties.author = TEAM_NAME

def rgb(h): return RGBColor.from_string(h)
def rect(slide, x,y,w,h, color, radius=False):
    s=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb=rgb(color)
    # Translucent fill and fine pale edge give cards and accents a glass-like finish.
    solid=s._element.spPr.solidFill
    alpha=OxmlElement('a:alpha'); alpha.set('val','76000'); solid.append(alpha)
    s.line.color.rgb=rgb("D2EBDD"); s.line.width=Pt(0.8)
    line_fill=s._element.spPr.ln.solidFill
    if line_fill is not None:
        edge_alpha=OxmlElement('a:alpha'); edge_alpha.set('val','65000'); line_fill.append(edge_alpha)
    if radius:
        try: s.adjustments[0]=0.12
        except Exception: pass
    return s
def corner_triangle(slide):
    # Right angle sits at the top-right slide corner; both legs follow slide edges.
    t=slide.shapes.add_shape(MSO_SHAPE.RIGHT_TRIANGLE, Inches(W-1.12), Inches(0), Inches(1.12), Inches(1.12))
    t.rotation=180
    t.fill.solid(); t.fill.fore_color.rgb=rgb(ORANGE); t.line.fill.background()
    return t
def green_gradient(slide):
    bg=slide._element.cSld.get_or_add_bg()
    bgPr=bg.get_or_add_bgPr()
    for child in list(bgPr):
        bgPr.remove(child)
    grad=OxmlElement('a:gradFill'); grad.set('rotWithShape','1')
    stops=OxmlElement('a:gsLst')
    for pos,col in ((0,'F8FFFA'),(55000,'EDF9F1'),(100000,'DDF1E5')):
        stop=OxmlElement('a:gs'); stop.set('pos',str(pos))
        color=OxmlElement('a:srgbClr'); color.set('val',col)
        stop.append(color); stops.append(stop)
    grad.append(stops)
    linear=OxmlElement('a:lin'); linear.set('ang','5400000'); linear.set('scaled','1')
    grad.append(linear); bgPr.append(grad)
    effect=OxmlElement('a:effectLst'); bgPr.append(effect)
def txt(slide, text, x,y,w,h, size=16, color=INK, bold=False, font="Aptos",
        align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, margin=0.04):
    box=slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf=box.text_frame; tf.clear(); tf.word_wrap=True
    tf.margin_left=tf.margin_right=Inches(margin); tf.margin_top=tf.margin_bottom=Inches(margin)
    tf.vertical_anchor=valign
    p=tf.paragraphs[0]; p.alignment=align
    r=p.add_run(); r.text=text; r.font.name=font; r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=rgb(color)
    return box
def base(title, kicker, page):
    s=prs.slides.add_slide(prs.slide_layouts[6]); green_gradient(s)
    corner_triangle(s)
    txt(s,kicker.upper(),0.62,0.38,11.8,0.25,10,ACCENT,True)
    txt(s,title,0.62,0.73,12,0.62,27,INK,True)
    rect(s,0.62,1.47,0.55,0.055,ACCENT)
    txt(s,PROJECT_NAME,0.62,7.08,6,0.2,9,MUTED,True)
    txt(s,f"{page:02d}",12.18,7.06,0.5,0.22,10,MUTED,True,align=PP_ALIGN.RIGHT)
    return s
def card(s,x,y,w,h,title,body,accent=ACCENT,body_size=15):
    rect(s,x,y,w,h,WHITE,True); rect(s,x,y,0.07,h,accent)
    txt(s,title,x+0.24,y+0.2,w-0.45,0.35,16,INK,True)
    txt(s,body,x+0.24,y+0.68,w-0.48,h-0.83,body_size,MUTED)
def bullets(s, items, x,y,w, size=17, color=MUTED, gap=0.52):
    for i,item in enumerate(items):
        yy=y+i*gap; rect(s,x,yy+0.1,0.10,0.10,ACCENT,True)
        txt(s,item,x+0.25,yy,w-0.25,gap-0.04,size,color)

# 1 — cover
s=prs.slides.add_slide(prs.slide_layouts[6]); green_gradient(s); corner_triangle(s)
txt(s,"PROJECT OVERVIEW",0.85,0.83,7.6,0.3,12,ACCENT,True)
txt(s,PROJECT_NAME,0.82,1.42,8.1,1.0,42,INK,True)
txt(s,TAGLINE,0.88,2.65,7.5,0.8,22,MUTED)
rect(s,0.88,3.75,1.1,0.08,ACCENT)
txt(s,"EXPLAINABLE  •  ADAPTIVE  •  BEHAVIOR-AWARE",0.88,4.12,7.9,0.35,12,ACCENT,True)
rect(s,9.75,0.95,2.72,2.45,WHITE,True)
txt(s,"Team",10.15,1.12,2.0,0.35,14,MUTED,True,align=PP_ALIGN.CENTER)
txt(s,TEAM_NAME,9.98,1.68,2.4,0.75,29,INK,True,align=PP_ALIGN.CENTER)
txt(s,"Fintech prototype",10.05,2.65,2.25,0.45,13,MUTED,False,align=PP_ALIGN.CENTER)
txt(s,"A clearer, more adaptive approach to transaction security.",0.9,6.55,8.0,0.45,11,MUTED)

# 2
s=base("The problem: blind alerts erode trust","Context",2)
txt(s,"A risk score alone does not tell a customer what happened—or what to do next.",0.78,1.82,11.7,0.65,22,INK,True)
card(s,0.78,2.8,3.75,2.7,"Opaque blocks","Generic declines give no useful reason and make legitimate users feel punished.")
card(s,4.78,2.8,3.75,2.7,"False alarms","Travel, a new phone, or festive spending can look unusual against a static profile.",AMBER)
card(s,8.78,2.8,3.75,2.7,"Changing behavior","A useful system needs to learn a user's evolving routine while still spotting hostile activity.",GREEN)
txt(s,"Project goal",0.82,5.92,1.4,0.3,12,ACCENT,True)
txt(s,"Surface the signals behind each decision and adapt when an anomaly is confirmed legitimate.",2.0,5.85,10.4,0.55,17,INK,True)

# 3
s=base("What SentinelUPI does","Solution",3)
txt(s,"An explainable UPI transaction verification prototype that combines user context with transaction signals.",0.78,1.82,11.7,0.65,20,INK,True)
card(s,0.78,2.75,3.75,2.75,"Build a baseline","Track typical spend and trusted devices / cities for a user.")
card(s,4.78,2.75,3.75,2.75,"Evaluate a transaction","Score amount, time, device, location, travel speed, and transaction burst.",AMBER)
card(s,8.78,2.75,3.75,2.75,"Explain & respond","Show risk tier, plain-language contributing factors, and a recommended action.",GREEN)
txt(s,"Designed to distinguish a benign lifestyle change from a likely account takeover.",0.82,6.0,11.7,0.42,17,ACCENT,True,align=PP_ALIGN.CENTER)

# 4 architecture
s=base("System architecture at a glance","Architecture",4)
steps=[("01  Transaction input","Amount • category • time • device • city"),("02  User profile","EWMA spend baseline • trusted devices • trusted cities"),("03  Feature & risk engine","Deviation • nocturnal activity • geo velocity • transaction burst"),("04  Explanation","Risk tier • diagnosis • attributed factors • next action"),("05  User interface","Python dashboard / Android app • simulator • profile • passbook")]
for i,(a,b) in enumerate(steps):
    y=1.82+i*0.91; rect(s,0.82,y,2.45,0.66,ACCENT if i==0 else INK,True)
    txt(s,a,0.98,y+0.15,2.15,0.34,14,WHITE,True,valign=MSO_ANCHOR.MIDDLE)
    txt(s,b,3.65,y+0.12,8.75,0.42,16,INK,False,valign=MSO_ANCHOR.MIDDLE)
    if i<4: rect(s,1.98,y+0.68,0.08,0.22,AMBER)
txt(s,"Two implementations: Python reference engine + Streamlit dashboard; native Kotlin engine + Android app.",0.82,6.53,11.8,0.3,12,MUTED,False,align=PP_ALIGN.CENTER)

# 5
s=base("Behavioral signals build context","Detection",5)
card(s,0.78,1.9,3.75,2.0,"Spend deviation","EWMA mean and spread; amount z-score and spend multiple.")
card(s,4.78,1.9,3.75,2.0,"Device & place","Known device / city status; unfamiliar combinations raise context.",AMBER)
card(s,8.78,1.9,3.75,2.0,"Time & velocity","Overnight activity, distance since last transaction, travel speed, and burst count.",GREEN)
txt(s,"Baseline adaptation",0.82,4.35,3.0,0.35,16,ACCENT,True)
bullets(s,["Python profile uses EWMA statistics and trusted entity registries.","Documented learning rates: α = 0.10 routine drift; α = 0.35 after confirmed legitimate anomaly.","Android profile stores spend mean / variance and updates from user feedback."],0.84,4.86,11.6,15,gap=0.52)

# 6 risk tiers
s=base("A risk tier leads to a proportionate action","Decisioning",6)
tiers=[("LOW","0–24.9","Allow",GREEN),("MEDIUM","25–54.9","Allow with notification / learn when benign",AMBER),("HIGH","55–74.9","Step-up OTP verification",ACCENT),("CRITICAL","75–100","Biometric challenge or block","527F67")]
for i,(a,b,c,d) in enumerate(tiers):
    y=1.88+i*1.06; rect(s,0.82,y,2.15,0.76,d,True); txt(s,a,0.98,y+0.15,1.8,0.4,16,WHITE,True,valign=MSO_ANCHOR.MIDDLE)
    txt(s,b,3.35,y+0.16,1.65,0.35,17,INK,True); txt(s,c,5.12,y+0.16,6.8,0.4,16,MUTED)
txt(s,"Tier thresholds and response labels are defined in project code / architecture notes; thresholds are prototype logic.",0.82,6.36,11.6,0.45,12,MUTED,False,align=PP_ALIGN.CENTER)

# 7 explainability
s=base("Explainability turns flags into useful signals","Explainability",7)
txt(s,"Instead of returning only a number, SentinelUPI can describe why a transaction looks different.",0.82,1.8,11.7,0.55,20,INK,True)
card(s,0.82,2.68,5.45,2.65,"Example: benign change","New device, familiar city, daytime transaction → may be a device upgrade. Notify and learn rather than repeatedly alarming.",GREEN,16)
card(s,7.02,2.68,5.45,2.65,"Example: hostile pattern","Novel device + overnight timing + rapid location jump / P2P → strong takeover signals; step-up or block.","527F67",16)
txt(s,"Outputs include a diagnosis, recommended action, narrative summary, factor list, and attribution breakdown.",0.85,5.86,11.5,0.45,16,ACCENT,True,align=PP_ALIGN.CENTER)

# 8 python stack
s=base("Python engine & interactive dashboard","Implementation • Python",8)
card(s,0.82,1.88,5.45,3.75,"Core engine","engine.py\n• ProfileManager + EWMA user profiles\n• FeatureExtractor: spend, device, geo, time, velocity\n• FraudModel: Random Forest workflow\n• ExplainabilityEngine: factor narratives\n• Synthetic transaction generator",ACCENT,15)
card(s,7.02,1.88,5.45,3.75,"Streamlit experience","app.py\n• Live transaction simulator + presets\n• Real-time stream / wrong-guess view\n• Adaptive baseline & drift view\n• Model studio and dataset specification\n\nSupporting scripts: dataset generation, condition inspection, stream tester.",AMBER,15)
txt(s,"Python dependencies include pandas, NumPy, scikit-learn, Streamlit, Plotly, and joblib.",0.84,6.04,11.5,0.4,15,MUTED,False,align=PP_ALIGN.CENTER)

# 9 android stack
s=base("Android app & local network demo","Implementation • Android",9)
card(s,0.82,1.88,5.45,3.75,"Native app","Kotlin • Jetpack Compose • Material 3\n\nScreens: Home / transfers, Threat Lab, Passbook, Profile.\n\nThreat Lab edits transaction inputs and presents risk attribution. Balance is customizable in the demo.",ACCENT,15)
card(s,7.02,1.88,5.45,3.75,"LAN peer-to-peer","LanP2PManager uses JSON over TCP on port 8989.\n\nDISCOVER probes a peer; PAYMENT sends a demo payload. A receiving device records a credit.\n\nThe Android FraudClassifier is a calibrated rule-based score path.",AMBER,15)
txt(s,"Android minimum SDK 26 • target SDK 34 (per architecture notes).",0.84,6.04,11.5,0.4,15,MUTED,False,align=PP_ALIGN.CENTER)

# 10 data/testing
s=base("Data, simulation & project artifacts","Project contents",10)
card(s,0.82,1.9,3.75,3.55,"Synthetic data","Dataset generator and sample CSV support repeatable scenarios without real banking records.")
card(s,4.78,1.9,3.75,3.55,"Scenario coverage","Routine purchases, festive spikes, travel, device changes, overnight takeover patterns, and transaction bursts.",AMBER)
card(s,8.78,1.9,3.75,3.55,"Repository pieces","Python dashboard / engine, Android app, architecture guide, diagnostic scripts, tests, and data folder.",GREEN)
txt(s,"The repository includes tests and diagnostic tools; this presentation describes functionality rather than claiming measured production performance.",0.85,5.96,11.5,0.55,14,MUTED,False,align=PP_ALIGN.CENTER)

# 11 scope
s=base("Prototype scope & next steps","Scope",11)
card(s,0.82,1.88,5.45,3.75,"What the prototype demonstrates","• Behavioral profiling and anomaly signals\n• Risk tiers with explainable factors\n• Python and Android experiences\n• Synthetic scenario simulation\n• LAN-only payment interaction demo",GREEN,16)
card(s,7.02,1.88,5.45,3.75,"What a next iteration can add","• Validate with representative, consented data\n• Measure false-positive / detection trade-offs\n• Secure and authenticate payment messages\n• Persist profiles and audit decisions\n• Integrate with a regulated payment stack",ACCENT,16)
txt(s,"LAN transfers and balances are a local demonstration, not a connection to UPI rails or a bank.",0.85,6.08,11.5,0.4,14,"527F67",True,align=PP_ALIGN.CENTER)

# 12 team
s=prs.slides.add_slide(prs.slide_layouts[6]); green_gradient(s); corner_triangle(s); txt(s,"THE TEAM",0.82,0.65,4,0.3,12,AMBER,True)
txt(s,TEAM_NAME,0.82,1.15,8,0.8,38,WHITE,True)
txt(s,"Building clearer, more adaptive transaction security.",0.86,2.08,8,0.55,20,MUTED)
for i,(role,name) in enumerate(TEAM):
    x=0.88+(i%2)*6.05; y=3.05+(i//2)*1.0
    rect(s,x,y,5.55,0.76,WHITE,True)
    txt(s,role.upper(),x+0.22,y+0.12,1.52,0.22,9,AMBER,True)
    txt(s,name,x+1.72,y+0.1,3.55,0.48,17,INK,True,valign=MSO_ANCHOR.MIDDLE)
txt(s,f"{PROJECT_NAME}  •  Thank you",0.86,6.93,11.8,0.3,12,MUTED,True)

# A native PowerPoint zoom-in transition is applied to each slide after the cover.
# Its focal box is centered, so the primary content on each slide is kept centered
# and the transition reads as moving into the main element introduced previously.
for slide in list(prs.slides)[1:]:
    transition=parse_xml(f'<p:transition {nsdecls("p")} spd="med"><p:zoom dir="in"/></p:transition>')
    slide._element.insert(1, transition)

prs.save(OUT)
print(f"Wrote {OUT}")
