print("Essaie pour découvrir les fonctions de R")

# librairie TimeSeries
require(timeSeries)
myvector = .1*(1:72) + sin((1:72)*pi/12) + rnorm(72, mean=0, sd=.3)
myts = ts(myvector, start=c(2009, 1), end=c(2014,12), frequency=12)

# librairie caschrono

data("sunspots")
help("sunspots")
plot.ts(sunspots, xlab="année", ylab="Nombre de taches solaires")

