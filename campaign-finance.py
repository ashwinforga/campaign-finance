import csv
import json
import re
import usaddress
from collections import defaultdict, OrderedDict
# from tqdm import tqdm

# 

# contributions_file = 'CON_2024_06-02-24.csv'
contributions_file = 'contribsover500-2022and2024-06-16-24.csv'
# Reporting Entity Name,Transaction Date,Contributor/Payee,Occupation,Contributor Address,Contribution Type,Contribution Amount
candidates_file = 'Candidates-2022and2024-06-16-24.csv'

REPORTING_THRESHOLD = 500

def convert(row):
    output = {
        "Transaction Amount": row["Contribution Amount"],
        "Transaction Date": row["Transaction Date"],
        "First Name": "",
        "Middle Name": "",
        "Last Name": row["Contributor/Payee"],
        "Committee Name": row["Reporting Entity Name"],
        "Candidate Last Name": row["Reporting Entity Name"]
    }
    address = row["Contributor Address"]
    if address:
        output["Contributor Address Line 1"] = address
        # address = address.replace(",,", ",")
        # mapping = {
        #     'Recipient': 'recipient',
        #     'AddressNumber': 'address1',
        #     'AddressNumberPrefix': 'address1',
        #     'AddressNumberSuffix': 'address1',
        #     'StreetName': 'address1',
        #     'StreetNamePreDirectional': 'address1',
        #     'StreetNamePreModifier': 'address1',
        #     'StreetNamePreType': 'address1',
        #     'StreetNamePostDirectional': 'address1',
        #     'StreetNamePostModifier': 'address1',
        #     'StreetNamePostType': 'address1',
        #     'CornerOf': 'address1',
        #     'IntersectionSeparator': 'address1',
        #     'LandmarkName': 'address1',
        #     'USPSBoxGroupID': 'address1',
        #     'USPSBoxGroupType': 'address1',
        #     'USPSBoxID': 'address1',
        #     'USPSBoxType': 'address1',
        #     'BuildingName': 'address2',
        #     'OccupancyType': 'address2',
        #     'OccupancyIdentifier': 'address2',
        #     'SubaddressIdentifier': 'address2',
        #     'SubaddressType': 'address2',
        #     'PlaceName': 'city',
        #     'StateName': 'state',
        #     'ZipCode': 'zip_code',
        # }
        # tagged = usaddress.tag(address, tag_mapping=mapping)[0]
        # output["Contributor Address Line 1"] = tagged.get("address1")
        # output["Contributor Address Line 2"] = tagged.get("address2")
        # output["Contributor Address City"] = tagged["city"]
        # output["Contributor Address State"] = tagged["state"]
        # output["Contributor Address Zip Code"] = tagged["zip_code"]
    return output
    

name_to_party = {}
committee_to_party = {}
with open(candidates_file) as f:
    reader = csv.DictReader(f)
    i = 0
    for row in reader:
        candidate = row['Candidate']
        committee = row['Campaign Committee']
        candidate = re.sub(' +', ' ', candidate).strip()
        committee = re.sub(' +', ' ', committee).strip()
        if candidate:
            name_to_party[candidate] = row['Party']
        if committee:
            committee_to_party[committee] = row['Party']

"""
{'Filer ID': '5530', 'Transaction Amount': '2745.7800', 'Transaction Date': '03/29/2021', 'Last Name': '', 'First Name': '', 'Middle Name': '', 'Prefix': '', 'Suffix': '', 'Contributor Address Line 1': '', 'Contributor Address Line 2': '', 'Contributor City': '', 'Contributor State': '  ', 'Contributor Zip Code': '', 'Description': '', 'Check Number': '', 'Transaction ID': '850291', 'Filed Date': '02/06/2024', 'Election': '2024 State/Statewide Election Cycle for Candidates (June and December)', 'Report Name': 'Campaign Contribution Disclosure Report - Non-Election Year - June 30 (June December)', 'Start of Period': 'Jan  1 2021 12:00AM', 'End of Period': 'Jun 30 2021 12:00AM', 'Contributor Code': '', 'Contribution Type': '', 'Report Entity Type': 'Candidate', 'Committee Name': 'Friends of Bert Guy', 'Candidate Last Name': 'Guy', 'Candidate First Name': 'Robert', 'Candidate Middle Name': 'Wayne "Bert"', 'Candidate Prefix': '', 'Candidate Suffix': '', 'Amended': 'N', 'Contributor Employer': '', 'Contributor Occupation': '', 'Occupation Comment': '', 'Employment Information Requested': 'N'}
"""

contribs = []

class Entry(object):
    total = 0
    D = 0
    R = 0
    other = 0
    line1 = ""
    line2 = ""
    city = ""
    state = ""
    zipcode = ""
    contribs = None
    contribs_large = None
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contribs = []
        self.contribs_large = []
    def add(self, contrib):
        self.contribs.append(contrib)
        if contrib['amount'] > REPORTING_THRESHOLD:
            self.contribs_large.append(contrib)
        self.total += contrib['amount']
        if contrib['committee']:
            party = committee_to_party.get(contrib['committee'])
            if not party:
                party = name_to_party.get(contrib['candidate'])
        else:
            party = name_to_party.get(contrib['candidate'])
        if party == "Democrat":
            self.D += contrib['amount']
        elif party == "Republican":
            self.R += contrib['amount']
        elif party == "Other" or party == "Non-Partisan":
            self.other += contrib['amount']
        else:
            # Party not found
            # print(contrib['candidate'], contrib['committee'])
            # import pdb; pdb.set_trace()
            self.other += contrib['amount']
        self.line1 = contrib['line1']
        self.line2 = contrib['line2']
        self.city = contrib['city']
        self.state = contrib['state']
        self.zipcode = contrib['zipcode']

by_committee = defaultdict(Entry)
by_contributor = defaultdict(Entry)

with open(contributions_file) as f:
    reader = csv.DictReader(f)
    i = 0
    for row in reader:
        if 'Reporting Entity Name' in row:
            row = convert(row)
        amount = float(row['Transaction Amount'])
        date = row["Transaction Date"]
        committee = row["Committee Name"] or ""
        # candidate = " ".join(e for e in [row["Candidate Prefix"], row["Candidate First Name"], row["Candidate Middle Name"], row["Candidate Last Name"], row["Candidate Suffix"]] if e)
        if row.get("Candidate Last Name"):
            candidate = row["Candidate Last Name"]
            if row.get("Candidate First Name"):
                row += ", " + row["Candidate First Name"]
            if row.get("Candidate Middle Name"):
                candidate += " " + row["Middle Name"]
            if row.get("Candidate Suffix"):
                candidate += ", " + row["Candidate Suffix"]
            candidate = re.sub(' +', ' ', candidate).strip()
        else:
            candidate = ""
        # if row["Candidate Prefix"]:
        #     raise Exception(row)
        contributor = " ".join(e for e in [row["First Name"], row["Middle Name"], row["Last Name"]] if e)
        contributor = re.sub(' +', ' ', contributor).strip()
        committee = re.sub(' +', ' ', committee).strip()
        contrib = dict(
            amount=amount,
            date=date,
            committee=committee,
            candidate=candidate,
            contributor=contributor,
            line1=row.get('Contributor Address Line 1'),
            line2=row.get('Contributor Address Line 2'),
            city=row.get('Contributor Address City'),
            state=row.get('Contributor Address State'),
            zipcode=row.get('Contributor Address Zip Code')
        )
        # print(contrib)
        by_committee[committee].add(contrib)
        by_contributor[contributor].add(contrib)
        i += 1
        # if i > 10000:
        #     break

print("Done.")

# import pdb; pdb.set_trace()

by_contributor = OrderedDict(sorted(by_contributor.items(), key=lambda k: k[1].D, reverse=True))
by_committee = OrderedDict(sorted(by_committee.items(), key=lambda k: k[1].D, reverse=True))

print("Done sorting.")

with open('output/top-contributors.csv', 'w+') as out:
    writer = csv.DictWriter(out, fieldnames=['contributor', 'D', 'R', 'other', 'total', 'line1', 'line2', 'city', 'state', 'zipcode', 'committees'])
    writer.writeheader()
    i = 0
    for contributor, val in by_contributor.items():
        if not contributor: continue
        contribs = sorted(val.contribs_large, key=lambda k: k['amount'], reverse=True)
        # contribs = val.contribs_large
        committees = ""
        committees = str(len(contribs)) + " in total. " + " ".join(str(int(c['amount'])) + ':' + c['committee'] for c in contribs)
        # " ".join(str(int(c['amount'])) + ':' + c['committee'] for c in contribs if c['committee'] and c['amount'] > 99)
        # committees = len(contribs)
        writer.writerow({'contributor': contributor, 'total': val.total, 'D': val.D, 'R': val.R, 'other': val.other, 'line1': val.line1, 'line2': val.line2, 'city': val.city, 'state': val.state, 'zipcode': val.zipcode, 'committees': committees})
        i += 1
        # if i > 50:
        #     break

print('Done contribs.')

# with open('output/top-committees.csv', 'w+') as out:
#     writer = csv.DictWriter(out, fieldnames=['committee', 'total', 'contributors'])
#     writer.writeheader()
#     i = 0
#     for committee, val in by_committee.items():
#         # contribs = sorted(val.contribs, key=lambda k: k['amount'], reverse=True)
#         contributors = ""
#         # contributors = " ".join(c['contributor'] for c in contribs if c['contributor'])
#         writer.writerow({'committee': committee, 'total': val.total, 'contributors': contributors})
#         i += 1
#         if i > 1000:
#             break
        
# print("Done writing.")