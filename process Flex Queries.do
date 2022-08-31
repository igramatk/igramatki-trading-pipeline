include "$GDRIVEJUMP/Stata functions/functionsall.do"

***prepare S&P500 return data
/*
import delimited "E:\Trading\Stock price data\downloadedhistoryclose.csv", bindquote(strict) clear 

keep v1 gspc
rename v1 reportdate
replace reportdate = subinstr(reportdate,"-","",.) 
destring reportdate , replace

save "E:\Trading\Stock price data\sp500.dta" , replace
*/

// retar_top_1 retar_top_4 bottom_macd_1 bottom_macd_4 discret_hold_5 - first wave of testing
// 0.2%_stop_loss 1%_stop_loss 3%_stop_loss 7%_stop_loss 50%_stop_loss - second wave of testing
foreach f in 0.2%_stop_loss 1%_stop_loss 3%_stop_loss 7%_stop_loss 50%_stop_loss {
	global folder `f'

	import delimited "E:\Trading\Log/$folder\Stock_holdings_day_by_day.csv", bindquote(strict) varnames(1) clear
	drop if symbol == "Symbol"
	destring quan - fifo ,  replace
	rename symbol position
	rename quantity sharesheld
	bys reportdate : gen j = _n
	reshape wide position sharesheld markprice openprice fifopnl, i(reportdate) j(j)
	tempfile f1
	save `f1' , replace

	import delimited "E:\Trading\Log/$folder\list_trades.csv", bindquote(strict) varnames(1) clear
	gen reportdate = substr(datetime,1,8)
	gen time = substr(datetime,10,6)
	drop datetime
	order reportdate time
	sort reportdate time
	rename commission fee

	*****total daily fees
	preserve
	collapse (sum) fee , by(reportdate)
	tempfile f2
	save `f2' , replace

	****list of trades
	restore
	drop fee
	drop if symbol == "IBKR"
	by reportdate : gen j = _n
	reshape wide time symbol quantity price , i(reportdate) j(j)
	tempfile f3
	save `f3' , replace

	import delimited "E:\Trading\Log/$folder\NAV_day_by_day.csv", bindquote(strict) varnames(1) clear
	drop if total == "Total"
	drop if total == "0" | total == "1000000"
	destring total , replace
	merge 1:1 reportdate using `f1' , nogen keep(match master)
	merge 1:1 reportdate using `f2' , nogen keep(match master)
	merge 1:1 reportdate using `f3' , nogen keep(match master)
	rename fifo* *
	destring reportdate , replace

	***
	//20220202 - remove activity before current algorithm run in the first paper trading account
	//20220314 - common period when all paper trading accounts were active
	//20220411 - start of stop loss testing
	foreach d in 20220411 { 
		preserve
		drop if reportdate < `d' 
		
		merge 1:1 reportdate using "E:\Trading\Stock price data\sp500.dta" , nogen keep(match)

		replace total = round(total, 0.01)
		replace fee = 0 if missing(fee)

		gen double cumfee = sum(fee)
		gen double return1day = (total / total[_n-1] - 1) * 100
		gen double ret1daySP500 = (gspc / gspc[_n-1] - 1) * 100
		gen double prof1day = return1day > 0 if !missing(return1day) & return1day!=0
		gen double return5day = (total / total[_n-5] - 1) * 100
		gen double ret5daySP500 = (gspc / gspc[_n-5] - 1) * 100
		gen double prof5day = return5day > 0 if !missing(return5day) & return5day!=0
		gen double returntodate = (total / total[1] - 1) * 100
		gen double retodateSP500 = (gspc / gspc[1] - 1) * 100
		gen double cummax = total in 1
		replace cummax = max(cummax[_n-1],total) if missing(cummax)
		gen double drawdown = cummax - total
		gen double drawdownperc = drawdown / cummax * 100
		gen double indrawdown = drawdown > 0 if !missing(drawdown)

		gen double drawdownduration = 0 in 1
		replace drawdownduration = cond(indrawdown==0,0,drawdownduration[_n-1]+1)
		replace drawdownduration = . if drawdownduration > 0 & _n<_N & drawdownduration[_n+1] > 0 
		gen negdate = -reportdate
		sort negdate
		carryforward drawdownduration , replace
		sort reportdate
		drop negdate

		order reportdate total
		order fee cumfee-drawdownduration , after(total)
	/*
		cls 
		sum *
		sum * , detail
	*/
		export excel using "E:\Trading\Log/from`d'_${folder}_metrics.xlsx" , replace cell(A10) firstrow(variables) 

		//add summary statistics on top via excel formula
		putexcel set "E:\Trading\Log/from`d'_${folder}_metrics.xlsx" , modify
		putexcel_outputreset
		
		putexcel_wait A1 = "count" A2 = "mean" A3 = "std" A4 = "min" A5 = "p25" A6 = "p50" A7 = "p75" A8 = "max" A9 = "last"
		
		forv i = 2/14 { //loop over columns
			local c : word `i' of `c(ALPHA)'
			putexcel_wait `c'1 = formula(=COUNT(`c'11:`c'9999)) ///
					`c'2 = formula(=AVERAGE(`c'11:`c'9999)) ///
					`c'3 = formula(=STDEV(`c'11:`c'9999)) ///
					`c'4 = formula(=MIN(`c'11:`c'9999)) ///
					`c'5 = formula(=PERCENTILE(`c'11:`c'9999,0.25)) ///
					`c'6 = formula(=PERCENTILE(`c'11:`c'9999,0.5)) ///
					`c'7 = formula(=PERCENTILE(`c'11:`c'9999,0.75)) ///
					`c'8 = formula(=MAX(`c'11:`c'9999)) ///
					`c'9 = formula(`"=LOOKUP(2,1/(`c':`c'<>""),`c':`c')"')			
		}
		putexcel_dump
		restore
	}
}
