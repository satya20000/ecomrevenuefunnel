import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root=process.argv[2] || '/workspace/scratch/76b94980ee6d/Data_Analytics_Portfolio';
const projects=['01_Olist_B2B_Revenue_Funnel','02_KKBOX_Subscription_Analytics','03_LendingClub_Credit_Portfolio','04_Olist_Customer_Experience'];
const titles=['Channel quality comparison','Subscription analysis template','Credit grade comparison','Delivery and review comparison'];
const col=n=>{let r='';for(n++;n;n=Math.floor((n-1)/26))r=String.fromCharCode(65+(n-1)%26)+r;return r;};
const header={fill:'#253D66',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'}};

for(let j=0;j<4;j++){
 const single=projects.findIndex(p=>path.basename(root)===p);
 if(single>=0 && j!==single) continue;
 if(process.argv[3] && Number(process.argv[3])!==j) continue;
 const dir=single>=0?root:path.join(root,projects[j]);let data={};
 try{data=JSON.parse(await fs.readFile(path.join(dir,'05_Excel/workbook_data.json'),'utf8'));}catch{}
 const wb=Workbook.create();const analysis=wb.worksheets.add('Analysis');analysis.showGridLines=false;
 analysis.getRange('B2').values=[[titles[j]]];analysis.getRange('B2').format.font={name:'Arial',size:16,bold:true,color:'#14243A'};
 analysis.getRange('B3').values=[[j===1?'Waiting for original KKBOX v1 data. Empty inputs are not measured zeroes.':'Historical source analysis. Raw data and detailed records are in the accompanying CSV files.']];
 analysis.getRange('B3').format.font={name:'Arial',size:10,color:'#5B687B'};
 analysis.getRange('B5:C5').values=[['Measure','Value']];analysis.getRange('B5:C5').format=header;
 analysis.getRange('B:C').format.columnWidth=32;analysis.getRange('D:I').format.columnWidth=22;analysis.getRange('B5:I45').format.font.name='Arial';analysis.getRange('B5:I45').format.font.size=10;
 const selected=[['channel_quality','seller_segments','monthly_leads','seller_pareto'],[],['grade_risk_return','vintage','purpose_risk','recovery'],['portfolio_kpis','delay_review','delivery_trend','seller_priority']][j];
 const maps={};
 for(const key of selected){
   const obj=data[key];if(!obj)continue;
   const name=key.slice(0,31);const sh=wb.worksheets.add(name);sh.showGridLines=false;maps[key]=sh;
   sh.getRange('A2').values=[[key.replaceAll('_',' ')]];sh.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#14243A'};
   sh.getRange('A3').values=[['Source: 03_SQL/results/'+key+'.csv. Complete query result; original historical currency.']];
   const matrix=[obj.columns,...obj.data];const end=col(obj.columns.length-1);sh.getRange(`A5:${end}${matrix.length+4}`).values=matrix;
   sh.getRange(`A5:${end}5`).format=header;sh.getRange(`A6:${end}${matrix.length+4}`).format.font={name:'Arial',size:10};
   sh.getRange(`A5:${end}${matrix.length+4}`).format.columnWidth=20;sh.getRange('A:A').format.columnWidth=30;sh.getRange(`A5:${end}5`).format.wrapText=true;sh.getRange(`A5:${end}5`).format.rowHeight=34;sh.freezePanes.freezeRows(5);
   sh.tables.add(`A5:${end}${matrix.length+4}`,true,'T_'+key);
   obj.columns.forEach((c,i)=>{if(/rate|share|return_proxy/.test(c))sh.getRange(`${col(i)}6:${col(i)}${matrix.length+4}`).setNumberFormat('0.0%');else if(obj.data.some(row=>typeof row[i]==='number'))sh.getRange(`${col(i)}6:${col(i)}${matrix.length+4}`).setNumberFormat(/year|loans|leads|sellers|orders|reviewed|eligible|rank|closed|defaulted|observations|current$/.test(c)?'#,##0':'#,##0.00;(#,##0.00);-');});
   const prev=await wb.render({sheetName:name,range:`A2:${col(Math.min(obj.columns.length-1,7))}${Math.min(matrix.length+4,18)}`,scale:1,format:'png'});
   await fs.writeFile(path.join(dir,'07_Images',`excel_${key}.png`),new Uint8Array(await prev.arrayBuffer()));
 }
 let rows=[];
 if(j===0){
  const n=data.channel_quality.data.length;const end=n+5;rows=[['Total MQLs',`=SUM(channel_quality!B6:B${end})`],['Closed deals',`=SUM(channel_quality!C6:C${end})`],['Conversion rate','=C7/C6'],['Attributed GMV (BRL)',`=SUM(channel_quality!G6:G${end})`],['GMV per lead (BRL)','=C9/C6'],['Active sellers',`=SUM(channel_quality!E6:E${end})`],['Activation rate','=C11/C7']];
  analysis.getRange('F6:G6').values=[['Minimum lead count',50]];analysis.getRange('G6').format.fill='#FFF0BF';analysis.getRange('G6').format.font.color='#315AA8';
  analysis.getRange('B15:H15').values=[['Channel','Leads','Wins','Conversion','GMV per lead','Activation','Sample flag']];analysis.getRange('B15:H15').format=header;
  const formulas=[];for(let r=0;r<n;r++){let s=r+6,o=r+16;formulas.push([`=channel_quality!A${s}`,`=channel_quality!B${s}`,`=channel_quality!C${s}`,`=D${o}/C${o}`,`=channel_quality!G${s}/C${o}`,`=channel_quality!E${s}/D${o}`,`=IF(C${o}>=$G$6,"Review eligible","Small sample")`]);}
  analysis.getRange(`B16:H${15+n}`).formulas=formulas;analysis.getRange(`E16:E${15+n}`).setNumberFormat('0.0%');analysis.getRange(`G16:G${15+n}`).setNumberFormat('0.0%');analysis.getRange(`F16:F${15+n}`).setNumberFormat('"BRL "#,##0.00');analysis.getRange(`H16:H${15+n}`).conditionalFormats.add('containsText',{text:'Small sample',format:{fill:'#FFF0BF'}});
  const chart=analysis.charts.add('bar',[analysis.getRange(`B15:B${15+n}`),analysis.getRange(`F15:F${15+n}`)]);chart.title='GMV per lead (BRL)';chart.hasLegend=false;chart.setPosition('J5','S24');
  analysis.getRange('B30').values=[['Compare won-lead value; SDR and representative conversion denominators are unavailable.']];
 }else if(j===2){
  const n=data.grade_risk_return.data.length;const end=n+5;rows=[['Total loans',`=SUM(grade_risk_return!B6:B${end})`],['Funded amount (USD)',`=SUM(grade_risk_return!D6:D${end})`],['Resolved loans',`=SUM(grade_risk_return!C6:C${end})`],['Current share','=1-C8/C6']];
  analysis.getRange('B15:F15').values=[['Grade','Default rate','Coupon rate','Net cash return','Funding share']];analysis.getRange('B15:F15').format=header;
  let fm=[];for(let r=0;r<n;r++){const s=r+6;fm.push([`=grade_risk_return!A${s}`,`=grade_risk_return!E${s}`,`=grade_risk_return!F${s}`,`=grade_risk_return!I${s}`,`=grade_risk_return!D${s}/$C$7`]);}
  analysis.getRange(`B16:F${15+n}`).formulas=fm;analysis.getRange(`C16:F${15+n}`).setNumberFormat('0.0%');analysis.getRange(`C16:C${15+n}`).conditionalFormats.add('colorScale',{colors:['#E8EEF7','#315AA8'],thresholds:['min','max']});
  const chart=analysis.charts.add('column',analysis.getRange(`B15:C${15+n}`));chart.title='Resolved default rate by grade';chart.hasLegend=false;chart.setPosition('H14','P29');
  analysis.getRange('B31').values=[['Net cash return is cumulative, not annualized. FICO is absent from this release.']];
 }else if(j===3){
  rows=[['Total orders','=portfolio_kpis!A6'],['Delivered','=portfolio_kpis!B6'],['Cancelled','=portfolio_kpis!C6'],['Cancellation rate','=C8/C6'],['Late delivery rate','=portfolio_kpis!E6'],['Average review score','=portfolio_kpis!J6']];
  analysis.getRange('B15:F15').values=[['Delay band','Orders','Reviewed','Mean score','1-star rate']];analysis.getRange('B15:F15').format=header;
  const n=data.delay_review.data.length;let fm=[];for(let r=0;r<n;r++){const s=r+6;fm.push([`=delay_review!A${s}`,`=delay_review!B${s}`,`=delay_review!C${s}`,`=delay_review!D${s}`,`=delay_review!E${s}`]);}analysis.getRange(`B16:F${15+n}`).formulas=fm;analysis.getRange(`E16:E${15+n}`).setNumberFormat('0.00');analysis.getRange(`F16:F${15+n}`).setNumberFormat('0.0%');
  const chart=analysis.charts.add('column',[analysis.getRange(`B15:B${15+n}`),analysis.getRange(`E15:E${15+n}`)]);chart.title='Review score by delivery band';chart.hasLegend=false;chart.setPosition('H14','P29');
  analysis.getRange('B31').values=[['Delivery delay and reviews are associated; these comparisons do not prove causation.']];
 }else{
  const input=wb.worksheets.add('Monthly inputs');input.showGridLines=false;input.getRange('A2').values=[['Paste monthly_metrics.csv after running the KKBOX pipeline.']];input.getRange('A5:F5').values=[['Month','Active','Previous active','Lost','Retained','MRR proxy (NTD)']];input.getRange('A5:F5').format=header;input.getRange('A6:F17').format.fill='#FFF0BF';input.getRange('A5:F17').format.columnWidth=23;
  rows=[['Active stock (first input month)','=IF(COUNT(\'Monthly inputs\'!B6)=0,"Missing data",\'Monthly inputs\'!B6)'],['Weighted stock churn rate','=IF(OR(COUNT(\'Monthly inputs\'!C6:C17)=0,COUNT(\'Monthly inputs\'!C6:C17)<>COUNT(\'Monthly inputs\'!D6:D17)),"Missing data",IF(SUM(\'Monthly inputs\'!C6:C17)=0,"Undefined",SUM(\'Monthly inputs\'!D6:D17)/SUM(\'Monthly inputs\'!C6:C17)))']];
  analysis.getRange('B14').values=[['No KKBOX data, measured findings or populated analytical workbook is claimed.']];
  const img=await wb.render({sheetName:'Monthly inputs',range:'A2:F17',scale:1,format:'png'});await fs.writeFile(path.join(dir,'07_Images/excel_monthly_inputs.png'),new Uint8Array(await img.arrayBuffer()));
 }
 rows.forEach(([label,formula],i)=>{analysis.getRange(`B${i+6}`).values=[[label]];analysis.getRange(`C${i+6}`).formulas=[[formula]];analysis.getRange(`C${i+6}`).setNumberFormat(/rate|share/i.test(label)?'0.0%':/review/.test(label)?'0.00':/loans|MQLs|deals|sellers|stock|orders|Delivered|Cancelled/.test(label)?'#,##0':'#,##0.00');});
 analysis.getRange('B15:H15').format.wrapText=true;analysis.getRange('B15:H15').format.rowHeight=35;
 wb.recalculate();
 const qa=[];const assert=(label,cond)=>{qa.push({check:label,passed:!!cond});if(!cond)throw new Error(label);};
 if(j===0){const old=maps.channel_quality.getRange('B6').values[0][0];const before=analysis.getRange('C6').values[0][0];maps.channel_quality.getRange('B6').values=[[old+1]];wb.recalculate();assert('Lead input change updates total MQLs',analysis.getRange('C6').values[0][0]===before+1);maps.channel_quality.getRange('B6').values=[[old]];analysis.getRange('G6').values=[[10000]];wb.recalculate();assert('Editable sample threshold updates classification',analysis.getRange('H16').values[0][0]==='Small sample');analysis.getRange('G6').values=[[50]];}
 if(j===1){const input=wb.worksheets.getItem('Monthly inputs');input.getRange('C6').values=[[100]];wb.recalculate();assert('Missing lost count remains missing',analysis.getRange('C7').values[0][0]==='Missing data');input.getRange('D6').values=[[0]];wb.recalculate();assert('Observed zero loss gives zero churn',analysis.getRange('C7').values[0][0]===0);input.getRange('C6').values=[[0]];wb.recalculate();assert('Zero denominator remains undefined',analysis.getRange('C7').values[0][0]==='Undefined');input.getRange('C6:D6').clear({applyTo:'contents'});}
 if(j===2){const old=maps.grade_risk_return.getRange('D6').values[0][0];const total=analysis.getRange('C7').values[0][0];maps.grade_risk_return.getRange('D6').values=[[old+100]];wb.recalculate();assert('Funding input changes portfolio funding',analysis.getRange('C7').values[0][0]===total+100);maps.grade_risk_return.getRange('D6').values=[[old]];}
 if(j===3){const old=maps.delay_review.getRange('D6').values[0][0];maps.delay_review.getRange('D6').values=[[1]];wb.recalculate();assert('Review source edits update comparison',analysis.getRange('E16').values[0][0]===1);maps.delay_review.getRange('D6').values=[[old]];}
 wb.recalculate();await fs.writeFile(path.join(dir,'08_Documentation/workbook_validation.json'),JSON.stringify(qa,null,2));
 console.log(projects[j],(await wb.inspect({kind:'table',range:'Analysis!B5:C12',include:'values,formulas',tableMaxRows:8,tableMaxCols:2,maxChars:1800})).ndjson);
 console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!',options:{useRegex:true,maxResults:15},maxChars:1000})).ndjson);
 const img=await wb.render({sheetName:'Analysis',range:j===1?'B2:H16':'B2:S33',scale:1,format:'png'});await fs.writeFile(path.join(dir,'07_Images/excel_analysis.png'),new Uint8Array(await img.arrayBuffer()));
 const out=await SpreadsheetFile.exportXlsx(wb);await out.save(path.join(dir,'05_Excel',j===1?'analysis_template.xlsx':'analysis.xlsx'));
}
