# sopel-modules
Some custom Sopel modules

## calc
Perform arbitrary math calculations.

```
Pilate> .calc floor(cos(pi*e))
bot> -1
```

## coinbase
Lookup current Coinbase spot prices.
```
Pilate> .coinbase
bot> Coinbase - BTC: $1783.57, ETH: $87.28, LTC: $33.04
```

## finance
Several triggers to display financial market data.

Symbols:
```
Pilate> .. goog nflx amzn
bot> GOOG (Alphabet Class C) Last: 928.78 -3.39 -0.3637% (Vol: 1162976) Daily Range: (925.16-932.00) 52-Week Range: (663.284-937.5)
bot> NFLX (Netflix Inc) Last: 160.28 +2.82 +1.79% (Vol: 6786342) Daily Range: (156.56-161.10) 52-Week Range: (84.5-161.1) Postmkt: 160.17 -0.11 -0.0686% (Vol: 59502)
bot> AMZN (Amazon.com Inc) Last: 948.95 -3.87 -0.4062% (Vol: 2021465) Daily Range: (945.00-953.7499) 52-Week Range: (682.115-957.89)
```

Forex:
```
Pilate> ..fx
bot> (EUR/USD 1.0866 +0.0 +0.0%) (GBP/USD 1.293 -0.0006 -0.0464%) (USD/JPY 114.33 +0.06 +0.05%) (USD/CHF 1.0089 +0.0001 +0.01%) (AUD/USD 0.7355 -0.0008 -0.1087%) (USD/CAD 1.3673 +0.002 +0.15%) (NZD/USD 0.6831 -0.0109 -1.5706%) (EUR/JPY 124.23 +0.06 +0.05%) (EUR/CHF 1.0963 +0.0001 +0.01%) (EUR/GBP 0.8403 +0.0006 +0.07%)
```

Bonds:
```
Pilate> ..b
bot> (US 2-YR 1.359 +0.0 +0.0%) (US 5-YR 1.935 +0.0 +0.0%) (US 10-YR 2.41 +0.0 +0.0%) (US 30-YR 3.036 +0.0 +0.0%)
```

Commodities:
```
Pilate> ..rtcom
bot> (OIL 47.38 +0.05 +0.11%) (GOLD 1218.6 -0.3 -0.0246%) (SILVER 16.195 -0.012 -0.07%) (NAT GAS 3.281 -0.011 -0.33%)
```

US markets:
```
Pilate> ..us
bot> (DJIA 20943.11 -32.67 -0.16%) (S&P 500 2399.63 +2.71 +0.11%) (NASDAQ 6129.14 +8.56 +0.14%) (NASD 100 5681.68 +3.37 +0.06%)
```

US futures:
```
Pilate> ..fus
bot> (DOW FUT 20894.0 +1.0 +0.0%) (S&P FUT 2394.75 -0.5 -0.02%) (NAS FUT 5673.75 -1.75 -0.03%)
```

Canadian markets:
```
Pilate> ..ca
bot> (TSX COMP 15633.21 +64.01 +0.41%)
```

EU markets:
```
Pilate> ..eu
bot> (DAX 12757.46 +8.34 +0.07%) (FTSE 7385.24 +43.03 +0.59%) (CAC 5400.46 +2.45 +0.05%)
```

Asian markets:
```
Pilate> ..asia
bot> (NIKKEI 19900.09 +0.0 +0.0%) (HSI 25015.42 +0.0 +0.0%) (SHANGHAI 3051.75 -28.78 -0.93%)
```

## sports
Display results of todays games. (Requires a stattleship API key)

```
Pilate> ..nba
bot> Spurs 47 - Rockets 52 (2nd Quarter, 2:27), Celtics 102 - Wizards 121 (F), Cavaliers 109 - Raptors 102 (F)

Pilate> ..nhl
bot> Ducks 1 - Oilers 7 (F), Blues 1 - Predators 3 (F)

Pilate> ..mlb
bot> Diamondbacks 4 - Dodgers 4 (5th), Rangers 0 - Mariners 0 (6th), ...
```

## twits

Some twitter stuff. (Requires an API key)

Latest tweet from a twitterer:
```
Pilate> ..tweet mets
bot> @mets: Tommy Boy! @TommyMilone_33 with an RBI single to extend our lead to 3-1! https://t.co/zGLmaZiv6t
```

Automatically prints tweet contents:
```
Pilate> https://twitter.com/RocketLeague/status/861638777701244928
bot> @Rocket League: What's coming in v1.34? Hit the link for details on our next update, coming later this week. https://t.co/2ZquPwVyz7 https://t.co/xZXhleq5r1
```


## ud
UrbanDictionary lookup.
```
Pilate> ..u pilate
bot> A form of torture created by Pontius Pilate, the man who crucified the savior.  It's not as easy as you might think. St. Paul was certified in Pilates and Advanced Spin.  The original 12 wanted to emphasize diet (bread, wine, omega 3s from fish oil, etc.)  This caused quite a schism as you might imagine.  This went on for awhile, until the Serfing craze caught on with the Barbarian invasion of Ringo, George, Cedric, and Dagobert.
```


## youtube
Print title and some meta information of pasted YouTube links. (Requires an API key)
```
Pilate> https://www.youtube.com/watch?v=dQw4w9WgXcQ
bot> YouTube - Rick Astley - Never Gonna Give You Up | Duration: 00:03:33 | Views: 312,075,375
```
