from locust import HttpUser, task, wait_time, between
class MyUser(HttpUser):
    wait_time = between(1, 3)  # thời gian nghỉ giữa các request
    @task(2)
    def get_all_venues(self):
        self.client.get("/")

    @task(1)
    def get_venue_detail(self):
        venue_id = 2
        self.client.get(f"/venue/{venue_id}", name="/venue/[id]")

