import requests
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
import pandas as pd
from django.http import FileResponse
import os
from .models import OpportunityTracker





PRIVATE_ACCESS_TOKEN = settings.PRIVATE_ACCESS_TOKEN
LOCATION_ID = settings.LOCATION_ID





def get_Create_match_opportunities(request):
    try:
        if "file" not in request.FILES:
            return JsonResponse({"status": "error", "message": "No file uploaded"}, status=400)

        file = request.FILES["file"]
        result = create_matching_opportunity_customField(LOCATION_ID, PRIVATE_ACCESS_TOKEN, file)

        return JsonResponse({"status": "success", "data": result})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def to_date(iso_string):
    """Convert ISO string (with Z) to date only (YYYY-MM-DD)."""
    try:
        return datetime.fromisoformat(iso_string.replace("Z", "+00:00")).date()
    except Exception:
        return None
    
import re

def excel_date_to_date_only(date_str):
    if not date_str:
        return None

    # Remove st, nd, rd, th
    clean_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

    try:
        # Format: "Sep 9 2025, 7:09 am"
        dt = datetime.strptime(clean_str, "%b %d %Y, %I:%M %p")
        return dt.date()
    except Exception as e:
        print("Excel date parse error:", e)
        return None    
    


#  FETCH ALL PAGES OF OPPORTUNITIES
def get_all_opportunities(base_url, headers, location_id):
    all_opps = []
    page = 1
    limit = 100

    while True:
        url = f"{base_url}/opportunities/search?location_id={location_id}&page={page}&limit={limit}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            break

        data = response.json()
        opps = data.get("opportunities", [])

        if not opps:
            break

        all_opps.extend(opps)
        page += 1

    return all_opps




def get_pipelines(base_url, headers, location_id):

    url = f"{base_url}/opportunities/pipelines"
    params = {"locationId": location_id}
    res = requests.get(url, headers=headers, params=params)

    if res.status_code not in [200, 201]:
        print("Failed to fetch pipelines:", res.text)
        return []

    data = res.json()
    return data.get("pipelines", [])


def create_new_opportunity(base_url, headers, location_id, contact_id, submission_date,pipeline_id, pipeline_stage_id):

    payload = {
        "locationId": location_id,
        "contactId": contact_id,
        "name": f"Imported Opportunity {contact_id} - {submission_date}",
        "pipelineId": pipeline_id,           
        "pipelineStageId": pipeline_stage_id , 
        "status": "open"
    }

    url = f"{base_url}/opportunities/"
    res = requests.post(url, json=payload, headers=headers)

    if res.status_code not in [200, 201]:
        print("Opportunity creation failed:", res.text)
        return None

    return res.json().get("id")




def create_matching_opportunity_customField(location_id, PRIVATE_ACCESS_TOKEN,uploaded_file):


    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        return {"error": "Invalid file format", "details": str(e)}

   
    excel_rows = df.to_dict("records")

   

    base_url = "https://services.leadconnectorhq.com"
    headers = {
        "Authorization": f"Bearer {PRIVATE_ACCESS_TOKEN}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }


    opportunities = get_all_opportunities(base_url, headers, location_id)
    print("TOTAL OPPORTUNITIES FOUND:", len(opportunities))

    updated_ids = []

    print("Fetching custom fields...")
    updated_count = 0



      #  Fetch all opportunity custom fields

    custom_fields_url = f"{base_url}/locations/{location_id}/customFields?model=opportunity"
    cf_response = requests.get(custom_fields_url, headers=headers)

    if cf_response.status_code != 200:
        return {"error": "Failed to fetch custom fields", "details": cf_response.text}

    custom_fields_data = cf_response.json().get("customFields", [])

    # Create mapping: fieldKey --> fieldId
    fieldkey_to_id = {
        field.get("fieldKey"): field.get("id") 
        for field in custom_fields_data
    }

    print("Total custom fields loaded:", len(fieldkey_to_id))

    # Step 2: Loop through each submission
    for submission in excel_rows:

        



        contact_id = submission.get("contact_id")
        submission_date = submission.get("submission_date")

        excel_date = excel_date_to_date_only(str(submission_date))




        if not contact_id or not submission_date:
            continue



        ###  CHECK LOCAL DB FIRST
        existing_entry = OpportunityTracker.objects.filter(
            contact_id=contact_id,
            submission_date=excel_date
        ).first()

        matched_opp = None

        if existing_entry:  
            print(f"Found stored opportunity {existing_entry.opportunity_id} for {contact_id}")
            matched_opp = next(
                (o for o in opportunities if o.get("id") == existing_entry.opportunity_id), None
            )

        if not matched_opp:    

            # Filter opportunities belonging to this contact_id
            contact_opps = [
                opp for opp in opportunities
                if str(opp.get("contactId")).strip() == str(contact_id).strip()
            ]


            matched_opp = None


            for opp in contact_opps:
                opp_created_date = to_date(opp.get("createdAt", ""))

                if not opp_created_date or not excel_date:
                    continue

                if excel_date.year == opp_created_date.year and excel_date.month == opp_created_date.month:
                    matched_opp = opp
                    break  # STOP after first match

            

        if not matched_opp:
            new_opp_id = create_new_opportunity(
                base_url, headers, location_id,
                contact_id, excel_date
            )

            if new_opp_id:
                ###  SAVE TO DB
                OpportunityTracker.objects.create(
                    contact_id=contact_id,
                    submission_date=excel_date,
                    opportunity_id=new_opp_id
                )

            opp_id = new_opp_id

        else:     
            opp_id = matched_opp.get("id")


        update_fields = []

        for column_name, column_value in submission.items():

            # Only process columns that match opportunity custom fields
            if not column_name.startswith("opportunity."):
                continue

            # match column to field key
            field_id = fieldkey_to_id.get(column_name)

            if not field_id:
                print("No custom field for column:", column_name)
                continue

            # append update structure
            update_fields.append({
                "id": field_id,
                "field_value": str(column_value)
            })



        if not update_fields:
            continue



         # Send update request
        update_url = f"{base_url}/opportunities/{opp_id}"

        payload = {
            "customFields": update_fields
        }

        update_res = requests.put(update_url, json=payload, headers=headers)

        if update_res.status_code in [200, 201]:
            updated_count += 1
            updated_ids.append({"contact_id": contact_id, "opportunity_id": opp_id}) 
            print(f"Updated opportunity {opp_id}")

           
        else:
            print(f"Failed to update {opp_id}", update_res.text)

    return {
        "status": "success",
        "updated_opportunities": updated_count,
        "updated_ids": updated_ids
    }




























