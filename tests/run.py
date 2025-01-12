from datetime import datetime, timedelta, timezone
from src.garage61api.client import Garage61Client

"""
Test script
"""

def __run_test():

    # Set your access token. If you use OAuth and want to test refresh token - set all variables.

    token = "YOUR_ACCESS_TOKEN"
    refresh_token = ""
    client_id = ""
    client_secret = ""
    redirect_uri = ""

    # Team slug, event and lap IDs to test them (optional)

    team_slug = ""
    event_id = ""
    lap_id = ""


    # Test body

    print("Test started")
    g61 = Garage61Client(token=token)
    print("Client instance created")

    gt = input("Refresh token? (y/n) ")
    if gt.lower() == 'y' and len(refresh_token) > 0 and len(client_id) > 0 and len(client_secret) > 0 and len(redirect_uri) > 0:
        new_token = g61.refresh_token(
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )
        print(new_token)
        g61.set_token(new_token['access_token'])
        print(".refresh_token OK")
    elif gt.lower() == 'y':
        print(".refresh_token --FAILED--")
        print("Set refresh_token, client_id, client_secret and redirect_uri to use refresh_token")

    g61.me()
    print("/me OK")

    g61.me_accounts(rating_history=True)
    print("/me/accounts OK")

    g61.me_statistics(date_start=datetime.now(timezone.utc) - timedelta(days=7), cars=[119, 10])
    print("/me/statistics OK")

    g61.teams()
    print("/teams OK")

    if len(team_slug) > 0:
        g61.teams(team_id=team_slug)
        print("/teams/{id} OK")

        g61.teams(team_id=team_slug, team_statistics=True)
        print("/teams/{id}/statistics OK")

    g61.cars()
    print("/cars OK")

    g61.car_groups()
    print("/car_groups OK")

    g61.tracks()
    print("/tracks OK")

    g61.platforms()
    print("/platforms OK")

    if len(lap_id) > 0:
        csv = g61.lap_csv(lap_id=lap_id)
        if type(csv) is not str or len(csv) < 500:
            print("/laps/{id}/csv --FAILED--")
        else:
            print("/laps/{id}/csv OK")

        g61.laps(lap_id=lap_id)
        print("/laps/{id} OK")

    g61.laps()
    print("/laps OK")

    if len(event_id) > 0:
        g61.laps(event_id=event_id)
        print("/laps with event ID OK")

    print("Test Passed!")


if __name__ == "__main__":
    __run_test()