"""Audio Guide Content dictionary and dynamic sentence templates for all application keys and languages."""
import json
import os

ENGLISH_GUIDE = {
    "welcome": "Welcome to LandfallReady. I will guide you. Move your cursor or click on any part of the screen and I will explain it.",
    "sidebar_region": "Select your target coastal region along the Bay of Bengal to analyze cyclone impact.",
    "sidebar_wind": "Adjust maximum sustained wind speed to simulate cyclone intensity.",
    "sidebar_rain": "Adjust 72-hour accumulated rainfall to estimate flooding and ground saturation.",
    "sidebar_landfall_shift": "Shift projected landfall coordinates north, south, east, or west to test track uncertainty.",
    "kpi_strip": "These metrics show total land cells analyzed, high and medium risk counts, and peak flood depth.",
    "map_area": "Interactive risk map showing colored flood cells, projected landfall eye, and exposed infrastructure.",
    "map_click": "Click any grid cell or facility marker to inspect exact risk level, elevation, and flood depth.",
    "map_satellite_toggle": "Toggle top-right map controls to switch between street map and Esri satellite imagery.",
    "map_layers": "Use layer controls to toggle hospitals, shelters, power stations, and primary road networks.",
    "hospital_marker": "Hospital marker indicating flood risk level and emergency medical vulnerability.",
    "shelter_marker": "Designated cyclone shelter location mapped to surrounding flood depth and risk score.",
    "substation_marker": "Electrical power substation vulnerable to wind damage and power grid disruption.",
    "road_layer": "Primary highways and evacuation routes. Red segments highlight probable flood cutoffs.",
    "infra_table": "Detailed table listing all exposed critical facilities sorted by risk score and flood depth.",
    "advisory_generate": "Click here to generate an AI-powered municipal early-warning advisory in your chosen language.",
    "advisory_language": "Choose target regional language for official municipal disaster management advisories.",
    "advisory_upload": "Upload satellite or cloud imagery for multimodal storm structure analysis.",
    "advisory_download": "Download the complete municipal disaster advisory as a markdown text file.",
    "insurance_card": "Pre-landfall parametric insurance trigger evaluation showing household liquidity payout tier.",
    "insurance_thresholds": "Adjust wind and rain policy thresholds to test parametric payout conditions.",
    "tab_home": "Home page with quick start guided tour, overview cards, and application workflow.",
    "tab_overview": "High-level disaster metrics, live weather baseline, and system architecture breakdown.",
    "tab_map": "Full-screen interactive spatial risk map with satellite tiles and layer controls.",
    "tab_infra": "Critical infrastructure exposure breakdown for hospitals, shelters, and power substations.",
    "tab_advisory": "Gemini multimodal AI advisory generator for municipal decision makers.",
    "tab_insurance": "Parametric micro-insurance trigger card and household payout calculator.",
}

HINDI_GUIDE = {
    "welcome": "LandfallReady me aapka swagat hai. Main aapka guide hoon. Screen par kisi bhi jagah cursor le jayen ya click karen, main samjhaunga.",
    "sidebar_region": "Cyclone ke prabhav ka vishleshan karne ke liye Bay of Bengal ke tatiya khetra ka chayan karen.",
    "sidebar_wind": "Cyclone ki tivrata ko badalne ke liye mahattam hawa ki gati ka slider adjust karen.",
    "sidebar_rain": "Badaav aur flood ka anuman lagane ke liye 72 ghante ki baarish ko slider se set karen.",
    "sidebar_landfall_shift": "Cyclone path ke anishchitata ko test karne ke liye landfall ko uttar, dakshin, purv ya paschim shift karen.",
    "kpi_strip": "Yeh metrics kul kshetra, high aur medium risk cells aur peak flood ki gahrai ko darshate hain.",
    "map_area": "Interactive risk map jo flood cells, landfall target aur exposed infrastructure dikhata hai.",
    "map_click": "Kisi bhi cell ya hospital marker par click karke exact risk level aur flood depth dekhen.",
    "map_satellite_toggle": "Satellite visual dekhne ke liye top right layer control se Esri Satellite imagery chunen.",
    "map_layers": "Hospitals, shelters aur power grids ko map par dikhane ya chipane ke liye layers switch karen.",
    "hospital_marker": "Hospital marker jo flood risk aur aapatkalin chikitsa sthiti ko darshata hai.",
    "shelter_marker": "Cyclone shelter ka sthan jo aas-paas ke flood depth ke saath judaa hai.",
    "substation_marker": "Power substation jo tej hawaon aur bijli katoti ke jokhim me hai.",
    "road_layer": "Evacuation roads. Laal rang ki sadken paani me doobne ke jokhim ko darshati hain.",
    "infra_table": "Prabhavit hospitals aur shelters ki vishtrit soochi jo risk score se sorted hai.",
    "advisory_generate": "Chuni hui bhasha me AI dwara taiyar municipal advisory ke liye yahan click karen.",
    "advisory_language": "Sarkari disaster management advisory ke liye regional bhasha ka chayan karen.",
    "advisory_upload": "Multimodal analysis ke liye satellite ya cloud ki photo upload karen.",
    "advisory_download": "Puri municipal advisory ko Markdown file ke roop me download karen.",
    "insurance_card": "Pre-landfall parametric insurance trigger card jo parivar ke bhugtan rashi ko dikhata hai.",
    "insurance_thresholds": "Insurance payout rules ko test karne ke liye wind aur rain threshold adjust karen.",
    "tab_home": "Home page jahan app ki mukhya jankari aur guided tour shuru hota hai.",
    "tab_overview": "Mukhya metrics, live mausam forecast aur system architecture ki jankari.",
    "tab_map": "Pura interactive spatial risk map satellite tiles aur layer controls ke saath.",
    "tab_infra": "Hospitals, shelters aur power grids ki suraksha sthiti ka vishleshan.",
    "tab_advisory": "Gemini AI dwara municipal aapatkalin salah taiyar karne ka tab.",
    "tab_insurance": "Parametric insurance trigger card aur household payout calculator.",
}

MAP_CLICK_TEMPLATES = {
    "English": "Selected location at latitude {lat}, longitude {lon}. Risk band is {band} with elevation {elev} meters, expected flood depth {flood_m} meters, and wind speed {wind} kilometers per hour. Nearest hospital is {dist_hosp} kilometers away.",
    "Hindi": "Chuna gaya sthan akshansh {lat}, deshantar {lon}. Risk band {band} hai, unchai {elev} meter, anumanit flood depth {flood_m} meter, aur hawa ki gati {wind} kilometer prati ghanta hai. Nikatatam hospital {dist_hosp} kilometer door hai.",
    "Bengali": "নির্বাচিত স্থান ল্যাটিটিউড {lat}, লঙ্গিটিউড {lon}। ঝুঁকি ব্যান্ড {band}, উচ্চতা {elev} মিটার, বন্যার গভীরতা {flood_m} মিটার এবং বাতাসের গতি {wind} কিলোমিটার প্রতি ঘণ্টা। নিকটতম হাসপাতাল {dist_hosp} কিলোমিটার দূরে।",
    "Odia": "ମନୋନୀତ ସ୍ଥାନ ଲ୍ୟାଟିଚ୍ୟୁଡ୍ {lat}, ଲଙ୍ଗିଚ୍ୟୁଡ୍ {lon}। ରିସ୍କ ବ୍ୟାଣ୍ଡ {band}, ଉଚ୍ଚତା {elev} ମିଟର, ବନ୍ୟା ଗଭୀରତା {flood_m} ମିଟର ଏବଂ ପବନ ଗତି {wind} କିଲୋମିଟର ପ୍ରତି ଘଣ୍ଟା। ନିକଟତମ ହସ୍ପିଟାଲ {dist_hosp} କିଲୋମିଟର ଦୂରରେ।",
    "Telugu": "ఎంచుకున్న ప్రాంతం అక్షాంశం {lat}, రేఖాంశం {lon}. రిస్క్ బ్యాండ్ {band}, ఎత్తు {elev} మీటర్లు, వరద లోతు {flood_m} మీటర్లు మరియు గాలి వేగం {wind} కిలోమీటర్లు. సమీప ఆసుపత్రి {dist_hosp} కిలోమీటర్ల దూరంలో ఉంది.",
}

GUIDES = {
    "English": ENGLISH_GUIDE,
    "Hindi": HINDI_GUIDE,
}

json_path = os.path.join(os.path.dirname(__file__), "guide_translations.json")
if os.path.exists(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            trans = json.load(f)
            for lang, d in trans.items():
                GUIDES[lang] = d
    except Exception:
        pass

for l_name in ["Bengali", "Odia", "Telugu"]:
    if l_name not in GUIDES:
        GUIDES[l_name] = ENGLISH_GUIDE


def get_guide_sentences(language: str) -> dict:
    """Return dictionary of guide key -> sentence for target language."""
    return GUIDES.get(language, ENGLISH_GUIDE)


def format_map_click_sentence(language: str, lat: float, lon: float, band: str, elev: float,
                               flood_m: float, wind: float, dist_hosp: float) -> str:
    """Format dynamic speech sentence for map click inspection."""
    template = MAP_CLICK_TEMPLATES.get(language, MAP_CLICK_TEMPLATES["English"])
    return template.format(
        lat=round(lat, 3),
        lon=round(lon, 3),
        band=band,
        elev=round(elev, 1),
        flood_m=round(flood_m, 1),
        wind=round(wind, 0),
        dist_hosp=round(dist_hosp, 1),
    )
