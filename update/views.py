import csv
import io
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import urlparse, parse_qs

from django.conf import settings

customFields = [
    {"id": "zBw0eN9F6x2XnxeYW7Mj","name": "utm_campaign"},
    {"id": "O7fItuUg9euteSBk3eO0","name": "utm_keyword"},
    {"id": "DbOfSKtp8DaR36PRApNx","name": "utm_medium"},
    {"id": "X01bWrXKcX2DHEDI4voi","name": "utm_content"},
    {"id": "LwoUO80HQnEJFVhxUDVX","name": "latest_utm_medium"},
    {"id": "N0zSoUhW5GPRY1G0b3EA","name": "latest_utm_content"},
    {"id": "NtHtRPRD8Vui6P7QRqYs","name": "latest_utm_keyword"},
    {"id": "xeCOydWDwBy3D3m0LFCG", "name": "latest_utm_campaign"},


]

custom_field_map = {field["name"].lower(): field["id"] for field in customFields}



def extract_utm_values(source):
    utm_data = {}

    if isinstance(source, str):
        parsed = urlparse(source)
        source = parse_qs(parsed.query)

    for key in ["utm_campaign", "utm_medium", "utm_content", "utm_keyword","latest_utm_campaign", "latest_utm_medium", "latest_utm_content", "latest_utm_keyword"]:
        values = source.get(key) or source.get(key.lower()) or []
        if not isinstance(values, list):
            values = [values]

        for v in values:
            if v and "{" not in v and "}" not in v:  
                utm_data[key] = v
                break

    return utm_data


@csrf_exempt
def update_contacts(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    csv_file = request.FILES.get("file")
    if not csv_file:
        return JsonResponse({"error": "No CSV file uploaded"}, status=400)

    PRIVATE_ACCESS_TOKEN = settings.PRIVATE_ACCESS_TOKEN
    API_VERSION = "2021-07-28"
    BASE_URL = "https://services.leadconnectorhq.com"

    reader = csv.DictReader(io.StringIO(csv_file.read().decode("utf-8")))
    updated_contacts = []
    failed_contacts = []

    for row in reader:
        contact_id = row.get("Contact Id")
        if not contact_id:
            continue

        headers = {
            "Authorization": f"Bearer {PRIVATE_ACCESS_TOKEN}",
            "Version": API_VERSION,
            "Content-Type": "application/json"
        }

        contact_url = f"{BASE_URL}/contacts/{contact_id}"
        contact_resp = requests.get(contact_url, headers=headers)

        if contact_resp.status_code != 200:
            failed_contacts.append({
                "contact_id": contact_id,
                "error": f"Fetch failed ({contact_resp.status_code})"
            })
            continue

        contact_data = contact_resp.json().get("contact", {})

        first_source = contact_data.get("attributionSource", {}) or {}
        last_source = contact_data.get("lastAttributionSource", {}) or {}

        first_url = first_source.get("url", "")
        last_url = last_source.get("url", "")


      

        first_utm = extract_utm_values(first_url)
        last_utm = extract_utm_values(last_url)

        if not first_utm and not last_utm:
            failed_contacts.append({
                "contact_id": contact_id,
                "error": "No non-placeholder UTM values found"
            })
            continue

        custom_fields = []
        customFields_first = []
        customFields_latest =[]
        customFields_latest_from_first = []
        


        for key, value in first_utm.items():
            field_name = key.lower() 
            field_id = custom_field_map.get(field_name.lower())
            if field_id:
                custom_fields.append({
                    "id": field_id,
                    "key": field_name,
                    "field_value": value
                })
                customFields_first.append({
                    "id": field_id,
                    "key": field_name,
                    "field_value": value
                })

        if last_utm:
            for key, value in last_utm.items():
                field_name = f"latest_{key.lower()}"  
                field_id = custom_field_map.get(field_name.lower())
                if field_id:
                    custom_fields.append({
                        "id": field_id,
                        "key": field_name,
                        "field_value": value
                    })
                    customFields_latest.append({
                    "id": field_id,
                    "key": field_name,
                    "field_value": value
                })
        else:
            for key, value in first_utm.items():
                field_name =  f"latest_{key.lower()}" 
                field_id = custom_field_map.get(field_name.lower())
                if field_id:
                    custom_fields.append({
                        "id": field_id,
                        "key": field_name,
                        "field_value": value
                    })
                    customFields_latest_from_first.append({
                    "id": field_id,
                    "key": field_name,
                    "field_value": value
                    })



        if not custom_fields:
            failed_contacts.append({
                "contact_id": contact_id,
                "error": "No valid fields to update"
            })
            continue


        update_payload = {"customFields": custom_fields}

        update_resp = requests.put(contact_url, headers=headers, json=update_payload)

        if update_resp.status_code in (200, 201):
            updated_contacts.append({
                "contact_id": contact_id,
                "customField_First":customFields_first,
                "customField_latest":customFields_latest,
                "customField_latest_from_first":customFields_latest_from_first, 
            })
        else:
            failed_contacts.append({
                "contact_id": contact_id,
                "error": f"Update failed ({update_resp.status_code})",
                "details": update_resp.text
            })


    return JsonResponse({
        "message": "Processing completed",
        "updated": updated_contacts,
        "failed": failed_contacts,
    })
