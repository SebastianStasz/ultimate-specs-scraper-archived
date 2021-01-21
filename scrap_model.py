import re
import time

import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver

from mac_notification import display_notification
from models import (
    CarsData,
    EngineType,
    Generation,
    Model,
    ModelLine,
    Version,
    Technical,
)
from save_data import save_data
from version_templates import keys_template, titles_template, values_to_split


def get_body_content(url):
    soup = None
    recaptcha = ""

    while recaptcha != None:
        r = requests.get(url)
        soup = bs(r.content, "html.parser").body
        recaptcha = soup.find(class_="g-recaptcha")
        if recaptcha != None:
            display_notification("Scraper", "Website Blocked")
            time.sleep(3)

    return soup


def render_page(url):
    desired_cap = {}
    path = "/Users/sebastian/Desktop/cars_data_scraper/ultimatespecs_scraper/edgedriver/msedgedriver"
    driver = webdriver.Edge(executable_path=path, capabilities=desired_cap)

    driver.get(url)
    rendered_page = driver.page_source

    return rendered_page


def clear_text(text):
    regex = re.compile(r"[\n\r\t:]")
    clear_text = regex.sub(" ", text)

    return clear_text.strip()


def split_value(value):
    result = re.split("or|OR|\/", value)
    return [i.strip() for i in result]


def get_year_period(period):
    years = re.match(r"\((.*) \- (.*)\)", period)
    years2 = years.group(2) if years.group(2) != "" else "present"
    production_period = f"{years.group(1)} - {years2}"

    return production_period


def format_values(key, value):
    if key in values_to_split:
        value = split_value(value)

    elif "Consumption" in key:
        r = re.match("(.*km)(.+)", value)
        value = [r.group(1)] + split_value(r.group(2))

    elif "Horsepower" in key or "torque" in key:
        r = re.match("(.+)[@](.+)", value)
        value = (
            split_value(r.group(1)) + [r.group(2).strip()]
            if r != None
            else split_value(value)
        )

    elif "Top Speed" in key:
        value = value.split("or")
        value = [i.strip() for i in value]

    elif "Fuel Tank Capacity" in key:
        value = value.replace("  ", "or")
        value = value.replace("gallons", "gallons or", 1)
        value = split_value(value)

    elif "Gearbox" in key:
        value = re.match("(.+)T", value).group(1).strip()

    elif "Bore" in key:
        value = value.replace("mm", "mm or")
        value = split_value(value)

    elif "Average energy consumption" in key:
        r = re.findall("[(](.*)[)]", value)[0]
        value = [value.replace(f"({r})", "").strip(), r]

    if isinstance(value, list):
        value_dict = {}
        for el in value:
            el = el.split(" ")
            key = el.pop()
            if key == "gallons":
                key = f"{el.pop()} {key}"

            value_dict[key] = " ".join([x for x in el])

        return value_dict

    return value


################################


def scrap_specification(rows, title):
    specification = {}

    for row in rows:
        cells = row.select(".tabletd, .tabletd_right")
        if cells != []:
            key = clear_text(cells[0].text)
            value = clear_text(cells[1].text)

            value = format_values(key, value)

            if key not in keys_template.keys():
                specification[key] = value
            else:
                new_key = keys_template[key]
                specification[new_key] = value

    technical_obj = Technical(title, specification)

    return technical_obj


def scrap_version(all_versions, model_name):
    result_versions = []
    i = 1

    for version in all_versions:
        print(f"Version: {i}/{len(all_versions)}")
        i += 1
        spec_tables = []
        technical = []

        link = f"https://www.ultimatespecs.com/{version}"
        version_soup = get_body_content(link)

        # rendered_page = render_page(link)
        # version_soup = bs(rendered_page, "html.parser").body

        version = version_soup.find(class_="ficha_specs_main")
        version_name = version.find(class_="spec_title").find("span").text
        version_code = version_name.replace(model_name, "").strip()
        version_year = version_soup.find(class_="right_column").find("b").text
        version_year = get_year_period(version_year)
        specification_div = version.select(".ficha_specs_left, .ficha_specs_right")

        # Getting spec sections
        for div in specification_div:
            tables = div.select("table")
            spec_tables += tables

        # Getting specifications from spec section
        for table in spec_tables:
            table_title_div = table.find(class_="spec_title")
            if table_title_div == None:
                continue

            table_title = clear_text(table_title_div.text).replace(
                f"{version_name} ", ""
            )
            if table_title in titles_template.keys():
                table_title = titles_template[table_title]

            rows = table.select("tr")
            technical.append(scrap_specification(rows, table_title))

        version_object = Version(version_name, version_code, version_year, technical)
        result_versions.append(version_object)

    return result_versions


def scrap_versions(soup, model_name):
    engine_types = soup.select(".versions_div")
    engineTypes = []

    for engine_type in engine_types:
        print(f"{engine_type['id']}")
        versions_list = []
        versions = engine_type.find_all("tr")
        nov = len(versions)
        num_of_versions = nov - 1 if nov > 0 else 0

        if versions != []:
            versions.pop(0)
            versions = list(map(lambda x: x.find("a")["href"], versions))
            versions_list = scrap_version(versions, model_name)

        engineTypeObject = EngineType(engine_type["id"], num_of_versions, versions_list)
        engineTypes.append(engineTypeObject)

    return engineTypes


def scrap_models(model_divs):
    models = []

    for model_div in model_divs:
        link_to_model = f"https://www.ultimatespecs.com{model_div['href']}"

        print("Version scraping\n")
        soup = ""
        recaptcha = ""
        while recaptcha != None:
            rendered_page = render_page(link_to_model)
            soup = bs(rendered_page, "html.parser").body
            recaptcha = soup.find(class_="g-recaptcha")

        model_name = soup.find(class_="page_title_text").find("h1").text
        model_name = model_name.replace(" Specs", "")
        model_code = re.findall("\w\d{2}", model_name)
        model_code = model_code[0] if len(model_code) > 0 else model_name
        if "LCI" in model_name:
            model_code += " LCI"
        model_code_image = model_code.replace(" ", "_")
        model_image = (
            f"http://v-ie.uek.krakow.pl/~s215740/bmw_catalog/bmw_{model_code_image}.png"
        )
        versions = scrap_versions(soup, model_name)

        car_model = Model(model_name, model_code, model_image, versions,)

        models.append(car_model)

    return models


def scrap_generations(link):
    soup = get_body_content(link)
    generations = []

    generation_divs = soup.find_all(class_="home_models_line gene")
    gen = len(generation_divs)

    for generation_div in generation_divs:
        model_divs = generation_div.find_all("a")

        models = scrap_models(model_divs)
        num_of_models = len(models)

        production_period = generation_div.find("h2").text
        production_period = re.findall("\(.*\)", production_period)[0]
        production_period = get_year_period(production_period)

        generation_image = models[0].model_image
        generation_number = gen

        generation_obj = Generation(
            generation_number,
            generation_image,
            production_period,
            num_of_models,
            models,
        )
        generations.append(generation_obj)
        gen -= 1

    return generations


def brand_scrap(start, stop):
    fuse = -1
    brand_lines = []

    link = "https://www.ultimatespecs.com/car-specs/BMW-models"
    soup = get_body_content(link)
    home_models_line = soup.find_all(class_="home_models_line")
    model_lines = []

    # Getting all model lines
    for model_divs in home_models_line:
        models_lines = model_divs.find_all("a")
        if models_lines != []:
            model_lines += models_lines

    # Scrapping model lines
    for model_line in model_lines:
        fuse += 1
        if fuse < start:
            continue
        elif fuse > stop:
            break

        link_to_generations = f"https://www.ultimatespecs.com{model_line['href']}"
        generations = scrap_generations(link_to_generations)
        num_of_models = sum([gen.num_of_models for gen in generations])

        line_name = model_line.find("h2").string
        line_name = clear_text(line_name)
        line_image = generations[0].models[0].model_image

        line_info = model_line.find("p").text
        line_info = re.split(",", line_info)

        if len(line_info) == 3:
            line_info = [clear_text(x) for x in line_info]
            from_year = line_info[0].split(" ")[1]
        else:
            from_year = "No data"

        obj = ModelLine(
            line_name,
            "",
            line_image,
            from_year,
            len(generations),
            num_of_models,
            generations,
        )
        save_data(obj, "test")

        brand_lines.append(obj)

    return brand_lines


def main():
    brand_lines = brand_scrap(11, 11)
    cars_data = CarsData("test", brand_lines)
    save_data(cars_data, "bmw_test")


main()


def test():
    global modelName

    versions = scrap_versions(
        "https://www.ultimatespecs.com/car-specs/BMW/M52/E31-8-Series", "test"
    )
    modelName = "model"

    car_model = Model(
        modelName,
        modelName,
        f"http://v-ie.uek.krakow.pl/~s215740/bmw_catalog/bmw_test.png",
        versions,
    )

    save_data(car_model, "test")

