"""Shared reproducible analytics utilities. No synthetic portfolio data."""
from pathlib import Path
import json, hashlib, sqlite3, re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

class Context:
    def __init__(self, root):
        self.root=Path(root); self.raw=self.root/'01_Raw_Data';self.clean=self.root/'02_Cleaned_Data'
        self.quality=[];self.manifest=[];self.tables={};self.results={};self.findings=[];self.recommendations=[];self.tests=[]
        for name in ['02_Cleaned_Data','03_SQL/results','07_Images','08_Documentation']:(self.root/name).mkdir(parents=True,exist_ok=True)
    def read(self, filename, key=None, dates=(), numeric=(), optional=False):
        path=self.raw/filename
        if not path.exists():
            if optional:return None
            raise FileNotFoundError(f'Required source file missing: {path}')
        h=hashlib.sha256()
        with path.open('rb') as f:
            for b in iter(lambda:f.read(2**20),b''):h.update(b)
        self.manifest.append({'file':filename,'bytes':path.stat().st_size,'sha256':h.hexdigest()})
        d=pd.read_csv(path,low_memory=False);n=len(d);missing=d.isna().sum().to_dict();dupes=int(d.duplicated().sum());d=d.drop_duplicates().copy()
        for c in d.select_dtypes('object'):
            d[c]=d[c].map(lambda v:v.strip() if isinstance(v,str) else v).replace('',np.nan)
        invalid={}
        for c in dates:
            if c in d:
                original=d[c].notna();d[c]=pd.to_datetime(d[c],errors='coerce',format='mixed');invalid[c]=int((original&d[c].isna()).sum())
        for c in numeric:
            if c in d:
                original=d[c].notna();d[c]=pd.to_numeric(d[c].astype(str).str.replace('%','',regex=False),errors='coerce');invalid[c]=int((original&d[c].isna()).sum())
        if key:
            cols=[key] if isinstance(key,str) else key
            if d[cols].isna().any().any():raise ValueError(f'{filename}: null primary key')
            if d.duplicated(cols).any():raise ValueError(f'{filename}: conflicting duplicate primary key; investigate before proceeding')
        self.quality.append({'file':filename,'original_rows':n,'cleaned_rows':len(d),'exact_duplicates_removed':dupes,'nulls_before':json.dumps(missing),'parse_failures':json.dumps(invalid),'rule':'Trim strings; preserve unknown numeric values as NULL; remove exact duplicate rows only; conflicting keys fail'})
        return d
    def check(self,name,condition):
        self.tests.append({'check':name,'passed':bool(condition)})
        if not condition:raise AssertionError(name)
    def fk(self,child,col,parent,pcol=None,allow_unmatched=False):
        pcol=pcol or col;bad=int((child[col].notna()&~child[col].isin(parent[pcol])).sum())
        self.quality.append({'file':f'FK {col} -> {pcol}','original_rows':len(child),'cleaned_rows':len(child),'unmatched_rows':bad,'rule':'Retain unmatched seller acquisitions for activation denominator' if allow_unmatched else 'Fail on unmatched non-null foreign key'})
        if not allow_unmatched:self.check(f'FK {col}',bad==0)
    def add(self,name,d):
        d=d.copy()
        for c in d.select_dtypes(include=['datetime64[ns]']):d[c]=d[c].dt.strftime('%Y-%m-%d %H:%M:%S')
        self.tables[name]=d
        d.to_csv(self.clean/f'{name}.csv',index=False)
    def run_sql(self):
        db=self.root/'03_SQL/analysis.sqlite';db.unlink(missing_ok=True)
        with sqlite3.connect(db) as con:
            schema=[]
            for name,d in self.tables.items():
                types={c:('INTEGER' if pd.api.types.is_integer_dtype(d[c]) or pd.api.types.is_bool_dtype(d[c]) else 'REAL' if pd.api.types.is_numeric_dtype(d[c]) else 'TEXT') for c in d}
                cols=',\n '.join(f'"{c}" {t}' for c,t in types.items());schema.append(f'CREATE TABLE "{name}" (\n {cols}\n);')
                con.execute(schema[-1]);d.to_sql(name,con,if_exists='append',index=False)
            (self.root/'03_SQL/schema.sql').write_text('-- SQLite 3.25+; populated by pipeline.py, CSV dates are ISO strings.\n'+'\n\n'.join(schema))
            for file in ['data_cleaning.sql','exploratory_analysis.sql','business_analysis.sql','advanced_analysis.sql']:
                content=(self.root/'03_SQL'/file).read_text()
                for name,query in re.findall(r'-- name: ([\w]+)\n(.*?);',content,re.S):
                    result=pd.read_sql_query(query,con);self.results[name]=result;result.to_csv(self.root/'03_SQL/results'/f'{name}.csv',index=False)
            self.check('SQLite integrity_check',con.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
    def export_audit(self):
        pd.DataFrame(self.quality).to_csv(self.root/'08_Documentation/data_quality_summary.csv',index=False)
        (self.root/'08_Documentation/source_manifest.json').write_text(json.dumps(self.manifest,indent=2))
        (self.root/'08_Documentation/validation.json').write_text(json.dumps(self.tests,indent=2))
        rows=[]
        meanings={'gmv':'Sum of item prices in BRL; excludes freight and platform commission','orders':'Distinct order count at stated table grain','review_score':'Selected order review, 1 to 5','late':'Delivered later than estimated calendar date, unknown is NULL','eligible_delivery':'Delivered with valid actual and estimate dates','default_flag':'1 for Charged Off/Default, 0 for Fully Paid, NULL for unresolved loans','resolved':'Fully Paid or Charged Off/Default','net_cash':'total_pymnt minus collection_recovery_fee minus funded_amnt; recovery already included in total_pymnt','cohort_month':'First observed paid subscription month, not guaranteed first-ever acquisition','mrr_proxy':'NTD month-end contracted daily-rate equivalent times 30.4375; not accounting MRR'}
        for name,d in self.tables.items():
            for c in d:rows.append({'field':c,'source_table':name,'data_type':str(d[c].dtype),'meaning':meanings.get(c,c.replace('_',' ').capitalize()),'transformation':'See pipeline.py and metric_definitions.md; NULL is unknown unless explicitly a structural zero'})
        pd.DataFrame(rows).to_csv(self.root/'08_Documentation/data_dictionary.csv',index=False)
        (self.root/'08_Documentation/findings.json').write_text(json.dumps({'findings':self.findings,'recommendations':self.recommendations},indent=2))
        # All result tables feed workbook authoring; no fabricated seed values.
        obj={k:json.loads(v.replace([np.inf,-np.inf],np.nan).to_json(orient='split',index=False)) for k,v in self.results.items() if len(v)<=5000}
        (self.root/'05_Excel/workbook_data.json').write_text(json.dumps(obj))
    def bar(self,data,x,y,title,filename):
        fig,ax=plt.subplots(figsize=(10,5));data=data.dropna(subset=[y]).head(15)
        ax.barh(data[x].astype(str),data[y],color='#315AA8');ax.invert_yaxis();ax.set_title(title,loc='left',fontsize=15);ax.set_xlabel(y.replace('_',' '));ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(self.root/'07_Images'/filename,dpi=150);plt.close(fig)

def date_dimension(start,end):
    d=pd.DataFrame({'date':pd.date_range(start,end,freq='D')});d['year']=d.date.dt.year;d['month']=d.date.dt.strftime('%Y-%m');d['quarter']=d.date.dt.quarter;d['month_number']=d.date.dt.month;d['date']=d.date.dt.strftime('%Y-%m-%d');return d

def rate(a,b):return a/b if b else np.nan

def statistical_compare(a,b):
    a=pd.Series(a).dropna();b=pd.Series(b).dropna()
    if len(a)<30 or len(b)<30:return {'status':'Insufficient observations; at least 30 per group required','n_a':len(a),'n_b':len(b)}
    r=stats.mannwhitneyu(a,b,alternative='two-sided');return {'test':'Mann-Whitney U, descriptive association, exploratory','n_a':len(a),'n_b':len(b),'mean_a':float(a.mean()),'mean_b':float(b.mean()),'p_value':float(r.pvalue),'caution':'Unadjusted for confounding and multiple comparisons. No causal interpretation.'}
