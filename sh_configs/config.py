from sh_configs.servers import db


class Settings(object):
    def __init__(self):
        self.isbn_pattern = r"^([0-9|X]){13}"
        self.meta_check = ['publishDate', 'sortTitle', 'genres', 'synopsis']

    def get_config(self):
        configs = db.collection("system").document("publishPortalConfigs").get().to_dict()
        if configs:
            if configs.get('meta_check'):
                print(f"meta_check now {configs.get('meta_check')}")
                self.meta_check = configs.get('meta_check', [])


settings = Settings()
