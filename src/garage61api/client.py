import json
import requests
from typing import Literal
from datetime import datetime, timezone
from importlib import resources as impresources


class Garage61Client:
    def __init__(self,
                 token: str
                 ):
        """
        Garage61Client is a simple Python wrapper around the Garage61 API with synchronous functions.

        Garage61 API Docs: https://garage61.net/developer
        GitHub: https://github.com/KuzmaLesnoy/garage61api

        Class using file "ids.json" as a source of convertion IDs from iRacing to Garage61 ones.

        - set_token: set new access token.
        - use_garage61_ids: False by default. If you provide Garage61 car and track IDs instead of iRacing ones set to True.
        - ids: dict of track and cars IDs.
        """
        self._session = requests.Session()
        self._base_url = "https://garage61.net/api/v1/"
        self._token = token
        self._use_garage61_ids = False
        ids_file = impresources.files() / 'ids.json'
        with ids_file.open('rt') as f:
            self.ids = json.loads(f.read())


    ####################################
    #   Setters
    ####################################


    def set_token(self, new_token: str) -> None:
        self._token = new_token
    def use_garage61_ids(self, value: bool) -> None:
        self._use_garage61_ids = value


    ####################################
    #   Functions
    ####################################


    def _build_url(self,
                   endpoint: str
                   ) -> str:
        return self._base_url + endpoint

    def _ids_converter(self,
                       track_ids: int | list[int] | None = None,
                       car_ids: int | list[int] | None = None
                       ) -> int | list[int]:

        def _get_track_id(iracing_track_id: int) -> int:
            if self._use_garage61_ids:
                return iracing_track_id
            for tr in self.ids['tracks']:
                if tr['ir_id'] == iracing_track_id:
                    return tr['g61_id']
            raise ValueError(f"Track ID {iracing_track_id} not found!")
        def _get_car_id(iracing_car_id: int) -> int:
            if self._use_garage61_ids:
                return iracing_car_id
            if iracing_car_id < 0:
                return iracing_car_id
            for car in self.ids['cars']:
                if car['ir_id'] == iracing_car_id:
                    return car['g61_id']
            raise ValueError(f"Car ID {iracing_car_id} not found!")


        if track_ids and car_ids:
            raise ValueError("Provide values for car OR track IDs")
        if not track_ids and not car_ids:
            return None
        if self._use_garage61_ids:
            return car_ids if car_ids else track_ids

        if car_ids:
            if isinstance(car_ids, list):
                for i, c in enumerate(car_ids):
                    car_ids[i] = _get_car_id(c)
            else:
                car_ids = _get_car_id(car_ids)
            return car_ids

        if track_ids:
            if isinstance(track_ids, list):
                for i, t in enumerate(track_ids):
                    track_ids[i] = _get_track_id(t)
            else:
                track_ids = _get_track_id(track_ids)
            return track_ids

    def _add_payload(self,
                     payload: dict
                     ) -> str:
        if not payload:
            return ""
        payload_url = "?"
        for k, v in payload.items():
            if v is not None:
                payload_url += f"&{k}={v}"
        return payload_url

    def _create_payload(self, **kwargs):
        if not kwargs:
            return None
        for k, v in kwargs.copy().items():
            if v is None:
                kwargs.pop(k)
                continue
            if isinstance(v, datetime):
                kwargs[k] = v.astimezone(timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds') + "Z"
            if isinstance(v, list):
                kwargs[k] = ','.join(map(str, v))
        return kwargs

    def _get_resource(self,
                      endpoint: str,
                      payload: dict | None = None
                       ) -> list | dict | None:
        request_url = self._build_url(endpoint)
        if payload:
            request_url += self._add_payload(payload)
        header = {'Authorization': f"Bearer {self._token}"}
        r = self._session.get(request_url, headers=header)
        return r.json()


    ####################################
    #   Functions available to user
    ####################################


    def refresh_token(self,
                      refresh_token: str,
                      client_id: str,
                      client_secret: str,
                      redirect_uri: str
                      ) -> dict:
        """
        Function for getting a new Access Token using a Refresh Token. Used in applications with OAuth2 authorization.

        Your application should check the validity of the Access Token itself and, when it expires, use the Refresh Token to obtain a new one.

        Details: https://de.garage61.net/developer/authentication

        :param refresh_token: refresh token.
        :param client_id: client ID of your application.
        :param client_secret: client secret of your application.
        :param redirect_uri: redirect of your application.

        :return: dict containing new Access Token and validity time.
        """
        token_url = "https://garage61.net/api/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri
        }

        r = self._session.post(token_url, data=data)
        r.raise_for_status()
        return r.json()


    ####################################
    #   General information
    ####################################


    def me(self) -> dict:
        """
        Information about the currently authenticated user.

        Structure of response: https://garage61.net/developer/endpoints/v1/me

        :return: A dictionary representing the currently authenticated user.
        """
        return self._get_resource(endpoint="me")

    def me_accounts(self,
                    rating_history: bool = False
                    ) -> list[dict]:
        """
        Get linked accounts for the current user such as the iRacing account.

        Structure of response: https://garage61.net/developer/endpoints/v1/getAccounts

        :param rating_history: optionally include rating history.

        :return: A dictionary for each attached account, optionally with their history.
        """
        return self._get_resource(
            endpoint="me/accounts",
            payload=self._create_payload(ratingHistory=rating_history)
        )['items']

    def me_statistics(self,
                      date_start: datetime | str | None = None,
                      date_end: datetime | str | None = None,
                      cars: int | list[int] | None = None,
                      tracks: int | list[int] | None = None,
                      ) -> list[dict]:
        """
        Driving statistics for the authenticated user.
        Each returned record is a combination of car, track and day. You'll need to sum up these rows according to the specific numbers you want to calculate (e.g. per car).

        Structure of response: https://garage61.net/developer/endpoints/v1/getStatistics

        :param date_start: select statistics starting at this date.
        :param date_end: select statistics ending at this date.
        :param cars: car IDs to search for (int or list of ints).
        :param tracks: track IDs to search for (int or list of ints).

        :return: A list representing the driving statistics.
        """
        return self._get_resource(
            endpoint="me/statistics",
            payload=self._create_payload(
                start=date_start,
                end=date_end,
                cars=self._ids_converter(car_ids=cars),
                tracks=self._ids_converter(track_ids=tracks)
            )
        )['drivingStatistics']

    def teams(self,
              team_id: str | None = None,
              team_statistics: bool | None = None,
              date_start: datetime | str | None = None,
              date_end: datetime | str | None = None,
              cars: int | list[int] | None = None,
              tracks: int | list[int] | None = None,
              ) -> list[dict] | dict:
        """
        Joined teams if Team ID is not provided.
        Teams that the authenticated user is part of.

        Structure of responses:
         - https://garage61.net/developer/endpoints/v1/findTeams
         - https://garage61.net/developer/endpoints/v1/getTeam
         - https://garage61.net/developer/endpoints/v1/getTeamStatistics


        If arguments provided:

        This method only returns information about teams that the authenticated user is a member of.
        The member list of a team might not be included if the authenticated user is not a team owner and the team is configured to only show the member list to team owners.

        :param team_id: team ID or Slug to get information about a specific team.
        :param team_statistics: team_id is required! Get team driving statistics. Driving statistics for the members of the team. Each returned record is a combination of car, track, day and driver.
            You'll need to sum up these rows according to the specific numbers you want to calculate (e.g. per car).
        :param date_start: team_id is required! Select statistics starting at this date.
        :param date_end: team_id is required! Select statistics ending at this date.
        :param cars: team_id is required! Car IDs to search for (int or list of ints).
        :param tracks: team_id is required! Track IDs to search for (int or list of ints).

        :return: A list or dict representing user teams, specific team or team statistics.
        """
        if not team_id:
            return self._get_resource(endpoint="teams")['items']
        elif not team_id and team_statistics:
            raise ValueError("Provide team ID to get statistics")
        elif team_id and not team_statistics:
            return self._get_resource(endpoint=f"teams/{team_id}")
        else:
            return self._get_resource(
                endpoint=f"teams/{team_id}/statistics",
                payload=self._create_payload(
                    start=date_start,
                    end=date_end,
                    cars=self._ids_converter(car_ids=cars),
                    tracks=self._ids_converter(track_ids=tracks)
                )
            )['drivingStatistics']


    ####################################
    #   Content
    ####################################


    def car_groups(self) -> list[dict]:
        """
        Available car groups.

        Car groups to which the user has access. This is a personalized view and depends on the enabled platforms.
        For simulator platforms such as iRacing, this returns all available car groups, not just the ones that are owned by the user.

        Structure of response: https://garage61.net/developer/endpoints/v1/findCarGroups

        :return: A list representing available car groups.
        """
        return self._get_resource(endpoint="car-groups")['items']

    def cars(self) -> list[dict]:
        """
        Available cars.

        Cars to which the user has access. This is a personalized view and depends on the enabled platforms.
        For simulator platforms such as iRacing, this returns all available cars, not just the ones that are owned by the user.

        Structure of response: https://garage61.net/developer/endpoints/v1/findCars

        :return: A list representing available car groups.
        """
        return self._get_resource(endpoint="cars")['items']

    def platforms(self) -> list[dict]:
        """
        Available platforms.

        All data is linked to a platform, which can either be a simulator platform (such as iRacing) or the real world (identified by -).

        Only platforms to which the user has access are returned.

        Structure of response: https://garage61.net/developer/endpoints/v1/findPlatforms

        :return: A list representing platforms.
        """
        return self._get_resource(endpoint="platforms")['items']

    def tracks(self) -> list[dict]:
        """
        Available tracks.

        Tracks to which the user has access. This is a personalized view and depends on the enabled platforms.
        For simulator platforms such as iRacing, this returns all available tracks, not just the ones that are owned by the user.

        Structure of response: https://garage61.net/developer/endpoints/v1/findTracks

        :return: A list representing available tracks.
        """
        return self._get_resource(endpoint="tracks")['items']


    ####################################
    #   Driving data
    ####################################


    def laps(self,
             lap_id: str | None = None,
             cars: int | list[int] | None = None,
             tracks: int | list[int] | None = None,
             iracing_seasons: int | list[int] | None = None,
             drivers: Literal["me", "following"] | list[Literal["me", "following"]] | None = None,
             teams: str | list[str] | None = None,
             extra_drivers: str | list[str] | None = None,
             age: int | None = None,
             date_after: datetime | str | None = None,
             session_types: Literal[1, 2, 3] | list[Literal[1, 2, 3]] | None = None,
             setup_types: Literal[1, 2] | list[Literal[1, 2]] | None = None,
             telemetry_required: bool | None = None,
             ghost_lap_required: bool | None = None,
             setup_required: bool | None = None,
             lap_types: Literal[1, 2, 3, 4] | list[Literal[1, 2, 3, 4]] | None = None,
             event_id: str | None = None,
             include_unclean: bool | None = None,
             min_rating: int | None = None,
             max_rating: int | None = None,
             min_fuel: float | None = None,
             max_fuel: float | None = None,
             min_fuel_used: float | None = None,
             max_fuel_used: float | None = None,
             min_lap_time: float | None = None,
             max_lap_time: float | None = None,
             min_cond_track_usage: int | None = None,
             max_cond_track_usage: int | None = None,
             min_cond_track_wetness: int | None = None,
             max_cond_track_wetness: int | None = None,
             min_cond_track_temp: float | None = None,
             max_cond_track_temp: float | None = None,
             min_cond_air_temp: float | None = None,
             max_cond_air_temp: float | None = None,
             min_cond_wind_vel: float | None = None,
             max_cond_wind_vel: float | None = None,
             min_cond_relative_humidity: float | None = None,
             max_cond_relative_humidity: float | None = None,
             min_cond_fog_level: float | None = None,
             max_cond_fog_level: float | None = None,
             min_cond_precipitation: float | None = None,
             max_cond_precipitation: float | None = None,
             min_cond_cloud: Literal[1, 2, 3, 4] | list[Literal[1, 2, 3, 4]] | None = None,
             max_cond_cloud: Literal[1, 2, 3, 4] | list[Literal[1, 2, 3, 4]] | None = None,
             cond_wind_dir: Literal[1, 2, 3, 4] | list[Literal[1, 2, 3, 4]] | None = None,
             rounding: Literal["metric", "englishStandard"] | None = None,
             group: Literal["driver", "driver-car", "none"] | None = None,
             limit: int | None = None,
             offset: int | None = None
             ) -> list[dict]:
        """
        Available tracks.

        Tracks to which the user has access. This is a personalized view and depends on the enabled platforms.
        For simulator platforms such as iRacing, this returns all available tracks, not just the ones that are owned by the user.

        Detailed Info: https://garage61.net/developer/endpoints/v1/findLaps

        Lap Filtering Docs: https://garage61.net/docs/usage/filtering

        The drivers selected by "drivers" are combined with those from the "teams" and "extra_drivers" parameters. If none of these parameters are given, yourself and all teammates will be selected.

        Limitations

        This method only returns laps driven yourself or your teammates. Use the relevant parameters to choose the desired selection of laps. For privacy reasons, no global lap search is available.
        Data returned adheres to the defined privacy settings and is thus specific to the user linked to the API token.

        :param lap_id: lap ID returns all info about a specific lap if provided. Ignoring other filters. Structure of response: https://garage61.net/developer/endpoints/v1/getLap
        :param cars: car IDs to search for (int or list of ints).
        :param teams: teams to include (by team slug) (str or list of str). Teammates from the given teams will be included in the results.
        :param tracks: track IDs to search for (int or list of ints).
        :param iracing_seasons: season IDs to search for (int or list of ints). Seasons (and their IDs) can be found in the ".platforms".
        :param drivers: drivers to include. Available values: me, following (str or list of str).
        :param extra_drivers: extra drivers to include (by user slug) (str or list of str).
        :param age: maximum lap age. Any positive number represents the maximum number of days ago (e.g. 7 would restrict the search to all laps driven in the past week). A negative value is interpreted as follows: Current season: -1; Current and previous season: -2; Last 3 seasons: -3; Last 4 seasons: -4.
        :param date_after: laps driven after given date (datetime or str).
        :param session_types: filter by session type (default = all) (int or list of ints). Available values: 1: Practice; 2: Qualifying; 3: Race.
        :param setup_types: filter by session setup type (default = all) (int or list of ints). Available values: 1: Open setup; 2: Fixed setup.
        :param telemetry_required: require the telemetry of each lap to be visible (bool). Requires the calling user to have a Pro plan.
        :param ghost_lap_required: require the ghost lap of each lap to be visible (bool). Only selects laps that have a ghost lap available. Requires the calling user to have a Pro plan.
        :param setup_required: require the setup of each lap to be visible (bool). Only selects laps that have a setup available. Requires the calling user to have a Pro plan.
        :param lap_types: filter by lap type (default = normal laps only) (int or list of ints). Available values: 1: Normal (full) laps; 2: Joker laps; 3: Out laps (exiting the pitlane); 4: In laps (entering the pitlane).
        :param event_id: laps for given event ID (str).
        :param include_unclean: allow returning unclean (and potentially incomplete) laps.
        :param min_rating: minimum driver rating.
        :param max_rating: maximum driver rating.
        :param min_fuel: minimum fuel level.
        :param max_fuel: maximum fuel level.
        :param min_fuel_used: minimum fuel used in lap.
        :param max_fuel_used: maximum fuel used in lap.
        :param min_lap_time: minimum lap time.
        :param max_lap_time: maximum lap time.
        :param min_cond_track_usage: minimum track usage, as a percentage (0 = clean track, 100 = fully rubberised).
        :param max_cond_track_usage: maximum track usage, as a percentage (0 = clean track, 100 = fully rubberised).
        :param min_cond_track_wetness: minimum track wetness, as a percentage (0 = dry, 100 = fully wet).
        :param max_cond_track_wetness: maximum track wetness, as a percentage (0 = dry, 100 = fully wet).
        :param min_cond_track_temp: minimum track temperature (℃).
        :param max_cond_track_temp: maximum track temperature (℃).
        :param min_cond_air_temp: minimum air temperature (℃).
        :param max_cond_air_temp: maximum air temperature (℃).
        :param min_cond_wind_vel: minimum wind velocity (m/s).
        :param max_cond_wind_vel: maximum wind velocity (m/s).
        :param min_cond_relative_humidity: minimum relative humidity.
        :param max_cond_relative_humidity: maximum relative humidity.
        :param min_cond_fog_level: minimum fog level.
        :param max_cond_fog_level: maximum fog level.
        :param min_cond_precipitation: minimum precipitation.
        :param max_cond_precipitation: maximum precipitation.
        :param min_cond_cloud: minimum cloud cover (int or list of ints). Available values: 1: Clear skies; 2: Partly cloudy; 3: Mostly cloudy; 4: Overcast.
        :param max_cond_cloud: maximum cloud cover (int or list of ints). Available values: 1: Clear skies; 2: Partly cloudy; 3: Mostly cloudy; 4: Overcast.
        :param cond_wind_dir: allowed wind directions (int or list of ints). Available values: 1: North; 2: East; 3: South; 4: West.
        :param rounding: correct parameters for rounding (str). When using the web app, lap searches are adjusted slightly to compensate for the fact that values are rounded for display. Supply the desired display units to apply rounding correction on your lap search. Available values: "metric", "englishStandard".
        :param group: grouping of results, determines which laps will be returned (default: driver) (str). Available values: "driver": Personal best laps per driver; "driver-car": Personal best laps per driver/car combination; "none": Return all laps.
        :param limit: limit results to the given amount of laps (maximum and default is 1000) (int).
        :param offset: start results at given offset (int).

        :return: A list of dicts representing lap(s).
        """
        if lap_id:
            return [self._get_resource(endpoint=f"laps/{lap_id}")]
        return self._get_resource(
            endpoint="laps",
            payload=self._create_payload(
                cars=self._ids_converter(car_ids=cars),
                tracks=self._ids_converter(track_ids=tracks),
                seasons=iracing_seasons,
                drivers=drivers,
                teams=teams,
                extraDrivers=extra_drivers,
                age=age,
                after=date_after,
                sessionTypes=session_types,
                sessionSetupTypes=setup_types,
                seeTelemetry=telemetry_required,
                seeGhostLap=ghost_lap_required,
                seeSetup=setup_required,
                lapTypes=lap_types,
                event=event_id,
                unclean=include_unclean,
                minRating=min_rating,
                maxRating=max_rating,
                minFuel=min_fuel,
                maxFuel=max_fuel,
                minFuelUsed=min_fuel_used,
                maxFuelUsed=max_fuel_used,
                minLapTime=min_lap_time,
                maxLapTime=max_lap_time,
                minConditionsTrackUsage=min_cond_track_usage,
                maxConditionsTrackUsage=max_cond_track_usage,
                minConditionsTrackWetness=min_cond_track_wetness,
                maxConditionsTrackWetness=max_cond_track_wetness,
                minConditionsTrackTemp=min_cond_track_temp,
                maxConditionsTrackTemp=max_cond_track_temp,
                minConditionsAirTemp=min_cond_air_temp,
                maxConditionsAirTemp=max_cond_air_temp,
                minConditionsWindVel=min_cond_wind_vel,
                maxConditionsWindVel=max_cond_wind_vel,
                minConditionsRelativeHumidity=min_cond_relative_humidity,
                maxConditionsRelativeHumidity=max_cond_relative_humidity,
                minConditionsFogLevel=min_cond_fog_level,
                maxConditionsFogLevel=max_cond_fog_level,
                minConditionsPrecipitation=min_cond_precipitation,
                maxConditionsPrecipitation=max_cond_precipitation,
                minConditionsCloud=min_cond_cloud,
                maxConditionsCloud=max_cond_cloud,
                conditionsWindDir=cond_wind_dir,
                round=rounding,
                group=group,
                limit=limit,
                offset=offset
            )
        )['items']

    def lap_csv(self,
                lap_id: str
                ) -> str:
        """
        Export the telemetry for a lap as a CSV file. Returns a CSV file with the telemetry for the requested lap (if available). Required permissions: driving_data

        Limitations
        This method only returns laps driven yourself or your teammates. Data returned adheres to the defined privacy settings and is thus specific to the user linked to the API token.

        Structure of response: https://garage61.net/developer/endpoints/v1/getLapCSV

        :param lap_id: lap ID (required).

        :return: A str representing 'text/csv'.
        """
        request_url = self._build_url(f"laps/{lap_id}/csv")
        header = {'Authorization': f"Bearer {self._token}"}
        r = self._session.get(request_url, headers=header)
        return r.content.decode("utf-8")