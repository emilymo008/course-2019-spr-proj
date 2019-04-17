import dml
import prov.model
import datetime
import uuid
import pandas as pd 
import numpy as np
import math

from dateutil.parser import parse


def percentage_change(start, end):
  diff = end - start
  if (start == 0):
    return float(diff)
  percentage = diff / start
  return float(percentage)
def running_mean(x, N):
  cumsum = np.cumsum(np.insert(x, 0, 0)) 
  return (cumsum[N:] - cumsum[:-N]) / float(N)

class constraint_satisfaction(dml.Algorithm):
  contributor = 'signior_jmu22_zhangyb'
  reads = ['signior_jmu22_zhangyb.power_plants_established_date_by_country', 'signior_jmu22_zhangyb.carbon_emissions', 'signior_jmu22_zhangyb.population']
  writes = ['signior_jmu22_zhangyb.countries_change_in_carbon_after_year']

  @staticmethod
  def execute(trial = False):
    startTime = datetime.datetime.now()

    # Set up database connection
    client = dml.pymongo.MongoClient()
    repo = client.repo
    repo.authenticate('signior_jmu22_zhangyb', 'signior_jmu22_zhangyb')

    population = list(repo.signior_jmu22_zhangyb.population.find())

    power_plants_by_country_year = list(repo.signior_jmu22_zhangyb.power_plants_established_date_by_country.find())

    carbon_emissions_by_country_year = list(repo.signior_jmu22_zhangyb.carbon_emissions.find())

    df_power_plants = pd.DataFrame(power_plants_by_country_year)
    df_carbon_emissions = pd.DataFrame(carbon_emissions_by_country_year)
    df_population = pd.DataFrame(population)

    power_plants_dict = df_power_plants.to_dict(orient='records')
    carbon_emissions_dict = df_carbon_emissions.to_dict(orient='records')
    population_dict = df_population.to_dict(orient='records')

    # country formatting
    for row in carbon_emissions_dict:
      if row.get('Country Name') == 'Korea, Dem. People’s Rep.':
        row['Country Name'] = 'North Korea'
      elif row.get('Country Name') == 'Korea, Rep.':
        row['Country Name'] = 'South Korea'
      elif row.get('Country Name') == 'United States':
        row['Country Name'] = 'United States of America'
    for row in population_dict:
      if row.get('Country Name') == 'Korea, Dem. People’s Rep.':
        row['Country Name'] = 'North Korea'
      elif row.get('Country Name') == 'Korea, Rep.':
        row['Country Name'] = 'South Korea'
      elif row.get('Country Name') == 'United States':
        row['Country Name'] = 'United States of America'
    for row in carbon_emissions_dict:
      for year in range(1960, 2015):
        if (math.isnan(row[str(year)])):
          row[str(year)] = 0

    # grabs all of the country names in power_plants 
    countries_with_power_plant_data = [row.get('country') for row in power_plants_dict]

    # List of all countries with emission data and fossil fuel power plants established
    countries_with_both = [row.get('Country Name') for row in carbon_emissions_dict if row.get('Country Name') in countries_with_power_plant_data]

    # get all entries with countries in both sets
    power_plants_dict = [row for row in power_plants_dict if row.get('country') in countries_with_both]
    carbon_emissions_dict = [row for row in carbon_emissions_dict if row.get('Country Name') in countries_with_both]
    population_dict = [row for row in population_dict if row.get('Country Name') in countries_with_both]

    # with open('test.txt', 'w') as f:
    #   print(power_plants_dict, file=f)  # Python 3.x
    # with open('test2.txt', 'w') as f:
    #   print(carbon_emissions_dict, file=f)  # Python 3.x
    # with open('out.txt', 'w') as f:
    #   print(population_dict, file=f)  # Python 3.x

    # results of the constrait solving will be entered here
    resulting_dataset = []

    for country in countries_with_both:
      curr_row = {}
      curr_row['country'] = country
      curr_row['data'] = []
      carbon_emissions_row = list(filter(lambda row: row['Country Name'] == country, carbon_emissions_dict))[0]
      power_plant_data_row = list(filter(lambda row: row['country'] == country, power_plants_dict))[0]
      population_data_row = list(filter(lambda row: row['Country Name'] == country, population_dict))[0]

      power_plant_years = sorted(power_plant_data_row['years'])

      for curr_year in power_plant_years:
        if (curr_year > 2014):
          break
        if (carbon_emissions_row.get(str(curr_year)) is None or population_data_row.get(str(curr_year)) is None or carbon_emissions_row.get(str(curr_year - 1)) is None or population_data_row.get(str(curr_year - 1)) is None or carbon_emissions_row.get(str(curr_year + 1)) is None or population_data_row.get(str(curr_year + 1)) is None):
          continue
        year_curr = carbon_emissions_row.get(str(curr_year)) * population_data_row.get(str(curr_year))
        prev_year = carbon_emissions_row.get(str(curr_year - 1)) * population_data_row.get(str(curr_year - 1))
        post_year = carbon_emissions_row.get(str(curr_year + 1)) * population_data_row.get(str(curr_year + 1))
        
        percentage_change_pre = percentage_change(prev_year, year_curr)
        percentage_change_post = percentage_change(year_curr, post_year)
        constraint_satisfied = percentage_change_pre < percentage_change_post
        curr_row['data'].append({str(curr_year): (percentage_change_pre, percentage_change_post), 'constraint satisfied': constraint_satisfied})

      resulting_dataset.append(curr_row)
    
    repo.dropCollection("countries_change_in_carbon_after_year")
    repo.createCollection("countries_change_in_carbon_after_year")
    repo['signior_jmu22_zhangyb.countries_change_in_carbon_after_year'].insert_many(resulting_dataset)
    repo['signior_jmu22_zhangyb.countries_change_in_carbon_after_year'].metadata({'complete': True})
        
    print(repo['signior_jmu22_zhangyb.countries_change_in_carbon_after_year'].metadata())

    repo.logout()

    endTime = datetime.datetime.now()
    return {"start": startTime, "end": endTime}
    
  
  @staticmethod
  def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
    return doc


constraint_satisfaction.execute()

    
