import streamlit as st
import pandas as pd
import plotly.express as px
import folium
import html
from pathlib import Path
from streamlit_folium import st_folium

st.set_page_config(page_title='NEXTWORK | 공주의 새로운 기회', page_icon='🧭', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp{font-family:'Manrope','Noto Sans KR',sans-serif}
.stApp{background:#f4f7fc;color:#15243b}
.block-container{padding-top:2rem;max-width:1500px}
[data-testid="stSidebar"]{background:#101d38}
[data-testid="stSidebar"] *{color:#eef4ff!important}
.hero{padding:38px 42px;border-radius:25px;background:linear-gradient(115deg,#101d38,#2149a3 78%,#4678d9);color:white;margin-bottom:25px;box-shadow:0 18px 38px #19366a24}
.hero h1{font-size:42px;font-weight:800;letter-spacing:-1.5px;margin:8px 0}
.hero p{color:#dce8ff;font-size:17px;line-height:1.7}
.eyebrow{font-size:13px;letter-spacing:2px;font-weight:800;color:#9ec6ff}
.kpi{padding:24px;border-radius:18px;background:white;border:1px solid #e7edf8;box-shadow:0 7px 22px #18315b0b}
.kpi .label{font-size:14px;color:#6c7890}.kpi .num{font-size:30px;font-weight:800;color:#183a85;margin-top:6px}
.job{background:white;border:1px solid #e5eafa;border-radius:17px;padding:20px 22px;margin-bottom:14px;box-shadow:0 6px 20px #203f7609}
.job .title{font-weight:800;font-size:20px;color:#172b51}.job .meta{color:#65738b;font-size:14px;margin-top:8px;line-height:1.9}
.badge{display:inline-block;background:#eaf1ff;color:#2756b7;padding:5px 10px;border-radius:9px;font-size:12px;font-weight:700}
.note{background:#fff8e9;padding:12px 18px;border-radius:12px;color:#74551b;font-size:14px;margin:12px 0 20px}
</style>''', unsafe_allow_html=True)

# 로컬 CSV 기반 탐색: 실제 공고 CSV로 교체할 수 있습니다.
import math
from folium.features import DivIcon

@st.cache_data
def load_jobs():
    path=Path(__file__).resolve().parent/'data'/'gongju_jobs.csv'
    data=pd.read_csv(path,encoding='utf-8-sig')
    for c in ['직무','지역','분야','근무형태','보수','관련경력','설명','출처']:
        data[c]=data[c].fillna('').astype(str)
    data['위도']=pd.to_numeric(data['위도'],errors='coerce')
    data['경도']=pd.to_numeric(data['경도'],errors='coerce')
    return data.dropna(subset=['위도','경도'])

df=load_jobs()
if 'searched' not in st.session_state:st.session_state.searched=False
if 'conditions' not in st.session_state:st.session_state.conditions={}

with st.sidebar:
    st.markdown('## ✦ NEXTWORK')
    st.caption('공주의 경험을 새로운 기회로')
    st.divider()
    st.markdown('### 🔎 나에게 맞는 일자리')
    with st.form('search_form'):
        keyword=st.text_input('검색어',placeholder='예: 경비, 관광, 돌봄')
        experience=st.text_input('이전 경력',placeholder='예: 경비원 10년')
        region=st.selectbox('희망 지역',['공주시 전체']+sorted(df['지역'].unique().tolist()))
        field=st.selectbox('희망 분야',['전체']+sorted(df['분야'].unique().tolist()))
        work=st.selectbox('근무 형태',['전체']+sorted(df['근무형태'].unique().tolist()))
        clicked=st.form_submit_button('🔍 일자리 검색하기',use_container_width=True)
    if clicked:
        st.session_state.searched=True
        st.session_state.conditions=dict(keyword=keyword.strip(),experience=experience.strip(),region=region,field=field,work=work)
    st.divider()
    st.caption('NEXTWORK · 일자리 탐색')

st.markdown('''<div class="hero"><div class="eyebrow">GONGJU · CAREER REDISCOVERY PLATFORM</div><h1>경험은 끝나지 않습니다.<br>다음 기회가 시작됩니다.</h1><p>공주시 중장년·시니어를 위한 새로운 일자리 탐색 지도<br>익숙한 경력에서 새로운 가능성을 발견하세요.</p></div>''',unsafe_allow_html=True)

filtered=df.iloc[0:0].copy()
if st.session_state.searched:
    filtered=df.copy()
    c=st.session_state.conditions
    if c['keyword']:
        hay=filtered[['직무','분야','설명','관련경력','지역']].astype(str).agg(' '.join,axis=1)
        filtered=filtered[hay.str.contains(c['keyword'],case=False,regex=False)]
    if c['region']!='공주시 전체':filtered=filtered[filtered['지역']==c['region']]
    if c['field']!='전체':filtered=filtered[filtered['분야']==c['field']]
    if c['work']!='전체':filtered=filtered[filtered['근무형태']==c['work']]
    if c['experience'] and not filtered.empty:
        tokens=[t for t in c['experience'].replace(',',' ').split() if len(t)>=2 and not t.isdigit()]
        filtered=filtered.assign(관련도=filtered.apply(lambda r:sum(t.lower() in (r['관련경력']+' '+r['직무']+' '+r['설명']).lower() for t in tokens),axis=1)).sort_values('관련도',ascending=False)

k1,k2,k3,k4=st.columns(4)
for col,label,value in [(k1,'탐색 중인 기회',f'{len(filtered)}개'),(k2,'일자리 분야',f'{filtered["분야"].nunique()}개'),(k3,'탐색 지역',f'{filtered["지역"].nunique()}곳'),(k4,'지도 마커',f'{len(filtered)}개')]:
    with col:st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="num">{value}</div></div>',unsafe_allow_html=True)


if not st.session_state.searched:st.info('왼쪽에서 검색 조건을 입력하고 검색 버튼을 누르면 지도 마커와 결과 개수가 동시에 나타납니다.')
elif filtered.empty:st.warning('검색 결과가 없습니다. 검색어를 지우고 공주시 전체 / 전체로 검색해 보세요.')
else:st.success(f'조건에 맞는 일자리 {len(filtered)}건을 찾았습니다.')

colors={'제조·생산':'#e17c22','관광·문화':'#8539c9','물류·관리':'#3476c7','공공·시설':'#148f72','판매·서비스':'#d94368','돌봄·교육':'#2687cf','사무·행정':'#5265b7'}
map_tab,analysis_tab=st.tabs(['🗺️ 일자리 탐색 지도','📊 데이터 인사이트'])
with map_tab:
    left,right=st.columns([1.45,1],gap='large')
    with left:
        st.subheader('공주시 일자리 지도')
        m=folium.Map(location=[36.4571,127.1190],zoom_start=15,tiles='OpenStreetMap',control_scale=True)
        coord_counts={}
        for _,r in filtered.iterrows():
            key=(float(r['위도']),float(r['경도']))
            n=coord_counts.get(key,0);coord_counts[key]=n+1
            lat,lon=key
            if n:lat+=0.00015*math.cos(n*2.4);lon+=0.00015*math.sin(n*2.4)
            title=html.escape(str(r['직무']));region_name=html.escape(str(r['지역']))
            color=colors.get(r['분야'],'#405c94')
            label=f'<div style="white-space:nowrap;transform:translate(-9px,-50%);background:white;border:2px solid {color};color:{color};border-radius:18px;padding:7px 12px;font-size:12px;font-weight:800;box-shadow:0 3px 12px #0003">📍 {title}</div>'
            popup=f'<div style="width:230px;font-family:sans-serif"><b>{title}</b><br>📍 {region_name}<br>💰 {html.escape(str(r["보수"]))}<br>🕒 {html.escape(str(r["근무형태"]))}<br><small>예시 위치 (실제 사업장 아님)</small></div>'
            folium.Marker([lat,lon],icon=DivIcon(icon_size=(240,38),icon_anchor=(0,19),html=label),tooltip=str(r['직무']),popup=folium.Popup(popup,max_width=270)).add_to(m)
        st_folium(m,height=630,use_container_width=True,returned_objects=[],key='gongju_map_v3')
        st.caption('※ 지도 마커는 예시 좌표입니다. 실제 사업장 위치가 아닙니다.')
    with right:
        st.subheader(f'🔎 발견한 일자리 · {len(filtered)}건')
        if filtered.empty:st.info('검색 후 일자리 카드가 나타납니다.')
        for _,r in filtered.iterrows():
            title=html.escape(str(r['직무']));category=html.escape(str(r['분야']));region_name=html.escape(str(r['지역']))
            st.markdown(f'<div class="job"><span class="badge">{category} · 예시</span><div class="title">{title}</div><div class="meta">📍 {region_name}<br>🕒 {html.escape(str(r["근무형태"]))}<br>💰 {html.escape(str(r["보수"]))}<br>💡 {html.escape(str(r["설명"]))}</div></div>',unsafe_allow_html=True)
with analysis_tab:
    st.subheader('📊 검색 결과 분석')
    if filtered.empty:st.info('검색하면 분야별·지역별 결과가 나타납니다.')
    else:
        a,b=st.columns(2)
        with a:st.plotly_chart(px.bar(filtered['분야'].value_counts().rename_axis('분야').reset_index(name='건수'),x='분야',y='건수',title='분야별 결과'),use_container_width=True)
        with b:st.plotly_chart(px.bar(filtered['지역'].value_counts().rename_axis('지역').reset_index(name='건수'),x='지역',y='건수',title='지역별 결과'),use_container_width=True)
        st.dataframe(filtered[['직무','지역','분야','근무형태','보수','출처']],use_container_width=True,hide_index=True)
st.divider()
st.caption('데이터 안내: 현재 표시되는 공고·급여·위치는 기능 확인용 예시이며 실제 모집 공고가 아닙니다.')
