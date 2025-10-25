from pymongo import MongoClient
import pprint

uri = "mongodb://localhost:27017/"
client = MongoClient(uri)

# Access your database and collection
db = client['live_dashborads'] 
collection = db['esg_live_dashboard']

# Define the query filter
query = { "company_name": "NTPC Ltd" }

# Execute the find command with the query
results = collection.find(query)

# Loop through and print each matching document
print("Found the following documents for 'NTPC Ltd':\n")
for document in results:
    pprint.pprint(document)

client.close()