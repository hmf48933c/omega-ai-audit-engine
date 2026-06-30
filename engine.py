#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Proprietary Horary Astrology Engine (Interactive Location + Interactive Date/Time)
Colab-safe: auto-installs missing dependencies (pyswisseph, astral, pytz)

IMPORTANT:
- Integrates dynamic Prashna Sthaana (Question Focus) logic based on the Hora Lord's D9 Tatva.
- Computes focus for the Primary Lagna and iterates over all Follow-up Lagnas.

Usage in Google Colab:
1) Put this entire script in a cell and run.
2) It will auto-install missing packages if needed.
3) It will prompt you for location + timezone + lat/lon, then date/time.

Dependencies:
- pyswisseph (import name: swisseph)
- astral
- pytz
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
import secrets

# ------------------------- Colab-safe installer -------------------------

def _pip_install(package: str) -> None:
    """Install a package via pip in the current Python environment."""
    print(f"Installing missing dependency: {package}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])

# Ensure pytz
try:
    import pytz  # type: ignore
except ModuleNotFoundError:
    _pip_install("pytz")
    import pytz  # type: ignore

# Ensure astral
try:
    from astral import LocationInfo  # type: ignore
    from astral.sun import sun  # type: ignore
except ModuleNotFoundError:
    _pip_install("astral")
    from astral import LocationInfo  # type: ignore
    from astral.sun import sun  # type: ignore

# Ensure pyswisseph (imported as swisseph)
try:
    import swisseph as swe  # type: ignore
except ModuleNotFoundError:
    _pip_install("pyswisseph")
    import swisseph as swe  # type: ignore

# ------------------------- Config / Switches -------------------------

# How to assign pre-sunrise horas:
#   "previous" = pre-sunrise belongs to previous night's weekday-ruler label
#   "current"  = pre-sunrise attached to current date's weekday-ruler label
HORA_CONVENTION = "current"

# Show a 24-hour table of hora start times (helpful for verification)
SHOW_HORA_TABLE = False

# ------------------------- Swiss Ephemeris -------------------------

EPHE_DIR = "ephe"
if not os.path.exists(EPHE_DIR):
    print(f"Creating directory for ephemeris files at: {os.path.abspath(EPHE_DIR)}")
    os.makedirs(EPHE_DIR)
swe.set_ephe_path(EPHE_DIR)

# Lahiri ayanamsa
swe.set_sid_mode(swe.SIDM_LAHIRI)

# ----------------------------- Constants --------------------------------

RASHIS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

PLANET_NAME_TO_SWEPH = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS, 'Mercury': swe.MERCURY,
    'Jupiter': swe.JUPITER, 'Venus': swe.VENUS, 'Saturn': swe.SATURN
}
PLANET_NAMES = list(PLANET_NAME_TO_SWEPH.keys())

# Chaldean order
CHALDEAN_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

# Python weekday: Monday=0 ... Sunday=6  (weekday ruler defined at sunrise)
WEEKDAY_RULERS = {
    0: "Moon", 1: "Mars", 2: "Mercury", 3: "Jupiter",
    4: "Venus", 5: "Saturn", 6: "Sun"
}

FOLLOWUP_REF_PLANET_SEQ = ['Moon', 'Sun', 'Jupiter', 'Venus', 'Mercury']

# Proprietary mapping (lagna_offset only)
NUMBER_LAGNA_MAP = {
    111: {'lagna_offset': 1}, 112: {'lagna_offset': 2}, 113: {'lagna_offset': 3}, 114: {'lagna_offset': 4},
    121: {'lagna_offset': 5}, 122: {'lagna_offset': 6}, 123: {'lagna_offset': 7}, 124: {'lagna_offset': 8},
    131: {'lagna_offset': 2}, 132: {'lagna_offset': 3}, 133: {'lagna_offset': 4}, 134: {'lagna_offset': 5},
    141: {'lagna_offset': 6}, 142: {'lagna_offset': 7}, 143: {'lagna_offset': 8}, 144: {'lagna_offset': 9},
    211: {'lagna_offset': 3}, 212: {'lagna_offset': 4}, 213: {'lagna_offset': 5}, 214: {'lagna_offset': 6},
    221: {'lagna_offset': 7}, 222: {'lagna_offset': 8}, 223: {'lagna_offset': 9}, 224: {'lagna_offset': 10},
    231: {'lagna_offset': 4}, 232: {'lagna_offset': 5}, 233: {'lagna_offset': 6}, 234: {'lagna_offset': 7},
    241: {'lagna_offset': 8}, 242: {'lagna_offset': 9}, 243: {'lagna_offset': 10}, 244: {'lagna_offset': 11},
    311: {'lagna_offset': 5}, 312: {'lagna_offset': 6}, 313: {'lagna_offset': 7}, 314: {'lagna_offset': 8},
    321: {'lagna_offset': 9}, 322: {'lagna_offset': 10}, 323: {'lagna_offset': 11}, 324: {'lagna_offset': 12},
    331: {'lagna_offset': 6}, 332: {'lagna_offset': 7}, 333: {'lagna_offset': 8}, 334: {'lagna_offset': 9},
    341: {'lagna_offset': 10}, 342: {'lagna_offset': 11}, 343: {'lagna_offset': 12}, 344: {'lagna_offset': 1},
    411: {'lagna_offset': 7}, 412: {'lagna_offset': 8}, 413: {'lagna_offset': 9}, 414: {'lagna_offset': 10},
    421: {'lagna_offset': 11}, 422: {'lagna_offset': 12}, 423: {'lagna_offset': 1}, 424: {'lagna_offset': 2},
    431: {'lagna_offset': 8}, 432: {'lagna_offset': 9}, 433: {'lagna_offset': 10}, 434: {'lagna_offset': 11},
    441: {'lagna_offset': 12}, 442: {'lagna_offset': 1}, 443: {'lagna_offset': 2}, 444: {'lagna_offset': 3}
}

RASHI_LORDS = {
    'Aries': ['Mars'], 'Taurus': ['Venus'], 'Gemini': ['Mercury'],
    'Cancer': ['Moon'], 'Leo': ['Sun'], 'Virgo': ['Mercury'],
    'Libra': ['Venus'], 'Scorpio': ['Mars', 'Ketu'], 'Sagittarius': ['Jupiter'],
    'Capricorn': ['Saturn'], 'Aquarius': ['Saturn', 'Rahu'], 'Pisces': ['Jupiter']
}

# ------------------------ Interactive Prompts ------------------------

def _parse_float(prompt: str, default=None) -> float:
    while True:
        s = input(prompt).strip()
        if s == "" and default is not None:
            return float(default)
        try:
            return float(s)
        except Exception:
            print("Please enter a valid number (example: 34.9888).")

def _parse_tz(prompt: str, default=None) -> str:
    while True:
        s = input(prompt).strip()
        if s == "" and default is not None:
            s = default
        try:
            pytz.timezone(s)
            return s
        except Exception:
            print("Invalid timezone. Examples: America/Chicago, America/New_York, Asia/Kolkata, Europe/London")

def ask_location_from_user():
    """
    Ask user for location label + timezone + lat/lon.
    Provides a quick default for Southaven, MS (user can override).
    """
    print("\nLOCATION SETUP")
    print("--------------")
    print("Timezone examples: America/Chicago, America/New_York, Asia/Kolkata, Europe/London")
    print("Longitude: West is negative (e.g., -89.9918). East is positive.\n")

    use_default = input("Use default location Southaven, Mississippi, USA? [Y/n]: ").strip().lower()
    if use_default in ("", "y", "yes"):
        location_label = "Southaven, Mississippi, USA"
        tz = "America/Chicago"
        lat = 34.9888
        lon = -89.9918
        print(f"→ Using default: {location_label} | {tz} | lat={lat} lon={lon}\n")
        return location_label, tz, lat, lon

    city = input("City (label only, e.g., Southaven): ").strip() or "Unknown City"
    region = input("Region/State (label only, e.g., Mississippi): ").strip() or ""
    country = input("Country (label only, e.g., USA): ").strip() or ""
    location_label = ", ".join([p for p in [city, region, country] if p])

    tz = _parse_tz("Timezone (IANA name, e.g., America/Chicago): ", default="America/Chicago")
    lat = _parse_float("Latitude  (e.g., 34.9888): ")
    lon = _parse_float("Longitude (e.g., -89.9918) [West is negative]: ")

    print(f"→ Using: {location_label} | {tz} | lat={lat} lon={lon}\n")
    return location_label, tz, lat, lon

def ask_datetime_from_user(tz: str):
    """
    Interactive prompt:
    - Press Enter to use current local time in the chosen timezone.
    - Or enter a specific local date & time.
    Returns:
        None -> use current time
        naive datetime -> will be localized to tz
    """
    print("\nTIME SETUP")
    print("----------")
    choice = input(f"Use CURRENT local time in {tz}? [Y/n]: ").strip().lower()
    if choice in ("", "y", "yes"):
        print("→ Using current local time.\n")
        return None

    date_str = input("Enter date (YYYY-MM-DD), e.g. 2025-12-10: ").strip()
    time_str = input("Enter time (HH:MM or HH:MM:SS, 24-hour), e.g. 09:30 or 09:30:00: ").strip()

    try:
        year, month, day = map(int, date_str.split("-"))
        parts = list(map(int, time_str.split(":")))
        if len(parts) == 2:
            hour, minute = parts
            second = 0
        elif len(parts) == 3:
            hour, minute, second = parts
        else:
            raise ValueError("Time must be HH:MM or HH:MM:SS")
        dt = datetime(year, month, day, hour, minute, second)
        print(f"→ Using custom local time: {dt} (will be interpreted in {tz})\n")
        return dt
    except Exception as e:
        print(f"Input error: {e}")
        print("Falling back to CURRENT local time.\n")
        return None

# ------------------------ Helpers (Engine core) ------------------------

def get_sun_times(lat, lon, tz, date):
    loc = LocationInfo(latitude=lat, longitude=lon)
    s = sun(loc.observer, date=date, tzinfo=pytz.timezone(tz))
    return s['sunrise'], s['sunset']

def get_planetary_hour_lord(now_local, lat, lon, tz):
    tzinfo = pytz.timezone(tz)
    now_local = now_local.astimezone(tzinfo)
    today = now_local.date()

    today_sunrise, today_sunset = get_sun_times(lat, lon, tz, today)
    next_sunrise, _ = get_sun_times(lat, lon, tz, today + timedelta(days=1))
    prev_sunrise, prev_sunset = get_sun_times(lat, lon, tz, today - timedelta(days=1))

    weekday_today = today_sunrise.weekday()
    weekday_prev = prev_sunrise.weekday()
    day_ruler_today = WEEKDAY_RULERS[weekday_today]
    day_ruler_prev = WEEKDAY_RULERS[weekday_prev]

    if today_sunrise <= now_local < today_sunset:
        elapsed = (now_local - today_sunrise).total_seconds()
        hora_len = (today_sunset - today_sunrise).total_seconds() / 12.0
        start_idx = CHALDEAN_ORDER.index(day_ruler_today)
    elif now_local >= today_sunset:
        elapsed = (now_local - today_sunset).total_seconds()
        hora_len = (next_sunrise - today_sunset).total_seconds() / 12.0
        start_idx = (CHALDEAN_ORDER.index(day_ruler_today) + 5) % 7
    else:
        elapsed = (now_local - prev_sunset).total_seconds()
        hora_len = (today_sunrise - prev_sunset).total_seconds() / 12.0
        if HORA_CONVENTION == "previous":
            start_idx = (CHALDEAN_ORDER.index(day_ruler_prev) + 5) % 7
        else:
            start_idx = (CHALDEAN_ORDER.index(day_ruler_today) + 5) % 7

    if hora_len <= 0:
        return "Unknown"

    hora_num = int(elapsed // hora_len)
    if hora_num > 11:
        hora_num = 11
    return CHALDEAN_ORDER[(start_idx + hora_num) % 7]

def print_hora_table(reference_dt_local, lat, lon, tz):
    reference_dt_local = reference_dt_local.astimezone(pytz.timezone(tz))
    today = reference_dt_local.date()

    today_sunrise, today_sunset = get_sun_times(lat, lon, tz, today)
    next_sunrise, _ = get_sun_times(lat, lon, tz, today + timedelta(days=1))
    prev_sunrise, prev_sunset = get_sun_times(lat, lon, tz, today - timedelta(days=1))

    weekday_today = today_sunrise.weekday()
    weekday_prev = prev_sunrise.weekday()
    day_ruler_today = WEEKDAY_RULERS[weekday_today]
    day_ruler_prev = WEEKDAY_RULERS[weekday_prev]

    day_len = (today_sunset - today_sunrise).total_seconds() / 12.0
    night1_len = (today_sunrise - prev_sunset).total_seconds() / 12.0
    night2_len = (next_sunrise - today_sunset).total_seconds() / 12.0

    day_start_idx = CHALDEAN_ORDER.index(day_ruler_today)
    if HORA_CONVENTION == "previous":
        night1_start_idx = (CHALDEAN_ORDER.index(day_ruler_prev) + 5) % 7
    else:
        night1_start_idx = (CHALDEAN_ORDER.index(day_ruler_today) + 5) % 7
    night2_start_idx = (CHALDEAN_ORDER.index(day_ruler_today) + 5) % 7

    print("\nHORA TABLE (local times):")
    t = prev_sunset
    for i in range(12):
        lord = CHALDEAN_ORDER[(night1_start_idx + i) % 7]
        print(f"{13+i:02d}th (prev night) Hora: {lord:7s}  starts {t.strftime('%Y-%m-%d %H:%M:%S')}")
        t += timedelta(seconds=night1_len)

    t = today_sunrise
    for i in range(12):
        lord = CHALDEAN_ORDER[(day_start_idx + i) % 7]
        print(f"{1+i:02d}th (day)       Hora: {lord:7s}  starts {t.strftime('%Y-%m-%d %H:%M:%S')}")
        t += timedelta(seconds=day_len)

    t = today_sunset
    for i in range(12):
        lord = CHALDEAN_ORDER[(night2_start_idx + i) % 7]
        print(f"{13+i:02d}th (tonight)   Hora: {lord:7s}  starts {t.strftime('%Y-%m-%d %H:%M:%S')}")
        t += timedelta(seconds=night2_len)

def sign_deg_min_str(position):
    sign_idx = int(position // 30)
    sign = RASHIS[sign_idx]
    deg_in_sign = position % 30.0
    deg = int(deg_in_sign)
    minutes = int(round((deg_in_sign - deg) * 60.0))
    if minutes == 60:
        minutes = 0
        deg = (deg + 1) % 30
        if deg == 0:
            sign_idx = (sign_idx + 1) % 12
            sign = RASHIS[sign_idx]
    return f"{sign} {deg:02d}° {minutes:02d}′"

# ------------- Vargas & positions -------------

def get_sidereal_position(planet_name, jd):
    planet_id_map = {**PLANET_NAME_TO_SWEPH, 'Rahu': swe.MEAN_NODE}
    planet_id = planet_id_map.get(planet_name)
    if planet_id is None:
        return (0.0, False)
    pos, _ = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    return pos[0], (pos[3] < 0)

def get_drekkana(pos):
    rashi_num = int(pos // 30)
    deg_in_rashi = pos % 30
    drekkana_num = int(deg_in_rashi // 10)
    d3_rashi_num = (rashi_num + drekkana_num * 4) % 12
    new_longitude = (deg_in_rashi % 10) * 3
    return RASHIS[d3_rashi_num], new_longitude

def get_navamsa(pos):
    navamsa_size = 10 / 3  # 3°20'
    rashi_num = int(pos // 30)
    deg_in_rashi = pos % 30
    pada = int(deg_in_rashi // navamsa_size)
    if rashi_num in [0, 4, 8]:
        start_rashi = 0
    elif rashi_num in [1, 5, 9]:
        start_rashi = 9
    elif rashi_num in [2, 6, 10]:
        start_rashi = 6
    else:
        start_rashi = 3
    d9_rashi_num = (start_rashi + pada) % 12
    pos_in_pada = deg_in_rashi % navamsa_size
    d9_longitude = (pos_in_pada / navamsa_size) * 30
    return RASHIS[d9_rashi_num], d9_longitude

def get_trimsamsa(pos):
    rashi_num = int(pos // 30)
    deg_in_rashi = pos % 30
    is_odd_sign = (rashi_num % 2) == 0
    if is_odd_sign:
        if deg_in_rashi < 5:
            d30_rashi_num, slice_size, slice_start = 0, 5, 0
        elif deg_in_rashi < 10:
            d30_rashi_num, slice_size, slice_start = 10, 5, 5
        elif deg_in_rashi < 18:
            d30_rashi_num, slice_size, slice_start = 8, 8, 10
        elif deg_in_rashi < 25:
            d30_rashi_num, slice_size, slice_start = 2, 7, 18
        else:
            d30_rashi_num, slice_size, slice_start = 6, 5, 25
    else:
        if deg_in_rashi < 5:
            d30_rashi_num, slice_size, slice_start = 1, 5, 0
        elif deg_in_rashi < 12:
            d30_rashi_num, slice_size, slice_start = 5, 7, 5
        elif deg_in_rashi < 20:
            d30_rashi_num, slice_size, slice_start = 11, 8, 12
        elif deg_in_rashi < 25:
            d30_rashi_num, slice_size, slice_start = 9, 5, 20
        else:
            d30_rashi_num, slice_size, slice_start = 7, 5, 25
    pos_in_slice = deg_in_rashi - slice_start
    new_longitude = (pos_in_slice / slice_size) * 30
    return RASHIS[d30_rashi_num], new_longitude

# --------- Dasha (simple illustrative) ---------

def get_stronger_lord(l1, l2, planetary_positions):
    p1, _ = planetary_positions[l1]
    p2, _ = planetary_positions[l2]
    return l2 if int(p2 // 30) > int(p1 // 30) else l1

def calculate_chara_dasha_period(rashi, planetary_positions):
    lords = RASHI_LORDS[rashi]
    chosen = lords[0] if len(lords) == 1 else get_stronger_lord(lords[0], lords[1], planetary_positions)
    lord_pos, _ = planetary_positions[chosen]
    lord_rashi_index = int(lord_pos // 30)
    rashi_index = RASHIS.index(rashi)
    count = (lord_rashi_index - rashi_index + 1) if lord_rashi_index >= rashi_index else (
        (12 - rashi_index) + lord_rashi_index + 1
    )
    return max(1, count - 1)

def display_active_dasha_periods(horary_lagna_pos, planetary_positions, query_date, ref_planet_name):
    print(f"\n--- Parashara Chara Dasha (Ref: {ref_planet_name}) ---")
    lagna_sign_index = int(horary_lagna_pos // 30)
    if lagna_sign_index < 6:
        seq = RASHIS[lagna_sign_index:] + RASHIS[:lagna_sign_index]
    else:
        rev = list(reversed(RASHIS))
        start = 11 - lagna_sign_index
        seq = rev[start:] + rev[:start]

    current_date = query_date.date()
    for md_rashi in seq:
        md_years = calculate_chara_dasha_period(md_rashi, planetary_positions)
        md_start = current_date
        md_end = md_start + timedelta(days=int(md_years * 365.25))
        if md_start <= query_date.date() < md_end:
            print(f"Maha Dasha : {md_rashi} ({md_start.strftime('%Y-%m-%d')} to {md_end.strftime('%Y-%m-%d')})")
            ad_len = (md_end - md_start).days / 12
            ad_start = md_start
            for ad_rashi in seq:
                ad_end = ad_start + timedelta(days=ad_len)
                if ad_start <= query_date.date() < ad_end:
                    print(f" Antardasha : {ad_rashi} ({ad_start.strftime('%Y-%m-%d')} to {ad_end.strftime('%Y-%m-%d')})")
                    pd_len = ad_len / 12
                    pd_start = ad_start
                    for pd_rashi in seq:
                        pd_end = pd_start + timedelta(days=pd_len)
                        if pd_start <= query_date.date() < pd_end:
                            print(f"  Pratyantardasha: {pd_rashi} ({pd_start.strftime('%Y-%m-%d')} to {pd_end.strftime('%Y-%m-%d')})")
                            break
                        pd_start = pd_end
                    break
                ad_start = ad_end
            break
        current_date = md_end
    print("-----------------------------------------------------------------")

# --------- Prashna Sthaana Logic ---------

def print_prashna_focus(hora_lord_name, planetary_positions, lagna_lon):
    """
    Computes and prints the Question Focus (Sthaana) dynamically based on
    the Hora Lord's D9 position, Tatva mapping, and distance from the active Lagna.
    """
    # 1. Get Hora Lord's D9 Sign
    hl_lon, _ = planetary_positions.get(hora_lord_name, (0.0, False))
    hl_d9_sign, _ = get_navamsa(hl_lon)

    # 1-based index (1=Aries, 12=Pisces)
    hl_sign_idx = RASHIS.index(hl_d9_sign) + 1

    # 2. Determine Tatva and Target Planet mapping
    if hl_sign_idx in [1, 5, 9]:
        tatva, target_planet = "Agni", "Mars"
    elif hl_sign_idx in [2, 6, 10]:
        tatva, target_planet = "Prithvi", "Mercury"
    elif hl_sign_idx in [3, 7, 11]:
        tatva, target_planet = "Vayu", "Saturn"
    elif hl_sign_idx in [4, 8, 12]:
        tatva, target_planet = "Jala", "Venus"
    else:
        print("Error determining Prashna Tatva.")
        return

    # 3. Get D1 Sign of the Target Planet
    tp_lon, _ = planetary_positions.get(target_planet, (0.0, False))
    tp_d1_sign = RASHIS[int(tp_lon // 30)]

    # 4. Get D1 Sign of the Active Lagna
    lagna_d1_sign = RASHIS[int(lagna_lon // 30)]

    # 5. Calculate Sthaana (Inclusive House Distance)
    lagna_idx = RASHIS.index(lagna_d1_sign) + 1
    tp_idx = RASHIS.index(tp_d1_sign) + 1
    sthana = (tp_idx - lagna_idx) % 12 + 1

    print("\n--- PRASHNA FOCUS (QUESTION INTENT) ---")
    print(f"Hora Lord       : {hora_lord_name}")
    print(f"Hora Lord D9    : {hl_d9_sign} ({tatva} Tatva)")
    print(f"Target Planet   : {target_planet} (placed in D1 {tp_d1_sign})")
    print(f"Lagna Used      : {lagna_d1_sign}")
    print(f"Result Sthaana  : {sthana}th House")
    print(f"Conclusion      : The querent is posing a question related to the {sthana}th Sthaana (House) from the active Lagna.")
    print("---------------------------------------")

# ----------------------------- Main ------------------------------------

def run_horary_analysis(location_label: str, tz: str, lat: float, lon: float, for_datetime_local=None):
    """
    Run full horary analysis for a supplied location + timezone.
    """
    print("==== Proprietary Horary Astrology Engine (Interactive) ====\n")
    tzinfo = pytz.timezone(tz)

    if for_datetime_local is None:
        now_local = datetime.now(tzinfo)
    else:
        if for_datetime_local.tzinfo is None:
            now_local = tzinfo.localize(for_datetime_local)
        else:
            now_local = for_datetime_local.astimezone(tzinfo)

    utc_dt = now_local.astimezone(pytz.UTC)
    jd = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    )
    print(f"JD used (UT): {jd}")

    positions = {}
    for p in PLANET_NAMES + ['Rahu']:
        positions[p] = get_sidereal_position(p, jd)
    rahu_lon, _ = positions['Rahu']
    positions['Ketu'] = ((rahu_lon + 180) % 360, True)

    hora_lord_name = get_planetary_hour_lord(now_local, lat, lon, tz)

    print("\n======================================================================")
    print("HORARY CHART FOR: PRIMARY QUESTION")
    print(f"Generated at: {now_local.strftime('%Y-%m-%d %H:%M:%S')} ({tz})")
    print(f"Location   : {location_label}")
    print(f"Lat/Lon    : {lat:.6f}, {lon:.6f}")
    print(f"Hora Lord  : {hora_lord_name}")
    primary_random_num = secrets.choice(list(NUMBER_LAGNA_MAP.keys()))
    print(f"Random Number: {primary_random_num}")
    print("======================================================================")

    if SHOW_HORA_TABLE:
        print_hora_table(now_local, lat, lon, tz)

    ref_planet_lon, _ = positions.get(hora_lord_name, (0.0, False))
    ref_rashi_num = int(ref_planet_lon // 30)
    ref_deg_in_rashi = ref_planet_lon % 30
    map_data = NUMBER_LAGNA_MAP[primary_random_num]
    lagna_rashi_num = (ref_rashi_num + map_data['lagna_offset'] - 1) % 12
    constructed_lagna = lagna_rashi_num * 30 + ref_deg_in_rashi

    d3_rashi, d3deg = get_drekkana(constructed_lagna)
    d9_rashi, d9deg = get_navamsa(constructed_lagna)
    d30_rashi, d30deg = get_trimsamsa(constructed_lagna)

    print(f"LAGNA (D1, Horary/Constructed):  {sign_deg_min_str(constructed_lagna)}")
    print(f"  D3 (Drekkana):   {d3_rashi} {int(d3deg):02d}° {int(round((d3deg - int(d3deg)) * 60)):02d}′  [base: Horary Lagna]")
    print(f"  D9 (Navamsa):    {d9_rashi} {int(d9deg):02d}° {int(round((d9deg - int(d9deg)) * 60)):02d}′  [base: Horary Lagna]")
    print(f"  D30 (Trimsamsa): {d30_rashi} {int(d30deg):02d}° {int(round((d30deg - int(d30deg)) * 60)):02d}′  [base: Horary Lagna]\n")

    print("PLANETARY POSITIONS (Sidereal, Lahiri):")
    print("-" * 110)
    print(f"{'Planet':<10} | {'Longitude (Sign DD° MM′)':<28} | {'Retro':<5} | {'D3 (Sign deg)':<18} | {'D9 (Sign deg)':<18} | {'D30 (Sign deg)':<18}")
    print("-" * 110)
    for pname in PLANET_NAMES + ['Rahu', 'Ketu']:
        pos, is_retro = positions[pname]
        retro_str = "R" if is_retro else ""
        d3r, d3d = get_drekkana(pos)
        d9r, d9d = get_navamsa(pos)
        d30r, d30d = get_trimsamsa(pos)
        print(f"{pname:<10} | {sign_deg_min_str(pos):<28} | {retro_str:<5} | {d3r + ' ' + f'{d3d:.2f}':<18} | {d9r + ' ' + f'{d9d:.2f}':<18} | {d30r + ' ' + f'{d30d:.2f}':<18}")
    print("-" * 110)

    # Injecting the primary Prashna focus
    print_prashna_focus(hora_lord_name, positions, constructed_lagna)

    display_active_dasha_periods(constructed_lagna, positions, now_local, "HoraryRef")

    for followup_planet in FOLLOWUP_REF_PLANET_SEQ:
        print("\n======================================================================")
        print(f"HORARY CHART FOR: FOLLOW-UP QUESTION (Ref: {followup_planet})")
        followup_random_num = secrets.choice(list(NUMBER_LAGNA_MAP.keys()))
        print(f"Random Number: {followup_random_num}")
        print("======================================================================")

        ref_planet_lon, _ = positions.get(followup_planet, (constructed_lagna, False))
        ref_rashi_num = int(ref_planet_lon // 30)
        ref_deg_in_rashi = ref_planet_lon % 30
        map_data = NUMBER_LAGNA_MAP[followup_random_num]
        lagna_rashi_num = (ref_rashi_num + map_data['lagna_offset'] - 1) % 12
        followup_lagna = lagna_rashi_num * 30 + ref_deg_in_rashi

        print(f"LAGNA (Constructed/Horary): {sign_deg_min_str(followup_lagna)}")

        # Injecting the follow-up Prashna focus using the shifted Lagna
        print_prashna_focus(hora_lord_name, positions, followup_lagna)

        display_active_dasha_periods(followup_lagna, positions, now_local, followup_planet)

# ------------------------------------------------------------------------

if __name__ == "__main__":
    location_label, tz, lat, lon = ask_location_from_user()
    dt = ask_datetime_from_user(tz)
    run_horary_analysis(location_label, tz, lat, lon, for_datetime_local=dt)
