import requests
from datetime import datetime
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import csv

#-----設定項目

wait = 0            # ループの待機時間
lot = 1             # BTCの注文枚数
slippage = 0.001    # 手数料・スリッページ


# バックテストのパラメーター設定
#---------------------------------------------------------------------------------------------
chart_sec_list  = [ 300, 900, 1800, 3600, 7200, ] # テストに使う時間軸
buy_term_list   = [ 10,15,20,25,30,35,40,45 ] # テストに使う上値ブレイクアウトの期間
sell_term_list  = [ 10,15,20,25,30,35,40,45 ] # テストに使う下値ブレイクアウトの期間
judge_price_list = [
	{"BUY":"close_price","SELL":"close_price"}, # ブレイクアウト判定に終値を使用
	{"BUY":"high_price","SELL":"low_price"}     # ブレイクアウト判定に高値・安値を使用
]
#---------------------------------------------------------------------------------------------



# CryptowatchのAPIを使用する関数
def get_price(min, before=0, after=0):
	price = []
	params = {"periods" : min }
	if before != 0:
		params["before"] = before
	if after != 0:
		params["after"] = after

	response = requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",params)
	data = response.json()
	
	if data["result"][str(min)] is not None:
		for i in data["result"][str(min)]:
			if i[1] != 0 and i[2] != 0 and i[3] != 0 and i[4] != 0:
				price.append({ "close_time" : i[0],
					"close_time_dt" : datetime.fromtimestamp(i[0]).strftime('%Y/%m/%d %H:%M'),
					"open_price" : i[1],
					"high_price" : i[2],
					"low_price" : i[3],
					"close_price": i[4] })
		return price
		
	else:
		print("データが存在しません")
		return None


# ドンチャンブレイクを判定する関数
def donchian( data,last_data ):
	
	highest = max(i["high_price"] for i in last_data[ (-1* buy_term): ])
	if data[ judge_price["BUY"] ] > highest:
		return {"side":"BUY","price":highest}
	
	lowest = min(i["low_price"] for i in last_data[ (-1* sell_term): ])
	if data[ judge_price["SELL"] ] < lowest:
		return {"side":"SELL","price":lowest}
	
	return {"side" : None , "price":0}


# ドンチャンブレイクを判定してエントリー注文を出す関数
def entry_signal( data,last_data,flag ):
	signal = donchian( data,last_data )
	if signal["side"] == "BUY":

		# ここに買い注文のコードを入れる
		
		flag["order"]["exist"] = True
		flag["order"]["side"] = "BUY"
		flag["order"]["price"] = round(data["close_price"] * lot)

	if signal["side"] == "SELL":

		# ここに売り注文のコードを入れる
		
		flag["order"]["exist"] = True
		flag["order"]["side"] = "SELL"
		flag["order"]["price"] = round(data["close_price"] * lot)

	return flag



# サーバーに出した注文が約定したか確認する関数
def check_order( flag ):
	
	# 注文状況を確認して通っていたら以下を実行
	# 一定時間で注文が通っていなければキャンセルする
	
	flag["order"]["exist"] = False
	flag["order"]["count"] = 0
	flag["position"]["exist"] = True
	flag["position"]["side"] = flag["order"]["side"]
	flag["position"]["price"] = flag["order"]["price"]
	
	return flag


# 手仕舞いのシグナルが出たら決済の成行注文 + ドテン注文 を出す関数
def close_position( data,last_data,flag ):
	
	flag["position"]["count"] += 1
	signal = donchian( data,last_data )
	
	if flag["position"]["side"] == "BUY":
		if signal["side"] == "SELL":
			
			# 決済の成行注文コードを入れる
			
			records( flag,data )
			flag["position"]["exist"] = False
			flag["position"]["count"] = 0
			
			# ここに売り注文のコードを入れる
			
			flag["order"]["exist"] = True
			flag["order"]["side"] = "SELL"
			flag["order"]["price"] = round(data["close_price"] * lot)
			

	if flag["position"]["side"] == "SELL":
		if signal["side"] == "BUY":
			
			# 決済の成行注文コードを入れる
			
			records( flag,data )
			flag["position"]["exist"] = False
			flag["position"]["count"] = 0
			
			# ここに買い注文のコードを入れる
			
			flag["order"]["exist"] = True
			flag["order"]["side"] = "BUY"
			flag["order"]["price"] = round(data["close_price"] * lot)
			
	return flag


# 各トレードのパフォーマンスを記録する関数
def records(flag,data):
	
	# 取引手数料等の計算
	entry_price = flag["position"]["price"]
	exit_price = round(data["close_price"] * lot)
	trade_cost = round( exit_price * slippage )
	flag["records"]["slippage"].append(trade_cost)
	
	# 手仕舞った日時と保有期間を記録
	flag["records"]["date"].append(data["close_time_dt"])
	flag["records"]["holding-periods"].append( flag["position"]["count"] )
	
	# 値幅の計算
	buy_profit = exit_price - entry_price - trade_cost
	sell_profit = entry_price - exit_price - trade_cost
	
	# 利益が出てるかの計算
	if flag["position"]["side"] == "BUY":
		flag["records"]["side"].append( "BUY" )
		flag["records"]["profit"].append( buy_profit )
		flag["records"]["return"].append( round( buy_profit / entry_price * 100, 4 ))
	
	if flag["position"]["side"] == "SELL":
		flag["records"]["side"].append( "SELL" )
		flag["records"]["profit"].append( sell_profit )
		flag["records"]["return"].append( round( sell_profit / entry_price * 100, 4 ))
	
	return flag

# バックテストの集計用の関数
def backtest(flag):
	
	# 成績を記録したpandas DataFrameを作成
	records = pd.DataFrame({
		"Date"     :  pd.to_datetime(flag["records"]["date"]),
		"Profit"   :  flag["records"]["profit"],
		"Side"     :  flag["records"]["side"],
		"Rate"     :  flag["records"]["return"],
		"Periods"  :  flag["records"]["holding-periods"],
		"Slippage" :  flag["records"]["slippage"]
	})
	
	# 総損益の列を追加する
	records["Gross"] = records.Profit.cumsum()
	
	# 最大ドローダウンの列を追加する
	records["Drawdown"] = records.Gross.cummax().subtract(records.Gross)
	records["DrawdownRate"] = round(records.Drawdown / records.Gross.cummax() * 100,1)

	print("バックテストの結果")
	print("-----------------------------------")
	print("総合の成績")
	print("-----------------------------------")
	print("全トレード数       :  {}回".format(len(records) ))
	print("勝率               :  {}％".format(round(len(records[records.Profit>0]) / len(records) * 100,1)))
	print("平均リターン       :  {}％".format(round(records.Rate.mean(),2)))
	print("平均保有期間       :  {}足分".format( round(records.Periods.mean(),1) ))
	print("")
	print("最大の勝ちトレード :  {}円".format(records.Profit.max()))
	print("最大の負けトレード :  {}円".format(records.Profit.min()))
	print("最大ドローダウン   :  {0}円 / {1}％".format(-1 * records.Drawdown.max(), -1 * records.DrawdownRate.loc[records.Drawdown.idxmax()]  ))
	print("利益合計           :  {}円".format( records[records.Profit>0].Profit.sum() ))
	print("損失合計           :  {}円".format( records[records.Profit<0].Profit.sum() ))
	print("")
	print("最終損益           :  {}円".format( records.Profit.sum() ))
	print("手数料合計         :  {}円".format( -1 * records.Slippage.sum() ))
	
	# バックテストの計算結果を返す
	result = {
		"トレード回数"     : len(records),
		"勝率"             : round(len(records[records.Profit>0]) / len(records) * 100,1),
		"平均リターン"     : round(records.Rate.mean(),2),
		"最大ドローダウン" : -1 * records.Drawdown.max(),
		"最終損益"         : records.Profit.sum(),
		"プロフィットファクタ―" : round( -1 * (records[records.Profit>0].Profit.sum() / records[records.Profit<0].Profit.sum()) ,2)
	}
	
	return result
	


# ここからメイン処理

# バックテストに必要な時間軸のチャートをすべて取得
price_list = {}
for chart_sec in chart_sec_list:
	price_list[ chart_sec ] = get_price(chart_sec,after=1451606400)
	print("-----{}分軸の価格データをCryptowatchから取得中-----".format( int(chart_sec/60) ))
	time.sleep(10)

# テストごとの各パラメーターの組み合わせと結果を記録する配列を準備
param_buy_term  = []
param_sell_term = []
param_chart_sec = []
param_judge_price = []

result_count = []
result_winRate = []
result_returnRate = []
result_drawdown = []
result_profitFactor = []
result_gross = []

# 総当たりのためのfor文の準備
combinations = [(chart_sec, buy_term, sell_term, judge_price)
	for chart_sec in chart_sec_list
	for buy_term  in buy_term_list
	for sell_term in sell_term_list
	for judge_price in judge_price_list]

for chart_sec, buy_term, sell_term,judge_price in combinations:
	
	price = price_list[ chart_sec ]
	last_data = []
	i = 0
	
	# フラッグ変数の初期化
	flag = {
		"order":{
			"exist" : False,
			"side" : "",
			"price" : 0,
			"count" : 0
		},
		"position":{
			"exist" : False,
			"side" : "",
			"price": 0,
			"count":0
		},
		"records":{
			"date":[],
			"profit":[],
			"return":[],
			"side":[],
			"holding-periods":[],
			"slippage":[]
		}
	}
	
	while i < len(price):
		
		# ドンチャンの判定に使う期間分の安値・高値データを準備する
		if len(last_data) < buy_term or len(last_data) < sell_term:
			last_data.append(price[i])
			time.sleep(wait)
			i += 1
			continue
		
		data = price[i]
		
		if flag["order"]["exist"]:
			flag = check_order( flag )
		elif flag["position"]["exist"]:
			flag = close_position( data,last_data,flag )
		else:
			flag = entry_signal( data,last_data,flag )
		
		last_data.append( data )
		i += 1
		time.sleep(wait)


	print("--------------------------")
	print("テスト期間   :")
	print("開始時点     : " + str(price[0]["close_time_dt"]))
	print("終了時点     : " + str(price[-1]["close_time_dt"]))
	print("時間軸       : " + str(int(chart_sec/60)) + "分足で検証")
	print("パラメータ１ : " + str(buy_term)  + "期間 / 買い" )
	print("パラメータ２ : " + str(sell_term) + "期間 / 売り" )
	print(str(len(price)) + "件のローソク足データで検証")
	print("--------------------------")

	
	result = backtest( flag )
	
	
	# 今回のループで使ったパラメータの組み合わせを配列に記録する
	param_buy_term.append( buy_term )
	param_sell_term.append( sell_term )
	param_chart_sec.append( chart_sec )
	if judge_price["BUY"] == "high_price":
		param_judge_price.append( "高値/安値" )
	else:
		param_judge_price.append( "終値/終値" )
	
	
	# 今回のループのバックテスト結果を配列に記録する
	result_count.append( result["トレード回数"] )
	result_winRate.append( result["勝率"] )
	result_returnRate.append( result["平均リターン"] )
	result_drawdown.append( result["最大ドローダウン"] )
	result_profitFactor.append( result["プロフィットファクタ―"] )
	result_gross.append( result["最終損益"] )
	
	

# 全てのパラメータによるバックテスト結果をPandasで１つの表にする
df = pd.DataFrame({
	"時間軸"        :  param_chart_sec,
	"買い期間"      :  param_buy_term,
	"売り期間"      :  param_sell_term,
	"判定基準"      :  param_judge_price,
	"トレード回数"  :  result_count,
	"勝率"          :  result_winRate,
	"平均リターン"  :  result_returnRate,
	"ドローダウン"  :  result_drawdown,
	"PF"            :  result_profitFactor,
	"最終損益"      :  result_gross
})

# 列の順番を固定する
df = df[[ "時間軸","買い期間","売り期間","判定基準","トレード回数","勝率","平均リターン","ドローダウン","PF","最終損益"  ]]

# トレード回数が100に満たない記録は消す
df.drop( df[ df["トレード回数"] < 100].index, inplace=True )

# 最終結果をcsvファイルに出力
df.to_csv("result-{}.csv".format(datetime.now().strftime("%Y-%m-%d-%H-%M")) )