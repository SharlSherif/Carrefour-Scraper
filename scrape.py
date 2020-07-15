import requests as req
from bs4 import BeautifulSoup
import json
import re
import time
from PIL import Image
from io import BytesIO
import base64
import pandas as pd


class Scraper:
    imgur_count = json.loads(open('./imgur_count.json').read())
    data = json.loads(open("./data.json", encoding="utf-8").read())

    def img_to_base64_str(self, img):
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        buffered.seek(0)
        img_byte = buffered.getvalue()
        img_str = base64.b64encode(img_byte).decode()
        return img_str

    def convert_image_to_base64(self, image_direct_link):
        response = req.get(image_direct_link)
        im = Image.open(BytesIO(response.content))
        image_in_base64 = self.img_to_base64_str(im)
        return image_in_base64

    def upload_image_to_imgur(self, image_direct_link):
        image_in_base64 = self.convert_image_to_base64(image_direct_link)
        if self.imgur_count['n'] >= 6:
            # sleep for 3 minutes
            print("GOING TO SLEEP ")
            time.sleep(180)
            print("WOKE UP..")
            image_count_file = open('./imgur_count.json', 'w+')
            image_count_file.write(json.dumps({"n": 0}))
            self.imgur_count['n'] = 0

        headers = {'Authorization': "Client-ID d1b3c0f47b77916"}
        multipart_form_data = {
            'image':  (None, image_in_base64),
            'type': (None, 'base64')
        }

        r = req.post("https://api.imgur.com/3/image",
                     files=multipart_form_data, headers=headers)
        if r.json()['status'] == 400:
            image_count_file = open('./imgur_count.json', 'w+')
            image_count_file.write(json.dumps({"n": 0}))
            self.imgur_count['n'] = 0
            time.sleep(1800)  # sleep 30 minutes
            print(r.json()['data'])
            raise Exception(r.json()['data']['error']['message'])
        else:
            self.imgur_count['n'] += 1
            image_count_file = open('./imgur_count.json', 'w+')
            image_count_file.write(json.dumps(self.imgur_count))

        return r.json()['data']['link']

    def get_one_product(self, url_en, url_ar):
        # url = f'https://www.carrefourksa.com/mafsau/en/home-garden/kitchen-dining/tableware/flasks/al-saif-deva-9-vacuum-flask-1l-s-gr/p/641270'
        html = req.get(url_en).content.decode("utf-8")
        document = BeautifulSoup(html, features="html.parser")
        html = req.get(url_ar).content.decode("utf-8")
        document_ar = BeautifulSoup(html, features="html.parser")

        all_categories = []
        images = []
        unit = "-"

        misc = document.find_all("div", {"class": "productinfo-misc__box"})

        for div in misc:
            if "Pack size" in div.text:
                unit = re.findall(r"[A-z]+$", div.text)[0]
        price = document.find("h2", {"class": "productinfo__price"}).text
        price = re.sub("[A-z]", "", price)

        name_eng = document.find("h1", {"class": "productinfo__name"}).text
        name_ar = document_ar.find("h1", {"class": "productinfo__name"}).text

        categories = document.find_all("a", {"class": "mafc-link"})
        categories_ar = document_ar.find_all("a", {"class": "mafc-link"})
        categories.pop(0)
        categories_ar.pop(0)

        for k in range(0, len(categories)):
            all_categories.append({k: categories[k].text})
            all_categories.append({k: categories_ar[k].text})

        crousel = document.find("div", {"class": "slick"}).div.find_all("img")

        for img in crousel:
            src = img['data-lazy']
            url = self.upload_image_to_imgur(src)
            images.append({crousel.index(img): url})
        if len(images)<1:
            images=""
        print(name_ar)
        print(name_eng)
        print(price)
        print(all_categories)
        print(images)
        print(unit)
        self.data['name_arabic'].append(name_ar)
        self.data['name_english'].append(name_eng)
        self.data['price'].append(price)
        self.data['images'].append(images)
        self.data['categories'].append(all_categories)
        self.data['product_url'].append(url_en)
        self.data['unit'].append(unit)
        previous_data = open("./data.json", "w+")
        previous_data.write(json.dumps(self.data))

    def begin(self):
        url_ens = [
            "https://www.carrefourksa.com/mafsau/en/beauty-personal-care/hair-care/hair-treatment/hair-cream/h-s-classicclean-oil-replcmnt-200ml/p/538516",
            "https://www.carrefourksa.com/mafsau/en/cleaning-household/cleaning-supplies/mops-brooms-dusters/baleno-toilet-wash-set-round/p/158704",
            "https://www.carrefourksa.com/mafsau/en/beverages/soft-drinks/carbonated-drinks/cola/coca-cola-pet-2-2l/p/639224",
            "https://www.carrefourksa.com/mafsau/en/beverages/soft-drinks/carbonated-drinks/cola/pepsi-nrb-250mlx24/p/332814",
            "https://www.carrefourksa.com/mafsau/en/food-cupboard/chocolate-confectionery/chocolates/minis-miniatures/galaxy-caramel-mini-168g/p/547071",
            "https://www.carrefourksa.com/mafsau/en/food-cupboard/chocolate-confectionery/chocolates/snacking-chocolates/galaxy-hazelnut-40g/p/543405"
        ]
        for url_en in url_ens:
            url_ar = re.sub(r"/en/", "/ar/", url_en)
            self.get_one_product(url_en, url_ar)


Scraper().begin()
