from enum import Enum

import requests

COOKIE_XSRF_TOKEN = "XSRF-TOKEN"
COOKIE_SSESYRANAC = "ssesyranac"

COOKIE_VALUE_SSESYRANAC = "token={}"

HEADER_XSRF_TOKEN = "X-XSRF-TOKEN"
HEADER_SSESYRANAC = "ssesyranac"
HEADER_AUTHORIZATION = "Authorization"

HEADER_VALUE_AUTHORIZATION = "Bearer {}"

URL_LOGIN_PAGE = "https://my.canary.is/login"
URL_LOGIN_API = "https://my.canary.is/api/auth/login"
URL_ME_API = "https://my.canary.is/api/customers/me"
URL_LOCATIONS_API = "https://my.canary.is/api/locations"
URL_READINGS_API = "https://my.canary.is/api/readings?deviceId={}&type={}"

ATTR_USERNAME = "username"
ATTR_EMAIL = "email"
ATTR_PASSWORD = "password"


class Api:
    def __init__(self, username, password, timeout=10):
        self._username = username
        self._password = password
        self._timeout = timeout
        self._token = None
        self._xsrf_token = None

    def login(self):
        r = requests.get(URL_LOGIN_PAGE)

        xsrf_token = r.cookies[COOKIE_XSRF_TOKEN]
        ssesyranac = r.cookies[COOKIE_SSESYRANAC]

        r = requests.post(URL_LOGIN_API, {
            ATTR_USERNAME: self._username,
            ATTR_PASSWORD: self._password
        }, headers={
            HEADER_XSRF_TOKEN: xsrf_token
        }, cookies={
            COOKIE_XSRF_TOKEN: xsrf_token,
            COOKIE_SSESYRANAC: ssesyranac
        })

        self._token = r.json()["access_token"]
        self._xsrf_token = xsrf_token

    def get_me(self):
        r = self._http_get(URL_ME_API, headers={
            HEADER_XSRF_TOKEN: self._xsrf_token,
            HEADER_AUTHORIZATION: HEADER_VALUE_AUTHORIZATION.format(self._token)
        }, cookies={
            COOKIE_XSRF_TOKEN: self._xsrf_token,
            COOKIE_SSESYRANAC: COOKIE_VALUE_SSESYRANAC.format(self._token)
        }, params={
            ATTR_EMAIL: self._username
        })

        return Customer(r.json())

    def get_locations(self):
        r = self._http_get(URL_LOCATIONS_API, headers={
            HEADER_XSRF_TOKEN: self._xsrf_token,
            HEADER_AUTHORIZATION: HEADER_VALUE_AUTHORIZATION.format(self._token)
        }, cookies={
            COOKIE_XSRF_TOKEN: self._xsrf_token,
            COOKIE_SSESYRANAC: COOKIE_VALUE_SSESYRANAC.format(self._token)
        })

        locations = []

        for location_json in r.json():
            devices_json = location_json["devices"]
            devices = []
            for device_json in devices_json:
                devices.append(Device(device_json))

            locations.append(Location(location_json, devices))

        return locations

    def get_readings(self, device):
        r = self._http_get(
            URL_READINGS_API.format(device.device_id, device.device_type),
            headers={
                HEADER_XSRF_TOKEN: self._xsrf_token,
                HEADER_AUTHORIZATION: HEADER_VALUE_AUTHORIZATION.format(self._token)
            }, cookies={
                COOKIE_XSRF_TOKEN: self._xsrf_token,
                COOKIE_SSESYRANAC: COOKIE_VALUE_SSESYRANAC.format(self._token)
            })

        readings = []
        for reading_json in r.json():
            readings.append(Reading(reading_json))

        return readings

    def _http_get(self, url, params=None, **kwargs):
        r = requests.get(url, params, **kwargs)
        status = r.status_code

        if str(status).startswith('4'):
            self.login()
            r = requests.get(url, params, **kwargs)

        return r


class Customer:
    def __init__(self, data):
        self._id = data["id"]
        self._first_name = data["first_name"]
        self._last_name = data["last_name"]
        self._is_celsius = data["celsius"]

    @property
    def customer_id(self):
        return self._id

    @property
    def first_name(self):
        return self._first_name

    @property
    def last_name(self):
        return self._last_name

    @property
    def is_celsius(self):
        return self._is_celsius


class Location:
    def __init__(self, data, devices):
        self._id = data["id"]
        self._name = data["name"]
        self._resource_uri = data["resource_uri"]
        self._devices = devices
        self._location_mode = LocationMode(data["mode"])
        self._is_private = data["is_private"]

    @property
    def location_id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def location_mode(self):
        return self._location_mode

    @property
    def resource_uri(self):
        return self._resource_uri

    @property
    def devices(self):
        return self._devices

    @property
    def is_private(self):
        return self._is_private


class LocationMode(Enum):
    AWAY = "away"
    HOME = "home"
    NIGHT = "night"


class Device:
    def __init__(self, data):
        self._id = data["id"]
        self._name = data["name"]
        self._device_mode = DeviceMode(data["device_mode"])
        self._is_online = data["online"]
        self._device_type = data["device_type"]

    @property
    def device_id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def device_mode(self):
        return self._device_mode

    @property
    def is_online(self):
        return self._is_online

    @property
    def device_type(self):
        return self._device_type


class DeviceMode(Enum):
    DISARMED = "disarmed"
    ARMED = "armed"
    PRIVACY = "privacy"


class Reading:
    def __init__(self, data):
        self._sensor_type = SensorType(data["sensor_type"])
        self._status = data["status"]
        self._value = data["value"]

    @property
    def sensor_type(self):
        return self._sensor_type

    @property
    def status(self):
        return self._status

    @property
    def value(self):
        return self._value


class SensorType(Enum):
    AIR_QUALITY = "air_quality"
    HUMIDITY = "humidity"
    TEMPERATURE = "temperature"