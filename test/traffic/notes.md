1. By keeping number of spawn vehicles low, one can simulate low intensity of traffic
2. At the same time increasing min distance and lowering internediate one can increase the traffic simulataneously and can generate good amount of trips
3. Runnning simulation for a longer duration of time can guarantee, low traffic for significant time and the peak traffic also
4. Reduncing the fringe factor can also guarantee uniform vehicle distribution
5. Increasing the binomial and lowering the p will increase the peaks while keeping average lower   

Currently using : python $SUMO_HOME/tools/randomTrips.py -n sumo.net.xml -r sumo.rou.xml -b 0 -e 6000 -p 0.04 --binomial 50  --min-distance 500 --fringe-factor 0.8 --intermediate 5  --trip-attributes 'departLane="best" departSpeed="max" departPos="random"' --random