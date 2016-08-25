#####Converts CHTS gps trips data to FT [passenger links](https://github.com/lmz/dyno-path/blob/patch-1/files/links.md) output.

---
### Assumptions:
CHTS gps trips file (w_gpstrips.csv) contains all the movements a person made during the day, and there is no obvious indicator for different sets of trips. So, some assumptions has been made to identify transit trips out of all the movements being made throughout the day.

* max access/egress walk = 50 min 
* max initial wait time = 30 min
* max transfer wait time = 20 min
* max egress time (to get off the transit vehicle) = 2 min