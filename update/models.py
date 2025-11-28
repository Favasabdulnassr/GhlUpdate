from django.db import models

class OpportunityTracker(models.Model):
    contact_id = models.CharField(max_length=200)
    submission_date = models.DateField()
    opportunity_id = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contact_id} - {self.opportunity_id}"
    




class LocationDetail(models.Model):
    ghl_location_id = models.CharField(max_length=255, primary_key=True)
    ghl_location_name = models.CharField(max_length=255, null=True, blank=True)
    ghl_timezone = models.CharField(max_length=255, null=True, blank=True)
    access_token = models.TextField( null=True, blank=True)
    refresh_token = models.TextField( null=True, blank=True)
    access_token_expires_at = models.DateTimeField(null=True, blank=True)
    pipeline_id = models.CharField(max_length=255, null=True, blank=True)
    pipeline_name = models.CharField(max_length=255, null=True, blank=True)
    archive_pipeline_id = models.CharField(max_length=255, null=True, blank=True)
    archive_pipeline_name = models.CharField(max_length=255, null=True, blank=True)
    archive_stage_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    target_customer_size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_customer_size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    contribution_lower = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    contribution_mid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    contribution_upper = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    customvalue_layer1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    customvalue_layer2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    customvalue_layer3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    impact_lower = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    impact_mid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    impact_upper = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reach_lower = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reach_mid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reach_upper = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    target_population = models.CharField(max_length=255, null=True, blank=True)
    location_dashboard_name = models.CharField(max_length=255, null=True, blank=True)
    # color_reach_lower = models.CharField(max_length=255, null=True, blank=True)
    # color_reach_mid = models.CharField(max_length=255, null=True, blank=True)
    # color_reach_upper = models.CharField(max_length=255, null=True, blank=True)
    
    
    def needs_token_refresh(self):
        five_minutes_ahead_refresh = timezone.timedelta(minutes=5)  
        refresh_time = self.access_token_expires_at - five_minutes_ahead_refresh if self.access_token_expires_at else None

        return (
            self.access_token_expires_at is None or 
            timezone.now() >= refresh_time
        )

    def __str__(self):
                return self.ghl_location_name or self.ghl_location_id

