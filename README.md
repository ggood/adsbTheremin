# adsbTheremin
Turns received ADS-B radio transmissions into music

Why?

Why not? Turn everything in our environment into music. 

Think about a theremin - a musical instrument played by bringing
your hands in proximity to an antenna on the instrument.
What if that antenna was your house, and instead of human
hands, our instrument was played by airplanes flying overhead?

This code listens to ADSB [https://www.faa.gov/nextgen/programs/adsb/]
trasmissions from aircraft, and turns those trasmission into
music.

Info about output format of dump1090:

http://www.airnavsystems.com/forum/index.php?topic=2896.0

To run this code, you need access to a computer that is running
dump1090. I'm running it on a Raspberry Pi Zero using the
FlightAware distro (https://flightaware.com/adsb/piaware/build).
This allows you to supply your received data to network of ground
stations that, in a crowdsourced fashion, feed data to a web site
that lets anyone see which aircraft are overhead.

You'll also need a music synthesizer - I use Ableton Live, but any
VST plugin host should work. In fact, the really creative part of
this is deciding what to do with the aircraft data. I've chosen
to make some very ambient tracks, but there's no reason this raw
data coudn't be turned into speedmetal. I hope someone will do
that at some point.

Some recent sonifications using this code:

[Long Airport Pads](https://soundcloud.com/gordongood/longairportpads)

Gordon Good
velo27@yahoo.com
