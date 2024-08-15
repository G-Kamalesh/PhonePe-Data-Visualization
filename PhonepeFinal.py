import streamlit as st
import json 
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px
import os
import folium
import geopandas as gpd
from streamlit_folium import st_folium
import mysql.connector
import locale
locale.setlocale(locale.LC_ALL,'en_IN.UTF-8')

#func to iterate over folders
def data_path(fname,sf_name):
    root = r"K:\data\pulse-master\data"
    folder_list = os.listdir(root) 
    state_path  =None

    for folder_name in folder_list: 
        if folder_name == fname: 
            folder_path = os.path.join(root,folder_name) 
            for sub_folder in os.listdir(folder_path):
                if sub_folder == sf_name:
                    r = os.path.join(folder_path,sub_folder)
                    for y in os.listdir(r):
                        if y == "state":
                            state_path = os.path.join(r,y)
    return state_path

#func to clean the df
def cleaning(d):
    
    df = pd.DataFrame(d)
    def change(df):
        df['State']=df['State'].replace("andaman-&-nicobar-islands","Andaman & Nicobar")
        df['State']=df['State'].str.replace("-"," ")
        df['State'] =df['State'].replace('dadra & nagar haveli & daman & diu','dadra & nagar haveli and daman & diu')
        df['State'] =df['State'].str.title()
        return df

    try:
        if df.isnull().sum() == 0:
           df = change(df)   
    except:
        df = df.dropna()
        df = change(df)
    return df

@st.cache_resource
def aggregated_transaction():
    success=[]
    error=[]
    trans=[]
    state_path = data_path("aggregated","transaction")
    for q in os.listdir(state_path):# titerate over states
        state_name_path = os.path.join(state_path,q) #q has state name
        for z in os.listdir(state_name_path):# z has year
            state_year = os.path.join(state_name_path,z)
            for c in os.listdir(state_year):#c has quaters
                a = os.path.join(state_year,c)
                with open(a,'r+') as files:
                    d = json.load(files)
                try:
                    for n in d['data']['transactionData']:
                        e = {
                        "State": q,
                        "Year":z,
                        "Quarter":int(c.strip(".json")),
                        "Transaction_Name" : n['name'],
                        "Transaction_Count" : int(n['paymentInstruments'][0]['count']),
                        "Transaction_Amount" : int(n['paymentInstruments'][0]['amount'])
                                }   
                        trans.append(e)
                        success.append("success")
                except Exception as e:
                    error.append("error")

    Agg_transaction = cleaning(trans)

    if success:
        print(f"{len(success)} Aggregated transaction data collected")
    if error:
        print(f"Error {len(error)} files in aggregated transaction folder doesn't have data ")
                
            
    return Agg_transaction

def aggT_charts(df,state,quarter,year):

    m = df.query(f"State== '{state}' and Quarter== {quarter}")
    c=m.groupby(["Quarter","Year","State"]).sum()
    c = c.reset_index()
    
    #amount count relationship line chart
    fig1 = px.line(c,x='Transaction_Count',y='Transaction_Amount',text='Year',
                    title = f"{state} Quarter {quarter} Trend Over years")
    fig1.update_traces(textposition="bottom right")

    
    #pie chart transaction amount segment analysis
    a = df.query(f"State== '{state}' and Quarter== {quarter} and Year== '{year}'").reset_index(drop=True)
    colors = ['gold', 'mediumturquoise', 'darkorange', 'lightgreen']

    fig2 = px.pie(a,values="Transaction_Amount", names="Transaction_Name",template= 'plotly_dark',
                title = f"{year} Quarter-{quarter} Category Analysis for Total Payment Value in {state}")

    fig2.update_traces(hoverinfo='label+percent',
                    marker=dict(colors=colors, line=dict(color='#000000', width=2)))
    
    #pie chart for transaction count category analysis
    fig3 = px.pie(a,values="Transaction_Count", names="Transaction_Name",template="plotly_dark",
             title = f"{year} Quarter-{quarter} Segment Analysis for Total Payment Made in {state}")

    fig3.update_traces(hoverinfo='label+percent',
                    marker=dict(colors=colors, line=dict(color='#000000', width=2)))
    
    return fig1,fig2,fig3

@st.cache_resource
def aggregated_user():
    state_path = data_path("aggregated","user")
    success=[]
    error=[]
    user=[]
    for q in os.listdir(state_path):# titerate over states
        state_name_path = os.path.join(state_path,q) #q has state name
        for z in os.listdir(state_name_path):# z has year
            state_year = os.path.join(state_name_path,z)
            for c in os.listdir(state_year):#c has quaters
                a = os.path.join(state_year,c)
                with open(a,'r+') as files:
                    d = json.load(files)
                    # to get user details
                try:
                    for n in d['data']['usersByDevice']:
                        e= {
                            "State": q,
                            "Year":z,
                            "Quarter":int(c.strip(".json")),
                            "Brand" : n['brand'],
                            "Registered User" : n['count']
                        }
                        user.append(e)
                        success.append("success")
                except Exception as e:
                    error.append("error")
    if error:
        print(f"Error {len(error)} files in aggregated user folder doesn't have data")
    if success:
        print(f"{len(success)} Aggregated user data collected")

    Agg_user = cleaning(user)

    return Agg_user

def overall_user(df):
    fig1 = px.pie(df,values="Registered User",names="Brand",title="Distribution of User's Mobile Brand Across All State ")
    fig1.update_traces(textposition='inside', textinfo='percent+label')
    
    fig2 = px.pie(df,names="State",values="Registered User",title="Distribution of User Across States")
    fig2.update_traces(textposition='inside', textinfo='percent+label')

    return fig1,fig2

def aggU_charts(df,state,quarter,year):
    
    q= df.query(f"State == '{state}' and Quarter == {quarter}")
    m= q.groupby(["Year","Quarter"]).sum()
    m.reset_index(inplace=True)
    fig2 = px.scatter(m,x="Year",y="Registered User",trendline="ols",title=f"{state} Q-{quarter} User Base Growth")

    v = df.query(f"State == '{state}' and Quarter == {quarter} and Year == '{year}'")
    fig3 = px.pie(v,values="Registered User",names="Brand",template="plotly_dark",title =f"{year} Q-{quarter} User Prefered Mobile Brand in {state}")
    
    l = q.groupby(["Year","State"]).sum()
    l.reset_index(inplace=True)
    fig4 = px.pie(l,values="Registered User",names="Year",title="User Base Analysis Over Year")
    

    return fig2,fig3,fig4

@st.cache_resource
def map_transaction():
    state_path = data_path("map","transaction")
    success=[]
    error=[]
    trans=[]
    for q in os.listdir(state_path):# titerate over states
        state_name_path = os.path.join(state_path,q) #q has state name
        for z in os.listdir(state_name_path):# z has year
            state_year = os.path.join(state_name_path,z)
            for c in os.listdir(state_year):#c has quaters
                a = os.path.join(state_year,c)
                with open(a,'r+') as files:
                    d = json.load(files)
                try:
                    for n in d['data']['hoverDataList']:
                        e = {
                        "State": q,
                        "Year":z,
                        "Quarter":int(c.strip(".json")),
                        'District' : n['name'],
                        'Transaction_Count' : n['metric'][0]['count'],
                        'Transaction_Amount' : n['metric'][0]['amount']
                                                                    }   
                        trans.append(e)
                        success.append("success")
                except Exception as e:
                    error.append("error")
    if success:
        print(f"{len(success)}  map transaction data collected")
    if error:
        print(f"{len(error)} error happened in collecting map transaction data")

    Map_transaction = cleaning(trans)
    
    return Map_transaction

def mapT_charts(df,state,quarter,year,district):
    a = df.query(f"State=='{state}' and Quarter=={quarter} and Year=='{year}'").reset_index(drop=True)
    a['District'] =a['District'].str.rstrip("district")
    #list of districts
    fig1 = px.sunburst(
        a, path = ['State','District'],
        color ='District',template= 'plotly_dark'
    )

    fig1.update_layout(margin = dict(t=0, l=0, r=0, b=0))

    fig2 = px.bar(a,y="Transaction_Amount", x="District", text_auto='.2s',
                title = f"{year} Q-{quarter} Segment Analysis for Total Payment Value")

    fig2.update_traces(textfont_size=24, textangle=0, textposition="outside", cliponaxis=False)

    fig3 = px.bar(a,y="Transaction_Count", x="District", text_auto='.2s',
                title = f"{year} Q-{quarter} Segment Analysis for Total Payment Made")

    fig3.update_traces(textfont_size=24, textangle=0, textposition="outside", cliponaxis=False)

    m = df.query(f"District=='{district}' and State=='{state}' and Quarter== {quarter}")
    c=m.groupby(["Quarter","Year","State"]).sum()
    c = c.reset_index()

    fig4 = px.line(c,x='Transaction_Count',y='Transaction_Amount',text='Year', template="plotly_dark",
                        title = f"{district} Q-{quarter} Trend Over years")
    fig4.update_traces(textposition="bottom right")
    
    return fig1,fig2,fig3,fig4

@st.cache_resource
def map_user():
    state_path = data_path("map","user")
    success=[]
    error=[]
    user = []
    for q in os.listdir(state_path):# titerate over states
        state_name_path = os.path.join(state_path,q) #q has state name
        for z in os.listdir(state_name_path):# z has year
            state_year = os.path.join(state_name_path,z)
            for c in os.listdir(state_year):#c has quaters
                a = os.path.join(state_year,c)
                with open(a,'r+') as files:
                    d = json.load(files)
                try:
                    for key,values in d['data']['hoverData'].items():
                        e= {
                            "State": q,
                            "Year":z,
                            "District":key,
                            "Quarter":int(c.strip(".json")),
                            "Registered User": values['registeredUsers'],
                            "App Open": values['appOpens']
                        }
                        user.append(e)
                        success.append("success")
                except Exception as e:
                    error.append("error")
                        
    if error:
        print(f"{len(error)} Error occured in collecting map user data")
    if success:
        print(f"{len(success)} map User data Successfully gathered")

    Map_user = cleaning(user)

    return Map_user

def mapU_charts(df,state,quarter,year,district):
    a = df.query(f"State== @state and Quarter== @quarter and Year== '{year}'").reset_index(drop=True)
    a['District'] =a['District'].str.rstrip("district")
    #list of districts
    fig1 = px.sunburst(
        a, path = ['State','District'],
        color ='District',template= 'plotly_dark'
    )

    fig1.update_layout(margin = dict(t=0, l=0, r=0, b=0))

    fig2 = px.bar(a,y="Registered User", x="District", text_auto='.2s',
                title = f"{year} Q-{quarter} Segment Analysis for Registered User in {district}")

    fig2.update_traces(textfont_size=24, textangle=0, textposition="outside", cliponaxis=False)

    q= df.query("State == @state and Quarter == @quarter and District == @district")
    m= q.groupby(["Year","Quarter"]).sum()
    m.reset_index(inplace=True)
    fig3 = px.scatter(m,x="Year",y="Registered User",
                      title=f" Q-{quarter} Trend of {district} over year",trendline="ols")
    fig4 = px.pie(a,values="Registered User",names="District",title=f"District Wise User Distribution")

    return fig1,fig2,fig3,fig4

@st.cache_resource
def top_transaction():
    success=[]
    error=[]
    er=[]
    sus=[]
    trans = {'top_district' : [],'top_pincode' : []}
    state_path = data_path("top","transaction")
    for q in os.listdir(state_path):# titerate over states
        state_name_path = os.path.join(state_path,q) #q has state name
        for z in os.listdir(state_name_path):# z has year
            state_year = os.path.join(state_name_path,z)
            for c in os.listdir(state_year):#c has quaters
                a = os.path.join(state_year,c)
                with open(a,'r+') as files:
                    d = json.load(files)
                try:
                    for i in d['data']['districts']:
                        e = {
                        "State": q,
                        "Year":z,
                        "Quarter":int(c.strip(".json")),
                        "District" :i['entityName'],
                        "Transaction_Count" : i['metric']['count'],
                        "Transaction_Amount": i['metric']['amount']
                            }   
                        trans['top_district'].append(e)
                        success.append("success")
                except Exception as e:
                    error.append("error")
                #for transaction pincode data
                try:
                    for i in d['data']['pincodes']:
                        e={
                            "State": q,
                            "Year":z,
                            "Quarter":int(c.strip(".json")),
                            "Pincode" : i['entityName'],
                            "Transaction_Count" : i['metric']['count'],
                            "Transaction_Amount" : i['metric']['amount']
                        }
                        trans['top_pincode'].append(e)
                        sus.append("ok")
                except Exception as e:
                    er.append("error")
    if success:
        print(f"{len(success)}  top district transaction data collected")
    if error:
        print(f"{len(error)} error happened in collecting top district transaction data")
    if sus:
        print(f"{len(sus)} top pincode transaction data collected")
    if er:
        print(f"{len(er)} error happened in collecting top pincode transaction data")

    district = cleaning(trans['top_district'])
    pincode = cleaning (trans['top_pincode'])
    Top_transaction = [district,pincode]

    return Top_transaction

def topTP_charts(df,state,quarter,year,pincode):
    a = df.query(f"State=='{state}' and Quarter=={quarter} and Year=='{year}'").reset_index(drop=True)
    
#list of districts
    fig1 = px.sunburst(
        a, path = ['State','Pincode'],
        color ='Pincode',template= 'plotly_dark'
    )

    fig1.update_layout(margin = dict(t=0, l=0, r=0, b=0))

    fig2 = px.bar(a,y="Transaction_Amount", x="Pincode",  hover_data=["State"],
                title = f"{year} Q-{quarter} Segment Analysis for Total Payment Value")

    fig2.update_xaxes(type='category')

    fig3 = px.bar(a,y="Transaction_Count", x="Pincode", hover_data=["State"],
                title = f"{year} Q-{quarter} Segment Analysis for Total Payment Made")

    fig3.update_xaxes(type='category')

    

    m = df.query(f"Pincode=='{pincode}' and State=='{state}' and Quarter=={quarter}")
    c=m.groupby(["Quarter","Year","State"]).sum()
    c = c.reset_index()

    fig4 = px.line(c,x='Transaction_Count',y='Transaction_Amount',text='Year',
                        title = f"{pincode} Q-{quarter} Trend Over years")
    fig4.update_traces(textposition="bottom right")
    
    return fig1,fig2,fig3,fig4

@st.cache_resource
def top_user():
    success=[]
    error=[]
    er=[]
    sus=[]
    user = {"top_district" : [],"top_pincode" : []}
    state_path = data_path("top","user")
    for q in os.listdir(state_path):# titerate over states
        state_name_path = os.path.join(state_path,q) #q has state name
        for z in os.listdir(state_name_path):# z has year
            state_year = os.path.join(state_name_path,z)
            for c in os.listdir(state_year):#c has quaters
                a = os.path.join(state_year,c)
                with open(a,'r+') as files:
                    d = json.load(files)
                try:
                    for v in d['data']['districts']:
                        e= {
                            "State": q,
                            "Year":z,
                            "Quarter":int(c.strip(".json")),
                            "District" : v['name'],
                            "Registered User" : v['registeredUsers']
                        }
                        user['top_district'].append(e)
                        success.append("success")
                except Exception as e:
                    error.append("error")
                try:
                    for v in d['data']['pincodes']:
                        e={
                            "State": q,
                            "Year":z,
                            "Quarter":int(c.strip(".json")),
                            "Pincode" : v['name'],
                            "Registered User" : v['registeredUsers']
                        }
                        user['top_pincode'].append(e)
                        sus.append("ok")
                except Exception as e:
                    er.append(e)

    if error:
        print(f"{len(error)} Error occured in collecting top district user data")
    if success:
        print(f"{len(success)} top district User data Successfully gathered")
    if sus:
        print(f"{len(sus)} top pincode user data collected")
    if er:
        print(f"{len(er)} error happened in collecting top pincode user data")

    district = cleaning(user["top_district"])
    pincode = cleaning(user["top_pincode"])
    Top_user = [district,pincode]

    return Top_user

def topU_charts(df,state,quarter,year,pincode):
    a = df.query(f"State=='{state}' and Quarter=={quarter} and Year=='{year}'").reset_index(drop=True)

    fig1 = px.sunburst(
            a, path = ['State','Pincode'],
            color ='Pincode',template= 'plotly_dark'
        )

    fig1.update_layout(margin = dict(t=0, l=0, r=0, b=0))

    c=a.groupby(["Quarter","Year","Pincode"]).sum()
    c = c.reset_index()

    fig2 = px.pie(c,values="Registered User",names="Pincode",
                        title = f"{year} Q-{quarter} Trend for {state}")
    
    fig3 = px.bar(a,y="Registered User", x="Pincode", text_auto='.2s',
            title = f"{year} Q-{quarter} Segment Analysis of Registered User")
    fig3.update_xaxes(type='category')

    fig3.update_traces(textfont_size=20, textangle=0, textposition="outside", cliponaxis=False)

    q= df.query("State == @state and Quarter == @quarter and Pincode == @pincode")
    m= q.groupby(["Year","Quarter"]).sum()
    m.reset_index(inplace=True)
    fig4 = px.scatter(m,x="Year",y="Registered User",
                        title=f" Q-{quarter} Trend of {pincode} over year",trendline="ols")
    
    return fig1,fig2,fig3,fig4

def app_opens(df,state,quarter,year,district):
    m = df.query("District == @district and  State== @state and Quarter== @quarter").reset_index()
    m['District'] =m['District'].str.rstrip("district")
    
    fig1 = px.scatter(m,x='Year',y='App Open',trendline="ols",
                        title = f"{district} Q-{quarter} Trend Over years")
    fig1.update_traces(textposition="bottom right")

    u = df.query(f"District == @district and  State== @state and Quarter== @quarter").reset_index()
    u['District'] =u['District'].str.rstrip("district")

    fig2 = px.line(u,x="Registered User",y="App Open",text="Year",
                                title = f"{district} Q-{quarter} Trend of User Usage Over years")
    fig2.update_traces(textposition= "bottom right")

    fig3 = px.pie(df,values="App Open",names="Year",template="plotly_dark",title="App Opens Growth over Years ")

    return fig1,fig2,fig3

def selectbox(df):
    if "Brand" in df.columns:
        option = f1.selectbox("Select one",["Overall","Mobile Wise","District Wise","Pincode Wise","App Usage"])
    else:
        option = f1.selectbox("Select one",["Overall",'State Wise Data','District Wise Data','Pincode Wise Data'])
    s = df['State'].unique()
    state = f2.selectbox("Select States",["Overall",*s])
    y = df['Year'].unique()
    year = f3.selectbox("Select Year",["Overall",*y])
    q = df['Quarter'].unique()
    quarter = f4.selectbox("Select Quarter",["Overall",*q])

    return option,state,year,quarter

def category(agg_tran):
    c = agg_tran.groupby(['Transaction_Name']).sum()
    v = c.reset_index()
    financial = locale.currency(v.iloc[0]['Transaction_Amount'],grouping=True)
    merchant = locale.currency(v.iloc[1]['Transaction_Amount'],grouping=True)
    ptp = locale.currency(v.iloc[2]['Transaction_Amount'],grouping=True)
    rbp = locale.currency(v.iloc[3]['Transaction_Amount'],grouping=True)
    others = locale.currency(v.iloc[4]['Transaction_Amount'],grouping=True)
    
    return financial,merchant,ptp,rbp,others 

def payment(financial,merchant,ptp,rbp,others):
    container = st.container(height= 880,border= True)
    container.subheader("Category")
    with container:
        st.caption("Financial Services")
        st.subheader(financial)
        st.divider()
        st.caption("Merchant payments")
        st.subheader(merchant)
        st.divider()
        st.caption("Peer-to-peer payments")
        st.subheader(ptp)
        st.divider()
        st.caption("Recharge & bill payments")
        st.subheader(rbp)
        st.divider()
        st.caption("Others")
        st.subheader(others)

def overall(df):
    TTA = locale.currency(df['Transaction_Amount'].sum(),grouping=True)
    TTC = locale.format_string("%d",df['Transaction_Count'].sum(),grouping=True)
    avg = locale.currency(df['Transaction_Amount'].sum()/df['Transaction_Count'].sum(),grouping=True)

    return TTA,TTC,avg

def container(name,value):
    container = st.container(height=120,border=True)
    container.caption(f"{name}")
    container.subheader(value)

def total(TTA,TTC,avg):
    with c1:
        container("Total Payment Value",TTA)
    with c2:
        container ("Total payment Made",TTC)
    with c3:
        container("Average",avg)

def user_total(Total):
    n = st.container(border=True)
    n.caption("Total User")
    n.subheader(Total)

def connection():
    db = mysql.connector.connect(host='localhost',user='root', password ="012345", database="phonepe")
    cursor = db.cursor()
    return db,cursor


def map_data(q,year,quarter,services):
    l= q.query(f"Year== '{year}' & Quarter == @quarter & Transaction_Name == @services ")
    l.reset_index(inplace=True)
    v =l.groupby("State").sum()
    v.drop(['index'],axis=1,inplace=True)
    v.reset_index(inplace=True)
    df = gpd.read_file(r"K:\data\India-State-and-Country-Shapefile-Updated-Jan-2020-master\India_State_Boundary.shp")
    change=[]
    correct=[]
    for i in v["State"].unique():
        if i not in df["State_Name"].unique():
            correct.append(i)
    for i in df["State_Name"].unique():
        if i not in v["State"].unique():
            change.append(i)
    change.sort()
    correct.sort()
    for i,j in zip(correct,change):
        df["State_Name"] = df["State_Name"].str.replace(f"{j}",f"{i}")

    z = df.drop(["geometry"],axis=1)
    c = pd.merge(v,z,left_on = "State", right_on = "State_Name",how = "inner")
    c.drop("State_Name",axis=1,inplace=True)
    
    return df,c

def display_map(q,year,quarter,services):

    df,c=map_data(q,year,quarter,services)
   
    m = folium.Map(location=[22.1900906,78.4440938 ],zoom_start=5, tiles="CartoDB positron")

    choropleth = folium.Choropleth(geo_data= df,
                    data =c,
                    columns = ("State",choice),
                    key_on='feature.properties.State_Name',
                    fill_color = "Set3",
                    legend_name=choice,
                    highlight = True, 
                            ).add_to(m)

    choropleth.geojson.add_to(m) 
    for f in choropleth.geojson.data['features']:
        name = f['properties']['State_Name']
        if choice == "Transaction_Amount":
            f['properties'][choice] = locale.currency(c.loc[c['State'] == name, 'Transaction_Amount'].values[0],grouping=True)
        else:
            f['properties'][choice] = locale.format_string("%d",c.loc[c['State'] == name, 'Transaction_Count'].values[0],grouping=True)

    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(['State_Name',choice])
    )

    return m

st.set_page_config(page_title="PhonePeData",layout="wide",initial_sidebar_state="auto")

select = option_menu(menu_title = None,
                     options = ['Home','Transaction Data','User Data','Queries'],
                     orientation = "horizontal",
                     default_index=0
                     )
agg_tran = aggregated_transaction()
agg_user = aggregated_user()
dw = map_user()
map_trans = map_transaction()
top_trans = top_transaction()
top = top_user()

c1 ,c2, c3 = st.columns([0.5,0.3,0.2])
f1,f2,f3,f4 = st.columns(spec=[1,1,1,1],gap="medium")
y1, y2 = st.columns([0.68,0.32],gap="small") 

if select == 'Home':

    TTA,TTC,avg = overall(agg_tran)
    total(TTA,TTC,avg)
    col1,col2,col3,col4= st.columns([0.2,0.2,0.3,0.3])
    with col1:
        z = agg_tran["Year"].unique()
        year = st.selectbox("Year",z)
    with col2:
        y = agg_tran["Quarter"].unique()
        quarter = st.selectbox("Quarter",y)
    with col3:
        choice = st.selectbox("Type",["Transaction_Count","Transaction_Amount"])
    with col4:
        services = st.selectbox("Services",agg_tran["Transaction_Name"].unique())
    b1,b2 = st.columns([0.7,0.3],gap="small")
    with b1:
        m = display_map(agg_tran,year,quarter,services)
        output = st_folium(
                m, width=750, height=740, returned_objects=[]
            )
    with b2:
        st.title("PhonePe Data Visualization")
        st.divider()
        st.header("OverView")
        e = st.container(border=True)
        e.text("""
               The Phonepe Data Visualization 
               project is a Python-based 
               solution that extracts data from
               the Phonepe Pulse Github repository,
               transforms and stores it in a MySQL
               database, and displays it through
               an interactive dashboard using 
               Streamlit,Folium,Geopandas, Plotly
               and few other visualization and
               data manipulation libraries..""") 


if select == 'Transaction Data':
   
    option,state,year,quarter = selectbox(agg_tran)
    
    if option and state and year and quarter == "Overall":
        TTA,TTC,avg = overall(agg_tran)
        total(TTA,TTC,avg)
        b = agg_tran.groupby(['State']).sum()
        b.reset_index(inplace=True)
        fig1 = px.pie(b,values="Transaction_Count",names="State",title= "Distribution of Overall Payment Made ")
        fig1.update_traces(textposition='inside', textinfo='percent+label')
        fig2 = px.pie(b,values="Transaction_Amount",names="State",title= "Distribution of Overall Payment Value")
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        with y1:
            c11 = st.container(border=True)
            st.plotly_chart(fig1)
            c12 = st.container(border=True)
            st.plotly_chart(fig2) 

        financial,merchant,ptp,rbp,others = category(agg_tran)
        with y2:
            payment(financial,merchant,ptp,rbp,others)
    if option == "State Wise Data" and state and year and quarter != "Overall":
        m = agg_tran.query(f"State == '{state}' and Year == '{year}' and Quarter == {quarter}")
        a = m.groupby(['State','Year','Quarter']).sum()
        TTA,TTC,avg = overall(a)
        total(TTA,TTC,avg)
        df = agg_tran.query(f"State== '{state}' and Quarter== {quarter} and Year== '{year}'").reset_index(drop=True)
        financial,merchant,ptp,rbp,others = category(df)

        f1,f2,f3 = aggT_charts(agg_tran,state,quarter,year)
       
        with y2:
            payment(financial,merchant,ptp,rbp,others)
        with y1: 
            st.plotly_chart(f1)
            st.plotly_chart(f3)
            st.plotly_chart(f2)
    if option == "District Wise Data" and  state and year and quarter != "Overall":

        df = map_trans
        df['District'] =df['District'].str.replace("district","")
        v= df.query(f"State== '{state}' and Quarter== {quarter} and Year== '{year}'").reset_index(drop=True)
        district = st.selectbox("Select one",v["District"].unique())
        if district:
            m = df.query(f"State=='{state}' and District=='{district}'").reset_index(drop=True)
            a= m.groupby(['District']).sum()
            TTA,TTC,avg = overall(a)
            total(TTA,TTC,avg)
            q1,q2,q3,q4 = mapT_charts(df,state,quarter,year,district)
            w1,w2 = st.columns([0.5,0.5],gap="small")
            with w1:
                st.plotly_chart(q4)
                st.plotly_chart(q3)
                
            with w2:
                st.plotly_chart(q1)
                st.plotly_chart(q2)
        
    if option == "Pincode Wise Data" and state and year and quarter != "Overall":

        df = top_trans
        v= df[1].query(f"State== '{state}' and Quarter== {quarter} and Year== '{year}'").reset_index(drop=True)
        pincode = st.selectbox("Select one",v["Pincode"].unique())
        if pincode:
            m = df[1].query(f"State=='{state}' and Pincode=='{pincode}'").reset_index(drop=True)
            a= m.groupby(['Pincode']).sum()
            TTA,TTC,avg = overall(a)
            total(TTA,TTC,avg)
            q1,q2,q3,q4 = topTP_charts(df[1],state,quarter,year,pincode)
            w1,w2 = st.columns([0.5,0.5],gap="small")
            with w1:
                st.plotly_chart(q4)
                st.plotly_chart(q3)
                
            with w2:
                st.plotly_chart(q1)
                st.plotly_chart(q2)

if select =="User Data":
   
    option,state,year,quarter = selectbox(agg_user)
    if option and state and year and quarter == "Overall":
        c= agg_user.groupby(['State']).sum()
        Total = locale.format_string("%d",c['Registered User'].sum(),grouping=True)
        with y2:    
            user_total(Total)
        f1,f2 = overall_user(agg_user)
        with y1:
            st.plotly_chart(f1)
            st.plotly_chart(f2)
    if option == "Mobile Wise" and state and year and quarter != "Overall":
        f2,f3,f4 = aggU_charts(agg_user,state,quarter,year)
        with y1:
            st.plotly_chart(f3)
            st.plotly_chart(f4)
        with y2:
            st.plotly_chart(f2)
            
    if option == "District Wise" and state and year and quarter != "Overall":
        
         v= dw.query(f"State== '{state}' and Quarter== {quarter} and Year== '{year}'").reset_index(drop=True)
         v['District'] = v["District"].str.rstrip("district")
         with y1:
            district = st.selectbox("List Of Districts",v['District'].unique())
         if district:
            c=dw
            c['District'] = c["District"].str.rstrip("district")
            m = c.query(f"State== '{state}' & District== '{district}'").reset_index(drop=True)
            a= m.groupby(['District']).sum()
            Total = locale.format_string("%d",a['Registered User'].sum(),grouping=True)
            f1,f2,f3,f4 = mapU_charts(dw,state,quarter,year,district)
            with y1:
                st.plotly_chart(f1)
                st.plotly_chart(f2)
            with y2:
                user_total(Total)
                st.plotly_chart(f3)
                st.plotly_chart(f4)
            
    if option == "Pincode Wise" and state and year and quarter != "Overall":

        df = top 
        v= df[1].query(f"State== '{state}' and Quarter== {quarter} and Year== '{year}'").reset_index(drop=True)
        with y1:
            pincode = st.selectbox("Select one",v["Pincode"].unique())
        if pincode:
            m = df[1].query(f"State=='{state}' and Pincode=='{pincode}'").reset_index(drop=True)
            a= m.groupby(['Pincode']).sum()
            Total = locale.format_string("%d",a['Registered User'].sum(),grouping=True)
            q1,q2,q3,q4 = topU_charts(df[1],state,quarter,year,pincode)
            with y1:
                st.plotly_chart(q4)
                st.plotly_chart(q3)
                
            with y2:
                user_total(Total)
                st.plotly_chart(q1)
                st.plotly_chart(q2)
    
    if option == "App Usage" and state and year and quarter != "Overall":
              
        v= dw.query(f"State== '{state}' and Quarter== {quarter} and Year== '{year}'").reset_index(drop=True)
        v['District'] = v["District"].str.rstrip("district")
        with y1:
            district = st.selectbox("List Of Districts",v['District'].unique())
        if district:
            c=dw
            c['District'] = c["District"].str.rstrip("district")
            m = c.query(f"State== '{state}' & District== '{district}'").reset_index(drop=True)
            a= m.groupby(['District']).sum()
            Total = locale.format_string("%d",a['Registered User'].sum(),grouping=True)
            f1,f2,f3 = app_opens(dw,state,quarter,year,district)
            with y1:
                st.plotly_chart(f2)
                st.plotly_chart(f1)
            with y2:
                user_total(Total)
                st.plotly_chart(f3)

if select =="Queries":

    db,cursor = connection()

    option = ['Select a Option','Segment in which High Value transaction happens',
            'Segment in which the most transaction happens across years',
            'A district who loves the phonepe app the most',
            'An effective payment method during the Covid-19 Lockdown period(2019-2020)',
            'The Quarter which tops the transaction list very often across years',
            'The State which has most the PhonePe Registered users All time',
            'The year which recorded highest no of Registered users across India',
            'The States which were unaware about Phonepe']
    select = st.selectbox("Select",option)

    if select == 'Segment in which High Value transaction happens':
        query = "SELECT transaction_name, SUM(transaction_amount) FROM agg_Tran GROUP BY transaction_name"
        cursor.execute(query)
        b = cursor.fetchall()
        v = pd.DataFrame(b,columns=['name','amount'])
        fig = px.pie(v,values='amount',names='name',title= "High Value Transaction")
        st.plotly_chart(fig)
    elif select == 'Segment in which the most transaction happens across years':
        query = "SELECT transaction_name, SUM(transaction_count) FROM agg_Tran GROUP BY transaction_name ORDER BY SUM(transaction_count) DESC"
        cursor.execute(query)
        b = cursor.fetchall()
        v = pd.DataFrame(b,columns=['name','counts'])
        fig = px.pie(v,values='counts',names='name',title= 'Segment where Phonepe Preferred Most')
        st.plotly_chart(fig)
    elif select == 'A district who loves the phonepe app the most':
        query = "SELECT district, SUM(transaction_count) FROM district_tran GROUP BY district ORDER BY SUM(transaction_count) DESC LIMIT 10"
        cursor.execute(query)
        y = cursor.fetchall()
        v = pd.DataFrame(y,columns=['district','counts'])
        fig = px.pie(v,values='counts', names = 'district' ,title= "Top districts")
        st.plotly_chart(fig)
    elif select == 'An effective payment method during the Covid-19 Lockdown period(2019-2020)':
        query = "SELECT year, SUM(transaction_count), SUM(transaction_amount) FROM agg_tran GROUP BY year"
        cursor.execute(query)
        b = cursor.fetchall()
        v = pd.DataFrame(b,columns=['year','counts','amount'])
        v['year'] = v['year'].replace({
            '2019': 'Covid-2019',
            '2020': 'Covid-2020',
            '2021': 'Covid-2021'
        })
        pie_amount = px.pie(v,values='amount',names='year',color='year',title='Growth of Transaction Amount Over Year')
        pie_count = px.pie(v,values='counts', names='year',color='year',title='Growth of User Over Years')
        st.plotly_chart(pie_amount)
        st.plotly_chart(pie_count)

    elif select == "The Quarter which tops the transaction list very often across years":
        query ="select year, quarter, sum(transaction_amount) from map_tran group by year, quarter"
        cursor.execute(query)
        y = cursor.fetchall()
        v = pd.DataFrame(y,columns=['year','quarter','amount'])
        bar = px.bar(v,x='quarter',y='amount',labels={'quarter':"Quarter",'amount':"Amount"},color='year')
        bar.update_xaxes(
            tickvals=['1', '2', '3', '4'],  
            title_text='Quarter'  
        )
        st.plotly_chart(bar)

    elif select == 'The State which has most the PhonePe Registered users All time':
        query = "SELECT state ,SUM(user_count) FROM agg_user GROUP BY state ORDER BY SUM(user_count) DESC LIMIT 10"
        cursor.execute(query)
        y = cursor.fetchall()
        v = pd.DataFrame(y,columns=['state','users'])
        bar = px.bar(v,x='state',y='users',color='state',labels={'state':'State',"users":"Users"})
        st.plotly_chart(bar)
        
    elif select == 'The year which recorded highest no of Registered users across India':
        query = "SELECT year,SUM(user_count) from map_user GROUP BY year ORDER BY SUM(user_count) DESC"
        cursor.execute(query)
        y = cursor.fetchall()
        v = pd.DataFrame(y,columns=['year','user'])
        bar = px.bar(v,x='year',y='user',color='year',labels={'year':'Year',"user":'Users'})
        st.plotly_chart(bar)

    elif select == "The States which were unaware about Phonepe":
        query = "SELECT state, year, SUM(app_opens) FROM map_user Group BY state, year ORDER BY SUM(app_opens) LIMIT 35"
        cursor.execute(query)
        y = cursor.fetchall()
        v = pd.DataFrame(y,columns=['state','year','app_opens'])
        state = v['state'].values
        y =v['year'].unique()
        st.text("""
    Till 2018 Andaman & Nicobar, Telangana, Punjab, Meghalaya, Uttar Pradesh,
    Kerala, Andhra Pradesh, Manipur, Dadra & Nagar Haveli And Daman & Diu, Ladakh, 
    Chhattisgarh, Himachal Pradesh, Arunachal Pradesh, Tamil Nadu, Maharashtra, 
    Karnataka, Haryana, Lakshadweep, Assam, Mizoram, Gujarat, Goa, Sikkim, Odisha, 
    Bihar, Jammu & Kashmir, Jharkhand, Nagaland, Rajasthan, Delhi, Chandigarh, 
    Puducherry, Tripura, Madhya Pradesh, Uttarakhand these states weren't using 
    PhonePe""")
        st.text(f"West Bengal is the only state that was using PhonePe")

