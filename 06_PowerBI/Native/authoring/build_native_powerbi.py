from pathlib import Path
import json, re, uuid, csv, hashlib
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
BASE = 'https://developer.microsoft.com/json-schemas/'
def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
def schema(kind, version):
    return BASE + f'fabric/item/report/definition/{kind}/{version}/schema.json'
def lit(v):
    if isinstance(v, bool): v = 'true' if v else 'false'
    elif isinstance(v, str): v = "'"+v.replace("'", "''")+"'"
    else: v = str(v)+'D'
    return {'expr': {'Literal': {'Value': v}}}
def color(v): return {'solid': {'color': lit(v)}}
def field(table, name, measure=False, alias=None):
    return {'Measure' if measure else 'Column': {'Expression': {'SourceRef': {'Source':alias} if alias else {'Entity':table}}, 'Property':name}}
def projection(table, name, measure=False, label=None):
    return {'field':field(table,name,measure),'queryRef':table+'.'+name,'nativeQueryRef':name,'displayName':label or name.replace('_',' ').title()}

CONFIGS = [{'folder': '.', 'id': 'RevenueFunnel', 'title': 'Seller acquisition & value', 'repo': 'ecomrevenuefunnel', 'fact': 'fact_lead', 'accent': '#007F78', 'tables': ['fact_lead', 'fact_seller_order', 'dim_channel', 'dim_segment', 'dim_sdr', 'dim_sales_rep', 'dim_seller', 'dim_date'], 'slicers': [('dim_date', 'month', 'Contact month'), ('dim_channel', 'origin', 'Acquisition channel'), ('fact_lead', 'seller_state', 'Seller state')], 'cards': ['Total MQLs', 'Conversion Rate', 'Activation Rate', 'Attributed GMV'], 'footer': 'Historical lead cohorts • GMV is item merchandise value, not platform revenue • Shorter observation for recent wins'}]

def read_measures(path):
    out={}; current=None
    for line in path.read_text().splitlines():
        if line.startswith('//') or not line.strip(): continue
        m=re.match(r'^([^=]+?)\s*=\s*(.*)',line)
        if m and not line.startswith(' '): current=m[1].strip();out[current]=m[2].strip()
        elif current: out[current]+='\n'+line.strip()
    return out

def measures(cfg, p):
    m=read_measures(p/'06_PowerBI/dax_measures.txt'); f=cfg['fact']
    if f=='fact_lead':
        m.update({
         'Onboarding Backlog':'[Closed Deals] - [Active Sellers]',
         'Onboarding Flag':'IF([Closed Deals] > 0 && [Active Sellers] = 0, 1, BLANK())',
         'Activation Gap':'1 - [Activation Rate]',
         'Attributed Marketplace Orders':'CALCULATE(DISTINCTCOUNT(fact_seller_order[order_id]), TREATAS(VALUES(fact_lead[seller_id]), fact_seller_order[seller_id]))',
         'Attributed Item AOV':'DIVIDE(CALCULATE(SUM(fact_seller_order[gmv]), TREATAS(VALUES(fact_lead[seller_id]), fact_seller_order[seller_id])), [Attributed Marketplace Orders])',
         'Average Active Seller GMV':'DIVIDE([Attributed GMV], [Active Sellers])',
         'Converted Segment Deals':'[Closed Deals]',
         'Context Insight':'IF([Total MQLs] = 0, "No leads match the current selection", FORMAT([Onboarding Backlog], "#,0") & " converted sellers have no observed post-close delivered order. Review cohort maturity before outreach.")',
         'Period Coverage':'FORMAT(MIN(fact_lead[contact_date]), "dd MMM yyyy") & " – " & FORMAT(MAX(fact_lead[contact_date]), "dd MMM yyyy")',
         'Invalid Close Records':'SUM(fact_lead[invalid_close_chronology])'})
    elif f=='fact_order':
        # Virtual bridge filters apply seller/category scope to every base order metric.
        for name,expr in list(m.items()):
            if name.startswith('Bridge '): del m[name];continue
            if 'fact_order[' in expr or 'COUNTROWS(fact_order)' in expr:
                m[name]='IF(ISCROSSFILTERED(dim_seller[seller_id]) || ISCROSSFILTERED(dim_category[category]), CALCULATE('+expr+', KEEPFILTERS(TREATAS(VALUES(bridge_order_seller_category[order_id]), fact_order[order_id]))), '+expr+')'
        m.update({
         'On Time Review Score':'CALCULATE([Average Review Score], fact_order[eligible_delivery] = 1, fact_order[late] = 0)',
         'Late Review Score':'CALCULATE([Average Review Score], fact_order[late] = 1)',
         'Review Score Gap':'[On Time Review Score] - [Late Review Score]',
         'Seller Baseline Late Rate':'CALCULATE([Late Delivery Rate], REMOVEFILTERS(dim_seller))',
         'Seller Excess Late pp':'100 * ([Late Delivery Rate] - [Seller Baseline Late Rate])',
         'Seller Priority Flag':'IF([Eligible Deliveries] >= 50 && [Late Delivery Rate] > [Seller Baseline Late Rate], 1, BLANK())',
         'Eligible Delivery Coverage':'DIVIDE([Eligible Deliveries], [Delivered Orders])',
         'Comparable Monthly Late Rate':'IF([Eligible Deliveries] >= 100, [Late Delivery Rate], BLANK())',
         'Common Duration Orders':'CALCULATE([Total Orders], FILTER(fact_order, NOT ISBLANK(fact_order[processing_days]) && NOT ISBLANK(fact_order[shipping_days])))',
         'Common Processing Days':'CALCULATE([Average Processing Days], FILTER(fact_order, NOT ISBLANK(fact_order[processing_days]) && NOT ISBLANK(fact_order[shipping_days])))',
         'Common Shipping Days':'CALCULATE([Average Shipping Days], FILTER(fact_order, NOT ISBLANK(fact_order[processing_days]) && NOT ISBLANK(fact_order[shipping_days])))',
         'Context Insight':'IF([Eligible Deliveries] = 0, "No eligible deliveries in the current selection", FORMAT([Late Deliveries], "#,0") & " late deliveries; late-order reviews average " & FORMAT([Late Review Score], "0.00") & " vs " & FORMAT([On Time Review Score], "0.00") & " on time. Investigate routes and handoff stages; association is not causation.")',
         'Period Coverage':'FORMAT(MIN(fact_order[purchase_date]), "dd MMM yyyy") & " – " & FORMAT(MAX(fact_order[purchase_date]), "dd MMM yyyy")'})
    else:
        m.update({
         'Resolved Funded Amount':'CALCULATE([Funded Amount], fact_loan[resolved] = 1)',
         'Resolved Payments':'CALCULATE([Payments Received], fact_loan[resolved] = 1)',
         'Resolved Net Cash':'CALCULATE(SUM(fact_loan[net_cash]), fact_loan[resolved] = 1)',
         'Net Return Proxy':'DIVIDE([Resolved Net Cash], [Resolved Funded Amount])',
         'Resolved Coverage':'DIVIDE([Resolved Loans], [Total Loans])',
         'Current Loans':'SUM(fact_loan[current])',
         'Default Rate Baseline':'CALCULATE([Default Rate], REMOVEFILTERS(fact_loan[purpose]))',
         'Segment Excess Default pp':'100 * ([Default Rate] - [Default Rate Baseline])',
         'Segment Review Flag':'IF([Resolved Loans] >= 200 && [Default Rate] > [Default Rate Baseline], 1, BLANK())',
         'Context Insight':'IF([Resolved Loans] = 0, "No resolved loans in the current selection", FORMAT([Defaulted Loans], "#,0") & " charged-off/default outcomes among " & FORMAT([Resolved Loans], "#,0") & " resolved loans. " & FORMAT([Current Loans], "#,0") & " current loans remain outside resolved-outcome rates.")',
         'Period Coverage':'FORMAT(MIN(fact_loan[issue_date]), "MMM yyyy") & " – " & FORMAT(MAX(fact_loan[issue_date]), "MMM yyyy")'})
    return m

def fmt(n):
    if n in ['Context Insight','Period Coverage']: return None
    if 'Rate' in n or 'Share' in n or n in ['Activation Gap','Net Return Proxy','Recovery Rate','Resolved Coverage','Eligible Delivery Coverage']:return '0.0%;-0.0%;0.0%'
    if 'pp' in n:return '0.0" pp";-0.0" pp";0.0" pp"'
    if any(x in n for x in ['Score','Days','DTI','per Active']):return '0.00'
    if any(x in n for x in ['GMV','Amount','Payments','Principal','Cash','Freight','AOV','Interest Received']):return '#,0.00;(#,0.00);0.00'
    return '#,0'

def make_model(cfg, p, native, m):
    types=json.loads((p/'06_PowerBI/column_types.json').read_text()); tables=[]
    for name in cfg['tables']:
        c=types[name];columns=[]
        filename='\\'+name+'.csv'
        if cfg['fact']=='fact_lead' and name=='dim_seller':
            sellers=pd.read_csv(p/'02_Cleaned_Data/dim_seller.csv')
            leads=pd.read_csv(p/'02_Cleaned_Data/fact_lead.csv')
            missing=leads.loc[leads.seller_id.notna() & ~leads.seller_id.isin(sellers.seller_id),list(c)].copy()
            merged=pd.concat([sellers,missing],ignore_index=True).drop_duplicates('seller_id')
            for key,t in c.items():
                if t=='Int64.Type':merged[key]=pd.to_numeric(merged[key],errors='coerce').astype('Int64')
            (native/'ModelData').mkdir(exist_ok=True)
            merged.to_csv(native/'ModelData/dim_seller.csv',index=False)
            filename='\\..\\06_PowerBI\\Native\\ModelData\\dim_seller.csv'
        for k,t in c.items():
            typ={'type text':'string','Int64.Type':'int64','type number':'double','type date':'dateTime','type datetime':'dateTime','type logical':'boolean'}[t]
            col={'name':k,'dataType':typ,'sourceColumn':k,'summarizeBy':'none'}
            if typ=='dateTime':col['formatString']='yyyy-MM-dd' if t=='type date' else 'yyyy-MM-dd HH:mm'
            columns.append(col)
        pairs=', '.join('{"'+k+'", '+t+'}' for k,t in c.items())
        source=['let','    Source = Csv.Document(File.Contents(DataFolder & "'+filename+'"), [Delimiter=",", Columns='+str(len(c))+', Encoding=65001, QuoteStyle=QuoteStyle.Csv]),','    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),','    Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),','    Typed = Table.TransformColumnTypes(Nulls, {'+pairs+'}, "en-US")','in','    Typed']
        tab={'name':name,'columns':columns,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':source}}]}
        if name.startswith('dim_'):tab['description']='Single-direction dimension; keys validated against source data.'
        if name==cfg['fact']:
            tab['measures']=[]
            for n,e in m.items():
                meas={'name':n,'expression':e,'displayFolder':'Context & quality' if n in ['Context Insight','Period Coverage'] or 'Coverage' in n else ('Investigations' if any(x in n for x in ['Flag','Baseline','Backlog','Excess']) else 'Performance'), 'description': n+'; defined over the current slicer and visual context. See report definitions and DAX source for population policy.'}
                if fmt(n):
                    meas['formatString']=fmt(n)
                    if any(x in n for x in ['GMV','Amount','Payments','Principal','Cash','Freight','AOV','Interest Received']):meas['formatString']='"'+('USD' if cfg['fact']=='fact_loan' else 'BRL')+' "'+fmt(n)
                tab['measures'].append(meas)
        tables.append(tab)
    rel=[]
    for row in csv.DictReader((p/'06_PowerBI/relationships.csv').open()):
        if row['one_table'] in cfg['tables'] and row['many_table'] in cfg['tables']:
            rel.append({'name':str(uuid.uuid5(uuid.NAMESPACE_URL,cfg['id']+str(row))), 'fromTable':row['many_table'],'fromColumn':row['many_key'],'toTable':row['one_table'],'toColumn':row['one_key'],'fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':True})
    definition=native/(cfg['id']+'.SemanticModel')
    write(definition/'definition.pbism',{'$schema':BASE+'fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{}})
    write(definition/'model.bim',{'name':cfg['id'],'compatibilityLevel':1600,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','dataAccessOptions':{'legacyRedirects':True,'returnErrorValuesAsNull':False},'expressions':[{'name':'DataFolder','kind':'m','expression':'"C:\\PowerBI\\Data" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}], 'tables':tables,'relationships':rel,'annotations':[{'name':'PBI_QueryOrder','value':json.dumps(cfg['tables'])},{'name':'__PBI_TimeIntelligenceEnabled','value':'0'}]}})
    return tables,rel

def make_report(cfg,p,native,m):
    report=native/(cfg['id']+'.Report'); d=report/'definition'; pages=[]; manifest=[]
    write(native/(cfg['id']+'.pbip'),{'$schema':BASE+'fabric/pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':cfg['id']+'.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(report/'definition.pbir',{'$schema':BASE+'fabric/item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../'+cfg['id']+'.SemanticModel'}}})
    write(d/'version.json',{'$schema':schema('versionMetadata','1.0.0'),'version':'2.0.0'})
    theme={'name':'ProfessionalAnalytics','dataColors':[cfg['accent'],'#D69036','#A23D4A','#8695AA','#49A79D','#7970BE'],'background':'#F4F6F9','foreground':'#172A43','tableAccent':cfg['accent'], 'textClasses':{'label':{'fontFace':'Segoe UI','fontSize':11},'title':{'fontFace':'Segoe UI Semibold','fontSize':13},'callout':{'fontFace':'Segoe UI Semibold','fontSize':28},'header':{'fontFace':'Segoe UI Semibold','fontSize':13}},'visualStyles':{'*':{'*':{'background':[{'show':True,'color':{'solid':{'color':'#FFFFFF'}},'transparency':0}], 'title':[{'show':True,'fontColor':{'solid':{'color':'#172A43'}},'fontSize':13,'fontFamily':'Segoe UI Semibold','alignment':'left'}],'border':[{'show':False}],'visualHeader':[{'show':True}]}}}}
    write(report/'StaticResources/RegisteredResources/ProfessionalAnalytics.json',theme)
    write(d/'report.json',{'$schema':schema('report','3.0.0'),'themeCollection':{'customTheme':{'name':'ProfessionalAnalytics','type':'RegisteredResources','reportVersionAtImport':{'visual':'2.4.0','page':'2.0.0','report':'3.0.0'}}},'resourcePackages':[{'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':'ProfessionalAnalytics','path':'ProfessionalAnalytics.json','type':'CustomTheme'}]}], 'settings':{'useEnhancedTooltips':True,'exportDataMode':'AllowSummarizedAndUnderlying','defaultFilterActionIsDataFilter':True,'defaultDrillFilterOtherVisuals':True,'pagesPosition':'Bottom','useStylableVisualContainerHeader':True}})
    f=cfg['fact']
    def mp(n):return projection(f,n,True,n)
    def cp(t,n,label=None):return projection(t,n,False,label)
    def page(title, cards=None, caveat=None):
        idx=len(pages)+1;name='page'+str(idx);pages.append(name);pd=d/'pages'/name
        write(pd/'page.json',{'$schema':schema('page','2.0.0'),'name':name,'displayName':title,'displayOption':'FitToPage','width':1440,'height':960,'objects':{'background':[{'properties':{'color':color('#F4F6F9'),'transparency':lit(0)}}]}})
        state={'path':pd,'name':name,'title':title,'count':0,'visuals':[]};
        text(state,cfg['title']+'  /  '+title,24,12,1388,62,26)
        for i,(t,n,l) in enumerate(cfg['slicers']):
            visual(state,'slicer',l,24+i*472,84,448,76,{'Values':[cp(t,n,l)]},objects={'data':[{'properties':{'mode':lit('Dropdown')}}],'selection':[{'properties':{'singleSelect':lit(False),'selectAllCheckboxEnabled':lit(True)}}]})
        for i,n in enumerate(cards or cfg['cards']):
            visual(state,'card',n,24+i*354,180,330,98,{'Values':[mp(n)]},objects={'labels':[{'properties':{'fontSize':lit(28),'color':color(cfg['accent']),'fontFamily':lit('Segoe UI Semibold')}}],'categoryLabels':[{'properties':{'show':lit(False)}}]})
        text(state,caveat or cfg['footer'],24,918,1392,32,11)
        manifest.append(state);return state
    def text(s,value,x,y,w,h,size=13):
        visual(s,'textbox','',x,y,w,h,{},objects={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':value,'textStyle':{'fontFamily':'Segoe UI','fontSize':str(size)+'pt','color':'#172A43','fontWeight':'bold' if size>20 else 'normal'}}]}]}}]},transparent=True)
    def visual(s,typ,title,x,y,w,h,roles,objects=None,sort=None,filter_measure=None,transparent=False):
        s['count']+=1;name=f'v{s["count"]:02d}';v={'$schema':schema('visualContainer','2.4.0'),'name':name,'position':{'x':x,'y':y,'width':w,'height':h,'z':s['count'],'tabOrder':s['count']},'visual':{'visualType':typ,'drillFilterOtherVisuals':True,'visualContainerObjects':{'title':[{'properties':{'show':lit(bool(title)),'text':lit(title),'fontSize':lit(13),'fontColor':color('#172A43'),'fontFamily':lit('Segoe UI Semibold'),'titleWrap':lit(True)}}], 'background':[{'properties':{'show':lit(not transparent),'color':color('#FFFFFF'),'transparency':lit(100 if transparent else 0)}}], 'general':[{'properties':{'altText':lit(title or 'Report text')}}]},'objects':objects or {}}}
        if roles:v['visual']['query']={'queryState':{r:{'projections':ps} for r,ps in roles.items()}}
        if sort:v['visual']['query']['sortDefinition']={'sort':[{'field':sort[0],'direction':sort[1]}],'isDefaultSort':False}
        if filter_measure:
            v['filterConfig']={'filters':[{'name':s['name']+name+'flag','field':field(f,filter_measure,True),'type':'Advanced','isLockedInViewMode':True,'filter':{'Version':2,'From':[{'Name':'a','Entity':f,'Type':0}],'Where':[{'Condition':{'Comparison':{'ComparisonKind':0,'Left':field(f,filter_measure,True,'a'),'Right':{'Literal':{'Value':'1L'}}}}}]}}]}
        write(s['path']/'visuals'/name/'visual.json',v);s['visuals'].append({'type':typ,'title':title,'position':v['position'],'roles':roles})
    def chart(s,typ,title,cat,meas,x,y,w=684,h=282,extra=None):
        roles={'Category':[cp(*cat)],'Y':[mp(n) for n in meas]};roles.update(extra or {})
        visual(s,typ,title,x,y,w,h,roles,objects={'legend':[{'properties':{'show':lit(len(meas)>1)}}],'labels':[{'properties':{'show':lit(True),'fontSize':lit(10)}}]},sort=(field(*cat),'Ascending') if typ=='lineChart' else (field(f,meas[0],True),'Descending'))
    def table(s,title,cols,meas,x=24,y=600,w=1392,h=292,flag=None):
        visual(s,'tableEx',title,x,y,w,h,{'Values':[cp(*c) for c in cols]+[mp(n) for n in meas]},objects={'grid':[{'properties':{'gridVertical':lit(False),'rowPadding':lit(7),'textSize':lit(11)}}]},sort=(field(f,meas[0],True),'Descending') if meas else None,filter_measure=flag)
    def insight(s):visual(s,'card','Investigation context',732,602,684,290,{'Values':[mp('Context Insight')]},objects={'labels':[{'properties':{'fontSize':lit(16),'color':color('#172A43')}}],'categoryLabels':[{'properties':{'show':lit(False)}}]})
    s=page('Overview')
    if f=='fact_lead':
        chart(s,'lineChart','Lead cohorts: contacts and closed deals',('dim_date','month'),['Total MQLs','Closed Deals'],24,300)
        chart(s,'clusteredBarChart','Observed GMV by acquisition channel · BRL',('dim_channel','origin'),['Attributed GMV'],732,300)
        chart(s,'clusteredBarChart','GMV per lead · channel quality, not ROI',('dim_channel','origin'),['GMV per Lead'],24,602,h=290);insight(s)
        s=page('Channels & cohorts',['GMV per Lead','Average Close Days','Repeat Seller Rate','Top 10 Percent GMV Share'])
        chart(s,'lineChart','Conversion by contact cohort · maturity differs',('dim_date','month'),['Conversion Rate'],24,300)
        chart(s,'clusteredBarChart','Activation among converted sellers',('dim_channel','origin'),['Activation Rate'],732,300)
        table(s,'Channel comparison · review counts before prioritizing spend',[('dim_channel','origin','Channel')],['Total MQLs','Closed Deals','Conversion Rate','Active Sellers','Activation Rate','Attributed GMV','GMV per Lead'])
        s=page('Seller investigations',['Onboarding Backlog','Active Sellers','Average First Sale Days','Average Active Seller GMV'])
        chart(s,'clusteredBarChart','GMV by business segment · converted sellers only',('dim_segment','business_segment'),['Attributed GMV'],24,300)
        chart(s,'clusteredBarChart','Activation by business segment · converted sellers only',('dim_segment','business_segment'),['Activation Rate'],732,300)
        table(s,'Onboarding queue · converted with no observed post-close delivered order',[('fact_lead','seller_id','Seller ID'),('fact_lead','origin','Channel'),('fact_lead','won_date','Closed date'),('fact_lead','business_segment','Segment')],['Average Close Days','Closed Deals'],flag='Onboarding Flag')
    elif f=='fact_order':
        chart(s,'lineChart','Monthly late rate · ≥100 eligible deliveries',('dim_date','month'),['Comparable Monthly Late Rate'],24,300,extra={'Tooltips':[mp('Eligible Deliveries'),mp('Late Deliveries')]})
        chart(s,'clusteredBarChart','Late-delivery rate by customer state',('fact_order','customer_state'),['Late Delivery Rate'],732,300)
        chart(s,'clusteredColumnChart','Reviews by delivery promise band',('fact_order','delay_band'),['Average Review Score'],24,602,h=290,extra={'Tooltips':[mp('Eligible Deliveries'),mp('Total Orders')]});insight(s)
        s=page('Delivery drivers',['Eligible Deliveries','Common Duration Orders','Common Processing Days','Common Shipping Days'])
        chart(s,'lineChart','Processing and shipping · same complete-timestamp sample',('dim_date','month'),['Common Processing Days','Common Shipping Days'],24,300)
        chart(s,'clusteredBarChart','Late-delivery rate by category · distinct order membership',('dim_category','category'),['Late Delivery Rate'],732,300,extra={'Tooltips':[mp('Eligible Deliveries'),mp('Late Deliveries')]})
        table(s,'Route investigation · customer states with counts and review context',[('fact_order','customer_state','Customer state')],['Eligible Deliveries','Late Deliveries','Late Delivery Rate','Common Processing Days','Common Shipping Days','Average Review Score'])
        s=page('Seller investigations',['Eligible Deliveries','Late Deliveries','On Time Review Score','Late Review Score'])
        chart(s,'clusteredBarChart','Late-delivery rate by seller state',('dim_seller','seller_state'),['Late Delivery Rate'],24,300,extra={'Tooltips':[mp('Eligible Deliveries')]})
        chart(s,'clusteredBarChart','Review score by product category',('dim_category','category'),['Average Review Score'],732,300,extra={'Tooltips':[mp('Reviewed Orders')]})
        table(s,'Seller review queue · ≥50 eligible orders and above peer late rate',[('dim_seller','seller_id','Seller ID'),('dim_seller','seller_state','State')],['Eligible Deliveries','Late Deliveries','Late Delivery Rate','Seller Excess Late pp','Average Review Score','Common Processing Days','Common Shipping Days'],flag='Seller Priority Flag')
    else:
        chart(s,'clusteredBarChart','Resolved default rate by grade',('dim_grade','grade'),['Default Rate'],24,300,extra={'Tooltips':[mp('Resolved Loans'),mp('Defaulted Loans')]})
        chart(s,'clusteredColumnChart','Cumulative net cash return by grade · not annualized',('dim_grade','grade'),['Net Return Proxy'],732,300,extra={'Tooltips':[mp('Resolved Funded Amount')]})
        chart(s,'lineChart','Resolved default rate by origination year',('fact_loan','issue_year'),['Default Rate'],24,602,h=290,extra={'Tooltips':[mp('Resolved Loans'),mp('Current Share')]});insight(s)
        s=page('Grades & vintages',['Resolved Loans','Resolved Coverage','Net Unreturned Principal','Recovery Rate'])
        visual(s,'scatterChart','Grade risk and return · bubble size = resolved funding',24,300,684,282,{'Category':[cp('dim_grade','grade')],'X':[mp('Default Rate')],'Y':[mp('Net Return Proxy')],'Size':[mp('Resolved Funded Amount')],'Tooltips':[mp('Resolved Loans')]})
        chart(s,'lineChart','Cumulative cash return by vintage · compare matched terms',('fact_loan','issue_year'),['Net Return Proxy'],732,300)
        table(s,'Grade outcomes · unresolved loans remain outside default and return rates',[('dim_grade','grade','Grade')],['Total Loans','Resolved Loans','Current Share','Default Rate','Resolved Funded Amount','Net Return Proxy','Recovery Rate'])
        s=page('Segment investigations',['Resolved Loans','Defaulted Loans','Average DTI','Average Interest Rate'])
        chart(s,'clusteredBarChart','Resolved default rate by DTI band',('fact_loan','dti_band'),['Default Rate'],24,300,extra={'Tooltips':[mp('Resolved Loans')]})
        chart(s,'clusteredBarChart','Resolved default rate by income band',('fact_loan','income_band'),['Default Rate'],732,300,extra={'Tooltips':[mp('Resolved Loans')]})
        table(s,'Purpose review queue · ≥200 resolved loans and above peer default rate',[('fact_loan','purpose','Loan purpose')],['Resolved Loans','Defaulted Loans','Default Rate','Segment Excess Default pp','Net Return Proxy','Average DTI','Average Interest Rate'],flag='Segment Review Flag')
    # A native text page provides the definitions and operating guidance without fake freshness.
    s=page('Definitions & use',cfg['cards'])
    lines=[('How to use this report','Start with Overview, use the three page filters, then compare drivers before opening the investigation queue. Click a chart mark to filter peer visuals. Clear a slicer or use Reset to default in the service to return to the full population.'),('Data and refresh','This is a historical source snapshot, not live operations. Run configure.py or Configure-DataPath.ps1 before opening the PBIP, then Refresh in Desktop. Refresh reloads local cleaned CSVs; it does not acquire new source data.'),('Metric policy',cfg['footer']),('Investigation policy','Queues shortlist records for review. Minimum sample thresholds are operational screening rules, not statistical significance or business targets. Filter context is retained; confirm maturity, denominator and missing coverage before decisions.'),('Release acceptance','JSON schemas, bindings, source totals and geometry are checked automatically. Power BI Desktop rendering, DAX execution, Service refresh and user acceptance must pass the included release checklist before production deployment.')]
    for i,(head,body) in enumerate(lines):
        text(s,head,32,302+i*112,1350,30,16);text(s,body,32,337+i*112,1350,72,13)
    write(d/'pages/pages.json',{'$schema':schema('pagesMetadata','1.0.0'),'pageOrder':pages,'activePageName':pages[0]})
    write(native/'report_manifest.json',{'project':cfg['id'],'pages':[{k:v for k,v in s.items() if k!='path'} for s in manifest],'metricExpressions':m})

def support(cfg,p,native,m):
    (native/'configure.py').write_text('''"""Configure the local data folder after cloning. No external dependencies."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
MODEL=next(Path(__file__).parent.glob("*.SemanticModel/model.bim"))
folder=ROOT/"02_Cleaned_Data"
if (folder/"fact_order.csv.gz.part001").exists() and not (folder/"fact_order.csv").exists():
    import runpy
    runpy.run_path(str(ROOT/"04_Python/restore_data.py"),run_name="__main__")
model=json.loads(MODEL.read_text(encoding="utf-8"))
model["model"]["expressions"][0]["expression"]='"'+str(folder).replace('"','""')+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
MODEL.write_text(json.dumps(model,indent=2)+"\\n",encoding="utf-8")
print("Configured:",folder)
print("Open the PBIP in Power BI Desktop and click Refresh.")
''',encoding='utf-8')
    (native/'Configure-DataPath.ps1').write_text('''$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$folder = Join-Path $root "02_Cleaned_Data"
if ((Test-Path (Join-Path $folder "fact_order.csv.gz.part001")) -and !(Test-Path (Join-Path $folder "fact_order.csv"))) {
  $target = Join-Path $folder "fact_order.csv"
  $combined = New-Object System.IO.MemoryStream
  Get-ChildItem (Join-Path $folder "fact_order.csv.gz.part*") | Sort-Object Name | ForEach-Object {
    $bytes = [IO.File]::ReadAllBytes($_.FullName); $combined.Write($bytes,0,$bytes.Length)
  }
  $combined.Position = 0
  $gzip = New-Object IO.Compression.GzipStream($combined,[IO.Compression.CompressionMode]::Decompress)
  $output = [IO.File]::Create($target)
  try {$gzip.CopyTo($output)} finally {$output.Dispose();$gzip.Dispose();$combined.Dispose()}
}
$modelFile = (Get-ChildItem (Join-Path $PSScriptRoot "*.SemanticModel/model.bim")).FullName
$model = Get-Content $modelFile -Raw | ConvertFrom-Json
$model.model.expressions[0].expression = '"' + $folder.Replace('"','""') + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
$json = $model | ConvertTo-Json -Depth 100
[IO.File]::WriteAllText($modelFile,$json,(New-Object Text.UTF8Encoding($false)))
Write-Host "Configured data path. Open the PBIP and Refresh."
''',encoding='utf-8')
    (native/'README.md').write_text(f'''# {cfg['title']} — native Power BI project

Open **{cfg['id']}.pbip** in a current Power BI Desktop installation. This package contains an actual semantic model and editable native report pages; the original analysis package remains available beside it.

## First open

1. Clone/download the complete repository, preserving folders.
2. Run `python 06_PowerBI/Native/configure.py`, or run `Configure-DataPath.ps1` from PowerShell. The Customer Experience setup restores its split order CSV automatically if needed.
3. Open `06_PowerBI/Native/{cfg['id']}.pbip`, select **Refresh**, and inspect all four pages. If prompted, enable Power BI project/report developer features supported by your Desktop release.
4. Save a PBIX copy from Desktop when needed. Publish to your own workspace after the release checks below pass.

## Report structure

- Overview: primary outcomes, trajectory, important driver comparison and filter-responsive context.
- Drivers: compatible cohorts/segments with counts and weighted ratios.
- Investigations: explicit sample thresholds and identifiable records for follow-up.
- Definitions & use: snapshot scope, denominators, refresh and acceptance guidance.

Three page-local slicers apply to that page. They intentionally reset scope when changing pages rather than silently carrying a hidden cross-page selection. Native chart selection filters peer visuals; use slicer clear controls to reset. Hover for denominators where provided. Table export includes the current context.

## Semantic model

Import mode, typed CSV sources, explicit DAX measures, and validated many-to-one relationships with single-direction filtering. All numeric raw columns have automatic summarization disabled. Dates use the supplied date dimension; automatic date tables are disabled. CX seller/category selection reaches order-grain measures via KEEPFILTERS/TREATAS, preventing item duplication. LendingClub return uses only resolved funding and resolved net cash. B2B date filters describe lead contact cohorts, not booking/revenue months.

Currency: {'USD' if cfg['fact']=='fact_loan' else 'BRL'}; return and rate measures are fractions with percentage formatting. No synthetic targets, unobserved spend/ROI, causal conclusions or FICO values are introduced. `{cfg['footer']}`.

## Validation and release status

See `validation.json` and `RELEASE_CHECKLIST.md`. JSON schema, field-binding, geometry, relationship and baseline-data checks run in the build environment. **No Power BI engine or Desktop is available here: report rendering and DAX execution are not certified.** Treat this as a release candidate until Desktop/Service checks pass. No .pbix or Service deployment is claimed.

Power BI project documentation: https://learn.microsoft.com/power-bi/developer/projects/projects-overview
Report format: https://learn.microsoft.com/power-bi/developer/projects/projects-report
Semantic models: https://learn.microsoft.com/power-bi/developer/projects/projects-dataset
''',encoding='utf-8')
    (native/'RELEASE_CHECKLIST.md').write_text('''# Release acceptance

## Automated build checks
- [x] JSON schemas checked against Microsoft published schemas.
- [x] Visual field references resolve to model fields and explicit measures.
- [x] Dimensions have unique keys; relationships have compatible types.
- [x] Card baselines reconciled to source CSVs.
- [x] Every visual stays inside the canvas; no peer visual overlap.

## Required Power BI Desktop checks — pending
- [ ] Configure local data path and Refresh without Power Query or relationship errors.
- [ ] Confirm baseline cards against validation.json and execute validation.dax.
- [ ] Test each slicer on a populated subgroup, clear back to All, and confirm all cards/charts/tables reconcile.
- [ ] CX: combine seller/category filters and confirm distinct order grain; compare priority queue with reviewed baselines.
- [ ] B2B: test contact-cohort filters and attributed seller-order scope; no converted-segment comparison is labeled lead conversion.
- [ ] Credit: filter year/grade/term; verify unresolved loans do not enter default/return denominators.
- [ ] Review all pages at Fit to page and 100%: labels, card text, legends, no clipping, keyboard order and contrast.
- [ ] Verify native chart role assignments, long category labels, tooltip denominators, queue measure filters and table sorting.
- [ ] Confirm empty selections show BLANK/empty state, never fabricated zero rates.
- [ ] Save a PBIX and reopen it; recheck report pages.

## Power BI Service checks — pending
- [ ] Publish to an authorized workspace and assign appropriate access.
- [ ] Configure an on-premises gateway for local CSV refresh, or deliberately migrate source queries to governed cloud storage.
- [ ] Test refresh credentials, failure notifications and refresh history; schedule only for a maintained source pipeline.
- [ ] Validate export permissions, accessibility and mobile layout; add RLS only if deploying non-public operational data.
- [ ] Obtain user acceptance before labeling this production-ready.
''',encoding='utf-8')
    (native/'validation.dax').write_text('EVALUATE\nROW(\n'+',\n'.join('    "'+n+'", ['+n+']' for n in cfg['cards'])+'\n)\n',encoding='utf-8')

if __name__=='__main__':
    for cfg in CONFIGS:
        p=ROOT/cfg['folder'];native=p/'06_PowerBI/Native';native.mkdir(parents=True,exist_ok=True)
        m=measures(cfg,p);make_model(cfg,p,native,m);make_report(cfg,p,native,m);support(cfg,p,native,m)
        print(cfg['id'],len(m),'measures',len(list(native.rglob('visual.json'))),'visuals')
