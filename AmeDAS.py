#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import datetime
import csv
import zipfile
import io
import pandas as pd
import json
import collections as cl
import os
import googlemaps
import urllib.error
import urllib.request

GOOGLE_MAP_API_KEY="AIzaSyCBPpt5PJauc95bnv5xC_yRDXSqPc9PlHw"

def geocoding(place):
	path="geocoding.csv"
	csvrs=[]
	if(os.path.exists(path)):
		with open(path,mode="r",encoding="Shift-JIS") as f:
			reader=csv.reader(f)
			for row in reader:
				r=[]
				for i in range(len(row)):
					d=row[i]
					if(i!=0):
						d=float(d)
					r.append(d)
				csvrs.append(r)
			f.close()	
	if(len(csvrs)!=0):
		for i in csvrs:
			if(len(i)==3):
				if(i[0]==place):
					return [i[1],i[2]]

	gmaps = googlemaps.Client(key=GOOGLE_MAP_API_KEY)
	geocode_result = gmaps.geocode(place)
	data = [place,geocode_result[0]["geometry"]["location"]["lat"],geocode_result[0]["geometry"]["location"]["lng"]]
	csvrs.append(data)
	
	with open(path,mode="w",newline="",encoding="Shift-JIS") as f:
		writer=csv.writer(f)
		for l in csvrs:
			writer.writerow(l)
		f.close()
	return [data[1],data[2]]

class AmeDAS(object):
	def __init__(self,name,point):
		if(not os.path.exists("amedas/")):
			os.mkdir("amedas/")
		self.point=int(point)
		self.name=name
		self.all=self.alldate()
		#self.csv_save(self.all[0])
		self.json_save(self.all)

	#一日分のデータ取得
	def data(self,date):
		datelist=['yesterday','today']
		url='https://www.jma.go.jp/jp/amedas_h/'+datelist[date]+'-'+str(self.point)+'.html'#URL
		column=26#縦列設定
		
		html=requests.get(url).content
		soup=BeautifulSoup(html, 'html.parser')
		title_text=soup.find(class_='td_title height2').get_text()
		
		#日付
		datetext=title_text[0:11]
		date_n=datetime.datetime.strptime(datetext,'%Y年%m月%d日').strftime('%Y%m%d')
		
		#場所
		location=self.location_import()
		
		#データ整理
		s0=soup.find(id='tbl_list').find_all('td')
		row=int(len(s0)/column)#横列設定
		list=[[s0[i*row+s].get_text().replace(u'\xa0','-') for s in range(row)] for i in range(column)]
		for l in list:
			l.insert(0,date_n)
		
		del list[1];#2行目削除
		if(date==1):
			del list[0];#1行目削除
		else:
			list[0][0]="日付"
		return [list,location]

	#昨日と今日のデータの取得
	def alldate(self):
		l=[self.data(i) for i in range(2)]
		return [l[0][0]+l[1][0],l[0][1]]

	def location_import(self):
		dir="http://www.jma.go.jp/jma/kishou/know/amedas/ame_master.zip"
		r=requests.get(dir,stream=True)
		zip=zipfile.ZipFile(io.BytesIO(r.content),'r')
		for file in zip.namelist():
			with zip.open(file, 'r') as f:
				binaryCSV=f.read()
			df=pd.read_csv(io.BytesIO(binaryCSV),encoding='cp932')
			data=df[df["観測所番号"]==self.point]
			address=data["所在地"].values[0]
			if("　" in address):
				address=address[:address.find("　")]
			return [self.name,data["観測所名"].values[0].replace("\n",""),address,geocoding(address)]

	#csvデータを保存
	def csv_save(self,data):
		with open("amedas/"+self.name+".csv",mode='w',encoding='utf-8') as f:
			writer=csv.writer(f)
			for l in data:
				writer.writerow(l)
		f.close()
		
	#jsonデータを保存
	def json_save(self,data):
		data_location=data[1]
		data_weather=data[0]
		name_list=data_weather[0]
		cldata=cl.OrderedDict()
		cllocation=cl.OrderedDict()
		cllocation["名前"]=data_location[0]
		cllocation["観測所名"]=data_location[1]
		cllocation["所在地"]=data_location[2]
		cllocation["geocoding"]=data_location[3]
		cldata["場所"]=cllocation
		for i in range(len(data_weather)):
			if(i!=0):
				cld=cl.OrderedDict()
				str=""
				for j in range(len(name_list)):
					cld[name_list[j]]=data_weather[i][j]
					if(j==0 or j==1):
						d_str=data_weather[i][j]
						if(len(d_str)==1):
							d_str='0'+data_weather[i][j]
						str+=d_str
				cldata[str]=cld
		f=open("amedas/"+self.name+".json",'w',encoding="utf-8")
		json.dump(cldata,f,indent=4,ensure_ascii=False)
		f.close()

def main():
	with open("setting.txt") as f:
		for l in [row for row in csv.reader(f)]:
			AmeDAS(l[1],l[0])
		f.close()

if __name__=='__main__':
	main()
