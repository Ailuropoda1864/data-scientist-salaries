import requests
from bs4 import BeautifulSoup
import pandas as pd
import time


DEFAULT_CITIES = {'New York', 'Chicago', 'San Francisco', 'Austin', 'Seattle',
                  'Los Angeles', 'Philadelphia', 'Atlanta', 'Dallas',
                  'Pittsburgh', 'Portland', 'Phoenix', 'Denver', 'Houston',
                  'Miami'}

YOUR_CITIES = {'Boston', 'Washington DC', 'St Louis', 'San Diego',
               'San Antonio', 'Columbus', 'Sacramento', 'Charlotte', 'Memphis',
               'Detroit', 'Nashville', 'Jacksonville', 'Indianapolis',
               'Fort Worth', 'Charlotte', 'El Paso', 'Oklahoma City',
               'Las Vegas', 'Louisville', 'Milwaukee', 'Albuquerque', 'Tucson',
               'Kansas City', 'Mesa', 'Colorado Springs', 'Raleigh', 'Omaha',
               'Virginia Beach', 'Minneapolis', 'New Orleans', 'Tampa',
               'San Jose', 'Baltimore', 'Fresno', 'Oakland', 'Tulsa', 'Madison',
               'Arlington', 'Wichita', 'Cleveland', 'Aurora', 'Honolulu',
               'Orlando', 'Anchorage', 'Des Moines', 'Salt Lake City',
               'Lexington', 'Cincinnati', 'Newark', 'Durham', 'Buffalo',
               'Baton Rouge', 'Richmond', 'Boise', 'Birmingham', 'Little Rock',
               'Grand Rapids', 'Worcester', 'Providence', 'Sioux Falls',
               'Jackson', 'Hartford', 'Bridgeport', 'Jersey City', 'Charleston',
               'Billings', 'Fargo', 'Augusta'}

URL = "http://www.indeed.com/jobs"
PARAMS = {'q': 'data scientist', 'radius': '100'}
MAX_RESULTS_PER_CITY = 1000
CSV_NAME = 'indeed.csv'
DEDUP_CSV_NAME = 'indeed_dedup.csv'


def main():
    print('Current system time: {}'.format(time.ctime()))

    # scrape data and save to CSV_NAME
    start_time = time.time()
    for city in DEFAULT_CITIES | YOUR_CITIES:

        for start in range(0, MAX_RESULTS_PER_CITY, 10):
            url_params = PARAMS.copy()
            url_params.update({'l': city, 'start': start})
            scrape_page_to_csv(URL, url_params, CSV_NAME)
        print('Finished scraping {}'.format(city))
    total_time = (time.time() - start_time) / 60
    print('Scraping run time: {:.1f} minutes'.format(total_time))

    # remove duplicates and save to DEDUP_CSV_NAME
    remove_duplicates()
    print('Script finished at {}\n'.format(time.ctime()))


def scrape_page_to_csv(url, url_params, csv):
    """
    extract information from a results page and save to an existing csv
    :param url: url template
    :param url_params: a dictionary to feed to params argument in requests.get
    :param csv:
    :return: a pandas dataframe containing the extracted information
    """
    # create a empty dictionary to store extracted information
    scraped_data = {'location': [],
                    'company': [],
                    'title': [],
                    'salary': [],
                    'description': [],
                    'review': [],
                    'star': []}

    html = requests.get(url, params=url_params)

    # make sure the response status is ok
    assert html.status_code == requests.codes.ok

    soup = BeautifulSoup(html.text, 'lxml')
    results = extract_results(soup)

    # append extracted info to the correspond list
    for result in results:
        scraped_data['location'].append(extract_location(result))
        scraped_data['company'].append(extract_company(result))
        scraped_data['title'].append(extract_title(result))
        scraped_data['salary'].append(extract_salary(result))
        scraped_data['description'].append(extract_description(result))
        scraped_data['review'].append(extract_review(result))
        scraped_data['star'].append(extract_star(result))

    # convert the dictionary to a pandas dataframe
    df = pd.DataFrame(scraped_data)

    # append the dataframe (without the header) to the existing CSV_NAME
    with open(csv, 'a') as f:
        df.to_csv(f, header=False, index=False)


def remove_duplicates():
    """remove duplicates in CSV_NAME and save to DEDUP_CSV_NAME"""
    df = pd.read_csv(CSV_NAME, dtype={'salary': object})
    nrows_before = df.shape[0]
    df.drop_duplicates(subset=['company', 'description',
                               'location', 'salary', 'title'],
                       keep='last', inplace=True)
    nrows_after = df.shape[0]
    df.to_csv(DEDUP_CSV_NAME, index=False)
    print('{} rows remain after removing duplicates from {} rows.'.format(
        nrows_after, nrows_before))
    print('{} rows have salary info; {} rows have yearly salary info.'.format(
        df.salary.notnull().sum(), df.salary.str.contains('year').sum()))


def extract_results(soup):
    return soup.find_all('div', class_='result')


# the following functions returns the specified information from *one* result
# div, or, if error is encountered, return None
def extract_location(result):
    """extract job location"""
    try:
        location = result.find('span', class_='location').get_text().strip()
        return location
    except:
        return None


def extract_company(result):
    """extract the name of the company"""
    try:
        company = result.find('span', class_='company').get_text().strip()
        return company
    except:
        return None


def extract_title(result):
    """extract the job title"""
    try:
        title = result.find('a', attrs={'data-tn-element': "jobTitle"}).get(
            'title')
        return title
    except:
        return None


def extract_salary(result):
    """extract the salary"""
    try:
        salary = result.find('td', class_='snip').\
            find('span', class_='no-wrap').\
            get_text().strip()
        return salary
    except:
        return None


def extract_description(result):
    """extract job description snippet"""
    try:
        description = result.find('span', class_='summary').get_text().strip()
        return description
    except:
        return None


def extract_review(result):
    """extract the number of reviews for the company"""
    try:
        review = result.find('a', attrs={'data-tn-element': "reviewStars"})
        review = review.find('span', class_="slNoUnderline")
        review = review.get_text().strip()
        # extract only the number
        review = review.replace(',', '').replace(' reviews', '')
        return review
    except:
        return None


def extract_star(result):
    """extract a number (width) that is proportional to the number of stars
    shown for the company"""
    try:
        # the 'style' attribute dictates how many stars are filled with color
        star = result.find('span', class_='rating').get('style')
        # extract only the number
        star = star.replace('width:', '').replace('px', '')
        return star
    except:
        return None


if __name__ == '__main__':
    main()
