#!/bin/bash
curl -s "https://api.twelvedata.com/quote?symbol=GDAXI&exchange=XETR&apikey=c25b65a4f77c488ca9b318faf5b21ef7" | python3 -m json.tool
