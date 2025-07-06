from geo_lookup import GeoLookup
from weather_fetcher import WeatherFetcher

def main():
    # geo lookup
    geo = GeoLookup()
    geo.run()
    
    # weather fetching
    weather_fetcher = WeatherFetcher()
    weather_fetcher.run('current')
    weather_fetcher.run('forecast')
    weather_fetcher.run('air_pollution')

if __name__ == "__main__":
    main()
