from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from fast_flights import FlightData, Passengers, create_filter, get_flights

app = FastAPI()

class FlightRequest(BaseModel):
    origin: str
    destination: str
    depart_date: str
    return_date: str
    adults: int = 1
    type: str = "economy"
    max_stops: int = None
    inject_eu_cookies: bool = False

def flight_to_dict(flight):
    return {
        "is_best": getattr(flight, 'is_best', None),
        "name": getattr(flight, 'name', None),
        "departure": getattr(flight, 'departure', None),
        "arrival": getattr(flight, 'arrival', None),
        "arrival_time_ahead": getattr(flight, 'arrival_time_ahead', None),
        "duration": getattr(flight, 'duration', None),
        "stops": getattr(flight, 'stops', None),
        "delay": getattr(flight, 'delay', None),
        "price": getattr(flight, 'price', None),
    }

def result_to_dict(result):
    return {
        "current_price": getattr(result, 'current_price', None),
        "flights": [flight_to_dict(flight) for flight in getattr(result, 'flights', [])]
    }

@app.post("/get_flights")
async def get_flight_info(request: FlightRequest):
    # Create a new filter
    filter = create_filter(
        flight_data=[
            FlightData(
                date=request.depart_date,
                from_airport=request.origin,
                to_airport=request.destination
            ),
            FlightData(
                date=request.return_date,
                from_airport=request.destination,
                to_airport=request.origin
            ),
        ],
        trip="round-trip",
        seat=request.type,
        passengers=Passengers(
            adults=request.adults,
            children=0,
            infants_in_seat=0,
            infants_on_lap=0
        ),
        max_stops=request.max_stops
    )

    b64 = filter.as_b64().decode('utf-8')
    flight_url = f"https://www.google.com/travel/flights?tfs={b64}"

    # Get flights with the filter
    result = get_flights(filter, inject_eu_cookies=request.inject_eu_cookies)

    try:
        result_dict = result_to_dict(result)
        return {"url": flight_url, "flights": result_dict}
    except TypeError as e:
        raise HTTPException(status_code=500, detail="Error in processing flight data")

