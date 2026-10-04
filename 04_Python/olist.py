import pandas as pd
import numpy as np
from common import Context,date_dimension,rate,statistical_compare

def load_olist(c,funnel=False):
    orders=c.read('olist_orders_dataset.csv','order_id',dates=['order_purchase_timestamp','order_approved_at','order_delivered_carrier_date','order_delivered_customer_date','order_estimated_delivery_date'])
    items=c.read('olist_order_items_dataset.csv',['order_id','order_item_id'],dates=['shipping_limit_date'],numeric=['price','freight_value'])
    sellers=c.read('olist_sellers_dataset.csv','seller_id');customers=c.read('olist_customers_dataset.csv','customer_id');products=c.read('olist_products_dataset.csv','product_id')
    payments=c.read('olist_order_payments_dataset.csv',['order_id','payment_sequential'],numeric=['payment_value'])
    for col,parent in [('order_id',orders),('seller_id',sellers),('product_id',products)]:c.fk(items,col,parent)
    c.fk(orders,'customer_id',customers);c.fk(payments,'order_id',orders)
    c.check('Nonnegative item price/freight',bool((items[['price','freight_value']].dropna()>=0).all().all()))
    c.add('dim_seller',sellers);c.add('dim_customer',customers);c.add('dim_product',products);c.add('fact_payment',payments)
    return orders,items,sellers,customers,products,payments

def funnel(root):
    c=Context(root);o,i,s,cu,p,pay=load_olist(c,True)
    m=c.read('olist_marketing_qualified_leads_dataset.csv','mql_id',dates=['first_contact_date'])
    deals=c.read('olist_closed_deals_dataset.csv','mql_id',dates=['won_date'],numeric=['declared_monthly_revenue'])
    c.check('One acquisition per converted seller',not deals.seller_id.duplicated().any());c.fk(deals,'mql_id',m);c.fk(deals,'seller_id',s,allow_unmatched=True)
    m['origin']=m.origin.fillna('unknown').str.lower()
    f=m.merge(deals,on='mql_id',how='left',validate='one_to_one').merge(s,on='seller_id',how='left',validate='many_to_one')
    f['converted']=f.won_date.notna().astype(int);f['close_days']=(f.won_date-f.first_contact_date).dt.total_seconds()/86400
    negative=f.close_days<0
    c.quality.append({'file':'lead close chronology','negative_durations':int(negative.sum()),'rule':'Negative lead-to-close duration excluded from speed KPI; converted flag and source won date retained'})
    f['invalid_close_chronology']=negative.astype(int);f['close_days']=f.close_days.mask(negative)
    # Commercial attribution is seller-item revenue, delivered orders purchased after acquisition only.
    eligible=i.merge(o[['order_id','order_status','order_purchase_timestamp']],on='order_id',validate='many_to_one').merge(deals[['seller_id','won_date']],on='seller_id',validate='many_to_one')
    eligible=eligible[(eligible.order_status=='delivered')&(eligible.order_purchase_timestamp>=eligible.won_date)].copy()
    seller_orders=eligible.groupby(['seller_id','order_id','order_purchase_timestamp'],as_index=False).agg(gmv=('price','sum'))
    aggregate=seller_orders.groupby('seller_id').agg(orders=('order_id','nunique'),gmv=('gmv','sum'),first_sale=('order_purchase_timestamp','min'))
    f=f.merge(aggregate,on='seller_id',how='left',validate='many_to_one');f[['orders','gmv']]=f[['orders','gmv']].fillna(0);f['orders']=f.orders.astype(int)
    f['active']=(f.orders>0).astype(int);f['repeat_seller']=(f.orders>=2).astype(int);f['close_to_first_sale_days']=(f.first_sale-f.won_date).dt.total_seconds()/86400
    active=f[f.active==1];v=active.gmv.median();freq=active.orders.median()
    f['seller_segment']=np.select([f.active==0,(f.gmv>=v)&(f.orders>=freq),f.gmv>=v,f.orders>=freq],['Not activated','High Value / High Frequency','High Value / Low Frequency','Low Value / High Frequency'],default='Low Value / Low Frequency')
    f['lead_month']=f.first_contact_date.dt.strftime('%Y-%m');f['close_month']=f.won_date.dt.strftime('%Y-%m')
    f['contact_date']=f.first_contact_date.dt.strftime('%Y-%m-%d');f['close_date']=f.won_date.dt.strftime('%Y-%m-%d');seller_orders['purchase_date']=seller_orders.order_purchase_timestamp.dt.strftime('%Y-%m-%d')
    for col,name in [('origin','dim_channel'),('business_segment','dim_segment'),('sdr_id','dim_sdr'),('sr_id','dim_sales_rep')]:c.add(name,f[[col]].dropna().drop_duplicates())
    c.add('fact_lead',f);c.add('fact_seller_order',seller_orders);c.add('dim_date',date_dimension(o.order_purchase_timestamp.min().normalize(),max(o.order_purchase_timestamp.max(),m.first_contact_date.max()).normalize()))
    c.check('Funnel row preservation',len(f)==len(m));c.check('Attribution reconciles',np.isclose(f.gmv.sum(),eligible.price.sum()));c.check('Stages monotonic',f.repeat_seller.sum()<=f.active.sum()<=f.converted.sum()<=len(f))
    c.run_sql();channels=c.results['channel_quality'];top=channels.sort_values('gmv_per_lead',ascending=False).query('leads >= 50')
    ranked=active.sort_values('gmv',ascending=False);n=max(1,int(np.ceil(len(ranked)*.1)));share=rate(ranked.head(n).gmv.sum(),ranked.gmv.sum())
    c.findings=[f'{len(f):,} MQLs produced {f.converted.sum():,} closed deals ({f.converted.mean():.2%} conversion).',f'{f.active.sum():,} converted sellers had delivered orders purchased after closing ({rate(f.active.sum(),f.converted.sum()):.2%} activation).',f'Attributed item GMV was BRL {f.gmv.sum():,.2f}; this is marketplace merchandise value, not Olist net revenue.',f'Top {n} active sellers (ceiling of 10%) contributed {share:.2%} of attributed GMV.',f'{f.repeat_seller.sum():,} sellers generated at least two post-close delivered orders.']
    if len(top):c.findings.append(f'{top.iloc[0].origin} had the highest observed GMV per lead among channels with at least 50 MQLs: BRL {top.iloc[0].gmv_per_lead:,.2f}.')
    c.recommendations=['Use observed GMV per lead together with activation to shortlist channel experiments; acquire spend data before claiming ROI.','Prioritize onboarding for converted sellers without post-close delivered orders. Separate recent wins from fully observed cohorts.','Inspect the largest seller accounts individually because concentration makes channel results sensitive to a few merchants.','Obtain assignment histories for lost leads before measuring SDR or sales-representative conversion rates.']
    groups=f.origin.value_counts().head(2).index
    c.root.joinpath('08_Documentation/statistical_test.json').write_text(__import__('json').dumps(statistical_compare(f.loc[f.origin==groups[0],'converted'],f.loc[f.origin==groups[1],'converted']),indent=2))
    c.bar(channels.sort_values('gmv_per_lead',ascending=False),'origin','gmv_per_lead','Observed post-close GMV per MQL (BRL)','channel_value.png')
    c.bar(c.results['funnel_stages'],'stage','sellers','Acquisition funnel; activation equals first observed sale','funnel.png')
    c.bar(c.results['sales_rep_value'],'sr_id','gmv','Delivered item GMV by acquisition representative','sales_value.png')
    c.bar(c.results['seller_segments'],'seller_segment','gmv','Active seller value segments; median thresholds','seller_segments.png')
    c.export_audit();return c

def experience(root):
    c=Context(root);o,i,s,cu,p,pay=load_olist(c)
    reviews=c.read('olist_order_reviews_dataset.csv',dates=['review_creation_date','review_answer_timestamp'],numeric=['review_score'])
    c.fk(reviews,'order_id',o);c.check('Review scores within 1-5',reviews.review_score.dropna().between(1,5).all())
    # Latest response wins deterministically; review ids can legitimately recur across orders.
    r=reviews.sort_values(['order_id','review_answer_timestamp','review_creation_date','review_id'],na_position='first').drop_duplicates('order_id',keep='last')
    c.quality.append({'file':'review selection','original_rows':len(reviews),'cleaned_rows':len(r),'rule':'Latest response then creation then review_id; one review per order; retain raw review history'})
    trans=c.read('product_category_name_translation.csv','product_category_name')
    geo=c.read('olist_geolocation_dataset.csv',numeric=['geolocation_lat','geolocation_lng'])
    valid=geo.geolocation_lat.between(-90,90)&geo.geolocation_lng.between(-180,180)
    g=geo.loc[valid].groupby('geolocation_zip_code_prefix',as_index=False).agg(latitude=('geolocation_lat','median'),longitude=('geolocation_lng','median'))
    c.quality.append({'file':'geolocation','original_rows':len(geo),'cleaned_rows':len(g),'rule':'Median lat/lng by postal prefix after global coordinate range checks; prefix records are many-to-one'})
    sums=i.groupby('order_id',as_index=False).agg(gmv=('price','sum'),freight=('freight_value','sum'),items=('order_item_id','count'))
    ps=pay.groupby('order_id',as_index=False).agg(payment_value=('payment_value','sum'))
    f=o.merge(sums,on='order_id',how='left',validate='one_to_one').merge(ps,on='order_id',how='left',validate='one_to_one').merge(cu,on='customer_id',validate='many_to_one').merge(r[['order_id','review_score']],on='order_id',how='left',validate='one_to_one')
    f['cancelled']=(f.order_status=='canceled').astype(int);f['delivered']=(f.order_status=='delivered').astype(int)
    f['eligible_delivery']=((f.delivered==1)&f.order_delivered_customer_date.notna()&f.order_estimated_delivery_date.notna()).astype(int)
    actual=f.order_delivered_customer_date.dt.normalize();estimate=f.order_estimated_delivery_date.dt.normalize()
    f['delay_days']=(actual-estimate).dt.days.where(f.eligible_delivery==1)
    f['late']=np.where(f.eligible_delivery==1,(f.delay_days>0).astype(int),np.nan)
    for name,a,b in [('processing_days','order_delivered_carrier_date','order_approved_at'),('shipping_days','order_delivered_customer_date','order_delivered_carrier_date'),('delivery_days','order_delivered_customer_date','order_purchase_timestamp')]:
        d=(f[a]-f[b]).dt.total_seconds()/86400;invalid=d<0;f[name]=d.mask(invalid).where(f.delivered==1);c.quality.append({'file':name,'negative_duration_excluded':int(invalid.sum()),'rule':'Negative timestamp intervals -> NULL independently; retain order in denominators'})
    f['delay_band']=np.select([f.delay_days.isna(),f.delay_days<0,f.delay_days==0,f.delay_days<=3,f.delay_days<=7],['Unknown','Early','On estimate day','1-3 late','4-7 late'],default='8+ late')
    f['purchase_month']=f.order_purchase_timestamp.dt.strftime('%Y-%m')
    f['purchase_date']=f.order_purchase_timestamp.dt.strftime('%Y-%m-%d')
    bridge=i[['order_id','seller_id','product_id','price','freight_value']].merge(p[['product_id','product_category_name']],on='product_id',validate='many_to_one').merge(trans,on='product_category_name',how='left',validate='many_to_one').merge(s[['seller_id','seller_state']],on='seller_id',validate='many_to_one')
    # Collapse to one row per order/seller/category; never sum duplicated order KPIs across bridge rows.
    bridge['category']=bridge.product_category_name_english.fillna(bridge.product_category_name).fillna('unknown')
    bridge=bridge.groupby(['order_id','seller_id','seller_state','category'],dropna=False,as_index=False).agg(item_gmv=('price','sum'),item_freight=('freight_value','sum'))
    c.add('dim_category',bridge[['category']].drop_duplicates())
    perf=bridge[['order_id','seller_id']].drop_duplicates().merge(f[['order_id','eligible_delivery','late','review_score','processing_days','shipping_days']],on='order_id',validate='many_to_one').groupby('seller_id',as_index=False).agg(orders=('order_id','nunique'),eligible=('eligible_delivery','sum'),late_rate=('late','mean'),review_score=('review_score','mean'),processing_days=('processing_days','mean'),shipping_days=('shipping_days','mean'))
    vol=perf.orders.median();base=f.late.mean();perf['segment']=np.where(perf.orders>=vol,'High Volume / ','Low Volume / ')+np.where(perf.late_rate<=base,'Reliable','Problematic');perf.loc[perf.eligible<20,'segment']='Insufficient eligible orders'
    c.add('fact_order',f);c.add('bridge_order_seller_category',bridge);c.add('seller_performance',perf);c.add('dim_geography',g);c.add('dim_date',date_dimension(o.order_purchase_timestamp.min().normalize(),o.order_purchase_timestamp.max().normalize()))
    c.check('Order grain preserved',len(f)==len(o));c.check('Order GMV reconciles with items',np.isclose(f.gmv.sum(),i.price.sum()));c.check('Order payments reconcile',np.isclose(f.payment_value.sum(),pay.payment_value.sum()))
    c.run_sql();on=f.loc[f.late==0,'review_score'];late=f.loc[f.late==1,'review_score'];worst=c.results['seller_priority'];bottleneck=f[['processing_days','shipping_days']].mean()
    c.findings=[f'{len(f):,} orders; {f.delivered.sum():,} delivered; {f.cancelled.sum():,} cancelled ({f.cancelled.mean():.2%}).',f'{f.eligible_delivery.sum():,} orders had valid delivery and estimated dates; {f.late.mean():.2%} were late by calendar date.',f'Mean review was {on.mean():.2f} for on-time orders versus {late.mean():.2f} for late orders; association does not establish causation.',f'Mean processing time was {bottleneck.processing_days:.2f} days and mean shipping time was {bottleneck.shipping_days:.2f} days; available-timestamp samples differ.',f'{len(worst):,} sellers met the priority rule: at least 50 eligible orders and a late rate above the portfolio rate.',f'{f.review_score.notna().sum():,} orders had a selected review; overall mean score was {f.review_score.mean():.2f}.']
    c.recommendations=['Audit high-volume sellers with above-baseline late rates first; verify carrier handoff records and inventory availability before attributing responsibility.','Compare processing and shipping separately on the same complete-timestamp sample before assigning an operational intervention.','Test revised delivery estimates on routes with persistent positive delays; track both promise accuracy and total transit time.','Use matched-route comparisons or controlled operational experiments to evaluate improvements in reviews.']
    cols=['delay_days','review_score','freight','gmv','processing_days','shipping_days','delivery_days'];corr=f[cols].corr(method='spearman');corr.to_csv(c.root/'08_Documentation/spearman_correlations.csv')
    c.root.joinpath('08_Documentation/statistical_test.json').write_text(__import__('json').dumps(statistical_compare(on,late),indent=2))
    c.bar(c.results['delay_review'],'delay_band','review_score','Order reviews by calendar delivery delay','delivery_reviews.png');c.bar(c.results['state_delivery'].sort_values('delivery_days',ascending=False),'customer_state','delivery_days','Mean delivery duration by customer state','state_delivery.png')
    c.bar(c.results['status_mix'],'order_status','orders','Order status distribution','order_status.png');c.bar(c.results['stage_times'],'stage','days','Mean stage durations; valid nonnegative intervals','stage_times.png');c.export_audit();return c
