# Itus 
![](imgs/examplelarge.gif)
>**itus** [ˈɪt̪ʊs̠]
>*(noun)* A Latin word for *departure*

**Itus** is a small console application for looking up upcoming departures from a public transport stop in Norway.

This uses the Journey Planner V3 API provided by Entur.

# Installation

**Option 1:**  
```
pip install git+https://github.com/SebastianGrans/itus
```

**Option 2:**  
Clone and install. 
```
git clone https://github.com/SebastianGrans/itus
cd itus
pip install .
```


# Usage 

The stop or platform ID can be found on https://stoppested.entur.org/
   * E.g.: NSR:StopPlace:44085 and NSR:Quay:75708
   * Local references like ATB:Quay:16011265 can't be used. 

```
usage: itus.py [-h] [-s stop_id [stop_id ...]]
               [-p platform_id [platform_id ...]] [-n value] [-tr HH:MM]

optional arguments:
  -h, --help            Show this help message and exit

  -s stop_id [stop_id ...], 
  --stop stop_id [stop_id ...]
                        The stop id according to the national stop registry.
                        E.g. NSR:StopPlace:44085. Find it at https://stoppested.entur.org/

  -p platform_id [platform_id ...], 
  --platform platform_id [platform_id ...]
                        The quay id according to the national stop registry.
                        E.g. NSR:Quay:75708. Find it at https://stoppested.entur.org/

  -n value              Number of upcoming departures to look up. Default is 5.

  -tr HH:MM, --time_range HH:MM
                        How long into the into the future we look for
                        departures. Defaults to 1 hour.
```


