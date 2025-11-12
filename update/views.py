import requests
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse



PRIVATE_ACCESS_TOKEN = settings.PRIVATE_ACCESS_TOKEN
LOCATION_ID = settings.LOCATION_ID



def get_match_opportunities(request):
    try:
        result = find_matching_opportunity(LOCATION_ID, PRIVATE_ACCESS_TOKEN)
        return JsonResponse({"status": "success", "data": result}, safe=False)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def to_date(iso_string):
    """Convert ISO string (with Z) to date only (YYYY-MM-DD)."""
    try:
        return datetime.fromisoformat(iso_string.replace("Z", "+00:00")).date()
    except Exception:
        return None
    

def find_matching_opportunity(location_id, PRIVATE_ACCESS_TOKEN):
   

    base_url = "https://services.leadconnectorhq.com"
    headers = {
        "Authorization": f"Bearer {PRIVATE_ACCESS_TOKEN}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }

    # Step 1: Get survey submissionrs
    submissions_url = f"{base_url}/surveys/submissions?locationId={location_id}"
    survey_response = requests.get(submissions_url, headers=headers)

    if survey_response.status_code != 200:
        print("Failed to fetch survey submissions:", survey_response.text)
        return None

    survey_data = survey_response.json().get("submissions", [])
    if not survey_data:
        print("No survey submissions found.")
        return None

    # Step 2: Loop through each submission
    for submission in survey_data:
        contact_id = submission.get("contactId")
        created_at = submission.get("createdAt")
        others_data = submission.get("others", {})

        if not contact_id or not created_at:
            continue

      
        # Step 3: Search opportunities for this location
        opportunity_url = f"{base_url}/opportunities/search?location_id={location_id}"
        opp_response = requests.get(opportunity_url, headers=headers)

        if opp_response.status_code != 200:
            print("Failed to fetch opportunities:", opp_response.text)
            continue

        opportunities = opp_response.json().get("opportunities", [])

        # Step 4: Match by contactId and creation date
        for opp in opportunities:
            submission_date = to_date(created_at)
            opportunity_date = to_date(opp.get("createdAt", ""))
            if opp.get("contactId") == contact_id and submission_date == opportunity_date:
                           
               # Step 5: Prepare custom field updates
                opp_custom_fields = {field["id"]: field.get("fieldValueString") for field in opp.get("customFields", [])}
                update_fields = []

                for field_id, value in others_data.items():
                    # Update if field exists or is new/missing value
                    if field_id not in opp_custom_fields or not opp_custom_fields[field_id]:
                        update_fields.append({
                            "id": field_id,
                            "value": value
                        })

                if not update_fields:
                    print(f"ℹ No new custom fields to update for {contact_id}")
                    continue

                # Step 6: Send PATCH request to update opportunity
                update_url = f"{base_url}/opportunities/{opp.get('id')}"
                payload = {
                    "customFields": update_fields
                }

                patch_resp = requests.patch(update_url, headers=headers, json=payload)
                if patch_resp.status_code in (200, 201):
                    print(f" Successfully updated opportunity {opp.get('id')} for contact {contact_id}")
                else:
                    print(f" Failed to update opportunity {opp.get('id')}: {patch_resp.text}")

                return opp


    print("No matching opportunities found.")
    return None


































# import csv
# import io
# import requests
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from urllib.parse import urlparse, parse_qs

# from django.conf import settings

# customFields = [
#     {"id": "zBw0eN9F6x2XnxeYW7Mj","name": "utm_campaign"},
#     {"id": "O7fItuUg9euteSBk3eO0","name": "utm_keyword"},
#     {"id": "DbOfSKtp8DaR36PRApNx","name": "utm_medium"},
#     {"id": "X01bWrXKcX2DHEDI4voi","name": "utm_content"},
#     {"id": "LwoUO80HQnEJFVhxUDVX","name": "latest_utm_medium"},
#     {"id": "N0zSoUhW5GPRY1G0b3EA","name": "latest_utm_content"},
#     {"id": "NtHtRPRD8Vui6P7QRqYs","name": "latest_utm_keyword"},
#     {"id": "xeCOydWDwBy3D3m0LFCG", "name": "latest_utm_campaign"},


# ]

# custom_field_map = {field["name"].lower(): field["id"] for field in customFields}



# def extract_utm_values(source):
#     utm_data = {}

#     if isinstance(source, str):
#         parsed = urlparse(source)
#         source = parse_qs(parsed.query)

#     for key in ["utm_campaign", "utm_medium", "utm_content", "utm_keyword","latest_utm_campaign", "latest_utm_medium", "latest_utm_content", "latest_utm_keyword"]:
#         values = source.get(key) or source.get(key.lower()) or []
#         if not isinstance(values, list):
#             values = [values]

#         for v in values:
#             if v and "{" not in v and "}" not in v:  
#                 utm_data[key] = v
#                 break

#     return utm_data


# @csrf_exempt
# def update_contacts(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST allowed"}, status=405)

#     csv_file = request.FILES.get("file")
#     if not csv_file:
#         return JsonResponse({"error": "No CSV file uploaded"}, status=400)

#     PRIVATE_ACCESS_TOKEN = settings.PRIVATE_ACCESS_TOKEN
#     API_VERSION = "2021-07-28"
#     BASE_URL = "https://services.leadconnectorhq.com"
#     count = 0

#     reader = csv.DictReader(io.StringIO(csv_file.read().decode("utf-8")))
#     updated_contacts = []
#     failed_contacts = []

#     for row in reader:
#         contact_id = row.get("Contact Id")
#         if not contact_id:
#             continue

#         headers = {
#             "Authorization": f"Bearer {PRIVATE_ACCESS_TOKEN}",
#             "Version": API_VERSION,
#             "Content-Type": "application/json"
#         }

#         contact_url = f"{BASE_URL}/contacts/{contact_id}"
#         contact_resp = requests.get(contact_url, headers=headers)

#         if contact_resp.status_code != 200:
#             failed_contacts.append({
#                 "contact_id": contact_id,
#                 "error": f"Fetch failed ({contact_resp.status_code})"
#             })
#             continue

#         contact_data = contact_resp.json().get("contact", {})

#         first_source = contact_data.get("attributionSource", {}) or {}
#         last_source = contact_data.get("lastAttributionSource", {}) or {}

#         first_url = first_source.get("url", "")
#         last_url = last_source.get("url", "")


      

#         first_utm = extract_utm_values(first_url)
#         last_utm = extract_utm_values(last_url)

#         if not first_utm and not last_utm:
#             failed_contacts.append({
#                 "contact_id": contact_id,
#                 "error": "No non-placeholder UTM values found"
#             })
#             continue

#         custom_fields = []
#         customFields_failed = []

        


#         for key in ["utm_campaign", "utm_medium", "utm_content"]:
#             value = last_utm.get(key) or first_utm.get(key)
#             if value:
#                 field_name = f"latest_{key.lower()}"
#                 field_id = custom_field_map.get(field_name.lower())
#                 if field_id:
#                     custom_fields.append({
#                         "id": field_id,
#                         "key": field_name,
#                         "field_value": value
#                     })
#                 else:
#                     customFields_failed.append({
#                         "key":field_name
#                     })  
                    
                    



#         if not custom_fields:
#             failed_contacts.append({
#                 "contact_id": contact_id,
#                 "error": "No valid fields to update",
#                 "failed_custom_fields": customFields_failed
#             })
#             continue


#         update_payload = {"customFields": custom_fields}

#         update_resp = requests.put(contact_url, headers=headers, json=update_payload)

#         if update_resp.status_code in (200, 201):
#             updated_contacts.append({
#                 "contact_id": contact_id,
#                 "customField":custom_fields,
#                 "failed_custom_fields":customFields_failed,

#             })
#         else:
#             failed_contacts.append({
#                 "contact_id": contact_id,
#                 "error": f"Update failed ({update_resp.status_code})",
#                 "details": update_resp.text
#             })
#         count += 1
#         print(count,'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',update_contacts,failed_contacts)    


#     return JsonResponse({
#         "message": "Processing completed",
#         "updated": updated_contacts,
#         "failed": failed_contacts,
#     })
