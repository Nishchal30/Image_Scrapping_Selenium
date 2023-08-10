import os, time
from flask import Flask, request, render_template
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

app = Flask(__name__)

@app.route('/', methods = ['GET','POST'])
def home():
    return render_template('index.html')

@app.route('/scrap', methods = ['GET','POST'])
def fetch_image_urls():

    query = request.form['search_for']
    max_links_to_fetch = int(request.form['image_count'])

    sleep_between_interactions = 1
    wd = webdriver.Chrome()

    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

    # Build the google url
    search_url = "https://www.google.com/search?sca_esv=554181109&rlz=1C1ONGR_enIN1041IN1053&sxsrf=AB5stBiFxmBbOYpInCdbKouAPdTBI_988w:1691302134273&q={q}&tbm=isch&source=lnms&sa=X&ved=2ahUKEwis4a63r8eAAxW1XGwGHSAXC98Q0pQJegQICxAB&biw=1366&bih=619&dpr=1"

    # Load the page
    wd.get(search_url.format(q=query))

    image_url = set()
    image_count = 0
    results_start = 0

    save_dir = "images/"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    target_folder = os.path.join(save_dir, query.lower().replace(" ", "_"))

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    while image_count < max_links_to_fetch:
        scroll_to_end(wd)

        thumbnail_results = wd.find_elements(By.CSS_SELECTOR, "img.Q4LuWd")
        number_of_results = len(thumbnail_results)

        # print(f"found : {thumbnail_results} search results. Extracting links from {results_start}:{number_of_results}")

        for img in thumbnail_results[results_start:number_of_results]:
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception:
                continue

            actual_images = wd.find_elements(By.CSS_SELECTOR, "img.r48jcc")

            for actual_image in actual_images:
                if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
                    image_url.add(actual_image.get_attribute('src'))

            image_count = len(image_url)

            if len(image_url) >= max_links_to_fetch:
                print(f"found {len(image_url)} image links, done!")
                break

            else:
                print(f"found:", len(image_url), "image links, looking for more...")
                time.sleep(30)
            
            load_more_button = wd.find_elements(By.CSS_SELECTOR, ".LZ4I")

            if load_more_button:
                wd.execute_script("document.querySelector('.LZ4I').click();")

        results_start = len(thumbnail_results)
    
        try:
            image_urls = list(image_url)
            for url in image_urls:
                try:
                    image_content = requests.get(url).content

                except Exception as e:
                    print(f"Error - could not download {url} - {e}")

                try:
                    f  = open(os.path.join(target_folder, f"{query}" + "_" + str(image_urls.index(url)) + ".jpg"), "wb")
                    f.write(image_content)
                    f.close()
                    print(f"success - saved {url} - as {target_folder}")

                except Exception as e:
                    print(f"Error - could not save {url} - {e}")
        
        except Exception as e:
            print(f"Something went wrong at file saving {e}")

    return str("The images are being loaded to the directory, Thank you!")


if __name__ == "__main__":
    app.run()