#!/usr/bin/env python
# coding: utf-8

# In[21]:


import pandas as pd
import numpy as np
import re # regex for string matching

# Important Notes (READ BEFORE RUNNING CODE):
# I flagged code areas that need user interaction with *UPDATE HERE* so ctrl-F *UPDATE HERE* whenever you do a new upload
# Ctrl-F *UPDATE GIFT TRACKING* after you run the code to find the data to update in the Gift Data Tracking workbook
# At any point if you want to check the data in Excel, ctrl-F "to_csv" to find the CSV export you need. Uncomment it out, update the path & run the code.

# Process gift data one year at a time

# *UPDATE HERE* - every CSV import below

# 1. UPDATE ACCORDING TO YEAR, T3010 Donees dataset - delete all unnecessary columns first
donees = pd.read_csv(r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\T3010 - Donees - 2020 - CW - prepped.csv',
                    encoding='ANSI')

# 2. UPDATE ACCORDING TO YEAR, Master Reference Table - Gift Data from Gift Data Tracking Sheet
#    If no gift data from this year has been added to GC yet, then just upload a CSV with the headers + empty columns
reference = pd.read_csv(r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\Gift Data Tracking - Master Reference Table 2020.csv')

# 3. Masterlist report from Contenta containing all foundations we have in GC
masterlist = pd.read_csv(r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\Contenta MasterList.csv')

# 4. CRA Charities - ALl
charities = pd.read_csv(r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\Charities - All.csv',
                           encoding='ANSI')

print (donees)


# In[22]:


# Step 4

# *UPDATE HERE* - if necessary
# Use this commented-out code if unnecessary columns haven't been deleted yet
donees = pd.DataFrame(donees, columns= ['BN/Registration number', 'Donee Business number', 'Donee Name', 
                                        'City', 'Total amount gifts'])

donees.rename(columns = {"BN/Registration number": "BN", "Donee Business number": "DoneeBN",
                        "Donee Name": "DoneeName", "Total amount gifts": "ReportedAmt"}, inplace = True)
print(donees)


# In[23]:


# Add columns
# *UPDATE HERE* - Update Year accordingly
donees['Year'] = 2020
donees['Purpose'] = ""
# donees['Foundation Activity'] = [] - might not need to add now, will add in step 7

print(donees)


# In[24]:


# Step 5 - Identify and remove any funder not in GC

# Rename masterlist Funder BN to match Donees BN column so we can join the two datasets
masterlist.rename(columns = {"BusinessNumber": "BN"}, inplace = True)
keep_bn = pd.DataFrame(masterlist, columns= ['BN'])


step_five = pd.merge(donees, keep_bn, on ='BN', how ='inner')
print(step_five)


# In[25]:


# Step 6 - Identify and remove any gifts already uploaded into GC
# Only check against reference gifts from the same year as the donees data

ref_bn = reference['BN'].tolist()

# ~ = is not in, i.e. this is keeping only BNs not in ref_bn
donees = step_five[~step_five['BN'].isin(ref_bn)]

print(donees)


# In[26]:


# Update the Master Reference Table - Gift Data sheet in the Gift Data Tracking workbook with new gifting funders this year
# Might want to create a pop-up notification here to remind user to update with this value

ref_update = pd.DataFrame(masterlist, columns= ['nid', 'uuid', 'FoundationTitle', 'BN'])
new_donees = pd.DataFrame(donees, columns= ['BN'])
ref_update = pd.merge(new_donees, ref_update, on ='BN', how ='inner')
ref_update = ref_update.drop_duplicates('BN')
print(ref_update)

# *UPDATE HERE* - Update path to your own local folder, and remember to use this CSV to update the Gift Data Tracking workbook
# *UPDATE GIFT TRACKING*
ref_update.to_csv (r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\step6_update_tracking.csv', 
                   encoding = 'ANSI', index = False, header=True)


# In[27]:


# Step 7 - Foundation Activity
# Create a subset of only foundations to work with
activity = masterlist[masterlist['FoundationCategory'] == "Foundations"]
activity = pd.DataFrame(masterlist, columns= ['BN', 'FoundationActivity'])

# Count by foundation activity
step_seven = pd.merge(donees, activity, on ='BN', how ='left')

# *UPDATE GIFT TRACKING*
# Update the Master Reference Table - Gift Data sheet in the Gift Data Tracking workbook with number of grantmaking foundations
# Add up all the counts of grantmaking values
step_seven['FoundationActivity'].value_counts()


# In[28]:


# Step 8
charities.rename(columns = {"BN/Registration number:": "BN"}, inplace = True)

cra_bn = charities['BN'].tolist()

# Keep only BNs that are in the Charities - All dataset
donees = donees[donees['BN'].isin(cra_bn)]

# Reset index of rows
donees.reset_index(drop=True, inplace=True)
print(donees)


# In[29]:


# Count by foundation activity again
grantmaking_foundations = pd.merge(donees, activity, on ='BN', how ='left')
print(grantmaking_foundations)

# *UPDATE GIFT TRACKING*
# Update the Master Reference Table - Gift Data sheet in the Gift Data Tracking workbook with number of grantmaking foundations
# Add up all the counts of grantmaking values
grantmaking_foundations['FoundationActivity'].value_counts()


# In[30]:


# Step 9 - Check length of BNs, missing RR0001, etc.

donees['DoneeBN_len'] = donees['DoneeBN'].str.len()
print(donees)

# Just for QA'ing the code:
# bn_check = donees[donees['DoneeBN_len'] < 15]
# bn_check.to_csv (r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\bn_check.csv', 
#                   encoding = 'ANSI', index = False, header=True)


# In[31]:


# Check if DoneeBNs have letters in them

#donees['contains_letters'] = donees['DoneeBN'].str.extract(pat ='([a-zA-Z])') - just for reference
donees['contains_letters'] = donees['DoneeBN'].str.findall("[a-zA-Z]")


# In[32]:


# Deal with different types of BN problems
# Start with easy DoneeBNs first
# 1. 9 characters, all numeric digits -> Just add RR0001 to the end
# 2. 11 characters, ends in RR and contains_letters = ['R','R'] -> Add 0001 to the end

# Add a column that is True if the only letters in DoneeBN are RR, and False otherwise
donees['RR'] = donees['contains_letters'].apply(lambda x: x==['R', 'R'])
donees['rr'] = donees['contains_letters'].apply(lambda x: x==['r', 'r'])

# Convert all boolean to string so we can use it in our np.select below
mask = donees.applymap(type) != bool
d = {True: 'TRUE', False: 'FALSE'}
donees = donees.where(mask, donees.replace(d))

# Apply conditions using np.select
cond_12 = [(donees.DoneeBN_len == 9) & (donees.contains_letters.str.len() == 0), 
          (donees.DoneeBN_len == 11) & donees.DoneeBN.str.endswith("RR") & (donees.RR == "TRUE")]
choices_12 = [donees.DoneeBN + "RR0001", donees.DoneeBN + "0001"]

donees['DoneeBN'] = np.select(cond_12, choices_12, donees.DoneeBN)

print(donees[donees['DoneeBN_len'] == 9])

# Checkpoint - Check that RR0001 and 0001 were added correctly
# donees.to_csv (r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\9digits.csv', 
#                   encoding = 'ANSI', index = False, header=True)


# In[33]:


# 3. Replace rr with RR in DoneeBN where contains_letters = ['r', 'r'] in 15-character BNs

donees['DoneeBN'] = np.where((donees['rr'] == 'TRUE') & (donees['DoneeBN_len'] == 15),
                       donees['DoneeBN'].str.replace(r'\drr\d','RR', regex = True),
                       donees['DoneeBN'])

# 4. Delete: 15 characters where contains_letters != ['R', 'R'] or ['r', 'r']

cond_4 = [(donees.DoneeBN_len == 15) & (donees.RR == "FALSE") & (donees.rr == "FALSE")]
choices_4 = [""]
donees['DoneeBN'] = np.select(cond_4, choices_4, donees.DoneeBN)

print(donees[donees['DoneeBN_len'] == 15])


# In[34]:


# 5. 14 characters
# Find and replace RR001 with RR0001, RR000 with RR0001
# Find and replace 0R0001 with 0RR0001, 1R0001 with 1RR0001, etc.
cond_5 = [(donees.DoneeBN_len == 14) & (donees.DoneeBN.str.endswith("RR001")), 
          (donees.DoneeBN_len == 14) & (donees.DoneeBN.str.endswith("RR000")),
          (donees.DoneeBN_len == 14) & (donees.DoneeBN.str.endswith("0R0001")),
          (donees.DoneeBN_len == 14) & (donees.DoneeBN.str.endswith("1R0001")),
          (donees.DoneeBN_len == 14) & (donees.DoneeBN.str.endswith("2R0001")),
          (donees.DoneeBN_len == 14) & (donees.DoneeBN.str.endswith("3R0001")),
          (donees.DoneeBN_len == 14) & (donees.DoneeBN.str.endswith("4R0001")),
          (donees.DoneeBN_len == 14) & (donees.DoneeBN.str.endswith("5R0001")),
          (donees.DoneeBN_len == 14) & (donees.DoneeBN.str.endswith("6R0001")),
          (donees.DoneeBN_len == 14) & (donees.DoneeBN.str.endswith("7R0001")),
          (donees.DoneeBN_len == 14) & (donees.DoneeBN.str.endswith("8R0001")),
          (donees.DoneeBN_len == 14) & (donees.DoneeBN.str.endswith("9R0001"))]
choices_5 = [donees.DoneeBN.str.replace("RR001", "RR0001"), 
            donees.DoneeBN.str.replace("RR000", "RR0001"),
            donees.DoneeBN.str.replace("0R0001", "0RR0001"),
            donees.DoneeBN.str.replace("1R0001", "1RR0001"), 
            donees.DoneeBN.str.replace("2R0001", "2RR0001"),
            donees.DoneeBN.str.replace("3R0001", "3RR0001"),
            donees.DoneeBN.str.replace("4R0001", "4RR0001"),
            donees.DoneeBN.str.replace("5R0001", "5RR0001"), 
            donees.DoneeBN.str.replace("6R0001", "6RR0001"),
            donees.DoneeBN.str.replace("7R0001", "7RR0001"),
            donees.DoneeBN.str.replace("8R0001", "8RR0001"),
            donees.DoneeBN.str.replace("9R0001", "9RR0001")]

donees['DoneeBN'] = np.select(cond_5, choices_5, donees.DoneeBN)
print(donees[donees['DoneeBN_len'] == 14])

# Checkpoint
#donees.to_csv (r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\14digits.csv', 
#                   encoding = 'ANSI', index = False, header=True)


# In[35]:


# 6. Where contains_letters = ["R"] and DoneeBN_len = 14, replace R with RR

# Add a column that is True if the only letter in DoneeBN is one R, and False otherwise
donees['just_R'] = donees['contains_letters'].apply(lambda x: x==['R'])

# Convert boolean to string so we can use it in our np.select below
mask = donees.applymap(type) != bool
d = {True: 'TRUE', False: 'FALSE'}
donees = donees.where(mask, donees.replace(d))

# Replace the R with RR following Condition #6
donees['DoneeBN'] = np.where((donees['just_R'] == 'TRUE') & (donees['DoneeBN_len'] == 14),
                       donees['DoneeBN'].str.replace(r'\dR\d','RR', regex = True),
                       donees['DoneeBN'])

# Checkpoint - Check that 14-character DoneeBNs with R now have RR instead 
#donees.to_csv (r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\replaceR.csv', 
#                   encoding = 'ANSI', index = False, header=True)


# In[36]:


# Calculate contains_letters and DoneeBN_len again, now that DoneeBN has been updated
donees['DoneeBN_len'] = donees['DoneeBN'].str.len()
donees['contains_letters'] = donees['DoneeBN'].str.findall("[a-zA-Z]")

# Checkpoint - check that the new columns have the right values
#donees.to_csv (r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\bn_check2.csv', 
#                   encoding = 'ANSI', index = False, header=True)


# In[37]:


# Calculate contains_letters and DoneeBN_len again, now that DoneeBN has been updated
donees['DoneeBN_len'] = donees['DoneeBN'].str.len()
donees['contains_letters'] = donees['DoneeBN'].str.findall("[a-zA-Z]")

# Checkpoint - check that no 15-character DoneeBNs have any letters other than RR
#donees.to_csv (r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\condition7.csv', 
#                   encoding = 'ANSI', index = False, header=True)


# In[38]:


# 8. Delete DoneeBN where length < 15
cond_8 = [donees.DoneeBN_len < 15]
choices_8 = [""]
donees['DoneeBN'] = np.select(cond_8, choices_8, donees.DoneeBN)

# Checkpoint - only 15-character DoneeBNs should remain
#donees.to_csv (r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\final_15digit.csv', 
#                   encoding = 'ANSI', index = False, header=True)
print(donees[donees['DoneeBN_len'] < 15])


# In[39]:


# Step 10 - Remove gift records missing both DoneeName and DoneeBN

donees.drop(donees[(donees['DoneeName'].isnull()) & (donees['DoneeBN'].isnull())].index, inplace = True)

# Check that the correct gift records were deleted
donees.to_csv (r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\nonameBN.csv', 
                   encoding = 'ANSI', index = False, header=True)


# In[40]:


# Step 12 before 11 since part of it can be automated
# Just create a column that marks all rows with "see attached, qualified donee, voir liste, etc."
# Then export to csv and manually delete them based on judgement

# Add column that is TRUE if DoneeName contains "see attached, qualified donee, voir liste, etc."
# (?i) makes regex Case Insensitive
donees['bad_Name'] = donees['DoneeName'].str.contains("attached|qualified donee|voir la liste|voir liste(?i)")
# Add column that is TRUE if ReportedAmt contains any letters/words
donees['bad_Amt'] = donees['ReportedAmt'].str.contains("[a-zA-Z]")

# Convert boolean to string so we can print the dataframe here
mask = donees.applymap(type) != bool
d = {True: 'TRUE', False: 'FALSE'}
donees = donees.where(mask, donees.replace(d))

print(donees[donees['bad_Amt'] == "TRUE"])

# Delete unnecessary columns
donees.drop(['DoneeBN_len', 'contains_letters', 'RR', 'rr', 'just_R'], axis=1, inplace=True)

# Step 11 - Remove gift records with ReportedAmt < $0
# To be done manually since, in a few instances, a funder may report ALL of their gifts as a deductible/negative value.
# In that case, the gifts need to be converted to positive values.

# Upon export, remove gifts with ReportedAmt < $0, then remove gifts with bad_Name or bad_Amt = TRUE (if it makes sense to)
# *UPDATE HERE* - Update path to your own local folder
donees.to_csv (r'C:\Users\Catherine\Documents\Imagine Canada\Gift Import Cleaning\readyforStep11.csv', 
                   encoding = 'ANSI', index = False, header=True)

