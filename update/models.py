from django.db import models

class OpportunityTracker(models.Model):
    contact_id = models.CharField(max_length=200)
    submission_date = models.DateField()
    opportunity_id = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contact_id} - {self.opportunity_id}"

