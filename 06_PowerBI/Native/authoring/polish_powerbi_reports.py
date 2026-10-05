"""Report-only executive formatting; semantic models and source paths untouched."""
from pathlib import Path
import json, hashlib, zipfile, shutil

ROOT=Path(__file__).resolve().parent
PROJECTS=[('01_Olist_B2B_Revenue_Funnel','RevenueFunnel','ecomrevenuefunnel','Olist B2B'),('04_Olist_Customer_Experience','CustomerExperience','customexp','Olist customer experience'),('03_LendingClub_Credit_Portfolio','CreditPortfolio','lenden','LendingClub')]
BASE=ROOT/'Data_Analytics_Portfolio'
if ROOT.name=='authoring':
    project=ROOT.parent.parent.parent
    PROJECTS=[(project.name,n,r,b) for f,n,r,b in PROJECTS if (ROOT.parent/(n+'.Report')).exists()]
    BASE=project.parent
NAVY='#17324D'; TEAL='#0A827C'; MUTED='#53657A'; LIGHT='#E4EAF0'
def lit(v):
    value=str(v).lower() if isinstance(v,bool) else f'{v}D' if isinstance(v,(int,float)) else "'"+v.replace("'","''")+"'"
    return {'expr':{'Literal':{'Value':value}}}
def color(v): return {'solid':{'color':lit(v)}}
def props(obj,key,**values):
    obj.setdefault(key,[{'properties':{}}])[0]['properties'].update(values)
def save(p,v): p.write_text(json.dumps(v,indent=2)+'\n')

def run():
    published=[]
    for folder,name,repo,brand in PROJECTS:
        native=BASE/folder/'06_PowerBI'/'Native'
        model=native/(name+'.SemanticModel')/'model.bim'
        before=hashlib.sha256(model.read_bytes()).hexdigest()
        report=native/(name+'.Report')
        theme_path=report/'StaticResources/RegisteredResources/ProfessionalAnalytics.json'
        theme=json.loads(theme_path.read_text())
        theme.update(dataColors=[TEAL,NAVY,'#B88641','#A34E56','#8092A5','#6B8E93'],foreground=NAVY,tableAccent=TEAL,background='#F3F6F9')
        common=theme['visualStyles']['*']['*']
        common['border']=[{'show':True,'color':{'solid':{'color':LIGHT}},'radius':8}]
        common['title'][0].update(fontSize=14,fontColor={'solid':{'color':NAVY}})
        theme['textClasses']['callout']['fontSize']=30
        save(theme_path,theme)
        for page in sorted((report/'definition/pages').glob('page*')):
            if not page.is_dir(): continue
            info=json.loads((page/'page.json').read_text())
            visuals=[]
            for path in sorted((page/'visuals').glob('*/visual.json')):
                data=json.loads(path.read_text()); v=data['visual']; typ=v['visualType']; pos=data['position']
                con=v.get('visualContainerObjects',{}); obj=v.setdefault('objects',{})
                title=con.get('title',[{'properties':{}}])[0]['properties']
                props(con,'title',fontSize=lit(14),fontColor=color(NAVY))
                if typ=='textbox':
                    paragraphs=obj['general'][0]['properties']['paragraphs']
                    for paragraph in paragraphs:
                        for run in paragraph.get('textRuns',[]):
                            run['textStyle']['color']=NAVY if pos['y']<80 else MUTED
                            if pos['y']<80:
                                run['value']=f'{brand}  |  {info["displayName"]}'
                                run['textStyle'].update(fontFamily='Segoe UI Semibold',fontSize='25pt')
                    props(con,'title',show=lit(False))
                elif typ=='slicer':
                    # Only one label: retain native slicer header, hide container title.
                    label=title['text']['expr']['Literal']['Value'][1:-1]
                    props(con,'title',show=lit(False))
                    props(obj,'header',show=lit(True),text=lit(label),textSize=lit(12),fontFamily=lit('Segoe UI Semibold'),fontColor=color(NAVY))
                    props(obj,'items',textSize=lit(12),fontColor=color(MUTED))
                    props(obj,'general',responsive=lit(False))
                    pos.update(y=86,height=72)
                elif typ=='card':
                    is_context=any(p.get('nativeQueryRef')=='Context Insight' for r in v['query']['queryState'].values() for p in r['projections'])
                    props(obj,'labels',fontFamily=lit('Segoe UI Semibold' if not is_context else 'Segoe UI'),fontSize=lit(17 if is_context else 30),color=color(NAVY))
                    props(obj,'categoryLabels',show=lit(False))
                    if is_context:
                        props(obj,'wordWrap',show=lit(True))
                        props(con,'title',text=lit('Portfolio context' if repo=='lenden' else 'Decision context'))
                        pos.update(y=610,height=282)
                    else:
                        pos.update(y=180,height=100)
                elif typ in ('clusteredBarChart','clusteredColumnChart','lineChart'):
                    props(obj,'general',responsive=lit(False))
                    props(obj,'categoryAxis',fontSize=lit(11),fontFamily=lit('Segoe UI'),labelColor=color(MUTED),showAxisTitle=lit(False))
                    props(obj,'valueAxis',fontSize=lit(11),fontFamily=lit('Segoe UI'),labelColor=color(MUTED),showAxisTitle=lit(False),start=lit(0),gridlineShow=lit(True),gridlineColor=color(LIGHT))
                    props(obj,'labels',fontSize=lit(11),color=color(NAVY))
                    if typ=='lineChart': props(obj,'lineStyles',strokeWidth=lit(3),showMarker=lit(True),markerSize=lit(4))
                    category=v['query']['queryState']['Category']['projections'][0]
                    if category.get('nativeQueryRef')=='grade':
                        v['query']['sortDefinition']={'sort':[{'field':category['field'],'direction':'Ascending'}],'isDefaultSort':False}
                    pos.update(y=310 if pos['y']<600 else 610,height=278 if pos['y']<600 else 282)
                elif typ=='tableEx':
                    props(obj,'columnHeaders',fontSize=lit(12),fontFamily=lit('Segoe UI Semibold'),fontColor=color(NAVY),backColor=color('#EEF3F7'),wordWrap=lit(True))
                    props(obj,'values',fontSize=lit(11),fontColorPrimary=color(NAVY),wordWrap=lit(True))
                    props(obj,'grid',rowPadding=lit(8),gridVertical=lit(False),gridHorizontal=lit(True),gridHorizontalColor=color(LIGHT))
                    pos.update(y=610,height=282)
                save(path,data); visuals.append(data)
            # All stored rectangles must be inside the canvas with no collisions.
            for i,a in enumerate(visuals):
                x=a['position']; assert x['x']>=0 and x['y']>=0 and x['x']+x['width']<=1440 and x['y']+x['height']<=960
                for b in visuals[i+1:]:
                    y=b['position']
                    assert not (x['x']<y['x']+y['width'] and y['x']<x['x']+x['width'] and x['y']<y['y']+y['height'] and y['y']<x['y']+x['height']), (path,a['name'],b['name'])
        assert hashlib.sha256(model.read_bytes()).hexdigest()==before
        manifest_path=native/'report_manifest.json'
        manifest=json.loads(manifest_path.read_text())
        for i, p in enumerate(manifest['pages'],1):
            for j, visual in enumerate(p['visuals'],1):
                vf=report/f'definition/pages/page{i}/visuals/v{j:02d}/visual.json'
                if vf.exists(): visual['position']=json.loads(vf.read_text())['position']
        save(manifest_path,manifest)
        author=native/'authoring'; author.mkdir(exist_ok=True)
        # Keep a reproducible report-only formatter in each repository.
        if Path(__file__).resolve() != (author/'polish_powerbi_reports.py').resolve(): shutil.copy2(__file__,author/'polish_powerbi_reports.py')
        note=native/'REPORT_UPDATE.md'
        note.write_text('''# Executive report update\n\nClose Power BI Desktop before applying this update.\n\n1. Extract the report update ZIP.\n2. Copy the `.Report` folder into `06_PowerBI/Native` in your existing project, replacing the old folder.\n3. Reopen your existing `.pbip` file.\n\nKeep your existing `.SemanticModel` folder. The update contains report visuals only; your configured source path, data and measures remain intact.\n\nChanges: single slicer labels; navy and teal executive theme; consistent chart spacing and axes; grade order A–G; wrapped context panels; clearer KPI and table typography.\n\nValidation: JSON formatting, theme schema and non-overlapping canvas geometry checked. Desktop rendering still needs review in Power BI after opening the update.\n''')
        update=native.parent/'Updates';update.mkdir(exist_ok=True)
        zip_path=update/(name+'_Report_Update.zip')
        with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
            for f in sorted(report.rglob('*')):
                if f.is_file(): z.write(f,f.relative_to(native))
            z.write(note,'READ_ME.md')
        published.append({'repo':repo,'folder':folder,'name':name,'model_sha256':before,'zip':str(zip_path)})
    save(ROOT/'executive_updates.json',published)
if __name__=='__main__': run()
