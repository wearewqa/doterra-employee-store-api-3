from __future__ import print_function
import time
from pyxb.utils.six.moves.urllib import request as urllib_request
import weather   # Bindings generated by PyXB
import pyxb.utils.domutils as domutils

uri = 'http://wsf.cdyne.com/WeatherWS/Weather.asmx/GetCityForecastByZIP?ZIP=55113'
xml = urllib_request.urlopen(uri).read()
doc = domutils.StringToDOM(xml)
fc_return = weather.CreateFromDOM(doc.documentElement)
if fc_return.Success:
    print('Weather forecast for %s, %s:' % (fc_return.City, fc_return.State))
    for fc in fc_return.ForecastResult.Forecast:
        when = time.strftime('%A, %B %d %Y', fc.Date.timetuple())
        outlook = fc.Desciption # typos in WSDL left unchanged
        low = fc.Temperatures.MorningLow
        high = fc.Temperatures.DaytimeHigh
        print('  %s: %s, from %s to %s' % (when, outlook, low, high))